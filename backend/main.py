
import shutil
from pathlib import Path
from uuid import uuid4, UUID

import pymupdf
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from backend.services.pdf_service import extract_text_from_pdf
from backend.services.chunk_service import chunk_pages
from backend.services.vector_service import create_vector_store
from backend.services.search_service import search_documents
from backend.services.llm_service import generate_answer


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="DocuMind AI",
    description="Multi-Document Intelligence System using RAG",
    version="1.0.0",
)


# --------------------------------------------------
# Paths and configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
INDEX_DIR = BASE_DIR / "data" / "indexes"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


# --------------------------------------------------
# Request models
# --------------------------------------------------

class SearchRequest(BaseModel):
    document_id: str
    query: str
    k: int = 3


class MultiDocumentSearchRequest(BaseModel):
    document_ids: list[str]
    query: str
    k: int = 3


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def validate_query(query: str, k: int):
    if not query or not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    if not 1 <= k <= 20:
        raise HTTPException(
            status_code=400,
            detail="k must be between 1 and 20.",
        )


def normalize_document_id(document_id: str) -> str:
    try:
        return str(UUID(document_id))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID.",
        )


def get_index_path(document_id: str) -> Path:
    document_id = normalize_document_id(document_id)
    return INDEX_DIR / document_id


def get_document_path(document_id: str) -> Path:
    document_id = normalize_document_id(document_id)
    return UPLOAD_DIR / f"{document_id}.pdf"


def search_one_document(document_id: str, query: str, k: int):
    document_id = normalize_document_id(document_id)
    index_path = get_index_path(document_id)

    if not index_path.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"No index found for document {document_id}.",
        )

    return search_documents(
        document_id=document_id,
        query=query,
        k=k,
    )


def get_result_content(result: dict) -> str:
    return str(
        result.get(
            "content",
            result.get("text", result.get("page_content", "")),
        )
    )


def build_context(results: list[dict]) -> str:
    context_parts = []

    for result in results:
        filename = result.get("filename", "Unknown document")
        page = result.get(
            "page_number",
            result.get("page", "Unknown"),
        )
        content = get_result_content(result)

        context_parts.append(
            f"Filename: {filename}\n"
            f"Page: {page}\n"
            f"Content: {content}"
        )

    return "\n\n".join(context_parts)


# --------------------------------------------------
# Root and health
# --------------------------------------------------

@app.get("/")
def read_root():
    return {
        "message": "Welcome to DocuMind AI",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# Upload and process PDFs
# --------------------------------------------------

@app.post("/documents/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Please upload at least one PDF.",
        )

    results = []

    for file in files:
        document_id = str(uuid4())
        pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
        index_path = INDEX_DIR / document_id

        try:
            if not file.filename:
                raise HTTPException(
                    status_code=400,
                    detail="Filename is missing.",
                )

            if Path(file.filename).suffix.lower() != ".pdf":
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is not a PDF file.",
                )

            pdf_bytes = await file.read()

            # Validate empty files.
            if not pdf_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is empty.",
                )

            # Validate maximum file size.
            if len(pdf_bytes) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"{file.filename} exceeds the 20 MB limit.",
                )

            # Check whether the PDF can be opened.
            try:
                with pymupdf.open(
                    stream=pdf_bytes,
                    filetype="pdf",
                ) as pdf:
                    page_count = len(pdf)

            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is not a valid readable PDF.",
                ) from exc

            if page_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} contains no pages.",
                )

            # Save the PDF.
            pdf_path.write_bytes(pdf_bytes)

            # Extract text from PDF.
            pages = extract_text_from_pdf(str(pdf_path))

            if not pages:
                raise HTTPException(
                    status_code=400,
                    detail=f"No text could be extracted from {file.filename}.",
                )

            # Split pages into chunks.
            chunks = chunk_pages(
                pages,
                filename=file.filename,
                document_id=document_id,
            )

            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail=f"No chunks were created for {file.filename}.",
                )

            # Create FAISS index from chunks.
            vector_store = create_vector_store(chunks)

            # Save index in the document-specific directory.
            vector_store.save_local(str(index_path))

            # Count pages containing text.
            pages_with_text = sum(
                1
                for page in pages
                if (
                    page.get("content", page.get("text", ""))
                    if isinstance(page, dict)
                    else str(page)
                ).strip()
            )

            results.append(
                {
                    "document_id": document_id,
                    "filename": file.filename,
                    "page_count": page_count,
                    "pages_with_text": pages_with_text,
                    "chunk_count": len(chunks),
                    "status": "processed",
                }
            )

        except HTTPException:
            if pdf_path.exists():
                pdf_path.unlink()

            if index_path.exists():
                shutil.rmtree(index_path, ignore_errors=True)

            raise

        except Exception as exc:
            if pdf_path.exists():
                pdf_path.unlink()

            if index_path.exists():
                shutil.rmtree(index_path, ignore_errors=True)

            raise HTTPException(
                status_code=500,
                detail=f"Failed to process {file.filename}: {str(exc)}",
            ) from exc

        finally:
            await file.close()

    return {
        "message": "Documents uploaded and processed successfully",
        "total_documents": len(results),
        "documents": results,
    }


