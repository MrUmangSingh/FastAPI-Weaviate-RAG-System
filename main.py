import weaviate
from weaviate.auth import AuthApiKey
import boto3
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from weaviate.classes.config import Property, DataType
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5
from weaviate.classes.config import Configure
from weaviate.exceptions import UnexpectedStatusCodeError
import requests

load_dotenv()

app = FastAPI()


weaviate_url = os.environ.get("WEAVIATE_URL")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=AuthApiKey(weaviate_api_key)
)

DOCUMENT_CLASS = "Documents"


def setup_schema():
    print("Setting up schema in Weaviate...")
    try:
        # Check if the collection exists
        existing_collections = client.collections.list_all()
        if DOCUMENT_CLASS not in existing_collections:
            # Create the collection if it doesn't exist
            client.collections.create(
                name=DOCUMENT_CLASS,
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="filename", data_type=DataType.TEXT),
                ],
                vectorizer_config=[
                    Configure.NamedVectors.text2vec_weaviate(
                        name="title_vector",
                        source_properties=["title"],
                        model="Snowflake/snowflake-arctic-embed-l-v2.0")
                ],
            )
            print("Schema created successfully.")
        else:
            print("Schema already exists.")
    except Exception as e:
        print(f"Error setting up schema: {e}")


setup_schema()


# response = collection.query.fetch_objects()

# Print properties of all objects
# for obj in response.objects:
#     print(obj.properties)

# TO DELETE FILE USING UUID
# try:
#     collection.data.delete_by_id(uuid="2bb923cc-e2fb-4dad-b253-d517f342b7e6")
#     print(f"File has been deleted successfully.")
# except Exception as e:
#     print(f"Failed to delete file': {e}")
# client.close()

# Document upload and ingestion


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    print(f"Received file upload request: {file.filename}")
    content = await file.read()
    # Assuming text files for simplicity
    text_content = content.decode("utf-8")
    file_name = file.filename
    object_data = {
        "content": text_content,
        "filename": file_name
    }
    collection = client.collections.get(DOCUMENT_CLASS)
    file_uuid = generate_uuid5(file_name, DOCUMENT_CLASS)

    exists = collection.query.fetch_object_by_id(file_uuid) is not None
    if exists:
        collection.data.replace(
            uuid=file_uuid,
            properties=object_data
        )
    else:
        collection.data.insert(
            uuid=file_uuid,
            properties=object_data
        )
    print("Object stored successfully!")
    client.close()
    return {"message": "Document uploaded successfully."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
