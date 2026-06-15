import os
import time
from pymongo import MongoClient
import certifi

# Load MongoDB connection URI from environment variable, default to local instance
MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017"

try:
    # Use certifi to load CA certificates for secure SSL validation
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
except TypeError:
    # Fallback if the installed pymongo version is older
    client = MongoClient(MONGO_URI, ssl_ca_certs=certifi.where())

db = client["chat"]
collection = db["chat_history"]

def init_db():
    """Initializes indexes for fast querying."""
    try:
        # Create a compound index on session_id and timestamp.
        # This makes reading and sorting history extremely fast.
        collection.create_index([("session_id", 1), ("timestamp", 1)])
    except Exception as e:
        print(f"Error creating indexes: {e}")

def save_message(session_id: str, role: str, content: str):
    """Saves a conversation turn into MongoDB."""
    try:
        collection.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": time.time()  # Float epoch time
        })
    except Exception as e:
        print(f"Error saving message to MongoDB: {e}")

def get_history(session_id: str, limit: int = 10):
    """Retrieves the recent context window of messages from MongoDB."""
    try:
        # Fetch documents matching session_id, sorted by timestamp (ascending)
        cursor = collection.find({"session_id": session_id}).sort("timestamp", 1)
        
        # Convert cursor to a list
        history = list(cursor)
        
        # Take the most recent 'limit' messages
        recent = history[-limit:]
        
        return [
            {
                "role": doc["role"],
                "content": doc["content"]
            }
            for doc in recent
        ]
    except Exception as e:
        print(f"Error fetching history from MongoDB: {e}")
        return []