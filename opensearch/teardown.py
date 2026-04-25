import os

# Define the shell script content
teardown_script = r"""#!/bin/bash

# ==============================================================================
# AWS AI AGENT LAB - COMPLETE TEARDOWN SCRIPT
# This script deletes all resources created in the lab to stop billing.
# ==============================================================================

# 1. Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting teardown of AI Agent System...${NC}"

# --- Environment Variables ---
# Attempt to get Account ID if not set
if [ -z "$ACCOUNT_ID" ]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
fi

# --- STEP 1: Bedrock Agent Teardown ---
echo -e "${GREEN}Step 1: Deleting Bedrock Agent and Alias...${NC}"

# We need to find the Agent ID based on the name 'enterprise-agent'
AGENT_ID=$(aws bedrock-agent list-agents --query "agentSummaries[?agentName=='enterprise-agent'].agentId" --output text)

if [ ! -z "$AGENT_ID" ] && [ "$AGENT_ID" != "None" ]; then
    # List and delete aliases
    ALIAS_IDS=$(aws bedrock-agent list-agent-aliases --agent-id $AGENT_ID --query "agentAliasSummaries[].agentAliasId" --output text)
    for ALIAS in $ALIAS_IDS; do
        echo "Deleting Alias: $ALIAS"
        aws bedrock-agent delete-agent-alias --agent-id $AGENT_ID --agent-alias-id $ALIAS
    done
    
    # Delete the Agent
    echo "Deleting Agent: $AGENT_ID"
    aws bedrock-agent delete-agent --agent-id $AGENT_ID
else
    echo "No Bedrock Agent found named 'enterprise-agent'."
fi


# --- STEP 2: Bedrock Knowledge Base Teardown ---
echo -e "${GREEN}Step 2: Deleting Bedrock Knowledge Base...${NC}"
KB_ID=$(aws bedrock-agent list-knowledge-bases --query "knowledgeBaseSummaries[?name=='enterprise-kb'].knowledgeBaseId" --output text)

if [ ! -z "$KB_ID" ] && [ "$KB_ID" != "None" ]; then
    aws bedrock-agent delete-knowledge-base --knowledge-base-id $KB_ID
    echo "Knowledge Base $KB_ID deleted."
else
    echo "No Knowledge Base found named 'enterprise-kb'."
fi


# --- STEP 3: OpenSearch Teardown (High Cost Item) ---
echo -e "${GREEN}Step 3: Deleting OpenSearch Domain (ai-agent-domain)...${NC}"
aws opensearch delete-domain --domain-name ai-agent-domain
echo "OpenSearch domain deletion initiated. (This takes 10-15 mins to fully clear)."


# --- STEP 4: Lambda Functions Teardown ---
echo -e "${GREEN}Step 4: Deleting Lambda Functions...${NC}"
aws lambda delete-function --function-name order-status-tool
aws lambda delete-function --function-name ticket-tool 2>/dev/null
aws lambda delete-function --function-name trigger_agent 2>/dev/null
echo "Lambda tools deleted."


# --- STEP 5: Step Functions Teardown ---
echo -e "${GREEN}Step 5: Deleting Step Functions State Machine...${NC}"
SF_ARN=$(aws stepfunctions list-state-machines --query "stateMachines[?name=='ai-agent-workflow'].stateMachineArn" --output text)
if [ ! -z "$SF_ARN" ] && [ "$SF_ARN" != "None" ]; then
    aws stepfunctions delete-state-machine --state-machine-arn $SF_ARN
    echo "State Machine deleted."
fi


# --- STEP 6: S3 Data Teardown ---
echo -e "${GREEN}Step 6: Deleting S3 Bucket and Data...${NC}"
BUCKET_NAME="ai-agent-kb-$ACCOUNT_ID"
# Delete all objects first, then the bucket
aws s3 rm s3://$BUCKET_NAME --recursive
aws s3 rb s3://$BUCKET_NAME
echo "S3 bucket $BUCKET_NAME removed."


# --- FINAL CHECK ---
echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}TEARDOWN COMMANDS ISSUED SUCCESSFULLY${NC}"
echo -e "Note: OpenSearch may still appear in 'Deleting' status for a few minutes."
echo -e "Check your billing dashboard tomorrow to ensure no 'Provisioned' costs remain."
echo -e "${BLUE}====================================================${NC}"
"""

with open("teardown.sh", "w") as f:
    f.write(teardown_script)

print("File 'teardown.sh' has been created.")
