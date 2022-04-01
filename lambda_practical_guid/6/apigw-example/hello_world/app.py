import base64
import decimal
import json
import os
import time

import boto3

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
client = boto3.client("ses")

MAILFORM = os.environ["MAILFORM"]


def sendmail(to, subject, body):
    reponse = client.send_email(
        Source=MAILFORM,
        ReplyToAddress=[MAILFORM],
        Destination={"ToAddresses": [to]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
        },
    )


def next_seq(table, tablename):
    response = table.update_item(
        Key={"tablename": tablename},
        UpdateExpression="set seq = seq + :val",
        ExpressionAttributeValues={":val": 1},
        ReturnValues="UPDATED_NEW",
    )

    return response["Attributes"]["seq"]


def lambda_handler(event, context):
    try:
        seqtable = dynamodb.Table(os.environ["SEQUENCETABLE"])
        nextseq = next_seq(seqtable, os.environ["USERTABLE"])

        body = event["body"]

        if event["isBase64Encoded"]:
            body = base64.b64decode(body)

        decoded = json.loads(body)
        username = decoded["username"]
        email = decoded["email"]
        host = event["requestContext"]["http"]["sourceIp"]

        now = time.time()

        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": os.environ["SAVEBUCKET"], "Key": "filename.pdf"},
            ExpiresIn=8 * 60 * 60,
            HttpMethod="GET",
        )

        usertable = dynamodb.Table("user")
        usertable.put_item(
            Item={
                "id": nextseq,
                "username": username,
                "email": email,
                "accept_at": decimal.Decimal(str(now)),
                "host": host,
                "url": url,
            }
        )

        mailbody = """
        Hello {0}!
            You can download the pdf file from {1}.
        """.format(
            username, url
        )

        sendmail(email, "Thansks", mailbody)
        return json.dumps({})
    # PEP8 do not user bare except here :(
    except:
        import traceback

        err = traceback.format_exc()
        print(err)

        return {
            "statusCode": 500,
            "headers": {"content-type": "text/json"},
            "body": json.dumps({"error": "Internal Error"}),
        }
