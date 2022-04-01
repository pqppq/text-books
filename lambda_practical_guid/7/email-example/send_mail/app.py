import json
import os

import boto3
from aws_xray_sdk.core import patch_all

patch_all()

sqs = boto3.resource("sqs")
s3 = boto3.resource("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("mailaddress")
client = boto3.client("ses")
MAILFROM = os.environ["MAILADDRESS"]


def lambda_handelr(event, context):
    for rec in event["Records"]:
        email = rec["body"]
        bucketname = rec["messageAttributes"]["bucketname"]["stringValue"]
        filename = rec["messageAttributes"]["filename"]["stringValue"]
        username = rec["messageAttributes"]["username"]["stringValue"]

        obj = s3.Object(bucketname, filename)
        response = obj.get()
        maildata = response["Body"].read().decode("utf-8")
        [subject, _, body] = maildata.split("\n", 3)

        response = table.update_item(
            Key={"email": email},
            UpdateExpression="set issend=:val",
            ExpressionAttributeValues={":val": 1},
            ReturnValues="UPDATED_OLD",
        )

        if response["Attributes"]["issend"] == 0:
            response = client.send_mail(
                Source=MAILFROM,
                ReplyToAddress=[MAILFROM],
                Destination={"ToAddress": [email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                },
            )
        else:
            print("Resend skip")
