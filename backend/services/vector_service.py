
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings


def get_embeddings():
    """Load the lightweight FastEmbed embedding model."""
    return FastEmbedEmbeddings(
       model_name="BAAI/bge-small-en-v1.5"
    )


def create_vector_store(chunks: list[dict]) -> FAISS:
    """Create a FAISS index from document chunks."""

    if not chunks:
        raise ValueError("No text chunks available to index.")

    texts = []
    metadatas = []

    for chunk in chunks:
        text = chunk.get("text", "")

        if not isinstance(text, str) or not text.strip():
            continue

        texts.append(text.strip())
        metadatas.append({
            "document_id": chunk.get("document_id", ""),
            "filename": chunk.get("filename", "Unknown document"),
            "page_number": chunk.get("page_number", 1),
        })

    if not texts:
        raise ValueError("No valid text chunks found.")

    embeddings = get_embeddings()

    return FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
    )


def save_vector_store(vector_store: FAISS, index_path: str) -> None:
    """Save the FAISS index."""
    vector_store.save_local(index_path)


def load_vector_store(index_path: str) -> FAISS:
    """Load an existing FAISS index."""
    return FAISS.load_local(
        index_path,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )
