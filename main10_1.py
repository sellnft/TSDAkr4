from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ErrorResponseModel(BaseModel):
    """Стандартная модель ответа об ошибке"""
    success: bool = False
    error_code: str
    message: str
    status_code: int
    timestamp: str = datetime.now().isoformat()
    details: Optional[Dict[str, Any]] = None

class CustomExceptionA(Exception):
    """Исключение для ошибок валидации (Status 400)"""
    def __init__(self, message: str = "Ошибка валидации данных", details: Optional[Dict] = None):
        self.message = message
        self.details = details
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.error_code = "VALIDATION_ERROR"
        super().__init__(self.message)

class CustomExceptionB(Exception):
    """Исключение для ошибок 'ресурс не найден' (Status 404)"""
    def __init__(self, resource_name: str = "Ресурс", resource_id: Optional[str] = None):
        self.resource_name = resource_name
        self.resource_id = resource_id
        self.status_code = status.HTTP_404_NOT_FOUND
        self.error_code = "RESOURCE_NOT_FOUND"
        
        if resource_id:
            self.message = f"{resource_name} с ID '{resource_id}' не найден"
        else:
            self.message = f"{resource_name} не найден"
        
        self.details = {"resource_name": resource_name, "resource_id": resource_id}
        super().__init__(self.message)

app = FastAPI(
    title="API с пользовательской обработкой ошибок",
    description="Демонстрация кастомных исключений и обработчиков ошибок",
    version="1.0.0"
)

@app.exception_handler(CustomExceptionA)
async def custom_exception_a_handler(request: Request, exc: CustomExceptionA):
    """Обработчик для CustomExceptionA (ошибки валидации)"""
    print(f"[ERROR] CustomExceptionA: {exc.message}")
    print(f"[ERROR] Details: {exc.details}")
    print(f"[ERROR] Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseModel(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        ).dict()
    )

@app.exception_handler(CustomExceptionB)
async def custom_exception_b_handler(request: Request, exc: CustomExceptionB):
    """Обработчик для CustomExceptionB (ресурс не найден)"""
    print(f"[ERROR] CustomExceptionB: {exc.message}")
    print(f"[ERROR] Resource: {exc.resource_name}, ID: {exc.resource_id}")
    print(f"[ERROR] Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseModel(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        ).dict()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Обработчик для всех необработанных исключений"""
    print(f"[ERROR] Unhandled exception: {type(exc).__name__}: {str(exc)}")
    print(f"[ERROR] Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponseModel(
            error_code="INTERNAL_SERVER_ERROR",
            message="Внутренняя ошибка сервера",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error_type": type(exc).__name__, "error_message": str(exc)}
        ).dict()
    )

class UserRegistrationRequest(BaseModel):
    name: str
    email: str
    age: int
    phone: Optional[str] = None

class ProductRequest(BaseModel):
    product_id: str

fake_users_db = {}
fake_products_db = {
    "P001": {"id": "P001", "name": "Ноутбук", "price": 50000, "stock": 10},
    "P002": {"id": "P002", "name": "Мышь", "price": 1500, "stock": 50},
    "P003": {"id": "P003", "name": "Клавиатура", "price": 3000, "stock": 30},
}


@app.get("/")
async def root():
    """Корневая конечная точка с информацией об API"""
    return {
        "message": "API с пользовательской обработкой ошибок",
        "endpoints": {
            "POST /register": "Регистрация пользователя (может вызвать CustomExceptionA)",
            "GET /products/{product_id}": "Получение продукта (может вызвать CustomExceptionB)",
            "GET /users/{user_id}": "Получение пользователя (может вызвать CustomExceptionB)",
            "POST /validate/{value}": "Валидация значения (может вызвать CustomExceptionA)"
        }
    }

