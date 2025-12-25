# Pereval API

API для добавления и модерации перевалов.

## Установка

1. Клонируйте репозиторий
2. Установите PostgreSQL
3. Создайте базу данных: `createdb pereval`
4. Настройте переменные окружения в `.env`
5. Установите зависимости: `pip install -r requirements.txt`
6. Инициализируйте БД: `python init_db.py`
7. Запустите сервер: `uvicorn main:app --reload`

## API Endpoints

- `POST /submitData` - добавление нового перевала
- `GET /` - информация о API
- `GET /health` - проверка здоровья

## Пример запроса

```bash
curl -X POST "http://localhost:8000/submitData" \
  -H "Content-Type: application/json" \
  -d '{
    "beauty_title": "пер.",
    "title": "Пхия",
    "add_time": "2021-09-22 13:18:13",
    "user": {
      "email": "test@mail.ru",
      "fam": "Иванов",
      "name": "Иван",
      "otc": "Иванович",
      "phone": "+7 999 123 45 67"
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
  }'
