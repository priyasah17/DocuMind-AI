
from pathlib import Path

from langchain_community.vectorstores import FAISS
from backend.services.vector_service import get_embeddings


INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "indexes"


def search_documents(
    document_id: str,
    query: str,
    k: int = 3,
) -> list[dict]:
    """Find relevant chunks using the same FastEmbed model."""

    index_path = INDEX_DIR / document_id

    if not index_path.is_dir():
        raise FileNotFoundError("No index found for this document.")

    vector_store = FAISS.load_local(
        str(index_path),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )

    results = vector_store.similarity_search_with_score(
        query,
        k=k,
    )

    return [
        {
            "text": doc.page_content,
            "filename": doc.metadata.get("filename"),
            "page_number": doc.metadata.get("page_number"),
            "score": float(score),
        }
        for doc, score in results
    ]
