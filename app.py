from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from models import *
from auth import *
from utils import *
from bson.objectid import ObjectId
import os
from typing import Optional
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

load_dotenv()

app = FastAPI()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URL"))
db = client["voting_system"]


def serialize_document(doc):
    """Convert MongoDB document to JSON-serializable format."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# Authentication Middleware
def admin_required(token: str = Depends()):
    decoded_token = decode_access_token(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
    if decoded_token["sub"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return decoded_token


# ===================== USER FEATURES =====================
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    token = create_access_token({"sub": user["username"]}, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
    return {"access_token": token, "token_type": "bearer"}


@app.post("/register/")
def register(user: UserRegister):
    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="User already exists")

    voter_address, private_key = generate_wallet()
    db.users.insert_one({
        "username": user.username,
        "password": hash_password(user.password),
        "voter_address": voter_address,
        "private_key": private_key
    })
    return {"message": "Registration successful", "voter_address": voter_address}


@app.post("/login/")
def login(user: UserLogin):
    db_user = db.users.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username}, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
    return {"access_token": token, "voter_address": db_user["voter_address"]}


# @app.get("/polls/")
# def view_polls():
#     polls = list(db.polls.find({}, {"candidates": 0}))
#     return {"polls": polls}

@app.get("/polls/")
def get_polls():
    polls = db.polls.find()
    serialized_polls = [serialize_document(poll) for poll in polls]
    return serialized_polls


@app.get("/polls/{poll_id}/candidates/")
def view_candidates(poll_id: str):
    poll = db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return {"poll": poll["title"], "candidates": poll["candidates"]}


@app.post("/cast_vote/")
def cast_vote(
        vote: Vote,
        token: str = Depends(get_current_token)
):
    username = decode_access_token(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))["sub"]
    db_user = db.users.find_one({"username": username})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    poll = db.polls.find_one({"_id": ObjectId(vote.poll_id)})
    if not poll or not poll.get("is_active", True):
        raise HTTPException(status_code=404, detail="Poll not active or not found")

    candidate = next((c for c in poll["candidates"] if c["id"] == vote.candidate_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if db.votes.find_one({"username": username, "poll_id": vote.poll_id}):
        raise HTTPException(status_code=400, detail="User has already voted in this poll")

    db.votes.insert_one({
        "username": username,
        "poll_id": vote.poll_id,
        "candidate_id": vote.candidate_id
    })
    return {"message": "Vote cast successfully"}


# @app.get("/voting_history/")
# def voting_history(token: str = Depends(get_current_token)):
#     username = decode_access_token(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))["sub"]
#     votes = list(db.votes.find({"username": username}))
#     return {"voting_history": votes}

@app.get("/voting_history/")
def voting_history(token: str = Depends(get_current_token)):
    username = decode_access_token(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))["sub"]
    votes = list(db.votes.find({"username": username}))

    # Convert ObjectId fields to strings
    for vote in votes:
        vote["_id"] = str(vote["_id"])
        vote["poll_id"] = str(vote["poll_id"])

    return {"voting_history": votes}


# ===================== ADMIN FEATURES =====================

@app.post("/admin/polls/")
def add_poll(poll: Poll):
    db.polls.insert_one({
        "title": poll.title,
        "description": poll.description,
        "is_active": poll.is_active,
        "candidates": []
    })
    return {"message": "Poll created successfully"}


@app.delete("/admin/polls/{poll_id}/")
def delete_poll(poll_id: str):
    result = db.polls.delete_one({"_id": ObjectId(poll_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Poll not found")
    db.votes.delete_many({"poll_id": poll_id})
    return {"message": "Poll and associated votes deleted"}


@app.put("/admin/polls/{poll_id}/")
def update_poll_status(poll_id: str, is_active: bool):
    result = db.polls.update_one({"_id": ObjectId(poll_id)}, {"$set": {"is_active": is_active}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Poll not found")
    return {"message": "Poll status updated"}


@app.post("/admin/polls/{poll_id}/candidates/")
def add_candidate_to_poll(poll_id: str, candidate: Candidate):
    candidate_id = str(ObjectId())
    result = db.polls.update_one(
        {"_id": ObjectId(poll_id)},
        {"$push": {"candidates": {"id": candidate_id, "name": candidate.name, "party": candidate.party}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Poll not found")
    return {"message": "Candidate added successfully", "candidate_id": candidate_id}


@app.delete("/admin/polls/{poll_id}/candidates/{candidate_id}/")
def delete_candidate_from_poll(poll_id: str, candidate_id: str):
    result = db.polls.update_one(
        {"_id": ObjectId(poll_id)},
        {"$pull": {"candidates": {"id": candidate_id}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Poll or candidate not found")
    return {"message": "Candidate deleted successfully"}


@app.get("/admin/polls/{poll_id}/votes/")
def get_poll_votes(poll_id: str):
    poll = db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    votes = list(db.votes.find({"poll_id": poll_id}))
    vote_counts = {candidate["id"]: 0 for candidate in poll["candidates"]}
    for vote in votes:
        vote_counts[vote["candidate_id"]] += 1

    return {"poll": poll["title"], "votes": vote_counts}
