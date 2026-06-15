from fastapi import APIRouter
from pydantic import BaseModel
from app.rag.generator import generate_answer

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
def chat(request: ChatRequest):
    result = generate_answer(
        request.question,
        session_id="default_session"
    )

    answer = result.get(
        "answer",
        "No answer generated"
    )

    # Truncate answer if it exceeds 1000 characters
    if len(answer) > 1000:
        answer = answer[:997] + "..."

    metadata = result.get(
        "metadata",
        {}
    )

    return {
        "question": request.question,
        "answer": answer,
        "metadata": metadata
    }