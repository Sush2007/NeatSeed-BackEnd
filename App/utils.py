import hashlib

def hash_password(password):
    """Simple password hashing using SHA256"""
    if not password:
        return None
    return hashlib.sha256(password.encode()).hexdigest()