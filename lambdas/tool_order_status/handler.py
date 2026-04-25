import random


# Quick POC upgrade
def lambda_handler(event, context):
    statuses = ["In Transit", "Delivered", "Delayed", "Processing"]
    return {
        "order_id": event.get("order_id"),
        "status": random.choice(statuses),
        "eta": "2-3 business days",
    }
