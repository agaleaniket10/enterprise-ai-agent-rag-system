"""tool_create_ticket — Create a support ticket."""

import logging
import uuid
from agent_commons import (extract_params, build_response, build_error,
                            log_event, utc_now, validate_required,
                            validate_enum, validate_max_length)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_CATEGORIES = {"billing", "technical", "shipping", "account", "general"}


def lambda_handler(event: dict, context) -> dict:
    log_event(event)
    ag, fn = event.get("actionGroup", "SupportManagement"), event.get("function", "create_ticket")

    try:
        p = extract_params(event.get("parameters", []), "title", "description", "priority", "category")
        priority = (p.get("priority") or "medium").lower()
        category = (p.get("category") or "general").lower()

        errors = (
            validate_required(p, "title", "description")
            + [e for e in [
                validate_max_length(p.get("title", ""), 200, "title"),
                validate_max_length(p.get("description", ""), 2000, "description"),
                validate_enum(priority, VALID_PRIORITIES, "priority"),
                validate_enum(category, VALID_CATEGORIES, "category"),
            ] if e]
        )
        if errors:
            return build_error(ag, fn, "Validation failed", "VALIDATION_ERROR", errors)

        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        ticket = {
            "ticket_id": ticket_id, "title": p["title"], "description": p["description"],
            "priority": priority, "category": category, "status": "open",
            "created_at": utc_now(),
            "estimated_response": "within 24 hours" if priority in {"low", "medium"} else "within 4 hours",
        }
        logger.info("Created ticket %s", ticket_id)
        return build_response(ag, fn, ticket)

    except Exception as e:
        logger.exception("Unexpected error")
        return build_error(ag, fn, "Internal server error", "INTERNAL_ERROR", [str(e)])
