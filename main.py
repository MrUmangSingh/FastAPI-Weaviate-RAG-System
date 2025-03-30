import boto3
import os
from dotenv import load_dotenv

load_dotenv()


bucket_name = os.environ.get("BUCKET_NAME")
file_path = "D:\Pictures\dp.jpg"
s3_key = "dp.jpg"

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
    region_name="ap-south-1"
)


try:
    s3.upload_file(file_path, bucket_name, s3_key)
    print(
        f"File '{file_path}' uploaded to '{bucket_name}/{s3_key}' successfully!")
except Exception as e:
    print(f"Error uploading file: {e}")
