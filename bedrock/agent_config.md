# Bedrock Agent Configuration

## Agent Details

- **Name**: enterprise-agent
- **Foundation Model**: `us.anthropic.claude-haiku-4-5-20251001-v1:0` (Claude Haiku 4.5 via inference profile)
- **Agent Resource Role**: `BedrockAgentRole`
- **Description**: Enterprise AI agent for handling order status lookups and support ticket creation.

## Instructions

You are an enterprise assistant. You can:
- Look up order statuses given an order ID
- Create support tickets with a title and description

Always confirm details with the user before taking action.

## Action Groups

### OrderStatus
- **Lambda**: `order-status-tool`
- **Description**: Retrieves the current status of an order by order ID.
- **Input**: `order_id` (string, required)
- **Output**: `order_id`, `status`, `eta`

### CreateTicket
- **Lambda**: `create-ticket-tool`
- **Description**: Creates a new support ticket with a title and description.
- **Input**: `title` (string, required), `description` (string, required)
- **Output**: `ticket_id`, `title`, `description`, `status`

## Knowledge Base

- **Name**: `enterprise-kb`
- **Source**: OpenSearch index `kb-index`
- **Embedding Model**: `amazon.titan-embed-text-v1`
- **Vector Dimension**: 1536

## IAM Roles

| Role | Trust Principal | Purpose |
|------|----------------|---------|
| `BedrockAgentRole` | `bedrock.amazonaws.com` | Agent execution and model invocation |
| `LambdaExecutionRole` | `lambda.amazonaws.com` | Lambda basic execution |

## Notes

- Model access for Claude Haiku 4.5 must be enabled in **Bedrock → Model access** before use
- The inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0` routes across `us-east-1`, `us-east-2`, and `us-west-2`
