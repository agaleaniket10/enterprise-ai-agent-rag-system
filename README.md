# Enterprise AI Agent on AWS

[![CI](https://github.com/agaleaniket10/enterprise-ai-agent-rag-system/actions/workflows/ci.yml/badge.svg)](https://github.com/agaleaniket10/enterprise-ai-agent-rag-system/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/) [![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/) [![Tests](https://img.shields.io/badge/tests-54%20passing-brightgreen.svg)]()

An enterprise-grade multi-agent AI system built on AWS Bedrock. A router agent classifies incoming queries by intent and dispatches to specialist sub-agents — each backed by dedicated Lambda tools and a shared Lambda Layer.

---

## Architecture

```
User
  │
  ▼
chat.py / Step Functions
  │
  ▼
┌─────────────────────────────────────────────────────┐
│              Router Agent (Claude Haiku)            │
│         Keyword intent classification               │
│   billing → BillingAgent                           │
│   support → SupportAgent                           │
│   order   → OrderAgent                             │
│   unknown → GeneralAgent (fallback)                │
└──────────┬──────────────┬──────────────┬───────────┘
           │              │              │
    ┌──────▼──────┐ ┌─────▼──────┐ ┌────▼────────┐
    │ Order Agent │ │Support Agent│ │Billing Agent│
    │─────────────│ │─────────────│ │─────────────│
    │order_status │ │create_ticket│ │ get_invoice │
    │order_history│ │escalate_issue│ │process_refund│
    │cancel_order │ └─────────────┘ └─────────────┘
    └─────────────┘
           │
    ┌──────▼──────────────────────────────┐
    │     Lambda Layer: agent_commons     │
    │  extract_param · build_response     │
    │  validate_required · build_error    │
    └─────────────────────────────────────┘
```

---

## Tools (7 Lambda functions)

| Agent | Tool | Description |
|---|---|---|
| Order | `tool_order_status` | Get current status + tracking for an order |
| Order | `tool_order_history` | List last N orders for a customer |
| Order | `tool_cancel_order` | Cancel an order (with eligibility check) |
| Support | `tool_create_ticket` | Create a support ticket with validation |
| Support | `tool_escalate_issue` | Escalate a ticket with SLA routing |
| Billing | `tool_get_invoice` | Retrieve invoice details for an order |
| Billing | `tool_process_refund` | Process a refund with method selection |

---

## Lambda Layer: agent_commons

All handlers share a single Lambda Layer (`layers/agent_commons/`) that provides:

- `extract_param` / `extract_params` — parse Bedrock Agents parameter lists
- `build_response` / `build_error` — structured Bedrock-compatible response envelopes
- `validate_required` / `validate_enum` / `validate_max_length` — input validation
- `utc_now` / `log_event` — shared utilities

This keeps each handler to ~40 lines and ensures consistent error responses across all tools.

---

## Error Handling

Every Lambda handler follows this pattern:

```python
try:
    # validate inputs
    errors = validate_required(params, "field1", "field2")
    if errors:
        return build_error(ag, fn, "Validation failed", "VALIDATION_ERROR", errors)
    # business logic
    return build_response(ag, fn, result)
except SpecificError as e:
    logger.error("...")
    return build_error(ag, fn, "Specific message", "SPECIFIC_CODE")
except Exception as e:
    logger.exception("Unexpected error")
    return build_error(ag, fn, "Internal server error", "INTERNAL_ERROR", [str(e)])
```

The router also implements a **fallback chain**: if a specialist agent fails or is unconfigured, it retries with the general agent before returning a 500.

---

## Step Functions Workflow

The Step Functions state machine (`stepfunctions/workflow.asl.json`) includes:

- **Retry logic** — 3 attempts with exponential backoff on Lambda errors
- **Intent-based routing** — `Choice` state branches on `order / billing / support`
- **Error states** — dedicated `HandleValidationError` and `HandleRoutingError` states with user-friendly messages

---

## Project Structure

```
enterprise-ai-agent-aws/
├── lambdas/
│   ├── tool_order_status/       # Get order status + tracking
│   ├── tool_order_history/      # List customer order history
│   ├── tool_cancel_order/       # Cancel eligible orders
│   ├── tool_create_ticket/      # Create support tickets
│   ├── tool_escalate_issue/     # Escalate tickets with SLA routing
│   ├── tool_get_invoice/        # Retrieve invoice details
│   ├── tool_process_refund/     # Process refunds
│   └── trigger_agent/           # Multi-agent router (Step Functions entry)
├── layers/
│   └── agent_commons/python/
│       └── agent_commons.py     # Shared utilities Lambda Layer
├── tests/
│   └── unit/
│       ├── test_order_tools.py  # 16 tests
│       ├── test_support_tools.py # 15 tests
│       ├── test_billing_tools.py # 13 tests
│       └── test_router.py       # 10 tests (54 total)
├── stepfunctions/
│   └── workflow.asl.json        # Multi-agent routing with retry + error handling
├── opensearch/
│   ├── index_setup.py           # Create KB index
│   └── teardown.py              # Cleanup script
├── bedrock/
│   └── agent_config.md          # Agent configuration reference
├── chat.py                      # Interactive CLI
├── .env.example                 # Environment variable template
├── requirements.txt
├── requirements-dev.txt
└── Makefile
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in agent IDs for each specialist agent
```

### 3. Deploy Lambda Layer

```bash
cd layers/agent_commons
zip -r agent_commons_layer.zip python/
aws lambda publish-layer-version \
  --layer-name agent-commons \
  --zip-file fileb://agent_commons_layer.zip \
  --compatible-runtimes python3.10 python3.11 python3.12
```

### 4. Deploy Lambda functions

```bash
# Example for one function — repeat for each tool
cd lambdas/tool_order_status
zip function.zip handler.py
aws lambda create-function \
  --function-name tool-order-status \
  --runtime python3.11 \
  --role arn:aws:iam::<ACCOUNT_ID>:role/LambdaExecutionRole \
  --handler handler.lambda_handler \
  --layers arn:aws:lambda:<REGION>:<ACCOUNT_ID>:layer:agent-commons:<VERSION> \
  --zip-file fileb://function.zip
```

### 5. Create Bedrock Agents

Create one agent per domain (Order, Support, Billing, General) and configure action groups pointing to the corresponding Lambda functions. See `bedrock/agent_config.md` for full configuration reference.

### 6. Chat with the system

```bash
python chat.py
```

---

## Running Tests

```bash
pip install -r requirements-dev.txt
make test          # run all 54 unit tests
make test-cov      # with coverage report
```

---

## IAM Roles Required

| Role | Trust | Permissions |
|---|---|---|
| `BedrockAgentRole` | `bedrock.amazonaws.com` | `bedrock:*` |
| `LambdaExecutionRole` | `lambda.amazonaws.com` | `AWSLambdaBasicExecutionRole` |

---

## License

MIT — see [LICENSE](LICENSE).
