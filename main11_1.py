from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Dict, List
from datetime import datetime
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: int = Field(..., gt=18, lt=120)
    password: str = Field(..., min_length=8, max_length=16)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers and underscore')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserResponse(BaseModel):
    username: str
    email: str
    age: int
    created_at: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(None, gt=18, lt=120)

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    status_code: int
    timestamp: str = datetime.now().isoformat()

fake_db: Dict[str, dict] = {}
user_created_at: Dict[str, str] = {}

app = FastAPI(title="User Management API", version="1.0.0")


def save_user(username: str, user_data: dict):
    """Сохраняет пользователя в базу данных"""
    fake_db[username] = user_data
    user_created_at[username] = datetime.now().isoformat()

def get_user_from_db(username: str) -> Optional[dict]:
    """Получает пользователя из базы данных"""
    return fake_db.get(username)

def delete_user_from_db(username: str) -> bool:
    """Удаляет пользователя из базы данных"""
    if username in fake_db:
        del fake_db[username]
        del user_created_at[username]
        return True
    return False

def user_exists(username: str) -> bool:
    """Проверяет существование пользователя"""
    return username in fake_db


@app.get("/")
async def root():
    return {
        "message": "Welcome to User Management API",
        "endpoints": {
            "POST /users": "Register a new user",
            "GET /users/{username}": "Get user by username",
            "DELETE /users/{username}": "Delete user by username",
            "GET /users": "Get all users",
            "PUT /users/{username}": "Update user information"
        }
    }

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate) -> UserResponse:

    
    if user_exists(user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{user.username}' already exists"
        )
    
    
    user_data = {
        "username": user.username,
        "email": user.email,
        "age": user.age,
        "password": user.password  
    }
    save_user(user.username, user_data)
    
    return UserResponse(
        username=user.username,
        email=user.email,
        age=user.age,
        created_at=user_created_at[user.username]
    )

@app.get("/users/{username}", status_code=status.HTTP_200_OK)
async def get_user(username: str) -> UserResponse:

    user = get_user_from_db(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    return UserResponse(
        username=user["username"],
        email=user["email"],
        age=user["age"],
        created_at=user_created_at.get(username, "Unknown")
    )

@app.delete("/users/{username}", status_code=status.HTTP_200_OK)
async def delete_user(username: str):
    if not user_exists(username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    delete_user_from_db(username)
    
    return {
        "success": True,
        "message": f"User '{username}' has been deleted successfully"
    }

@app.get("/users", status_code=status.HTTP_200_OK)
async def get_all_users(limit: int = 10, skip: int = 0) -> List[UserResponse]:

    users = []
    for username, user_data in list(fake_db.items())[skip:skip + limit]:
        users.append(UserResponse(
            username=username,
            email=user_data["email"],
            age=user_data["age"],
            created_at=user_created_at.get(username, "Unknown")
        ))
    
    return users

@app.put("/users/{username}", status_code=status.HTTP_200_OK)
async def update_user(username: str, user_update: UserUpdate) -> UserResponse:

    if not user_exists(username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    user = get_user_from_db(username)
    
    if user_update.email is not None:
        user["email"] = user_update.email
    if user_update.age is not None:
        user["age"] = user_update.age
    
    fake_db[username] = user
    
    return UserResponse(
        username=username,
        email=user["email"],
        age=user["age"],
        created_at=user_created_at.get(username, "Unknown")
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)