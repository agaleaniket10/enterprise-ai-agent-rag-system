import boto3
import os

AGENT_ID = os.environ.get("AGENT_ID", "AFRKJZJDE7")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID", "TSTALIASID")
REGION = os.environ.get("AWS_REGION", "us-east-1")

client = boto3.client("bedrock-agent-runtime", region_name=REGION)
session_id = "session-001"

print("Chat with your agent (type 'quit' to exit)\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=user_input,
    )

    print("Agent: ", end="")
    for event in response["completion"]:
        if "chunk" in event:
            print(event["chunk"]["bytes"].decode(), end="")
    print("\n")
