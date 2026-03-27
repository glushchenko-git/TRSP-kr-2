# main.py - основной файл приложения
from fastapi import FastAPI, HTTPException, status, Request, Response, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
import uuid
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import time
from datetime import datetime
import re

app = FastAPI(title="Server Applications Development")

# ==================== Задание 3.1 ====================
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)
    is_subscribed: bool = False

@app.post("/create_user", status_code=status.HTTP_200_OK)
async def create_user(user: UserCreate):
    return user.model_dump()

# ==================== Задание 3.2 ====================
sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99}
]

@app.get("/product/{product_id}")
async def get_product(product_id: int):
    for product in sample_products:
        if product["product_id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/products/search")
async def search_products(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 10
):
    results = []
    for product in sample_products:
        if keyword.lower() in product["name"].lower():
            if category is None or product["category"].lower() == category.lower():
                results.append(product)
    return results[:limit]

# ==================== Задание 5.1 ====================
# Временное хранилище сессий (в реальном приложении используйте Redis или БД)
sessions = {}

class LoginRequest(BaseModel):
    username: str
    password: str

# Простая проверка учетных данных (для демонстрации)
VALID_CREDENTIALS = {"user123": "password123", "alice": "secret"}

@app.post("/login")
async def login(login_data: LoginRequest, response: Response):
    if login_data.username in VALID_CREDENTIALS and \
       VALID_CREDENTIALS[login_data.username] == login_data.password:
        
        session_token = str(uuid.uuid4())
        sessions[session_token] = {
            "user_id": login_data.username,
            "created_at": time.time()
        }
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=3600,  # 1 час
            secure=False   # Для тестирования, в продакшене должно быть True
        )
        return {"message": "Login successful"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/user")
async def get_user(request: Request):
    session_token = request.cookies.get("session_token")
    
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session = sessions[session_token]
    return {
        "user_id": session["user_id"],
        "profile": {
            "username": session["user_id"],
            "email": f"{session['user_id']}@example.com"
        }
    }

# ==================== Задание 5.2 ====================
SECRET_KEY = "your-secret-key-here-change-in-production"
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Хранилище пользователей
users_db = {
    "user123": {"id": "550e8400-e29b-41d4-a716-446655440000", "password": "password123", "name": "John Doe"},
    "alice": {"id": "660e8400-e29b-41d4-a716-446655440001", "password": "secret", "name": "Alice Smith"}
}

@app.post("/login_signed")
async def login_signed(login_data: LoginRequest, response: Response):
    if login_data.username in users_db and \
       users_db[login_data.username]["password"] == login_data.password:
        
        user_id = users_db[login_data.username]["id"]
        # Создаем подписанный токен
        signed_token = serializer.dumps(user_id)
        
        response.set_cookie(
            key="session_token",
            value=signed_token,
            httponly=True,
            max_age=3600,
            secure=False
        )
        return {"message": "Login successful", "user_id": user_id}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/profile")
async def get_profile(request: Request):
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail={"message": "Unauthorized"})
    
    try:
        user_id = serializer.loads(session_token, max_age=3600)
    except SignatureExpired:
        raise HTTPException(status_code=401, detail={"message": "Session expired"})
    except BadSignature:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"})
    
    # Находим пользователя по ID
    user = None
    for u in users_db.values():
        if u["id"] == user_id:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail={"message": "Unauthorized"})
    
    return {
        "user_id": user_id,
        "username": [k for k, v in users_db.items() if v["id"] == user_id][0],
        "name": user["name"]
    }

# ==================== Задание 5.3 ====================
# Расширенная версия с динамическим временем жизни сессии
class SessionData:
    def __init__(self, user_id: str, last_activity: float):
        self.user_id = user_id
        self.last_activity = last_activity

def create_signed_session(user_id: str, timestamp: int) -> str:
    """Создает подписанную сессию в формате user_id.timestamp.signature"""
    data = f"{user_id}.{timestamp}"
    signature = serializer.dumps(data)
    return f"{data}.{signature}"

