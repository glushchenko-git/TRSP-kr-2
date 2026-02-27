# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from pydantic import ValidationError
import uvicorn
from typing import List

# Импортируем модели из models.py
from models import User, UserWithAge, Feedback, FeedbackValidated

# Создание экземпляра приложения FastAPI
# Можно менять имя переменной для проверки задания 1.1 (например, application = FastAPI())
app = FastAPI(title="Контрольная работа №1", description="Решение всех заданий")

# --- Хранилища данных (in-memory) ---
# Задание 1.4: Создаем экземпляр пользователя
user_db: User = User(name="Georgi", id=1)  

# Задание 2.1 и 2.2: Хранилище для отзывов (список)
feedbacks_db: List[FeedbackValidated] = []

# ------------------------------------------------------------
# Задание 1.1: Корневой маршрут с JSON
# ------------------------------------------------------------
@app.get("/")
async def read_root():
    return {"message": "Welcome to my FastAPI application!"}
    # Для проверки автоперезагрузки:
    # return {"message": "Auto-reload really works"}

# ------------------------------------------------------------
# Задание 1.2: Возврат HTML-страницы    
# ------------------------------------------------------------
@app.get("/html", response_class=HTMLResponse)
async def get_html_page():
    """
    Возвращает HTML страницу из файла index.html.
    """
    return FileResponse("index.html")

# Альтернативный вариант: корневой маршрут тоже может возвращать HTML
# Чтобы не ломать задание 1.1, я сделал отдельный маршрут /html
# Если нужно именно на "/", замените декоратор на @app.get("/", response_class=HTMLResponse)

# ------------------------------------------------------------
# Задание 1.3: POST /calculate с двумя числами
# ------------------------------------------------------------
@app.post("/calculate")
async def calculate_sum(num1: int, num2: int):
    """
    Принимает два числа (num1 и num2) в виде query параметров
    и возвращает их сумму.
    Пример запроса: POST /calculate?num1=5&num2=10
    """
    result = num1 + num2
    return {"result": result}

# ------------------------------------------------------------
# Задание 1.4: GET /users возвращает данные пользователя из models.py
# ------------------------------------------------------------
@app.get("/users", response_model=User)
async def get_user():
    """
    Возвращает данные пользователя, созданного в user_db.
    """
    return user_db

# ------------------------------------------------------------
# Задание 1.5: POST /user принимает JSON и добавляет поле is_adult
# ------------------------------------------------------------
@app.post("/user")
async def check_user_age(user: UserWithAge):
    """
    Принимает JSON с именем и возрастом, возвращает те же данные
    с дополнительным полем is_adult.
    """
    is_adult = user.age >= 18
    # Возвращаем расширенный словарь
    return {
        "name": user.name,
        "age": user.age,
        "is_adult": is_adult
    }

# ------------------------------------------------------------
# Задание 2.1: POST /feedback (базовый, без валидации)
# ------------------------------------------------------------
@app.post("/feedback_v1")
async def create_feedback(feedback: Feedback):
    """
    Принимает обратную связь и сохраняет её в список.
    Внимание: Это задание 2.1 (без строгой валидации).
    Для удобства я сделал отдельный эндпоинт /feedback_v1.
    """
    # Преобразуем в словарь и сохраняем (можно хранить как есть)
    feedbacks_db.append(FeedbackValidated(name=feedback.name, message=feedback.message))
    return {"message": f"Feedback received. Thank you, {feedback.name}."}

# ------------------------------------------------------------
# Задание 2.2: POST /feedback с расширенной валидацией
# ------------------------------------------------------------
@app.post("/feedback", response_model=dict)
async def create_feedback_validated(feedback: FeedbackValidated):
    """
    Принимает обратную связь с валидацией:
    - name: 2-50 символов
    - message: 10-500 символов, без запрещенных слов ("крингк", "рофл", "вайб")
    Сохраняет данные в список и возвращает подтверждение.
    """
    # Сохраняем отзыв в базу данных (список)
    feedbacks_db.append(feedback)
    
    # Возвращаем успешный ответ
    return {"message": f"Спасибо, {feedback.name}! Ваш отзыв сохранён."}

# ------------------------------------------------------------
# Дополнительный эндпоинт для просмотра всех отзывов (не обязателен, но полезен)
# ------------------------------------------------------------
@app.get("/feedbacks", response_model=List[FeedbackValidated])
async def get_all_feedbacks():
    """
    Возвращает список всех сохраненных отзывов.
    """
    return feedbacks_db

# ------------------------------------------------------------
# Запуск приложения (для разработки)
# ------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    # Если имя переменной приложения изменить, например на "application",
    # то команда запуска станет: uvicorn app:application --reload