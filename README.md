# Enterprise AI Agent on AWS

An enterprise-grade AI agent built with Amazon Bedrock Agents, AWS Lambda, Step Functions, and OpenSearch.

## Architecture

```
User → chat.py → Bedrock Agent (Claude Haiku 4.5)
                      ↓
              Action Groups (Lambda)
              ├── order-status-tool   → look up order status
              └── create-ticket-tool  → create support ticket
                      ↓
              Knowledge Base (OpenSearch)
```

## Project Structure

```
enterprise-ai-agent-aws/
├── lambdas/
│   ├── tool_order_status/    # Lambda: fetch order status by ID
│   ├── tool_create_ticket/   # Lambda: create support ticket
│   └── trigger_agent/        # Lambda: invoke Bedrock agent (for Step Functions)
├── stepfunctions/
│   └── workflow.asl.json     # Step Functions state machine
├── opensearch/
│   ├── index_setup.py        # Create OpenSearch knowledge base index
│   └── teardown.py           # Generate teardown script for all AWS resources
├── bedrock/
│   └── agent_config.md       # Bedrock agent configuration reference
├── chat.py                   # Interactive CLI chat with the agent
├── .env.example              # Environment variable template
└── README.md
```

## Prerequisites

- AWS CLI v2 configured (`aws configure`)
- Python 3.10+
- `boto3` and `opensearch-py` packages
- Bedrock model access enabled for **Claude Haiku 4.5**

## Setup

### 1. Deploy Lambda Functions

```bash
cd lambdas/tool_order_status
zip function.zip handler.py
aws lambda create-function \
  --function-name order-status-tool \
  --runtime python3.10 \
  --role arn:aws:iam::<ACCOUNT_ID>:role/BedrockAgentRole \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip
```

Repeat for `tool_create_ticket`.

### 2. Create Bedrock Agent

```bash
aws bedrock-agent create-agent \
  --agent-name enterprise-agent \
  --foundation-model us.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --agent-resource-role-arn arn:aws:iam::<ACCOUNT_ID>:role/BedrockAgentRole \
  --instruction "You are an enterprise assistant. You can look up order statuses and create support tickets."
```

### 3. Prepare and Alias the Agent

```bash
aws bedrock-agent prepare-agent --agent-id <AGENT_ID>
aws bedrock-agent create-agent-alias --agent-id <AGENT_ID> --agent-alias-name prod
```

### 4. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your AGENT_ID and AGENT_ALIAS_ID
```

### 5. Chat with the Agent

```bash
export AGENT_ID=<your-agent-id>
export AGENT_ALIAS_ID=<your-alias-id>
python3 chat.py
```

## Teardown

To delete all AWS resources and stop billing:

```bash
cd opensearch
python teardown.py
bash teardown.sh
```

## IAM Roles Required

| Role | Trust | Permissions |
|------|-------|-------------|
| `BedrockAgentRole` | `bedrock.amazonaws.com` | `bedrock:*` |
| `LambdaExecutionRole` | `lambda.amazonaws.com` | `AWSLambdaBasicExecutionRole` |
