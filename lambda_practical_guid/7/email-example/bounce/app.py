import json
import os

import boto3
from aws_xray_sdk.core import patch_all

patch_all()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["MAILTABLE"])


def lambda_handler(event, context):
    for rec in event["Records"]:
        message = rec["Sns"]["Message"]
        data = json.loads(message)

        if data["notificationType"] == "Bounce":
            bouces = data["bounce"]["bounceRecipients"]

            for b in bouces:
                email = b["emailAddress"]
                resposne = table.update_item(
                    Key={"email": email},
                    UpdateExpression="set haserror=:val",
                    ExpressionAttributeValues={":val": 1},
                )
