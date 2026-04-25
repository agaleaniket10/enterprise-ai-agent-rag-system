# Bedrock Agent Configuration

## Agent Details

- **Name**: EnterpriseAIAgent
- **Foundation Model**: anthropic.claude-3-sonnet-20240229-v1:0
- **Description**: Enterprise AI agent for handling order status and ticket creation.

## Instructions

You are an enterprise assistant. You can:
- Look up order statuses given an order ID
- Create support tickets with a title and description

Always confirm details with the user before taking action.

## Action Groups

### OrderStatus
- **Lambda**: `tool_order_status`
- **Description**: Retrieves the current status of an order by order ID.

### CreateTicket
- **Lambda**: `tool_create_ticket`
- **Description**: Creates a new support ticket with a title and description.

## Knowledge Base

- **Source**: OpenSearch index `enterprise-knowledge-base`
- **Embedding Model**: amazon.titan-embed-text-v1
