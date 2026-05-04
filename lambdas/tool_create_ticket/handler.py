import json
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Received event: %s", event)

    title = event.get("title")
    description = event.get("description")

    if not title:
        logger.error("Missing required field: title")
        return {"statusCode": 400, "error": "Missing required field: title"}

    if not description:
        logger.error("Missing required field: description")
        return {"statusCode": 400, "error": "Missing required field: description"}

    try:
        ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
        result = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "ticket_id": ticket_id,
                    "title": title,
                    "description": description,
                    "status": "open",
                }
            ),
        }
        logger.info("Created ticket: %s", ticket_id)
        return result

    except Exception as e:
        logger.exception("Unexpected error creating ticket")
        return {"statusCode": 500, "error": "Internal server error", "detail": str(e)}
