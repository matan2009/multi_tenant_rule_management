from dataclasses import asdict
from datetime import datetime
from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException
from pymongo.asynchronous.collection import AsyncCollection

from models import RuleData, Operation


async def _log_audit(collection: AsyncCollection, rule_name: str, action: Operation, customer_id: str,
                     details: Optional[dict] = None):
    audit_entry = {
        "rule_name": rule_name,
        "action": action.value,
        "timestamp": datetime.utcnow(),
        "customer_id": customer_id,
        "details": details or {},
    }
    await collection.insert_one(audit_entry)


async def get_rule(rules_collection: AsyncCollection, rule_name: str, customer_id: str) -> RuleData:
    record_filter = {"customer_id": customer_id, "name": rule_name}
    rule = await rules_collection.find_one(record_filter)
    if not rule:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Rule not found for the requested customer "
                                   f"[customer_id={customer_id}]"
                                   f"[rule_name={rule_name}]")

    expired_date = rule.get("expired_date")
    expired_str = expired_date.isoformat() if expired_date else None
    return RuleData(rule["name"], rule["description"], rule["ip"], expired_str)


async def add_rule(rules_collection: AsyncCollection, audit_collection: AsyncCollection,
                   rule: RuleData, customer_id: str) -> str:
    existing_rule = await rules_collection.find_one({"name": rule.name, "customer_id": customer_id})
    if existing_rule:
        raise HTTPException(status_code=HTTPStatus.CONFLICT,
                            detail="Rule with this name already exists for this customer")

    now = datetime.utcnow()
    rule_data = {**asdict(rule), "customer_id": customer_id, "update_date": now, "creation_date": now}
    result = await rules_collection.insert_one(rule_data)

    await _log_audit(audit_collection, rule.name, Operation.UPDATE, customer_id,
                     {"description": rule.description, "ip": rule.ip, "expired_date": rule.expired_date})

    return str(result.inserted_id)


async def edit_rule(rules_collection: AsyncCollection, audit_collection: AsyncCollection,
                    rule: RuleData, customer_id: str) -> bool:
    now = datetime.utcnow()
    update_data = {**asdict(rule), "update_date": now, "customer_id": customer_id}

    result = await rules_collection.update_one({"name": rule.name, "customer_id": customer_id}, {"$set": update_data})

    if result.matched_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Rule not found for the requested customer "
                                                                     f"[customer_id={customer_id}]"
                                                                     f"[rule_name={rule.name}]")

    await _log_audit(audit_collection, rule.name, Operation.UPDATE, customer_id,
                     {"description": rule.description, "ip": rule.ip, "expired_date": rule.expired_date})
    return True


async def delete_rule(rules_collection: AsyncCollection, audit_collection: AsyncCollection,
                      rule_name: str, customer_id: str) -> bool:
    result = await rules_collection.delete_one({"name": rule_name, "customer_id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Rule not found for the requested customer "
                                                                     f"[customer_id={customer_id}]"
                                                                     f"[rule_name={rule_name}]")
    await _log_audit(audit_collection, rule_name, Operation.DELETE, customer_id)
    return True
