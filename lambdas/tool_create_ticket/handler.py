import json


def lambda_handler(event, context):
    title = event.get("title")
    description = event.get("description")
    # TODO: implement ticket creation logic
    return {
        "statusCode": 200,
        "body": json.dumps({"ticket_id": "TKT-001", "title": title, "status": "open"}),
    }
