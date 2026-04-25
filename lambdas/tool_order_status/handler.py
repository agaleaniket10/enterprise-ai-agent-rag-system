import json


def lambda_handler(event, context):
    order_id = event.get("order_id")
    # TODO: implement order status lookup
    return {
        "statusCode": 200,
        "body": json.dumps({"order_id": order_id, "status": "in_progress"})
    }
