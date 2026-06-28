# C:\Users\sajja\vscode\health\backend\app\utils\security.py
import hashlib
import os

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 HMAC-SHA256 with a random salt."""
    salt = os.urandom(16)
    # 100,000 iterations for secure key stretching
    db_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # Store salt and hash separated by a colon
    return f"{salt.hex()}:{db_hash.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored hex-encoded hash."""
    try:
        salt_hex, hash_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        # Compute the hash of the plain password
        test_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        # Compare securely
        return test_hash == expected_hash
    except Exception:
        return False