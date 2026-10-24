
from fastapi import FastAPI

app = FastAPI(
    title="DocuMind AI",
    description="AI-powered multi-document intelligence system",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to DocuMind AI",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "DocuMind AI"
    }
