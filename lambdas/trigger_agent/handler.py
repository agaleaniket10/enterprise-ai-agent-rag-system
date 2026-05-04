import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-agent-runtime")


def lambda_handler(event, context):
    logger.info("Received event: %s", event)

    agent_id = event.get("agent_id")
    agent_alias_id = event.get("agent_alias_id")
    session_id = event.get("session_id")
    input_text = event.get("input_text")

    # Validate required fields
    missing = [
        f
        for f, v in {
            "agent_id": agent_id,
            "agent_alias_id": agent_alias_id,
            "session_id": session_id,
            "input_text": input_text,
        }.items()
        if not v
    ]

    if missing:
        logger.error("Missing required fields: %s", missing)
        return {"statusCode": 400, "error": f"Missing required fields: {missing}"}

    try:
        response = bedrock.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=input_text,
        )

        # Stream and collect the response chunks
        output_text = ""
        for event in response.get("completion", []):
            if "chunk" in event:
                output_text += event["chunk"]["bytes"].decode("utf-8")

        logger.info("Agent response collected, length: %d chars", len(output_text))
        return {"statusCode": 200, "body": json.dumps({"response": output_text})}

    except ClientError as e:
        logger.exception("AWS ClientError invoking agent")
        return {
            "statusCode": 502,
            "error": "Failed to invoke Bedrock agent",
            "detail": str(e),
        }
    except Exception as e:
        logger.exception("Unexpected error invoking agent")
        return {"statusCode": 500, "error": "Internal server error", "detail": str(e)}
