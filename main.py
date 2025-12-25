from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import os
from dotenv import load_dotenv
from database import Database

# Загружаем переменные окружения
load_dotenv()

# Инициализируем FastAPI приложение
app = FastAPI(
    title="Pereval API",
    description="API для добавления, редактирования и получения данных о перевалах",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация базы данных
db = Database()

# Модели Pydantic для валидации

class User(BaseModel):
    """Модель пользователя"""
    email: EmailStr = Field(..., description="Email пользователя")
    fam: str = Field(..., min_length=1, max_length=255, description="Фамилия")
    name: str = Field(..., min_length=1, max_length=255, description="Имя")
    otc: Optional[str] = Field(None, max_length=255, description="Отчество")
    phone: str = Field(..., description="Номер телефона")
    
    @validator('phone')
    def validate_phone(cls, v):
        """Валидация номера телефона"""
        phone_digits = re.sub(r'\D', '', v)
        if len(phone_digits) < 10:
            raise ValueError('Некорректный номер телефона')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "fam": "Иванов",
                "name": "Иван",
                "otc": "Иванович",
                "phone": "+7 999 123 45 67"
            }
        }

class Coords(BaseModel):
    """Модель координат"""
    latitude: str = Field(..., description="Широта")
    longitude: str = Field(..., description="Долгота")
    height: str = Field(..., description="Высота")
    
    @validator('latitude', 'longitude')
    def validate_coordinate(cls, v):
        """Валидация координат"""
        try:
            float(v)
        except ValueError:
            raise ValueError('Координата должна быть числом')
        return v
    
    @validator('height')
    def validate_height(cls, v):
        """Валидация высоты"""
        if not v.isdigit():
            raise ValueError('Высота должна быть целым числом')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "latitude": "45.3842",
                "longitude": "7.1525",
                "height": "1200"
            }
        }

class Level(BaseModel):
    """Модель уровня сложности"""
    winter: Optional[str] = Field("", description="Сложность зимой")
    summer: Optional[str] = Field("", description="Сложность летом")
    autumn: Optional[str] = Field("", description="Сложность осенью")
    spring: Optional[str] = Field("", description="Сложность весной")
    
    class Config:
        schema_extra = {
            "example": {
                "winter": "",
                "summer": "1А",
                "autumn": "1А",
                "spring": ""
            }
        }

class Image(BaseModel):
    """Модель изображения"""
    data: str = Field(..., description="Base64 encoded image data")
    title: Optional[str] = Field(None, description="Название изображения")
    
    class Config:
        schema_extra = {
            "example": {
                "data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQE...",
                "title": "Вид с перевала"
            }
        }

class PerevalRequest(BaseModel):
    """Модель запроса для добавления перевала"""
    beauty_title: Optional[str] = Field(None, description="Красивое название")
    title: str = Field(..., min_length=1, description="Название")
    other_titles: Optional[str] = Field(None, description="Другие названия")
    connect: Optional[str] = Field(None, description="Что соединяет")
    add_time: str = Field(..., description="Время добавления")
    user: User = Field(..., description="Пользователь")
    coords: Coords = Field(..., description="Координаты")
    level: Level = Field(..., description="Уровень сложности")
    images: List[Image] = Field(default=[], description="Изображения")
    
    @validator('add_time')
    def validate_add_time(cls, v):
        """Валидация формата времени"""
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError('Неверный формат даты. Используйте: YYYY-MM-DD HH:MM:SS')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "beauty_title": "пер.",
                "title": "Пхия",
                "other_titles": "Триев",
                "connect": "",
                "add_time": "2021-09-22 13:18:13",
                "user": {
                    "email": "qwerty@mail.ru",
                    "fam": "Пупкин",
                    "name": "Василий",
                    "otc": "Иванович",
                    "phone": "+7 555 55 55"
                },
                "coords": {
                    "latitude": "45.3842",
                    "longitude": "7.1525",
                    "height": "1200"
                },
                "level": {
                    "winter": "",
                    "summer": "1А",
                    "autumn": "1А",
                    "spring": ""
                },
                "images": []
            }
        }

class UpdatePerevalRequest(BaseModel):
    """Модель запроса для обновления перевала"""
    beauty_title: Optional[str] = Field(None, description="Красивое название")
    title: Optional[str] = Field(None, description="Название")
    other_titles: Optional[str] = Field(None, description="Другие названия")
    connect: Optional[str] = Field(None, description="Что соединяет")
    add_time: Optional[str] = Field(None, description="Время добавления")
    coords: Optional[Coords] = Field(None, description="Координаты")
    level: Optional[Level] = Field(None, description="Уровень сложности")
    images: Optional[List[Image]] = Field(None, description="Изображения")
    
    @validator('add_time')
    def validate_add_time(cls, v):
        """Валидация формата времени"""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError('Неверный формат даты. Используйте: YYYY-MM-DD HH:MM:SS')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Обновленное название",
                "level": {
                    "summer": "2А"
                }
            }
        }

class PerevalResponse(BaseModel):
    """Модель ответа для добавления перевала"""
    status: int = Field(..., description="HTTP статус код")
    message: Optional[str] = Field(None, description="Сообщение")
    id: Optional[int] = Field(None, description="ID созданной записи")

class UpdatePerevalResponse(BaseModel):
    """Модель ответа для обновления перевала"""
    state: int = Field(..., description="Состояние операции (1 - успех, 0 - ошибка)")
    message: Optional[str] = Field(None, description="Сообщение")

# Endpoint-ы API

@app.get("/",
         summary="Информация о API",
         description="Возвращает информацию о доступных endpoint-ах")
async def root():
    """Корневой endpoint с информацией о API"""
    return {
        "message": "Добро пожаловать в Pereval API",
        "version": "2.0.0",
        "description": "API для работы с данными о перевалах",
        "endpoints": {
            "POST /submitData": "Добавить новый перевал",
            "GET /submitData/{id}": "Получить перевал по ID",
            "PATCH /submitData/{id}": "Редактировать перевал",
            "GET /submitData/": "Получить перевалы по email пользователя",
            "GET /health": "Проверка здоровья API",
            "GET /docs": "Документация Swagger",
            "GET /redoc": "Альтернативная документация"
        }
    }

@app.get("/health",
         summary="Проверка здоровья API",
         description="Проверяет доступность API и подключение к базе данных")
async def health_check():
    """Health check endpoint"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        
        return {
            "status": "healthy",
            "database
