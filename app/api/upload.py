import os
from typing import List
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    UploadFile,
)
from app.rag.vector_store import store_vectors

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".csv",
    ".xlsx",
    ".xls",
    ".txt",
}

def run_rag_indexing():
    """Load docs, split text, embed, and store in Qdrant."""
    store_vectors()

# Triggers document indexing in the background
@router.post("/index")
def index_documents(
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(run_rag_indexing)

    return {
        "message": (
            "RAG indexing started "
            "(load → split → embed → store)"
        )
    }
# Endpoint for uploading multiple files
@router.post("/upload-files/")
async def upload_multiple_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(
        ...,
        description="Multiple files as UploadFile",
    ),
):
    # 1. Validate all files before saving
    for file in files:
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File '{file.filename}' is not allowed. "
                    "Only PDF, DOCX, CSV, XLSX, XLS, TXT files are allowed."
                )
            )

    # 2. Create directory and save files
    os.makedirs("data/pdfs", exist_ok=True)
    saved_files = []
    
    for file in files:
        file_path = os.path.join("data/pdfs", file.filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        saved_files.append({
            "filename": file.filename,
            "content_type": file.content_type
        })

    # Trigger indexing in background
    background_tasks.add_task(run_rag_indexing)

    return {
        "message": f"Successfully uploaded {len(files)} files. RAG indexing started.",
        "files": saved_files,
    }

@router.get("/files")
def list_uploaded_files():
    pdf_dir = "data/pdfs"
    if not os.path.exists(pdf_dir):
        return []
    
    files_list = []
    for filename in os.listdir(pdf_dir):
        file_path = os.path.join(pdf_dir, filename)
        if os.path.isfile(file_path):
            files_list.append({
                "filename": filename,
                "size": os.path.getsize(file_path)
            })
    return files_list