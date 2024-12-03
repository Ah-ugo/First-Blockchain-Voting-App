from passlib.context import CryptContext
import os
from eth_account import Account
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_token(token: str = Depends(oauth2_scheme)) -> str:
    return token


# Hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Generate Ethereum wallet (address and private key)
def generate_wallet():
    account = Account.create(os.urandom(32))
    return account.address, account._private_key.hex()
