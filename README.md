# multi_tenant_rule_management

## Project Description

Rule Management API built with FastAPI. It enables customers to manage IP-based rules that can be created, updated, deleted, and queried. The system supports bulk operations, expiration handling, audit logging, and rate limiting.

## Features
- Create / update / delete rules per customer
- Bulk operations (create, update, delete in a single request)
- Automatic expiration cleanup of rules
- Audit logging for all rule changes
- Per-customer rate limiting (default: 100 req/min)
- Dockerized for easy deployment
- User Identification via `X-User-ID` header

## Technologies Used

- **FastAPI** – High-performance Python web framework
- **MongoDB** – NoSQL database for storing rules and audit logs
- **Redis** – Used for rate limiting
- **Docker & Docker Compose** – Containerized development environment
- **Uvicorn** – ASGI server for running the app
- **asyncio** / **aiohttp** – Asynchronous tasks and HTTP clients
- **Dataclasses** – Data modeling and validation

## ✅ Prerequisites

- Docker & Docker Compose
- Python 3.8+

## 🏗️ Build & Run the Services
### Step 1: Clone the repository
```
$ git clone https://github.com/matan2009/stock-exchange-quote.git
$ cd stock-exchange-quote
```
#### Step 2: Build and start the services
```
$ docker-compose up --build
```

## Headers Requirement
All modifying requests (get, create, update, delete, bulk) must include the following header:
```
X-User-ID: <string>
```

## The services will be available at:
```
GET /multi_tenant_rule_management/customers/rules/{rule_name} — Get a specific rule

POST /multi_tenant_rule_management/customers/rules — Create a new rule

PUT /multi_tenant_rule_management/customers/rules — Update an existing rule

DELETE /multi_tenant_rule_management/customers/rules/{rule_name} — Delete a rule

POST /multi_tenant_rule_management/rules/bulk - Bulk create, update, delete rules

```
- Rate Limiting: 100 requests/min per customer by default (returns HTTP 429 if exceeded)
- Audit Log: Automatically tracks create/update/delete actions per rule
- Automatic Cleanup – Periodic background task deletes expired rules

