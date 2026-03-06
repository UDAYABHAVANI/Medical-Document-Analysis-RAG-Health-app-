import chromadb
from chromadb.config import Settings
import os

# Create the storage path
persist_path = os.path.join(os.getcwd(), "embeddings", "chroma_store")

client = chromadb.PersistentClient(path=persist_path)
# Updated Line 9 in services/chroma_service.py
collection = client.get_or_create_collection(
    name="medical_docs",
    # This is the magic line for better scores
    metadata={"hnsw:space": "cosine"}
)


def add_document(chunk_id, embedding, text, metadata):
    """Stores the text and its numerical vector in ChromaDB."""
    collection.add(
        ids=[chunk_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata]
    )


def search_documents(query_embedding, top_k=3):
    """Finds the top 3 most relevant chunks for a question."""
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
