import asyncio
from datetime import datetime
import logging.config
from pymongo.asynchronous.collection import AsyncCollection

from logger.configurations import LOGGING_DICT_CONFIG
from settings import DEFAULT_INTERVAL_TIME

logging.config.dictConfig(LOGGING_DICT_CONFIG)
logger = logging.getLogger(__name__)


class ExpiredRuleCleaner:
    def __init__(self, rules_collection: AsyncCollection, interval=DEFAULT_INTERVAL_TIME):
        self.rules_collection = rules_collection
        self.interval = interval

    async def cleanup_once(self):
        now = datetime.utcnow()
        result = await self.rules_collection.delete_many({"expired_date": {"$lt": now}})
        logger.error(f"cleanup task deleted {result.deleted_count} expired rules")

    async def clean_expired_rules(self):
        while True:
            try:
                await self.cleanup_once()
            except Exception as ex:
                logger.error(f"cleanup task raised an unexpected error: {ex}")
            await asyncio.sleep(self.interval)
