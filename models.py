# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re

# Задание 1.4: Простая модель пользователя (только для GET)
class User(BaseModel):
    name: str
    id: int

# Задание 1.5: Модель пользователя с возрастом (для POST /user)
class UserWithAge(BaseModel):
    name: str
    age: int

# Задание 2.1: Базовая модель обратной связи
class Feedback(BaseModel):
    name: str
    message: str

# Задание 2.2: Модель обратной связи с валидацией
class FeedbackValidated(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Имя должно быть от 2 до 50 символов")
    message: str = Field(..., min_length=10, max_length=500, description="Сообщение должно быть от 10 до 500 символов")

    # Кастомная валидация для поля message
    @field_validator('message')
    @classmethod
    def check_forbidden_words(cls, v: str) -> str:
        # Список запрещенных слов в нижнем регистре
        forbidden_words = ['крингк', 'рофл', 'вайб']
        
        # Приводим сообщение к нижнему регистру для поиска (регистронезависимо)
        message_lower = v.lower()
        
        # Проверяем наличие каждого запрещенного слова
        for word in forbidden_words:
            # Используем границы слова \b для поиска целых слов
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, message_lower):
                raise ValueError(f"Использование недопустимых слов. Слово '{word}' запрещено.")
        
        return v