from fastapi import FastAPI, HTTPException, Depends, Header
from bson import ObjectId
from app.db import users
from app.auth import hash_password, verify_password, create_token, decode_token
from app.models import UserCreate, LoginRequest

app = FastAPI()


def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization
        payload = decode_token(token)
        user = users.find_one({"_id": ObjectId(payload["id"])})
        if not user or not user["isActive"]:
            raise HTTPException(status_code=403, detail="Access denied")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/signup")
def signup(data: UserCreate):
    if users.find_one({"username": data.username}):
        raise HTTPException(400, "User exists")

    user = {
        "username": data.username,
        "password": hash_password(data.password),
        "role": "user",
        "isActive": True
    }

    users.insert_one(user)
    return {"msg": "User created"}


@app.post("/login")
def login(data: LoginRequest):
    user = users.find_one({"username": data.username})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")

    if not user["isActive"]:
        raise HTTPException(403, "User revoked")

    token = create_token({
        "id": str(user["_id"]),
        "role": user["role"]
    })

    return {"token": token}


@app.get("/me")
def hello(user=Depends(get_current_user)):
    return {"message": f"Hello {user['username']}"}


@app.post("/revoke/{user_id}")
def revoke(user_id: str, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admins only")

    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"isActive": False}}
    )

    return {"msg": "User revoked"}
