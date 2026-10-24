
import os

from dotenv import load_dotenv
from groq import Groq


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY is missing. Check your project's .env file."
    )

client = Groq(
    api_key=api_key,
    timeout=30.0,
    max_retries=1,
)


def generate_answer(question: str, context: str) -> str:
    """Generate an answer based only on retrieved document passages."""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are DocuMind AI, a document question-answering "
                    "assistant. Answer using only the supplied context. "
                    "If the answer is missing, say the documents do not "
                    "provide enough information. Do not invent facts. "
                    "Be concise and accurate."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Context:\n{context[:12000]}\n\n"
                    f"Question: {question}"
                ),
            },
        ],
        temperature=0.2,
        max_completion_tokens=400,
    )

    answer = response.choices[0].message.content
    return answer or "I could not generate an answer."
