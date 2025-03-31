from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda
from manageDocument import search_files
import warnings
from pydantic import PydanticDeprecatedSince211
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

warnings.filterwarnings(
    "ignore",
    category=PydanticDeprecatedSince211,
    message=".*instance is deprecated.*"
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model_name="llama-3.3-70b-versatile")


class StructuredResponse(BaseModel):
    response: str = Field(description="The answer to the user's question")
    source: str = Field(description="Filename containing the answer")
    content_snippet: str = Field(
        description="Relevant portion of the source document")


# Function to format the documents
def format_docs(docs: list[Document]) -> str:
    formatted = []
    for i, doc in enumerate(docs, 1):
        if not isinstance(doc, Document):
            continue

        filename = doc.metadata.get("filename", "unknown")
        content = doc.page_content[:500] + "..."

        formatted.append(
            f"DOCUMENT {i} ({filename}) [Relevance: {doc.metadata.get('score', 0):.2f}]:\n{content}"
        )

    return "\n\n".join(formatted) if formatted else "No relevant documents found"


template = """Answer the question using only the provided context.
Format your answer as JSON with these keys: response, source, content_snippet.

Context:
{context}

Question: {question}

Return only valid JSON, no additional text:
"""


def search_and_answer(client, query):
    results = search_files(client, query)

    # Convert to LangChain Documents with proper validation
    docs = []
    for result in results:
        try:
            doc = Document(
                page_content=str(result.properties.get("content", "")),
                metadata={
                    "filename": str(result.properties.get("filename", "unknown")),
                    "score": float(result.metadata.score)
                }
            )
            docs.append(doc)
        except Exception as e:
            print(f"Error creating document: {str(e)}")
            continue

    chain = (
        {
            "context": RunnableLambda(lambda x: x["docs"]) | format_docs,
            "question": RunnablePassthrough()
        }
        | ChatPromptTemplate.from_template(template)
        | llm
        | JsonOutputParser(pydantic_object=StructuredResponse)
    )

    response = chain.invoke({
        "question": query,
        "docs": docs
    })

    return response
