from weaviate.classes.query import MetadataQuery
from pypdf import PdfReader
from docx import Document
import json
from weaviate.util import generate_uuid5
import weaviate
from weaviate.classes.query import HybridFusion

DOCUMENT_CLASS = "Documents"


def uploading_file(client, file, content):
    print(f"Received file upload request: {file.filename}")
    file_name = file.filename.lower()

    if file_name.endswith(".pdf"):
        reader = PdfReader(file.file)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text()
        print(text_content)

    elif file_name.endswith(".docx"):
        document = Document(file.file)
        text_content = "\n".join([para.text for para in document.paragraphs])

    elif file_name.endswith(".json"):
        try:
            text_content = json.loads(content.decode("utf-8"))
            print(text_content)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {"error": "Invalid JSON file"}

    elif file_name.endswith(".txt"):
        text_content = content.decode("utf-8")
    else:
        return {"error": "Unsupported file format"}

    def normalize_text(content):
        return ' '.join(str(content).split()).strip()

    object_data = {
        "content": normalize_text(text_content),
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


def delete_file(client, filename: str):
    file_uuid = generate_uuid5(filename, DOCUMENT_CLASS)
    collection = client.collections.get(DOCUMENT_CLASS)
    exists = collection.query.fetch_object_by_id(file_uuid) is not None
    if exists:
        try:
            collection.data.delete_by_id(file_uuid)
            print(f"File '{filename}' deleted successfully.")
        except Exception as e:
            print(f"Deletion failed: {str(e)}")
    else:
        print(f"File '{filename}' does not exist in the database.")


def get_files(client):
    collection = client.collections.get(DOCUMENT_CLASS)
    response = collection.query.fetch_objects()
    for obj in response.objects:
        print(obj.properties["filename"])


def search_files(client, query: str, limit: int = 5):
    response = client.collections.get("Documents").query.hybrid(
        query=query,
        alpha=0.7,
        limit=limit,
        fusion_type=HybridFusion.RELATIVE_SCORE,
        auto_limit=10,
        return_metadata=MetadataQuery(score=True),
        query_properties=["content^3", "filename"]
    )
    threshold = 0.6
    filtered_results = [
        result for result in response.objects if result.metadata.score >= threshold]
    sorted_results = sorted(
        filtered_results, key=lambda x: x.metadata.score, reverse=True)

    # Print results
    for obj in sorted_results:
        print(f"Filename: {obj.properties['filename']}")
        print(f"Content Snippet: {obj.properties['content']}")
        print(f"Score: {obj.metadata.score:.3f}")
        print("-" * 50)
    return sorted_results
