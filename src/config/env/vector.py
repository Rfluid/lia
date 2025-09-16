import os

# Database
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_USERNAME = os.getenv("MILVUS_USERNAME")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "lia")

RAG_AVAILABLE = os.getenv("RAG_AVAILABLE", "true").lower() != "false"
