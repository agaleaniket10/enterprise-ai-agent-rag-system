"""tool_order_status — Return the current status of an order."""

import logging
import random
from agent_commons import extract_param, build_response, build_error, log_event, utc_now

logger = logging.getLogger()
logger.setLevel(logging.INFO)

STATUSES = ["Processing", "Shipped", "Out for Delivery", "Delivered", "Cancelled"]

MOCK_ORDERS = {
    "ORD-001": {"status": "Shipped",         "carrier": "FedEx", "tracking": "FX123456"},
    "ORD-002": {"status": "Delivered",        "carrier": "UPS",   "tracking": "UP789012"},
    "ORD-003": {"status": "Processing",       "carrier": None,    "tracking": None},
    "ORD-004": {"status": "Out for Delivery", "carrier": "USPS",  "tracking": "US345678"},
    "ORD-005": {"status": "Cancelled",        "carrier": None,    "tracking": None},
}


def lambda_handler(event: dict, context) -> dict:
    log_event(event)
    ag, fn = event.get("actionGroup", "OrderManagement"), event.get("function", "get_order_status")

    try:
        order_id = extract_param(event.get("parameters", []), "order_id")
        if not order_id:
            return build_error(ag, fn, "Missing required parameter: order_id", "MISSING_PARAMETER")

        order_id = order_id.strip().upper()
        order = MOCK_ORDERS.get(order_id, {"status": random.choice(STATUSES), "carrier": None, "tracking": None})

        result = {"order_id": order_id, "status": order["status"], "last_updated": utc_now()}
        if order.get("carrier"):
            result.update({"carrier": order["carrier"], "tracking_number": order["tracking"]})

        return build_response(ag, fn, result)

    except Exception as e:
        logger.exception("Unexpected error")
        return build_error(ag, fn, "Internal server error", "INTERNAL_ERROR", [str(e)])
