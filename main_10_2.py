from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, EmailStr, constr, conint, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import re
from typing_extensions import Annotated

class User(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50, description="Имя пользователя")]
    age: Annotated[int, Field(gt=18, lt=120, description="Возраст (должен быть больше 18 и меньше 120)")]
    email: EmailStr = Field(..., description="Email адрес")
    password: Annotated[str, Field(min_length=8, max_length=16, description="Пароль (8-16 символов)")]
    phone: Optional[str] = 'Unknown'
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Имя пользователя может содержать только буквы, цифры и знак подчеркивания')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну букву')
        if not re.search(r'[0-9]', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if v != 'Unknown' and not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValueError('Неверный формат телефона. Используйте формат: +1234567890 (10-15 цифр)')
        return v

class ErrorResponseModel(BaseModel):
    success: bool = False
    error_type: str
    message: str
    status_code: int
    timestamp: str = datetime.now().isoformat()
    details: Optional[Dict[str, Any]] = None

app = FastAPI(
    title="API с валидацией данных пользователя",
    description="Демонстрация проверки данных запроса и пользовательской обработки ошибок",
    version="1.0.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error['loc'])
        message = error['msg']
        error_type = error['type']
        
        errors.append({
            "field": field,
            "message": message,
            "type": error_type
        })
    
    print(f"[VALIDATION ERROR] Path: {request.url.path}")
    print(f"[VALIDATION ERROR] Errors: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponseModel(
            error_type="VALIDATION_ERROR",
            message="Ошибка валидации данных запроса",
            status_code=422,
            details={
                "errors": errors,
                "body_received": exc.body if hasattr(exc, 'body') else None
            }
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    print(f"[HTTP ERROR] Path: {request.url.path}, Status: {exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseModel(
            error_type="HTTP_ERROR",
            message=exc.detail,
            status_code=exc.status_code,
            details={"path": request.url.path}
        ).dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    print(f"[UNHANDLED ERROR] {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponseModel(
            error_type="INTERNAL_ERROR",
            message="Внутренняя ошибка сервера",
            status_code=500,
            details={"error": str(exc) if app.debug else None}
        ).dict()
    )

fake_users_db = {}

@app.get("/")
async def root():
    """Корневая конечная точка с информацией об API"""
    return {
        "message": "API регистрации пользователей с валидацией данных",
        "endpoints": {
            "POST /register": "Регистрация нового пользователя",
            "GET /users": "Получить список всех пользователей",
            "GET /users/{username}": "Получить пользователя по имени"
        },
        "validation_rules": {
            "username": "Только буквы, цифры и _, 3-50 символов",
            "age": "Целое число, больше 18 и меньше 120",
            "email": "Действительный email адрес",
            "password": "8-16 символов, минимум одна буква и одна цифра",
            "phone": "Необязательно, формат: +1234567890 (10-15 цифр)"
        }
    }

@app.post("/register")
async def register_user(user: User):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Пользователь с именем '{user.username}' уже существует"
        )
    
    fake_users_db[user.username] = user.dict()
    
    print(f"[INFO] User registered: {user.username}")
    
    return {
        "success": True,
        "message": "Пользователь успешно зарегистрирован",
        "user": {
            "username": user.username,
            "age": user.age,
            "email": user.email,
            "phone": user.phone,
            "password": "***" 
        }
    }

@app.get("/users")
async def get_all_users():
    # Возвращаем пользователей без паролей
    safe_users = []
    for username, user_data in fake_users_db.items():
        safe_user = user_data.copy()
        safe_user['password'] = '***'
        safe_users.append(safe_user)
    
    return {
        "success": True,
        "count": len(safe_users),
        "users": safe_users
    }

@app.get("/users/{username}")
async def get_user(username: str):
    user = fake_users_db.get(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с именем '{username}' не найден"
        )
    
    # Возвращаем пользователя без пароля
    safe_user = user.copy()
    safe_user['password'] = '***'
    
    return {
        "success": True,
        "user": safe_user
    }

@app.post("/validate-batch")
async def validate_batch(users: list[User]):
    """
    Конечная точка для массовой валидации пользователей
    """
    valid_users = []
    for user in users:
        if user.username not in fake_users_db:
            valid_users.append(user.dict())
    
    return {
        "success": True,
        "message": f"Валидация пройдена для {len(valid_users)} пользователей",
        "users": valid_users
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)