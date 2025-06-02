from dataclasses import asdict
from logging import Logger
from typing import List, Dict
from aiohttp import ClientSession
from starlette.datastructures import Headers

from api.api_client import APIClient
from api.models import HTTPMethod
from models import Operation, RuleOperation, RuleData

api_client = APIClient()


class BulkOperations:
    def __init__(self, logger: Logger, client: ClientSession):
        self.logger = logger
        self.client = client

    @staticmethod
    def _parse_rule_data(rule_data: RuleData) -> Dict[str, str]:
        rule_dict = dict()
        if rule_data and rule_data.expired_date:
            rule_dict = asdict(rule_data)
            if rule_dict.get("expired_date"):
                rule_dict["expired_date"] = rule_dict["expired_date"].isoformat().replace("+00:00", "Z")

        return rule_dict if rule_dict else rule_data

    async def process_operation(self, rule_operation: RuleOperation, customer_id: str):
        rule_data = self._parse_rule_data(rule_operation.rule_data)
        if rule_operation.operation == Operation.CREATE:
            return await api_client.request(self.client, HTTPMethod.POST, "customers/rules",
                                            headers=Headers({"X-User-ID": customer_id}), json=rule_data)

        elif rule_operation.operation == Operation.UPDATE:
            return await api_client.request(self.client, HTTPMethod.PUT, "customers/rules",
                                            headers=Headers({"X-User-ID": customer_id}), json=rule_data)
        else:  # rule_operation.operation == Operations.DELETE:
            return await api_client.request(self.client, HTTPMethod.DELETE,
                                            f"customers/rules/{rule_operation.rule_name}",
                                            headers=Headers({"X-User-ID": customer_id}))

    async def handle_results(self, results, operations: List[RuleOperation]) -> dict:
        successful_responses = []
        errors = []

        for index, result in enumerate(results):
            operation = operations[index]

            if isinstance(result, Exception):
                self.logger.error(f"operation {operation.operation.name} failed with exception: {result}")
                errors.append({
                    "operation": operation.operation.name,
                    "customer_id": operation.customer_id,
                    "error": str(result)
                })
            elif result.ok is not True:
                error_detail = await result.text()
                self.logger.error(f"operation {operation.operation.name} failed with HTTP {result.status}: {error_detail}")
                errors.append({
                    "operation": operation.operation.name,
                    "customer_id": operation.customer_id,
                    "error": f"Error {result.status}: {error_detail}"
                })
            else:
                data = await result.json()
                successful_responses.append({
                    "operation": operation.operation.name,
                    "customer_id": operation.customer_id,
                    "result": data
                })

        response_payload = {"successful": successful_responses, "errors": errors}
        return response_payload
