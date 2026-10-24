
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


# --------------------------------------------------
# Embedding model
# --------------------------------------------------

def get_embeddings():
    """Load the embedding model used by DocuMind AI."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# --------------------------------------------------
# Create FAISS vector store
# --------------------------------------------------

def create_vector_store(chunks: list[dict]) -> FAISS:
    """
    Convert text chunks into embeddings and create a FAISS index.

    Each chunk must contain:
    - text
    - document_id
    - filename
    - page_number
    """

    if not chunks:
        raise ValueError("No text chunks available to index.")

    texts = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        # Validate the chunk text.
        text = chunk.get("text", "")

        if not isinstance(text, str) or not text.strip():
            continue

        # Preserve metadata for source citations.
        metadata = {
            "document_id": chunk.get("document_id", ""),
            "filename": chunk.get("filename", "Unknown document"),
            "page_number": chunk.get("page_number", 1),
        }

        texts.append(text.strip())
        metadatas.append(metadata)

    if not texts:
        raise ValueError(
            "No valid text chunks found. "
            "Check PDF extraction and chunk_service.py."
        )

    embeddings = get_embeddings()

    vector_store = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
    )

    return vector_store


# --------------------------------------------------
# Save FAISS vector store
# --------------------------------------------------

def save_vector_store(
    vector_store: FAISS,
    index_path: str,
) -> None:
    """Save the FAISS index to a local directory."""

    vector_store.save_local(index_path)


# --------------------------------------------------
# Load FAISS vector store
# --------------------------------------------------

def load_vector_store(index_path: str) -> FAISS:
    """Load a previously saved local FAISS index."""

    embeddings = get_embeddings()

    return FAISS.load_local(
        index_path,
        embeddings,
        allow_dangerous_deserialization=True,
    )
