# FastAPI Weaviate RAG System

## Overview

This project is a **FastAPI-based application** that integrates with **Weaviate** to manage document ingestion, embedding, and retrieval using a **Retrieval-Augmented Generation (RAG)** approach. The system supports **hybrid search** for text documents and **structured queries** for JSON data.

## Features

- Upload documents (**PDF, DOCX, TXT, JSON**) and store embeddings in Weaviate.
- Perform **semantic search** on stored documents.
- Execute **structured queries** on JSON data.
- Supports **hybrid search** for text and metadata.
- Automates **embedding generation and indexing**.

## Project Workflow

### 1. **Setup**

The project connects to a Weaviate instance using credentials stored in the `.env` file. It sets up schemas for two document classes:

- **Documents**: Stores text-based document embeddings.
- **JSONDocuments**: Stores structured JSON data for querying.

### 2. **Endpoints**

| Endpoint      | Method | Description                                               |
| ------------- | ------ | --------------------------------------------------------- |
| `/upload`     | `POST` | Uploads a document (PDF, DOCX, TXT, JSON) to Weaviate.    |
| `/search`     | `POST` | Performs semantic search on the **Documents** collection. |
| `/query-json` | `POST` | Executes structured queries on **JSONDocuments**.         |

### 3. **Weaviate Integration**

- Documents are stored in **Weaviate collections** (`Documents` or `JSONDocuments`).
- The system supports **hybrid search** and **structured queries** for JSON data.

## How to Use the Project

### 1. **Prerequisites**

Ensure you have Python installed, then install dependencies:

```bash
pip install -r requirements.txt
```

Set up a `.env` file with the following variables:

```
WEAVIATE_URL="your_weaviate_url"
WEAVIATE_API_KEY="your_weaviate_api_key"
GROQ_API_KEY="your_groq_api_key"
```

### 2. **Start the Server**

Run the FastAPI server:

```bash
python main.py
```

The server will be available at [**http://0.0.0.0:8000**](http://0.0.0.0:8000).

## Using Postman

### **1. Upload a File**

**Endpoint:** `POST /upload`

- **Description:** Uploads a document to Weaviate.
- **Body (multipart/form-data):**
  - `key`: file (type: file). Don't forget this else it will give you 422 error
  - `Value`: Select a file (e.g., sample.pdf, data.json)

- **Response:**

```json
{
  "message": "Document uploaded successfully."
}
```

### **2. Search for Documents**

**Endpoint:** `POST /search`

- **Description:** Performs a semantic search on stored documents.
- **Body (JSON):**

```json
{
  "query": "Find documents about machine learning"
}
```

- **Response:**

```json
{
  "response": "Machine learning is a subset of AI...",
  "source": "ml_document.pdf",
  "content_snippet": "Machine learning is a..."
}
```

### **3. Query JSON Data**

**Endpoint:** `POST /query-json`

- **Description:** Executes structured queries on JSON documents.
- **Body (JSON):**

```json
{
  "query": "max price"
}
```

- **Response:**

```json
{
  "operation": "max",
  "field": "price",
  "result": 13300000
}
```

## Workflow Details

### **1. Uploading Files**

- Use the `/upload` endpoint to upload files.
- The system processes documents based on type (PDF, DOCX, TXT, or JSON).
- Extracted content is **embedded** using unbuilt `Snowflake/snowflake-arctic-embed-l-v2.0` model and **stored** in Weaviate.

### **2. Searching Files**

- Use the `/search` endpoint to perform **semantic searches** in the `Documents` collection using hybrid technique.
- Results are **ranked based on relevance**.

### **3. Querying JSON Data**

- Use the `/query-json` endpoint to run **aggregations** (max, min, sum, average) on **JSON fields**. So you only have to give 2 words input. {operation field-name}


## Future Enhancements

- **UI Integration:** A web interface for document uploads and search.
- **Advanced Querying:** Natural language querying for JSON documents
---