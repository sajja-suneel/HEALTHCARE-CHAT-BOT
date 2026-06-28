# C:\Users\sajja\vscode\health\backend\app\api\auth.py
import os
import certifi
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from pymongo import MongoClient
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "Medical Assistant"

class LoginRequest(BaseModel):
    email: str
    password: str

# MongoDB Connection (matching your chat_history.py setup)
MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017"
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
except TypeError:
    client = MongoClient(MONGO_URI, ssl_ca_certs=certifi.where())

db = client["healthcare_db"]
users_collection = db["users"]

@router.post("/signup")
def signup(request: SignupRequest):
    email = request.email.strip().lower()
    
    # Simple email validation
    if "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address."
        )

    # Check if email is already registered
    if users_collection.find_one({"email": email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Hash user password
    hashed_pwd = hash_password(request.password)

    user_data = {
        "name": request.name.strip(),
        "email": email,
        "password": hashed_pwd,
        "role": request.role
    }
    
    users_collection.insert_one(user_data)

    return {
        "message": "User registered successfully",
        "user": {
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data["role"]
        }
    }

@router.post("/login")
def login(request: LoginRequest):
    email = request.email.strip().lower()
    user = users_collection.find_one({"email": email})

    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    return {
        "message": "Login successful",
        "user": {
            "name": user["name"],
            "email": user["email"],
            "role": user.get("role", "Medical Assistant")
        }
    }