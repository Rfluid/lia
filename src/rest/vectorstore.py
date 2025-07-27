import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from langchain_core.documents import Document

from src.agent import workflow

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/documents",
    summary="Upload and add text files to the vector database (Milvus).",
    description="""
Upload one or more text-based files to be stored in the vector database.

**Accepted file types:**
- Plain text files (`.txt`)
- JSON files (`.json`)
- CSV files (`.csv`)

**Requirements:**
- Files must be UTF-8 decodable.
- Each file will be embedded and stored along with its metadata (`filename`, `content_type`).

**Notes:**
- Binary files (e.g., images, PDFs, Word documents) are not supported in this endpoint.
- To add richer document types (e.g., PDF, DOCX), use specialized extraction endpoints.
""",
)
async def upload_documents_to_vectorstore(
    files: Annotated[list[UploadFile], File(...)]
):
    """
    Uploads text-based files and adds them to the Milvus vector store.

    Args:
        files (List[UploadFile]): List of uploaded files (must be text-based and UTF-8 decodable).

    Returns:
        str: Message indicating the number of successfully added documents.

    Raises:
        HTTPException: If any error occurs during file reading or document storage.
    """
    try:
        logger.info(f"Received {len(files)} files to add to the vectorstore.")

        documents: list[Document] = []

        for file in files:
            content = await file.read()
            content_str = content.decode(
                "utf-8", errors="ignore"
            )  # decode binary to string
            doc = Document(
                page_content=content_str,
                metadata={"filename": file.filename, "content_type": file.content_type},
            )
            documents.append(doc)

        if not documents:
            raise ValueError("No valid documents extracted from uploaded files.")

        workflow.vector_manager.add_documents(documents)

        logger.info(
            f"Successfully added {len(documents)} documents to the vectorstore."
        )
        return f"Successfully added {len(documents)} documents."
    except Exception as e:
        logger.error(
            f"Error uploading documents to vectorstore: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Error uploading documents: {str(e)}"
        ) from e
