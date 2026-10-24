
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "indexes"


def search_documents(
    document_id: str,
    query: str,
    k: int = 3
) -> list[dict]:
    """Find the most relevant chunks in a saved document index."""

    index_path = INDEX_DIR / document_id

    if not index_path.exists():
        raise FileNotFoundError("No index found for this document.")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True
    )

    results = vector_store.similarity_search_with_score(
        query,
        k=k
    )

    return [
        {
            "text": doc.page_content,
            "filename": doc.metadata.get("filename"),
            "page_number": doc.metadata.get("page_number"),
            "score": float(score)
        }
        for doc, score in results
    ]
