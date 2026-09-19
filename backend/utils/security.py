import os
import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "examcloud-ai-super-secret-jwt-key-2026-secure-token")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

# Robust, zero-dependency, Python 3.13 compatible password hashing using SHA256 PBKDF2
def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2:{salt}:{key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not isinstance(hashed_password, str):
        return False
    if not hashed_password.startswith("pbkdf2:"):
        return plain_password == hashed_password
    try:
        parts = hashed_password.split(":")
        if len(parts) != 3:
            return False
        _, salt, key_hex = parts
        key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

# Try optional JWT library, fallback to native PyJWT / python-jose / built-in HMAC-SHA256
_jwt_lib = None
try:
    import jwt as pyjwt
    _jwt_lib = pyjwt
except ImportError:
    try:
        from jose import jwt as jose_jwt
        _jwt_lib = jose_jwt
    except ImportError:
        _jwt_lib = None

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})

    if _jwt_lib:
        try:
            res = _jwt_lib.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            if isinstance(res, bytes):
                res = res.decode('utf-8')
            return res
        except Exception:
            pass

    # Built-in HS256 JWT Generator
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(to_encode, separators=(',', ':')).encode('utf-8'))
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        f"{header_b64}.{payload_b64}".encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[dict]:
    if _jwt_lib:
        try:
            return _jwt_lib.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception:
            pass

    # Built-in HS256 JWT Verification
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        expected_sig = base64url_encode(
            hmac.new(
                SECRET_KEY.encode('utf-8'),
                f"{header_b64}.{payload_b64}".encode('utf-8'),
                hashlib.sha256
            ).digest()
        )
        if not hmac.compare_digest(sig_b64, expected_sig):
            return None

        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None
        return payload
    except Exception:
        return None
