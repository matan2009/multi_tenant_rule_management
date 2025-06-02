import asyncio
import logging.config
import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from http import HTTPStatus
import uvicorn
from aiohttp import ClientSession

from fastapi import FastAPI, Request, Depends
from pymongo import AsyncMongoClient
from starlette.responses import JSONResponse

import dal.db
from services.bulk_operations import BulkOperations
from services.cleanup import ExpiredRuleCleaner
from utils.rate_limiter import limit_rate
from utils.validators import validate_rule_data, validate_rule_name, get_customer_id
from logger.configurations import LOGGING_DICT_CONFIG
from models import RuleData, BulkOperationsRequest
from settings import LOCALHOST, PORT, DB_NAME


logging.config.dictConfig(LOGGING_DICT_CONFIG)
logger = logging.getLogger(__name__)

mongo_client = AsyncMongoClient(os.environ["MONGO_URI"])
db_client = mongo_client[DB_NAME]


@asynccontextmanager
async def lifespan(application: FastAPI):
    session = ClientSession()
    application.state.aiohttp_session = session
    application.state.rules_collection = db_client.get_collection("rules")
    application.state.audit_collection = db_client.get_collection("audit_logs")
    asyncio.create_task(ExpiredRuleCleaner(application.state.rules_collection).clean_expired_rules())
    yield

    await session.close()

app = FastAPI(lifespan=lifespan)


@app.get('/multi_tenant_rule_management/customers/rules/{rule_name}')
@validate_rule_name("rule_name")
async def get_rule(request: Request, rule_name: str, customer_id: str = Depends(get_customer_id)) -> JSONResponse:
    logger.info(f"Got a request to get a rule [customer_id={customer_id}][rule_name={rule_name}]")
    rule = await dal.db.get_rule(request.app.state.rules_collection, rule_name, customer_id)
    return JSONResponse(status_code=HTTPStatus.OK, content={"rule": asdict(rule)})


@app.post('/multi_tenant_rule_management/customers/rules')
@limit_rate
@validate_rule_data()
async def create_rule(request: Request, rule: RuleData, customer_id: str = Depends(get_customer_id)):
    logger.info(f"Got a request to create a new rule [customer_id={customer_id}]")
    rule_id = await dal.db.add_rule(request.app.state.rules_collection, request.app.state.audit_collection,
                                    rule, customer_id)
    logger.info(f"A new rule was added successfully [customer_id={customer_id}][rule_id={rule_id}]")
    return JSONResponse(status_code=HTTPStatus.OK, content={"rule_id": rule_id})


@app.put('/multi_tenant_rule_management/customers/rules')
@limit_rate
@validate_rule_data()
async def edit_rule(request: Request, rule: RuleData, customer_id: str = Depends(get_customer_id)):
    logger.info(f"Got a request to edit an existing rule [customer_id={customer_id}][rule_name={rule.name}]")
    success = await dal.db.edit_rule(request.app.state.rules_collection, request.app.state.audit_collection,
                                     rule, customer_id)
    logger.info(f"The rule was edited successfully [customer_id={customer_id}][rule_name={rule.name}]")
    return JSONResponse(status_code=HTTPStatus.OK, content={"success": success})


@app.delete('/multi_tenant_rule_management/customers/rules/{rule_name}')
@limit_rate
@validate_rule_name("rule_name")
async def delete_rule(request: Request, rule_name: str, customer_id: str = Depends(get_customer_id)):
    logger.info(f"Got a request to edit an existing rule [customer_id={customer_id}][rule_name={rule_name}]")
    success = await dal.db.delete_rule(request.app.state.rules_collection, request.app.state.audit_collection,
                                       rule_name, customer_id)
    logger.info(f"The rule was deleted successfully [customer_id={customer_id}][rule_name={rule_name}]")
    return JSONResponse(status_code=HTTPStatus.OK, content={"success": success})


@app.post('/multi_tenant_rule_management/rules/bulk')
@limit_rate
async def bulk_operations(request: Request, bulk_operations_request: BulkOperationsRequest,
                          customer_id: str = Depends(get_customer_id)):
    logger.info(f"Got a request to preform bulk of operations")
    bulk_operations_service = BulkOperations(logger, request.app.state.aiohttp_session)
    tasks = [bulk_operations_service.process_operation(op, customer_id) for op in bulk_operations_request.operations]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    response_payload = await bulk_operations_service.handle_results(results, bulk_operations_request.operations)
    return JSONResponse(status_code=HTTPStatus.MULTI_STATUS, content=response_payload)
