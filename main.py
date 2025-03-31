import weaviate
from weaviate.auth import AuthApiKey
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
import uvicorn
from weaviate.classes.config import Property, DataType
from weaviate.classes.config import Configure
from llm import search_and_answer
from manageDocument import uploading_file, delete_file, get_files, search_files
from weaviate.classes.config import (
    Property,
    DataType,
    Configure
)

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
                        name="content_vector",
                        source_properties=["content", "filename"],
                        model="Snowflake/snowflake-arctic-embed-l-v2.0"
                    )
                ]
            )
            print("Schema created successfully.")
        else:
            print("Schema already exists.")
    except Exception as e:
        print(f"Error setting up schema: {e}")


setup_schema()


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    uploading_file(client, file, content)
    return {"message": "Document uploaded successfully."}


if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # delete_file(client, "coursera u18j840hi5nl.pdf")
    # delete_file(client, "whistleblower-policy-ba-revised.pdf")
    get_files(client)
    # search_files(client, "membership of Customer 103")
    # response = search_and_answer(
    #     client, "what is father name of ananya singh?")
    # print(response)
    response = search_and_answer(
        client, "Total spent of customer 120 and customer 101 together?")
    print(response)
    client.close()
