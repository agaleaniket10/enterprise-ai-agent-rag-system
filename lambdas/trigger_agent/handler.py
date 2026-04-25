import json
import boto3

bedrock = boto3.client("bedrock-agent-runtime")


def lambda_handler(event, context):
    agent_id = event.get("agent_id")
    agent_alias_id = event.get("agent_alias_id")
    session_id = event.get("session_id")
    input_text = event.get("input_text")

    response = bedrock.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        inputText=input_text,
    )

    return {"statusCode": 200, "body": json.dumps({"response": str(response)})}
