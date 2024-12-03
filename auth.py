from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Union
from config import SECRET_KEY, ALGORITHM


# Generate JWT token
def create_access_token(data: dict, secret_key: str, algorithm: str):
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


# Decode JWT token
def decode_access_token(token: str, secret_key: str, algorithm: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        raise Exception("Token is invalid or expired")
