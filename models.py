from pydantic import BaseModel
from typing import Optional, List


# User Models
class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# Poll and Candidate Models
class Poll(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True


class Candidate(BaseModel):
    name: str
    party: Optional[str] = None


# Voting Model
class Vote(BaseModel):
    poll_id: str
    candidate_id: str
