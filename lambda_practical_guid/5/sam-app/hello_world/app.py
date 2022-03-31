import json
import os
import tempfile
import pyminizip
import boto3


def lambda_handler(event, context):
    s3 = boto3.resource("s3")
    tmpdir = tempfile.TemporaryDirectory()

    for rec in event["Records"]:
        filename = rec["s3"]["object"]["key"]
        bucketname = rec["s3"]["object"]["name"]

        obj = s3.Object(bucketname, filename)
        response = obj.get()
        localfilename = os.path.join(tmpdir.name, filename)
        with open(localfilename, "wb") as fp:
            fp.write(response["Body"].read())

        zipfilename = tempfile.mkstemp(suffix='.zip')[1]
        os.chdir(tmpdir.name)
        pyminizip.compress(localfilename, None, zipfilename, 'mypassword', 0)

        destbucketname = os.environ["OUTPUTBUCKET"]
        obj2 = s3.Object(destbucketname, filename + '.zip')

        response = obj2.put(Body=open(zipfilename, "rd"))
        tmpdir.cleanup()
