from pypdf import PdfReader
from docx import Document
import json
from weaviate.util import generate_uuid5

DOCUMENT_CLASS = "Documents"


def uploading_file(client, file, content):
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
            text_content = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {"error": "Invalid JSON file"}

    elif file_name.endswith(".txt"):
        text_content = content.decode("utf-8")
    else:
        return {"error": "Unsupported file format"}

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
