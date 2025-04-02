import weaviate
from weaviate.auth import AuthApiKey
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
import uvicorn
from weaviate.classes.config import Property, DataType, Configure
from llm import search_and_answer
from manageDocument import uploading_file, delete_file, get_files, search_files, query_json_data
from weaviate.classes.config import (
    Property,
    DataType,
    Configure
)
from pydantic import BaseModel

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
    print("Setting up schemas in Weaviate...")
    try:
        classes_to_create = ["Documents", "JSONDocuments"]

        for class_name in classes_to_create:
            # Check existence for each collection
            if not client.collections.exists(class_name):
                client.collections.create(
                    name=class_name,
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
                print(f"Schema for {class_name} created successfully.")
            else:
                print(f"Schema for {class_name} already exists.")

    except Exception as e:
        print(f"Error setting up schemas: {e}")


class SearchRequest(BaseModel):
    query: str


class JSONSearchRequest(BaseModel):
    query: str


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    uploading_file(client, file, content)
    return {"message": "Document uploaded successfully."}


@app.post("/search")
async def search(request: SearchRequest):
    results = search_and_answer(client, request.query)
    return results


@app.post("/query-json")
async def query_json(request: JSONSearchRequest):
    result = query_json_data(client, request.query)
    return result

if __name__ == "__main__":
    setup_schema()
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # delete_file(client, "cuet_stats_syllabus.pdf")
    # delete_file(client, "jam_ana.pdf")
    # delete_file(client, "resume.txt")
    # delete_file(client, "sample.json")
    # delete_file(client, "house-price.json")
    get_files(client)
    # search_files(client, "membership of Customer 103")
    # print(response)
    # response = search_and_answer(
    #     client, "Total spent of customer 120 and customer 101 together?")
    # print(response)
    client.close()
