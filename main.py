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
# Example data
text_content = "This is an example document 2."
file_name = "example1.txt"

# Generate embeddings using all-MiniLM-L6-v2 (replace with your embedding logic)
# embeddings = embedding_model.encode([text_content])[0].tolist()

# Prepare object data
object_data = {
    "content": text_content,
    "filename": file_name
}

# Get the collection
collection = client.collections.get(DOCUMENT_CLASS)

# # INSERT OBJECT INTO WEAVIATE
file_uuid = generate_uuid5(file_name, DOCUMENT_CLASS)
# collection.data.replace(
#     uuid=file_uuid,
#     properties=object_data
# )
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


response = collection.query.fetch_objects()

# Print properties of all objects
for obj in response.objects:
    print(obj.properties)

# TO DELETE FILE USING UUID
# try:
#     collection.data.delete_by_id(uuid="2bb923cc-e2fb-4dad-b253-d517f342b7e6")
#     print(f"File has been deleted successfully.")
# except Exception as e:
#     print(f"Failed to delete file': {e}")
client.close()

# Document upload and ingestion


# @app.post("/upload")
# async def upload_document(file: UploadFile = File(...)):
#     print(f"Received file upload request: {file.filename}")
#     content = await file.read()
#     # Assuming text files for simplicity
#     text_content = content.decode("utf-8")
#     filename = file.filename

#     # Generate embeddings
#     print("Generating embeddings...")
#     embeddings = embedding_model.encode([text_content])[0].tolist()
#     print("Embeddings generated successfully.")

#     # # Delete old entries if same filename exists
#     # print(f"Deleting old embeddings for filename: {filename}")
#     # client.query.delete(DOCUMENT_CLASS, where={
#     #     "path": ["filename"],
#     #     "operator": "Equal",
#     #     "valueText": filename
#     # }).do()
#     # print("Old embeddings deleted successfully.")

#     # Store in Weaviate
#     print("Storing new embeddings in Weaviate...")
#     client.batch.configure(batch_size=10)  # Adjust batch size if needed
#     client.batch.add_data_object(
#         {"content": text_content, "filename": filename}, DOCUMENT_CLASS, vector=embeddings)
#     client.batch.flush()

#     print("Document indexed successfully.")
#     client.close()
#     return {"message": "Document uploaded and indexed successfully."}


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
