from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from itertools import count
from threading import Lock

app = FastAPI()
db: dict[int, dict] = {}
_id_seq = count(start=1)
_id_lock = Lock()

def next_user_id() -> int:
    with _id_lock:
        return next(_id_seq)

def clear_db():
    """Вспомогательная функция для очистки БД в тестах"""
    global db, _id_seq
    db.clear()
    _id_seq = count(start=1)

class UserIn(BaseModel):
    username: str
    age: int

class UserOut(BaseModel):
    id: int
    username: str
    age: int

@app.post("/users", response_model=UserOut, status_code=201)
def create_user(user: UserIn):
    user_id = next_user_id()
    db[user_id] = user.model_dump()
    return {"id": user_id, **db[user_id]}

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    if user_id not in db:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, **db[user_id]}

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    if db.pop(user_id, None) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=204)

@app.get("/")
async def root():
    return {"message": "User API", "users_count": len(db)}