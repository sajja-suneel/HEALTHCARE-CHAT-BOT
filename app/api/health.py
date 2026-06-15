from fastapi import APIRouter

# Initialize the router instance
router = APIRouter()

@router.get("/")
def home():
    return {
        "message": "Health Running"
    }

@router.get("/health")
def health():
    return {
        "status": "ok"
    }