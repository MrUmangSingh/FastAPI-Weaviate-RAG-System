import statistics
from weaviate.classes.query import MetadataQuery
from pypdf import PdfReader
from docx import Document
import json
from weaviate.util import generate_uuid5
from weaviate.classes.query import HybridFusion


def uploading_file(client, file, content):
    DOCUMENT_CLASS = "Documents"
    print(f"Received file upload request: {file.filename}")
    file_name = file.filename.lower()

    if file_name.endswith(".pdf"):
        reader = PdfReader(file.file)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text()

    elif file_name.endswith(".docx"):
        document = Document(file.file)
        text_content = "\n".join([para.text for para in document.paragraphs])

    elif file_name.endswith(".json"):
        try:
            DOCUMENT_CLASS = "JSONDocuments"
            text_content = json.loads(content.decode("utf-8"))
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
    DOCUMENT_CLASS = "Documents"
    if filename.endswith(".json"):
        DOCUMENT_CLASS = "JSONDocuments"
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
    DOCUMENT_CLASSES = ["Documents", "JSONDocuments"]
    for DOCUMENT_CLASS in DOCUMENT_CLASSES:
        print(f"\nFetching all files from the {DOCUMENT_CLASS} database...")
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
    # for obj in sorted_results:
    #     print(f"Filename: {obj.properties['filename']}")
    #     print(f"Content Snippet: {obj.properties['content']}")
    #     print(f"Score: {obj.metadata.score:.3f}")
    #     print("-" * 50)
    return sorted_results


def query_json_data(client, query: str):
    # Map keywords in the query to operations
    operation_mapping = {
        "minimum": "min",
        "maximum": "max",
        "min": "min",
        "max": "max",
        "sum": "sum",
        "total": "sum",
        "average": "average",
        "mean": "average"
    }
    # Extract the operation and field from the query
    operation = None
    field = None
    for keyword, mapped_operation in operation_mapping.items():
        if keyword in query.lower():
            operation = mapped_operation
            break

    # Extract the field name (assumes the field name comes after the operation keyword)
    if operation:
        field = query.lower().replace(keyword, "").strip()

    if not operation or not field:
        return {"error": "Unable to interpret the query. Please use a valid format."}

    collection = client.collections.get("JSONDocuments")
    response = collection.query.fetch_objects()

    # Debug
    if not response.objects:
        return {"error": "No objects found in the database."}

    field_values = {}
    for obj in response.objects:
        try:
            # Debug
            # print(f"Parsing content: {obj.properties['content']}")
            content = obj.properties["content"]

            if isinstance(content, str):
                content = json.loads(content.replace("'", '"'))

            if isinstance(content, dict):
                content = [content]

            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if isinstance(value, (int, float)):
                                if key not in field_values:
                                    field_values[key] = []
                                field_values[key].append(value)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Debug: Print the error if parsing fails
            print(f"Error parsing object: {e}")
            continue

    # Debug
    # print(f"Detected numerical fields: {field_values}")

    if field not in field_values:
        return {"error": f"Field '{field}' not found in the JSON data."}

    # Perform the requested operation on the specified field
    values = field_values[field]
    if operation == "max":
        result = max(values)
    elif operation == "min":
        result = min(values)
    elif operation == "sum":
        result = sum(values)
    elif operation == "average":
        result = statistics.mean(values)
    else:
        return {"error": f"Unsupported operation '{operation}'."}

    return {"operation": operation, "field": field, "result": result}
