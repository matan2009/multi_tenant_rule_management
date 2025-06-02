import os

from dotenv import load_dotenv

load_dotenv()

# app settings
LOCALHOST = "127.0.0.1"
PORT = 8000
BASE_URL = "http://localhost:8000/multi_tenant_rule_management/"


# DB settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "multi_tenant_rule_management")

# Rate Limiter Configurations
DEFAULT_INTERVAL_TIME = 600
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_PERIOD = 60
