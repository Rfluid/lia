import logging
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_milvus import Milvus

from src.config import env
from src.llm.service import load_embedding

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class VectorManager:
    """
    Manages interaction with the Milvus vector database, handling retrieval,
    insertion, and deletion of documents for RAG systems.
    """

    vectorstore: Milvus
    embeddings_model: Embeddings

    def __init__(self):
        """
        Initialize the VectorManager with an embeddings model and set up the Milvus vectorstore.
        """
        self.embeddings_model = load_embedding(
            env.TEXT_EMBEDDING_PROVIDER,
            env.TEXT_EMBEDDING_API_KEY,
            env.TEXT_EMBEDDING_MODEL_NAME,
        )
        self.vectorstore = self._load_vectorstore()

    def _load_vectorstore(self) -> Milvus:
        """
        Private method to initialize the Milvus vector store connection
        using environment variables.

        Returns:
            Milvus: Configured Milvus vectorstore instance.
        """
        try:
            logger.info("Loading Milvus vectorstore...")

            milvus_uri = env.MILVUS_URI  # Example: "http://localhost:19530"
            milvus_user = env.MILVUS_USERNAME  # Optional
            milvus_pass = env.MILVUS_PASSWORD  # Optional
            milvus_collection = env.MILVUS_COLLECTION  # Example: "my_collection"

            if not milvus_uri or not milvus_collection:
                raise ValueError(
                    "Milvus URI or Collection name not configured in env variables."
                )

            vectorstore = Milvus(
                embedding_function=self.embeddings_model,
                collection_name=milvus_collection,
                connection_args={
                    "uri": milvus_uri,
                    "user": milvus_user,
                    "password": milvus_pass,
                    # Additional args like "secure": True if you're using TLS
                },
                auto_id=True,
            )

            logger.info("Milvus vectorstore loaded successfully.")

            return vectorstore

        except Exception as e:
            logger.error(f"Error loading Milvus vectorstore: {str(e)}", exc_info=True)
            raise

    def retrieve(
        self, query: str, top_k: int = 5, metadata_filter: dict | None = None
    ) -> list[Document]:
        """
        Retrieve relevant documents from the Milvus vectorstore based on a query.

        Args:
            query (str): User's search query.
            top_k (int): Number of top documents to retrieve.
            metadata_filter (Optional[dict]): Optional metadata filters to narrow results.

        Returns:
            List[Document]: List of documents ordered by similarity.
        """
        try:
            logger.info(f"Retrieving documents for query: '{query}' (top_k={top_k})")

            results = self.vectorstore.similarity_search(
                query=query,
                k=top_k,
                filter=metadata_filter,
            )

            logger.info(f"Retrieved {len(results)} documents.")
            return results
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}", exc_info=True)
            raise

    def add_documents(self, documents: list[Document]):
        """
        Add new documents to the Milvus vectorstore.

        Args:
            documents (List[Document]): Documents to be embedded and stored.
        """
        try:
            logger.info(f"Adding {len(documents)} documents to Milvus.")
            self.vectorstore.add_documents(
                documents,
            )
            logger.info(f"Successfully added {len(documents)} documents.")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}", exc_info=True)
            raise

    def delete_document(self, document_id: str):
        """
        Delete a document from the Milvus vectorstore by its ID.

        Args:
            document_id (str): The ID of the document to delete.
        """
        try:
            logger.info(f"Deleting document with ID: {document_id}")
            self.vectorstore.delete(ids=[document_id])
            logger.info(f"Successfully deleted document with ID: {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}", exc_info=True)
            raise

    def retrieve_raw_vector(self, query: str) -> Any:
        """
        (Optional utility) Get the raw vector representation of a query.

        Args:
            query (str): Natural language query.

        Returns:
            Any: Raw vector embedding.
        """
        try:
            logger.info(f"Generating raw vector for query: '{query}'")
            return self.embeddings_model.embed_query(query)
        except Exception as e:
            logger.error(f"Error generating raw vector: {str(e)}", exc_info=True)
            raise
