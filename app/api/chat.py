import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from app.rag.generator import generate_answer

router = APIRouter()

# Schema is clean - only contains 'question'
class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
def chat(request: ChatRequest):
    # Generates a fresh, unique session for every single query
    # This keeps history isolated and prevents any pollution
    session_id = str(uuid.uuid4())
    
    result = generate_answer(
        request.question,
        session_id=session_id
    )

    answer = result.get(
        "answer",
        "No answer generated"
    )

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