@app.post("/register")
async def register_user(user: UserRegistrationRequest):
    """
    Конечная точка для регистрации пользователя.
    Вызывает CustomExceptionA при ошибках валидации.
    """
    if user.age < 18:
        raise CustomExceptionA(
            message="Регистрация доступна только пользователям старше 18 лет",
            details={
                "provided_age": user.age,
                "minimum_age": 18,
                "field": "age"
            }
        )
    
    if user.age > 120:
        raise CustomExceptionA(
            message="Некорректный возраст",
            details={
                "provided_age": user.age,
                "max_age": 120,
                "field": "age"
            }
        )
    
    if "@" not in user.email:
        raise CustomExceptionA(
            message="Неверный формат email",
            details={
                "provided_email": user.email,
                "required_format": "email@domain.com",
                "field": "email"
            }
        )
    
    if len(user.name.strip()) < 2:
        raise CustomExceptionA(
            message="Имя должно содержать минимум 2 символа",
            details={
                "provided_name": user.name,
                "min_length": 2,
                "field": "name"
            }
        )
    
    if any(char.isdigit() for char in user.name):
        raise CustomExceptionA(
            message="Имя не должно содержать цифры",
            details={
                "provided_name": user.name,
                "field": "name"
            }
        )
    
    user_id = str(len(fake_users_db) + 1)
    fake_users_db[user_id] = user.dict()
    
    print(f"[INFO] User registered successfully: {user.name} (ID: {user_id})")
    
    return {
        "success": True,
        "message": "Пользователь успешно зарегистрирован",
        "user_id": user_id,
        "user": user.dict()
    }

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """
    Конечная точка для получения продукта по ID.
    Вызывает CustomExceptionB, если продукт не найден.
    """
    product = fake_products_db.get(product_id)
    
    if not product:
        raise CustomExceptionB(
            resource_name="Продукт",
            resource_id=product_id
        )
    
    return {
        "success": True,
        "message": "Продукт найден",
        "product": product
    }

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """
    Конечная точка для получения пользователя по ID.
    Вызывает CustomExceptionB, если пользователь не найден.
    """
    user = fake_users_db.get(user_id)
    
    if not user:
        raise CustomExceptionB(
            resource_name="Пользователь",
            resource_id=user_id
        )
    
    return {
        "success": True,
        "message": "Пользователь найден",
        "user": user
    }

@app.post("/validate/{value}")
async def validate_value(value: str, min_length: int = 3, max_length: int = 10):
    """
    Конечная точка для валидации строковых значений.
    Вызывает CustomExceptionA при нарушении правил валидации.
    """
    if len(value) < min_length:
        raise CustomExceptionA(
            message=f"Значение слишком короткое",
            details={
                "value": value,
                "current_length": len(value),
                "min_length": min_length,
                "field": "value"
            }
        )
    
    if len(value) > max_length:
        raise CustomExceptionA(
            message=f"Значение слишком длинное",
            details={
                "value": value,
                "current_length": len(value),
                "max_length": max_length,
                "field": "value"
            }
        )
    
    if not value.isalnum():
        raise CustomExceptionA(
            message="Значение должно содержать только буквы и цифры",
            details={
                "value": value,
                "allowed_chars": "a-z, A-Z, 0-9",
                "field": "value"
            }
        )
    
    return {
        "success": True,
        "message": "Валидация пройдена успешно",
        "validated_value": value
    }

@app.get("/test-exceptions")
async def test_exceptions(error_type: str = "validation"):
    """
    Тестовая конечная точка для демонстрации работы исключений.
    Параметры: validation, not_found, none
    """
    if error_type == "validation":
        raise CustomExceptionA(
            message="Это тестовая ошибка валидации",
            details={"test": True, "type": "validation_test"}
        )
    elif error_type == "not_found":
        raise CustomExceptionB(
            resource_name="Тестовый ресурс",
            resource_id="test_123"
        )
    elif error_type == "none":
        return {"message": "Исключение не вызвано"}
    else:
        return {"message": f"Неизвестный тип ошибки: {error_type}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)