import weaviate
from weaviate.auth import AuthApiKey
import boto3
import os
from dotenv import load_dotenv

load_dotenv()


weaviate_url = os.environ.get("WEAVIATE_URL")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=AuthApiKey(weaviate_api_key)
)

print(client.is_ready())
client.close()
