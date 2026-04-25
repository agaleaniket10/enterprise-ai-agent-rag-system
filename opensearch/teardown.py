import os

# Define the shell script content
teardown_script = r"""#!/bin/bash

# ==============================================================================
# AWS AI AGENT LAB - COMPLETE TEARDOWN SCRIPT
# This script deletes all resources created in the lab to stop billing.
# ==============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting teardown of AI Agent System...${NC}"

# --- Environment Variables ---
if [ -z "$ACCOUNT_ID" ]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
fi

# --- STEP 1: Bedrock Agent Teardown ---
echo -e "${GREEN}Step 1: Deleting Bedrock Agent and Alias...${NC}"

AGENT_ID=$(aws bedrock-agent list-agents --query "agentSummaries[?agentName=='enterprise-agent'].agentId" --output text)

if [ ! -z "$AGENT_ID" ] && [ "$AGENT_ID" != "None" ]; then
    ALIAS_IDS=$(aws bedrock-agent list-agent-aliases --agent-id $AGENT_ID --query "agentAliasSummaries[].agentAliasId" --output text)
    for ALIAS in $ALIAS_IDS; do
        echo "Deleting Alias: $ALIAS"
        aws bedrock-agent delete-agent-alias --agent-id $AGENT_ID --agent-alias-id $ALIAS
    done
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


# --- STEP 3: OpenSearch Teardown ---
echo -e "${GREEN}Step 3: Deleting OpenSearch Domain (ai-agent-domain)...${NC}"
aws opensearch delete-domain --domain-name ai-agent-domain 2>/dev/null && \
    echo "OpenSearch domain deletion initiated. (Takes 10-15 mins to fully clear)." || \
    echo "No OpenSearch domain found or already deleted."


# --- STEP 4: Lambda Functions Teardown ---
echo -e "${GREEN}Step 4: Deleting Lambda Functions...${NC}"
for FN in order-status-tool create-ticket-tool trigger-agent trigger_agent; do
    aws lambda delete-function --function-name $FN 2>/dev/null && \
        echo "Deleted Lambda: $FN" || \
        echo "Lambda not found (skipping): $FN"
done


# --- STEP 5: Step Functions Teardown ---
echo -e "${GREEN}Step 5: Deleting Step Functions State Machine...${NC}"
SF_ARN=$(aws stepfunctions list-state-machines --query "stateMachines[?name=='ai-agent-workflow'].stateMachineArn" --output text)
if [ ! -z "$SF_ARN" ] && [ "$SF_ARN" != "None" ]; then
    aws stepfunctions delete-state-machine --state-machine-arn $SF_ARN
    echo "State Machine deleted."
else
    echo "No State Machine found named 'ai-agent-workflow'."
fi


# --- STEP 6: S3 Data Teardown ---
echo -e "${GREEN}Step 6: Deleting S3 Bucket and Data...${NC}"
BUCKET_NAME="ai-agent-kb-$ACCOUNT_ID"
aws s3 rm s3://$BUCKET_NAME --recursive 2>/dev/null
aws s3 rb s3://$BUCKET_NAME 2>/dev/null && \
    echo "S3 bucket $BUCKET_NAME removed." || \
    echo "S3 bucket not found or already deleted."


# --- STEP 7: IAM Role Teardown ---
echo -e "${GREEN}Step 7: Deleting IAM Roles...${NC}"

for ROLE in BedrockAgentRole LambdaExecutionRole; do
    # Detach managed policies
    ATTACHED=$(aws iam list-attached-role-policies --role-name $ROLE --query "AttachedPolicies[].PolicyArn" --output text 2>/dev/null)
    for ARN in $ATTACHED; do
        aws iam detach-role-policy --role-name $ROLE --policy-arn $ARN 2>/dev/null
    done

    # Delete inline policies
    INLINE=$(aws iam list-role-policies --role-name $ROLE --query "PolicyNames[]" --output text 2>/dev/null)
    for POLICY in $INLINE; do
        aws iam delete-role-policy --role-name $ROLE --policy-name $POLICY 2>/dev/null
    done

    # Delete the role
    aws iam delete-role --role-name $ROLE 2>/dev/null && \
        echo "Deleted IAM role: $ROLE" || \
        echo "IAM role not found (skipping): $ROLE"
done


# --- STEP 8: IAM User Inline Policy Cleanup ---
echo -e "${GREEN}Step 8: Cleaning up IAM user inline policies...${NC}"
for POLICY in BedrockFullAccess BedrockAgentCoreMemoryAccess bedrock_additional_permissions IAMFullAccess1 OpenSearchAccess Policy_2.0 Policy_2.1 S3_vectors MarketplaceAccess; do
    aws iam delete-user-policy --user-name bedrock-tutoria --policy-name $POLICY 2>/dev/null && \
        echo "Deleted user policy: $POLICY" || true
done


# --- FINAL CHECK ---
echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}TEARDOWN COMPLETE${NC}"
echo -e "Note: OpenSearch may still appear as 'Deleting' for a few minutes."
echo -e "Check your billing dashboard tomorrow to confirm no costs remain."
echo -e "${BLUE}====================================================${NC}"
"""

with open("teardown.sh", "w") as f:
    f.write(teardown_script)

print("teardown.sh has been created.")
