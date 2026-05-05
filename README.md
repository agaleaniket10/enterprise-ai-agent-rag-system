# Enterprise AI Agent on AWS

[![CI](https://github.com/agaleaniket10/enterprise-ai-agent-rag-system/actions/workflows/ci.yml/badge.svg)](https://github.com/agaleaniket10/enterprise-ai-agent-rag-system/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)

An enterprise-grade AI agent built on **Amazon Bedrock Agents** (Claude Haiku 4.5) with tool-use via AWS Lambda, workflow orchestration via Step Functions, and a RAG knowledge base backed by OpenSearch.

The agent handles two real enterprise workflows — order status lookups and support ticket creation — demonstrating how to wire Bedrock Action Groups to serverless backends with proper IAM, error handling, and session management.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (chat.py CLI)                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  invoke_agent()
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Amazon Bedrock Agent (Claude Haiku 4.5)                │
│                                                                     │
│  System prompt: enterprise assistant with tool-use instructions     │
│  Session management: unique session ID per conversation             │
│                                                                     │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐   │
│  │   Action Groups      │    │        Knowledge Base            │   │
│  │                     │    │                                  │   │
│  │  OrderStatus ───────┼──▶ │  OpenSearch (kNN vector index)   │   │
│  │  (order_id → status)│    │  Titan Embed v1 (1536-dim)       │   │
│  │                     │    │  RAG over enterprise docs        │   │
│  │  CreateTicket ──────┼──▶ └──────────────────────────────────┘   │
│  │  (title + desc      │                                           │
│  │   → ticket_id)      │                                           │
│  └──────────┬──────────┘                                           │
└─────────────┼───────────────────────────────────────────────────────┘
              │  Lambda invoke
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AWS Lambda Functions                           │
│                                                                     │
│  order-status-tool     ── returns order status + ETA               │
│  create-ticket-tool    ── creates ticket, returns TKT-XXXXXX ID    │
│  trigger_agent         ── Step Functions entry point               │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              AWS Step Functions (workflow.asl.json)                 │
│  Orchestrates agent invocation for async / batch workflows          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

**Why Bedrock Agents over a custom LangChain agent?**
Bedrock Agents handles session state, tool routing, and retry logic natively — no custom orchestration code. This is the production pattern AWS recommends for enterprise deployments.

**Why Claude Haiku 4.5 via inference profile?**
The `us.*` inference profile routes across `us-east-1`, `us-east-2`, and `us-west-2` automatically — built-in regional failover with no extra code.

**Why Step Functions alongside the CLI?**
The CLI (`chat.py`) is for interactive use. Step Functions (`workflow.asl.json`) enables the same agent to be triggered from async pipelines, scheduled jobs, or other AWS services — showing the architecture scales beyond a chatbot.

---

## Project Structure

```
enterprise-ai-agent-rag-system/
├── chat.py                          # Interactive CLI — streams agent responses
├── bedrock/
│   └── agent_config.md              # Agent setup reference (model, action groups, KB)
├── lambdas/
│   ├── tool_order_status/
│   │   └── handler.py               # Returns order status + ETA by order_id
│   ├── tool_create_ticket/
│   │   └── handler.py               # Creates support ticket, returns TKT-XXXXXX
│   └── trigger_agent/
│       └── handler.py               # Step Functions entry point for async invocation
├── opensearch/
│   ├── index_setup.py               # Creates kNN vector index for knowledge base
│   └── teardown.py                  # Deletes all AWS resources (stops billing)
├── stepfunctions/
│   └── workflow.asl.json            # State machine for async agent orchestration
├── .github/workflows/ci.yml         # CI pipeline
├── .env.example                     # Environment variable template
├── requirements.txt
└── Makefile                         # Common commands
```

---

## Quick Start

### Prerequisites

- AWS CLI v2 configured (`aws configure`)
- Python 3.10+
- Bedrock model access enabled for **Claude Haiku 4.5** in your AWS account
  (Console → Bedrock → Model access → enable `anthropic.claude-haiku-4-5`)

### 1. Deploy Lambda Functions

```bash
# order-status-tool
cd lambdas/tool_order_status
zip function.zip handler.py
aws lambda create-function \
  --function-name order-status-tool \
  --runtime python3.10 \
  --role arn:aws:iam::<ACCOUNT_ID>:role/LambdaExecutionRole \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip

# create-ticket-tool
cd ../tool_create_ticket
zip function.zip handler.py
aws lambda create-function \
  --function-name create-ticket-tool \
  --runtime python3.10 \
  --role arn:aws:iam::<ACCOUNT_ID>:role/LambdaExecutionRole \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip
```

### 2. Set Up OpenSearch Knowledge Base

```bash
# Edit opensearch/index_setup.py — replace YOUR-OPENSEARCH-ENDPOINT
python opensearch/index_setup.py
```

### 3. Create Bedrock Agent

See [`bedrock/agent_config.md`](bedrock/agent_config.md) for the full configuration reference.

```bash
aws bedrock-agent create-agent \
  --agent-name enterprise-agent \
  --foundation-model us.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --agent-resource-role-arn arn:aws:iam::<ACCOUNT_ID>:role/BedrockAgentRole \
  --instruction "You are an enterprise assistant. You can look up order statuses and create support tickets. Always confirm details before taking action."

aws bedrock-agent prepare-agent --agent-id <AGENT_ID>
aws bedrock-agent create-agent-alias \
  --agent-id <AGENT_ID> \
  --agent-alias-name prod
```

### 4. Configure Environment

```bash
cp .env.example .env
# Set AGENT_ID and AGENT_ALIAS_ID from the steps above
```

### 5. Chat with the Agent

```bash
pip install -r requirements.txt
export AGENT_ID=<your-agent-id>
export AGENT_ALIAS_ID=<your-alias-id>
python chat.py
```

**Example session:**
```
Chat with your agent (session: session-a3f2c1b0)

You: What's the status of order ORD-12345?
Agent: Order ORD-12345 is currently In Transit with an ETA of 2-3 business days.

You: Create a ticket — title: "Delayed shipment", description: "Order ORD-12345 is delayed"
Agent: Done. Support ticket TKT-8A2F1C has been created and is now open.
```

---

## AWS Cost Estimate

| Service | Purpose | Approx. Cost |
|---------|---------|-------------|
| Bedrock (Claude Haiku 4.5) | Agent + LLM | ~$0.00025/1k input tokens |
| Lambda (3 functions) | Tool execution | ~$0 (free tier) |
| OpenSearch | Vector search / RAG | ~$0.10/hr (t3.small.search) |
| Step Functions | Async orchestration | ~$0 (free tier: 4k transitions/month) |

**Estimated cost for development and demo: < $5/day** (OpenSearch dominates if left running — stop it when not in use)

---

## IAM Roles Required

| Role | Trust Principal | Permissions |
|------|----------------|-------------|
| `BedrockAgentRole` | `bedrock.amazonaws.com` | `bedrock:InvokeModel`, `bedrock:Retrieve`, `lambda:InvokeFunction` |
| `LambdaExecutionRole` | `lambda.amazonaws.com` | `AWSLambdaBasicExecutionRole` |

---

## Teardown (Stop All Billing)

```bash
python opensearch/teardown.py
bash teardown.sh
```

---

## What This Demonstrates

- **Bedrock Agents** — production tool-use pattern without custom orchestration
- **Action Groups** — Lambda functions as typed agent tools with input validation
- **RAG Knowledge Base** — OpenSearch kNN index with Titan embeddings (1536-dim)
- **Step Functions** — async agent invocation for pipeline and batch integration
- **Session management** — unique session IDs prevent conversation bleed across users
- **Serverless architecture** — zero infrastructure to manage, scales to zero

---

## License

MIT
