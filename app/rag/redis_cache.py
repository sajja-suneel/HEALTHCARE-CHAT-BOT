# C:\Users\sajja\vscode\health\backend\app\rag\redis_cache.py
import os
import hashlib
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

# Connect to  Cloud Redis instance
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"Redis initialization failed: {e}")
    redis_client = None

def get_question_hash(question: str) -> str:
    """Generates a clean SHA-256 hash of the question to use as a key."""
    clean_q = question.strip().lower()
    return hashlib.sha256(clean_q.encode("utf-8")).hexdigest()

def get_cached_response(question: str) -> str:
    """Retrieves JSON payload containing answer and metadata from Redis."""
    if not redis_client:
        return None
    try:
        key = f"cache:{get_question_hash(question)}"
        return redis_client.get(key)
    except Exception as e:
        print(f"Redis cache lookup failed: {e}")
        return None

def set_cached_response(question: str, payload_json: str, ttl: int = 3600):
    """Saves RAG results to Redis with a TTL (default: 3600 seconds/1 hour)."""
    if not redis_client or not payload_json:
        return
    try:
        key = f"cache:{get_question_hash(question)}"
        redis_client.setex(key, ttl, payload_json)
    except Exception as e:
        print(f"Redis cache set failed: {e}")