def verify_signed_session(token: str) -> tuple:
    """Проверяет подпись и возвращает (user_id, timestamp) или выбрасывает исключение"""
    try:
        # Извлекаем данные и подпись
        parts = token.split('.')
        if len(parts) != 4:  # user_id, timestamp, signature_part1, signature_part2
            raise BadSignature("Invalid format")
        
        user_id = parts[0]
        timestamp = int(parts[1])
        signature = f"{parts[2]}.{parts[3]}"
        
        data = f"{user_id}.{timestamp}"
        # Проверяем подпись
        expected_signature = serializer.dumps(data)
        if signature != expected_signature:
            raise BadSignature("Invalid signature")
        
        return user_id, timestamp
    except (ValueError, IndexError, BadSignature):
        raise BadSignature("Invalid token")

@app.post("/login_dynamic")
async def login_dynamic(login_data: LoginRequest, response: Response):
    """Логин с динамической сессией"""
    if login_data.username in users_db and \
       users_db[login_data.username]["password"] == login_data.password:
        
        user_id = users_db[login_data.username]["id"]
        timestamp = int(time.time())
        
        # Создаем подписанный токен с временем
        token = create_signed_session(user_id, timestamp)
        
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            max_age=300,  # 5 минут
            secure=False
        )
        return {"message": "Login successful", "user_id": user_id}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/profile_dynamic")
async def get_profile_dynamic(request: Request, response: Response):
    """Защищенный маршрут с динамическим продлением сессии"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail={"message": "Unauthorized"})
    
    try:
        user_id, last_activity = verify_signed_session(session_token)
    except BadSignature:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"})
    
    current_time = int(time.time())
    time_since_last_activity = current_time - last_activity
    
    # Проверяем, не истекла ли сессия (более 5 минут)
    if time_since_last_activity > 300:
        raise HTTPException(status_code=401, detail={"message": "Session expired"})
    
    # Находим пользователя
    user = None
    username = None
    for u_name, u_data in users_db.items():
        if u_data["id"] == user_id:
            user = u_data
            username = u_name
            break
    
    if not user:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"})
    
    # Обновляем сессию, если прошло более 3 минут
    if time_since_last_activity >= 180:
        new_timestamp = current_time
        new_token = create_signed_session(user_id, new_timestamp)
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            max_age=300,
            secure=False
        )
    
    return {
        "user_id": user_id,
        "username": username,
        "name": user["name"],
        "last_activity": datetime.fromtimestamp(last_activity).isoformat(),
        "time_since_last_activity": time_since_last_activity
    }

# ==================== Задание 5.4 ====================
from fastapi import Header as FastAPIHeader
from pydantic import BaseModel

@app.get("/headers")
async def get_headers(
    user_agent: str = FastAPIHeader(..., alias="User-Agent"),
    accept_language: str = FastAPIHeader(..., alias="Accept-Language")
):
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }

# ==================== Задание 5.4 (расширенная версия с моделью) ====================
class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")
    
    @validator("accept_language")
    def validate_accept_language(cls, v):
        # Проверяем формат Accept-Language (простая валидация)
        pattern = r'^[a-zA-Z]{2}(-[a-zA-Z]{2})?(,[a-zA-Z]{2}(-[a-zA-Z]{2})?;q=[0-9]\.[0-9])*$'
        # Более простая проверка - наличие хотя бы одного языкового кода
        if not v or len(v.strip()) == 0:
            raise ValueError("Accept-Language header is required")
        return v
    
    class Config:
        allow_population_by_field_name = True

@app.get("/headers_advanced")
async def get_headers_advanced(headers: CommonHeaders = Depends()):
    return headers.dict(by_alias=True)

@app.get("/info")
async def get_info(
    headers: CommonHeaders = Depends(),
    response: Response = Depends()
):
    # Добавляем заголовок с серверным временем
    response.headers["X-Server-Time"] = datetime.now().isoformat()
    
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": headers.dict(by_alias=True)
    }

# ==================== Дополнительно: эндпоинт для тестирования ====================
@app.get("/test")
async def test_endpoint():
    return {
        "status": "ok",
        "message": "All endpoints are available",
        "endpoints": [
            "POST /create_user",
            "GET /product/{product_id}",
            "GET /products/search",
            "POST /login",
            "GET /user",
            "POST /login_signed",
            "GET /profile",
            "POST /login_dynamic",
            "GET /profile_dynamic",
            "GET /headers",
            "GET /headers_advanced",
            "GET /info"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)