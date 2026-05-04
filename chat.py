import boto3
import os
import uuid
from botocore.exceptions import ClientError

AGENT_ID = os.environ.get("AGENT_ID", "")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID", "")
REGION = os.environ.get("AWS_REGION", "us-east-1")

if not AGENT_ID or not AGENT_ALIAS_ID:
    raise EnvironmentError(
        "AGENT_ID and AGENT_ALIAS_ID must be set as environment variables.\n"
        "Run: export AGENT_ID=<id> && export AGENT_ALIAS_ID=<alias-id>"
    )

client = boto3.client("bedrock-agent-runtime", region_name=REGION)

# Unique session per run so conversations don't bleed into each other
session_id = f"session-{uuid.uuid4().hex[:8]}"

print(f"Chat with your agent (session: {session_id})")
print("Type 'quit' to exit\n")

while True:
    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        break

    if not user_input:
        continue

    if user_input.lower() == "quit":
        break

    try:
        response = client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=user_input,
        )

        print("Agent: ", end="", flush=True)
        for event in response["completion"]:
            if "chunk" in event:
                print(event["chunk"]["bytes"].decode(), end="", flush=True)
        print("\n")

    except ClientError as e:
        print(f"[Error] AWS error: {e}\n")
    except Exception as e:
        print(f"[Error] Unexpected error: {e}\n")
