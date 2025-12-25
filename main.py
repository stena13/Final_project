from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
from database import Database

app = FastAPI(
    title="Pereval API",
    description="API для добавления перевалов",
    version="1.0.0"
)

db = Database()

# Модели для валидации
class User(BaseModel):
    email: EmailStr
    fam: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    otc: Optional[str] = Field(None, max_length=255)
    phone: str
    
    @validator('phone')
    def validate_phone(cls, v):
        # Упрощенная валидация телефона
        phone_digits = re.sub(r'\D', '', v)
        if len(phone_digits) < 10:
            raise ValueError('Некорректный номер телефона')
        return v

class Coords(BaseModel):
    latitude: str
    longitude: str
    height: str
    
    @validator('latitude', 'longitude')
    def validate_coordinate(cls, v):
        try:
            float(v)
        except ValueError:
            raise ValueError('Координата должна быть числом')
        return v
    
    @validator('height')
    def validate_height(cls, v):
        if not v.isdigit():
            raise ValueError('Высота должна быть целым числом')
        return v

class Level(BaseModel):
    winter: Optional[str] = ""
    summer: Optional[str] = ""
    autumn: Optional[str] = ""
    spring: Optional[str] = ""

class Image(BaseModel):
    data: str  # base64 encoded image
    title: Optional[str] = None

class PerevalRequest(BaseModel):
    beauty_title: Optional[str] = None
    title: str = Field(..., min_length=1)
    other_titles: Optional[str] = None
    connect: Optional[str] = None
    add_time: str
    user: User
    coords: Coords
    level: Level
    images: List[Image] = []
    
    @validator('add_time')
    def validate_add_time(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError('Неверный формат даты. Используйте: YYYY-MM-DD HH:MM:SS')
        return v

class PerevalResponse(BaseModel):
    status: int
    message: Optional[str] = None
    id: Optional[int] = None

@app.post("/submitData", 
          response_model=PerevalResponse,
          summary="Добавить новый перевал",
          description="Принимает данные о перевале и сохраняет в БД")
async def submit_data(pereval: PerevalRequest):
    """
    Метод для добавления нового перевала.
    
    - Проверяет обязательные поля
    - Сохраняет данные в БД
    - Возвращает ID созданной записи
    """
    
    # Проверка обязательных полей
    required_fields = ['title', 'add_time']
    missing_fields = []
    
    for field in required_fields:
        if not getattr(pereval, field):
            missing_fields.append(field)
    
    if missing_fields:
        return PerevalResponse(
            status=400,
            message=f"Недостаточно обязательных полей: {', '.join(missing_fields)}"
        )
    
    try:
        # Преобразуем в dict
        data = pereval.dict()
        
        # Добавляем в БД
        pereval_id = db.add_pereval(data)
        
        if pereval_id:
            return PerevalResponse(
                status=200,
                message="Отправлено успешно",
                id=pereval_id
            )
        else:
            return PerevalResponse(
                status=500,
                message="Ошибка при сохранении в БД"
            )
            
    except Exception as e:
        return PerevalResponse(
            status=500,
            message=f"Ошибка сервера: {str(e)}"
        )

@app.get("/")
async def root():
    return {
        "message": "Pereval API",
        "version": "1.0.0",
        "endpoints": {
            "POST /submitData": "Добавить новый перевал"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
