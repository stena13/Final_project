О проекте

Pereval API — RESTful веб-сервис для сбора и модерации данных о горных перевалах, разработанный для Федерации спортивного туризма России (ФСТР).
Цели проекта

    Для туристов: Добавление информации о покоренных перевалах через API

    Для модераторов ФСТР: Проверка и верификация добавленных данных

    Для системы: Централизованное хранение данных о перевалах с системой модерации

Основные возможности

    Добавление новых перевалов с координатами и изображениями

    Система модерации с 4 статусами

    Редактирование записей (только со статусом "new")

    Поиск перевалов по пользователю

    Полная валидация входных данных

    Автоматическая документация API

    Комплексное тестирование

Установка и запуск
Предварительные требования

    Python 3.8+

    PostgreSQL 12+

    pip (менеджер пакетов Python)
    
Примеры запросов
1. Добавление нового перевала
bash

curl -X POST "http://localhost:8000/submitData" \
  -H "Content-Type: application/json" \
  -d '{
    "beauty_title": "пер.",
    "title": "Пхия",
    "other_titles": "Триев",
    "connect": "",
    "add_time": "2021-09-22 13:18:13",
    "user": {
      "email": "user@example.com",
      "fam": "Пупкин",
      "name": "Василий",
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
    "images": [
      {
       "data": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
        "title": "Вид с перевала"
      }
    ]
  }'

Успешный ответ:
json

{
  "status": 200,
  "message": "Отправлено успешно",
  "id": 1
}

Пример теста
python

def test_full_workflow():
    """Полный рабочий процесс: создание → получение → редактирование"""
    
    # 1. Создание перевала
    response = client.post("/submitData", json={
        "title": "Тестовый перевал",
        "add_time": "2024-01-15 10:30:00",
        "user": {
            "email": "test@example.com",
            "fam": "Тестов",
            "name": "Тест",
            "phone": "+7 999 888 77 66"
        },
        "coords": {
            "latitude": "45.1234",
            "longitude": "7.5678",
            "height": "1500"
        },
        "level": {
            "summer": "1А"
        }
    })
    
    assert response.status_code == 200
    pereval_id = response.json()["id"]
    
    # 2. Получение созданного перевала
    response = client.get(f"/submitData/{pereval_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "new"
    
    # 3. Редактирование перевала
    response = client.patch(f"/submitData/{pereval_id}", json={
        "title": "Обновленное название"
    })
    assert response.status_code == 200
    assert response.json()["state"] == 1
    
    # 4. Проверка изменений
    response = client.get(f"/submitData/{pereval_id}")
    assert response.json()["title"] == "Обновленное название"

    Описание файлов
main.py

Главный файл приложения FastAPI. Содержит:

    Модели Pydantic для валидации данных

    Все endpoint-ы API

    Конфигурацию приложения

    Middleware (CORS и другие)

database.py

Класс Database для работы с PostgreSQL. Содержит методы:

    add_pereval() - добавление нового перевала

    get_pereval_by_id() - получение перевала по ID

    update_pereval() - редактирование перевала

    get_pereval_by_email() - получение перевалов по email

    Подключение к БД с использованием переменных окружения

init_db.py

Скрипт для инициализации базы данных:

    Создание всех необходимых таблиц

    Создание индексов для производительности

    Добавление тестовых данных (опционально)

test_api.py

Полный набор тестов для API:

    Unit тесты для отдельных функций

    Интеграционные тесты для работы с БД

    End-to-end тесты для полного рабочего процесса


Технические требования

Минимальные требования

    Python: 3.8+

    PostgreSQL: 12+

    RAM: 512 MB

    Диск: 100 MB свободного места

Рекомендуемые требования

    Python: 3.10+

    PostgreSQL: 14+

    RAM: 1 GB

    Диск: 500 MB свободного места

    CPU: 2+ ядра

Зависимости

    FastAPI: Веб-фреймворк

    Uvicorn: ASGI сервер

    Psycopg2: Адаптер PostgreSQL для Python

    Pydantic: Валидация данных

    Python-dotenv: Работа с переменными окружения
