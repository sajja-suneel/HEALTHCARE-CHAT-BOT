# C:\Users\sajja\vscode\health\backend\app\api\chat.py
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.rag.generator import generate_answer_stream

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    session_id: str = None  # Accept active session ID from frontend

@router.post("/chat")
def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    # Return StreamingResponse with Server-Sent Events (SSE)
    return StreamingResponse(
        generate_answer_stream(request.question, session_id=session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )