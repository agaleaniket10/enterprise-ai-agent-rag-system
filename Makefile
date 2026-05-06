.PHONY: help install chat deploy-lambdas teardown lint

help:
	@echo ""
	@echo "Enterprise AI Agent - Available Commands"
	@echo "-----------------------------------------"
	@echo "  make install          Install Python dependencies"
	@echo "  make chat             Start interactive CLI chat with the agent"
	@echo "  make deploy-lambdas   Zip and deploy all Lambda functions to AWS"
	@echo "  make teardown         Generate and run the AWS teardown script"
	@echo "  make lint             Run code style checks"
	@echo ""

install:
	pip install -r requirements.txt

chat:
	@if [ -z "$$AGENT_ID" ] || [ -z "$$AGENT_ALIAS_ID" ]; then \
		echo "Error: AGENT_ID and AGENT_ALIAS_ID must be set."; \
		echo "Run: export AGENT_ID=<id> && export AGENT_ALIAS_ID=<alias-id>"; \
		exit 1; \
	fi
	python3 chat.py

deploy-lambdas:
	@echo "Deploying order-status-tool..."
	cd lambdas/tool_order_status && zip -q function.zip handler.py && \
		aws lambda update-function-code \
			--function-name order-status-tool \
			--zip-file fileb://function.zip

	@echo "Deploying create-ticket-tool..."
	cd lambdas/tool_create_ticket && zip -q function.zip handler.py && \
		aws lambda update-function-code \
			--function-name create-ticket-tool \
			--zip-file fileb://function.zip

	@echo "Deploying trigger-agent..."
	cd lambdas/trigger_agent && zip -q function.zip handler.py && \
		aws lambda update-function-code \
			--function-name trigger-agent \
			--zip-file fileb://function.zip

	@echo "All Lambda functions deployed."

teardown:
	@echo "Generating teardown script..."
	cd opensearch && python3 teardown.py
	@echo "Running teardown..."
	bash opensearch/teardown.sh

lint:
	pip install pyflakes --quiet
	python3 -m pyflakes lambdas/tool_order_status/handler.py \
		lambdas/tool_create_ticket/handler.py \
		lambdas/trigger_agent/handler.py \
		chat.py
	@echo "Lint complete."