# --------------------------------------------------
# List uploaded documents
# --------------------------------------------------

@app.get("/documents")
def list_documents():
    documents = []

    for pdf_path in UPLOAD_DIR.glob("*.pdf"):
        document_id = pdf_path.stem
        index_path = INDEX_DIR / document_id

        documents.append(
            {
                "document_id": document_id,
                "filename": pdf_path.name,
                "status": (
                    "processed"
                    if index_path.is_dir()
                    else "index_missing"
                ),
            }
        )

    return {
        "total_documents": len(documents),
        "documents": documents,
    }


# --------------------------------------------------
# Delete a document and its index
# --------------------------------------------------

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    document_id = normalize_document_id(document_id)

    pdf_path = get_document_path(document_id)
    index_path = get_index_path(document_id)

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    pdf_path.unlink()

    if index_path.exists():
        shutil.rmtree(index_path)

    return {
        "message": "Document and its index deleted successfully",
        "document_id": document_id,
    }


# --------------------------------------------------
# Search a document
# --------------------------------------------------

@app.post("/documents/search")
def search_document(request: SearchRequest):
    validate_query(request.query, request.k)

    results = search_one_document(
        document_id=request.document_id,
        query=request.query,
        k=request.k,
    )

    return {
        "document_id": request.document_id,
        "query": request.query,
        "results": results,
    }


# --------------------------------------------------
# Ask a question about one document
# --------------------------------------------------

@app.post("/documents/ask")
def ask_question(request: SearchRequest):
    validate_query(request.query, request.k)

    results = search_one_document(
        document_id=request.document_id,
        query=request.query,
        k=request.k,
    )

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No relevant information was found.",
        )

    context = build_context(results)

    answer = generate_answer(
        question=request.query,
        context=context,
    )

    return {
        "document_id": request.document_id,
        "question": request.query,
        "answer": answer,
        "sources": results,
    }


# --------------------------------------------------
# Ask across multiple documents
# --------------------------------------------------

@app.post("/documents/ask-multiple")
def ask_multiple_documents(request: MultiDocumentSearchRequest):
    validate_query(request.query, request.k)

    if not request.document_ids:
        raise HTTPException(
            status_code=400,
            detail="Select at least one document.",
        )

    document_ids = list(dict.fromkeys(request.document_ids))
    all_results = []

    for document_id in document_ids:
        results = search_one_document(
            document_id=document_id,
            query=request.query,
            k=request.k,
        )

        for result in results:
            if isinstance(result, dict):
                source = result.copy()
            else:
                source = {"content": str(result)}

            source.setdefault("document_id", document_id)
            all_results.append(source)

    if not all_results:
        raise HTTPException(
            status_code=404,
            detail="No relevant information was found.",
        )

    context = build_context(all_results)

    answer = generate_answer(
        question=request.query,
        context=context,
    )

    return {
        "question": request.query,
        "document_ids": document_ids,
        "answer": answer,
        "sources": all_results,
    }
