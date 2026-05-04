import random
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

STATUSES = ["In Transit", "Delivered", "Delayed", "Processing"]


def lambda_handler(event, context):
    logger.info("Received event: %s", event)

    order_id = event.get("order_id")
    if not order_id:
        logger.error("Missing required field: order_id")
        return {"statusCode": 400, "error": "Missing required field: order_id"}

    try:
        status = random.choice(STATUSES)
        result = {
            "statusCode": 200,
            "order_id": order_id,
            "status": status,
            "eta": "2-3 business days",
        }
        logger.info("Returning order status: %s", result)
        return result

    except Exception as e:
        logger.exception("Unexpected error processing order status")
        return {"statusCode": 500, "error": "Internal server error", "detail": str(e)}
