"""
trigger_agent — Multi-agent router for AWS Step Functions.

Routes incoming requests to the correct specialist sub-agent based on intent,
then invokes that agent via Bedrock Agents and returns the response.

Routing logic:
  ORDER intent   → Order Management Agent  (order status, history, cancellation)
  SUPPORT intent → Support Agent           (tickets, escalation, KB search)
  BILLING intent → Billing Agent           (invoices, refunds)
  UNKNOWN        → General Agent           (fallback)
"""

import json
import logging
import os
import re
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-agent-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# Agent IDs loaded from environment — set these in Lambda env vars or .env
AGENT_MAP = {
    "order":   {"id": os.environ.get("ORDER_AGENT_ID"),   "alias": os.environ.get("ORDER_AGENT_ALIAS_ID")},
    "support": {"id": os.environ.get("SUPPORT_AGENT_ID"), "alias": os.environ.get("SUPPORT_AGENT_ALIAS_ID")},
    "billing": {"id": os.environ.get("BILLING_AGENT_ID"), "alias": os.environ.get("BILLING_AGENT_ALIAS_ID")},
    "general": {"id": os.environ.get("AGENT_ID"),         "alias": os.environ.get("AGENT_ALIAS_ID")},
}

# Billing checked BEFORE order — "refund for my order" should route to billing
INTENT_PATTERNS = {
    "billing": re.compile(r"\b(invoice|refund|charge|charged|payment|bill|receipt|price|cost|reimburse)\b", re.I),
    "support": re.compile(r"\b(ticket|issue|problem|help|support|escalat|broken|error|bug)\b", re.I),
    "order":   re.compile(r"\b(order|track|ship|deliver|cancel|dispatch|package)\b", re.I),
}


def classify_intent(query: str) -> str:
    """Classify query into order / billing / support / general."""
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(query):
            return intent
    return "general"


def invoke_agent(agent_id: str, alias_id: str, session_id: str, query: str) -> str:
    """Invoke a Bedrock Agent and collect the full streamed response."""
    if not agent_id or not alias_id:
        raise ValueError("Agent ID or Alias ID not configured for this intent")

    response = bedrock.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=session_id,
        inputText=query,
    )

    chunks = []
    for event in response.get("completion", []):
        if "chunk" in event:
            chunks.append(event["chunk"]["bytes"].decode("utf-8"))

    return "".join(chunks)


def lambda_handler(event: dict, context) -> dict:
    logger.info("Router invoked: %s", json.dumps({k: v for k, v in event.items() if k != "sessionAttributes"}))

    query      = event.get("inputText") or event.get("query", "")
    session_id = event.get("sessionId", context.aws_request_id if context else "default-session")

    if not query:
        return {"statusCode": 400, "error": "Missing inputText or query in event"}

    # 1. Classify intent
    intent = classify_intent(query)
    agent  = AGENT_MAP[intent]
    logger.info("Classified intent='%s' → agentId=%s", intent, agent.get("id", "NOT_SET"))

    # 2. Fallback chain: if specialist agent not configured, use general
    if not agent.get("id") and intent != "general":
        logger.warning("No agent configured for intent '%s', falling back to general", intent)
        intent = "general"
        agent  = AGENT_MAP["general"]

    try:
        answer = invoke_agent(agent["id"], agent["alias"], session_id, query)
        return {
            "statusCode": 200,
            "intent":     intent,
            "sessionId":  session_id,
            "response":   answer,
        }

    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        logger.error("Bedrock ClientError [%s]: %s", code, msg)

        # Retry with general agent if specialist fails
        if intent != "general":
            logger.warning("Retrying with general agent after specialist failure")
            try:
                general = AGENT_MAP["general"]
                answer  = invoke_agent(general["id"], general["alias"], session_id, query)
                return {"statusCode": 200, "intent": "general_fallback", "sessionId": session_id, "response": answer}
            except Exception as fallback_err:
                logger.exception("General agent fallback also failed")
                return {"statusCode": 500, "error": str(fallback_err)}

        return {"statusCode": 500, "error": f"Bedrock error [{code}]: {msg}"}

    except ValueError as e:
        logger.error("Configuration error: %s", e)
        return {"statusCode": 500, "error": f"Agent not configured: {e}"}

    except Exception as e:
        logger.exception("Unexpected error in router")
        return {"statusCode": 500, "error": str(e)}
