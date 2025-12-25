"""
Тесты для Pereval API.
Запуск: pytest test_api.py -v
"""

import pytest
import json
import base64
from fastapi.testclient import TestClient
from main import app, db
from database import Database
import os

# Тестовый клиент
client = TestClient(app)

# Тестовые данные
TEST_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

@pytest.fixture(scope="module")
def test_user_data():
    """Фикстура с тестовыми данными пользователя"""
    return {
        "email": "test_user@example.com",
        "fam": "Тестов",
        "name": "Тест",
        "otc": "Тестович",
        "phone": "+7 999 888 77 66"
    }

@pytest.fixture(scope="module")
def test_pereval_data(test_user_data):
    """Фикстура с тестовыми данными перевала"""
    return {
        "beauty_title": "пер.",
        "title": "Тестовый перевал",
        "other_titles": "Тест",
        "connect": "Соединяет две долины",
        "add_time": "2024-01-15 10:30:00",
        "user": test_user_data,
        "coords": {
            "latitude": "45.1234",
            "longitude": "7.5678",
            "height": "1500"
        },
        "level": {
            "winter": "",
            "summer": "1А",
            "autumn": "",
            "spring": ""
        },
        "images": [
            {
                "data": f"data:image/png;base64,{TEST_IMAGE_BASE64}",
                "title": "Тестовое изображение"
            }
        ]
    }

@pytest.fixture(scope="module")
def created_pereval_id(test_pereval_data):
    """Фикстура создает перевал и возвращает его ID"""
    response = client.post("/submitData", json=test_pereval_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["id"] is not None
    
    yield data["id"]
    
    # Очистка после тестов (опционально)
    # В реальном проекте используйте тестовую БД

class TestPerevalAPI:
    """Класс с тестами для Pereval API"""
    
    def test_root_endpoint(self):
        """Тест корневого endpoint-а"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "POST /submitData" in data["endpoints"]
    
    def test_health_check(self):
        """Тест проверки здоровья API"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    def test_create_pereval_success(self, test_pereval_data):
        """Тест успешного создания перевала"""
        response = client.post("/submitData", json=test_pereval_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == 200
        assert data["message"] == "Отправлено успешно"
        assert isinstance(data["id"], int)
        assert data["id"] > 0
    
    def test_create_pereval_missing_required_fields(self):
        """Тест создания перевала без обязательных полей"""
        invalid_data = {
            "title": "Только название",  # Нет других обязательных полей
            "user": {
                "email": "test@test.com",
                "fam": "Test",
                "name": "Test",
                "phone": "+7 999 999 99 99"
            }
        }
        
        response = client.post("/submitData", json=invalid_data)
        assert response.status_code == 422  # Unprocessable Entity
        
    def test_create_pereval_invalid_email(self, test_pereval_data):
        """Тест создания перевала с невалидным email"""
        invalid_data = test_pereval_data.copy()
        invalid_data["user"]["email"] = "invalid-email"
        
        response = client.post("/submitData", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_pereval_invalid_phone(self, test_pereval_data):
        """Тест создания перевала с невалидным телефоном"""
        invalid_data = test_pereval_data.copy()
        invalid_data["user"]["phone"] = "123"  # Слишком короткий номер
        
        response = client.post("/submitData", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_pereval_invalid_coords(self, test_pereval_data):
        """Тест создания перевала с невалидными координатами"""
        invalid_data = test_pereval_data.copy()
        invalid_data["coords"]["latitude"] = "не число"
        
        response = client.post("/submitData", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_pereval_invalid_height(self, test_pereval_data):
        """Тест создания перевала с невалидной высотой"""
        invalid_data = test_pereval_data.copy()
        invalid_data["coords"]["height"] = "не число"
        
        response = client.post("/submitData", json=invalid_data)
        assert response.status_code == 422
    
    def test_get_pereval_by_id_success(self, created_pereval_id):
        """Тест успешного получения перевала по ID"""
        response = client.get(f"/submitData/{created_pereval_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == created_pereval_id
        assert data["title"] == "Тестовый перевал"
        assert data["status"] == "new"
        assert "user" in data
        assert "coords" in data
        assert "level" in data
        assert "images" in data
        assert data["user"]["email"] == "test_user@example.com"
    
    def test_get_pereval_by_id_not_found(self):
        """Тест получения несуществующего перевала"""
        non_existent_id = 999999
        response = client.get(f"/submitData/{non_existent_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_get_pereval_by_id_invalid_id(self):
        """Тест получения перевала с невалидным ID"""
        response = client.get("/submitData/нечисло")
        assert response.status_code == 422
    
    def test_update_pereval_success(self, created_pereval_id):
        """Тест успешного обновления перевала"""
        update_data = {
            "title": "Обновленное название перевала",
            "connect": "Соединяет три долины",
            "level": {
                "summer": "2А",
                "winter": "1Б"
            }
        }
        
        response = client.patch(f"/submitData/{created_pereval_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["state"] == 1
        assert data["message"] == "Запись успешно обновлена"
        
        # Проверяем, что данные действительно обновились
        response = client.get(f"/submitData/{created_pereval_id}")
        data = response.json()
        
        assert data["title"] == "Обновленное название перевала"
        assert data["connect"] == "Соединяет три долины"
        assert data["level"]["summer"] == "2А"
        assert data["level"]["winter"] == "1Б"
    
    def test_update_pereval_not_found(self):
        """Тест обновления несуществующего перевала"""
        update_data = {"title": "Новое название"}
        non_existent_id = 999999
        
        response = client.patch(f"/submitData/{non_existent_id}", json=update_data)
        
        assert response.status_code == 200  # PATCH возвращает 200 даже при ошибке
        data = response.json()
        
        assert data["state"] == 0
        assert "Запись не найдена" in data["message"]
    
    def test_update_pereval_try_update_user_data(self, created_pereval_id):
        """Тест попытки обновления данных пользователя (не должно быть возможно)"""
        update_data = {
            "user": {
                "email": "newemail@test.com",
                "fam": "Новая фамилия",
                "name": "Новое имя",
                "phone": "+7 111 222 33 44"
            }
        }
        
        # В нашей реализации данные пользователя игнорируются при обновлении
        # Поэтому этот тест проверяет, что система работает корректно
        response = client.patch(f"/submitData/{created_pereval_id}", json=update_data)
        
        # Проверяем, что email остался прежним
        response = client.get(f"/submitData/{created_pereval_id}")
        data = response.json()
        
        # Email должен остаться оригинальным
        assert data["user"]["email"] == "test_user@example.com"
    
    def test_update_pereval_with_images(self, created_pereval_id):
        """Тест обновления перевала с новыми изображениями"""
        new_image_data = {
            "data": f"data:image/jpeg;base64,{TEST_IMAGE_BASE64}",
            "title": "Новое изображение"
        }
        
        update_data = {
            "title": "Перевал с новыми изображениями",
            "images": [new_image_data]
        }
        
        response = client.patch(f"/submitData/{created_pereval_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == 1
        
        # Проверяем, что изображения обновились
        response = client.get(f"/submitData/{created_pereval_id}")
        data = response.json()
        
        assert len(data["images"]) == 1
        assert data["images"][0]["title"] == "Новое изображение"
    
    def test_get_pereval_by_email_success(self, test_user_data):
        """Тест получения перевалов по email"""
        email = test_user_data["email"]
        response = client.get(f"/submitData/?user__email={email}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Проверяем, что все перевалы принадлежат указанному email
        for pereval in data:
            assert pereval["user"]["email"] == email
    
    def test_get_pereval_by_email_not_found(self):
        """Тест получения перевалов по несуществующему email"""
        non_existent_email = "nonexistent@example.com"
        response = client.get(f"/submitData/?user__email={non_existent_email}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_get_pereval_by_email_missing_param(self):
        """Тест получения перевалов без указания email"""
        response = client.get("/submitData/")
        assert response.status_code == 422  # Параметр обязателен
    
    def test_get_pereval_by_email_invalid_email_format(self):
        """Тест получения перевалов с невалидным форматом email"""
        response = client.get("/submitData/?user__email=invalid-email")
        assert response.status_code == 422
    
    def test_create_and_get_multiple_pereval(self, test_pereval_data):
        """Тест создания нескольких перевалов и получения их по email"""
        # Создаем первого пользователя
        user1_data = test_pereval_data.copy()
        user1_data["user"]["email"] = "user1@test.com"
        user1_data["title"] = "Перевал пользователя 1"
        
        response1 = client.post("/submitData", json=user1_data)
        assert response1.status_code == 200
        
        # Создаем второго пользователя
        user2_data = test_pereval_data.copy()
        user2_data["user"]["email"] = "user2@test.com"
        user2_data["title"] = "Перевал пользователя 2"
        
        response2 = client.post("/submitData", json=user2_data)
        assert response2.status_code == 200
        
        # Получаем перевалы первого пользователя
        response = client.get("/submitData/?user__email=user1@test.com")
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем, что получили только перевалы первого пользователя
        for pereval in data:
            assert pereval["user"]["email"] == "user1@test.com"
            assert pereval["title"] == "Перевал пользователя 1"
    
    def test_edge_cases_coordinates(self):
        """Тест граничных случаев для координат"""
        test_cases = [
            {
                "data": {
                    "title": "Перевал с нулевыми координатами",
                    "add_time": "2024-01-15 10:30:00",
                    "user": {
                        "email": "edge@test.com",
                        "fam": "Тест",
                        "name": "Тест",
                        "phone": "+7 999 999 99 99"
                    },
                    "coords": {
                        "latitude": "0",
                        "longitude": "0",
                        "height": "0"
                    },
                    "level": {
                        "summer": "1А"
                    }
                },
                "should_pass": True
            },
            {
                "data": {
                    "title": "Перевал с отрицательными координатами",
                    "add_time": "2024-01-15 10:30:00",
                    "user": {
                        "email": "edge2@test.com",
                        "fam": "Тест",
                        "name": "Тест",
                        "phone": "+7 999 999 99 99"
                    },
                    "coords": {
                        "latitude": "-45.1234",
                        "longitude": "-7.5678",
                        "height": "-100"  # Отрицательная высота
                    },
                    "level": {
                        "summer": "1А"
                    }
                },
                "should_pass": True  # Отрицательная высота допустима
            },
            {
                "data": {
                    "title": "Перевал с очень большими координатами",
                    "add_time": "2024-01-15 10:30:00",
                    "user": {
                        "email": "edge3@test.com",
                        "fam": "Тест",
                        "name": "Тест",
                        "phone": "+7 999 999 99 99"
                    },
                    "coords": {
                        "latitude": "90",  # Максимальная широта
                        "longitude": "180",  # Максимальная долгота
                        "height": "8848"  # Эверест
                    },
                    "level": {
                        "summer": "1А"
                    }
                },
                "should_pass": True
            }
        ]
        
        for test_case in test_cases:
            response = client.post("/submitData", json=test_case["data"])
            
            if test_case["should_pass"]:
                assert response.status_code == 200, f"Тест не прошел: {test_case['data']['title']}"
            else:
                assert response.status_code != 200, f"Тест должен был провалиться: {test_case['data']['title']}"
    
    def test_empty_images_array(self, test_user_data):
        """Тест создания перевала с пустым массивом изображений"""
        data = {
            "title": "Перевал без изображений",
            "add_time": "2024-01-15 10:30:00",
            "user": test_user_data,
            "coords": {
                "latitude": "45.1234",
                "longitude": "7.5678",
                "height": "1500"
            },
            "level": {
                "summer": "1А"
            },
            "images": []  # Пустой массив
        }
        
        response = client.post("/submitData", json=data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == 200
    
    def test_performance_multiple_requests(self):
        """Тест производительности при нескольких запросах"""
        import time
        
        test_data = {
            "title": "Перевал для теста производительности",
            "add_time": "2024-01-15 10:30:00",
            "user": {
                "email": "perf@test.com",
                "fam": "Тест",
                "name": "Тест",
                "phone": "+7 999 999 99 99"
            },
            "coords": {
                "latitude": "45.1234",
                "longitude": "7.5678",
                "height": "1500"
            },
            "level": {
                "summer": "1А"
            }
        }
        
        num_requests = 5
        times = []
        
        for i in range(num_requests):
            data = test_data.copy()
            data["title"] = f"Перевал {i}"
            
            start_time = time.time()
            response = client.post("/submitData", json=data)
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        print(f"\nСреднее время создания перевала: {avg_time:.3f} секунд")
        print(f"Минимальное время: {min(times):.3f} секунд")
        print(f"Максимальное время: {max(times):.3f} секунд")
        
        # Проверяем, что среднее время меньше 1 секунды
        assert avg_time < 1.0, f"Среднее время слишком большое: {avg_time:.3f} секунд"

class TestDatabaseIntegration:
    """Тесты интеграции с базой данных"""
    
    def test_database_connection(self):
        """Тест подключения к базе данных"""
        # Используем тот же экземпляр базы данных, что и в приложении
        conn = db.get_connection()
        assert conn is not None
        assert not conn.closed
    
    def test_database_query_execution(self):
        """Тест выполнения запросов к базе данных"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Простой запрос для проверки соединения
            cursor.execute("SELECT 1 as test_value")
            result = cursor.fetchone()
            assert result["test_value"] == 1
        finally:
            cursor.close()

def test_concurrent_requests():
    """Тест конкурентных запросов (опционально)"""
    import threading
    import queue
    
    results = queue.Queue()
    
    def make_request(request_num):
        """Функция для выполнения запроса в отдельном потоке"""
        data = {
            "title": f"Конкурентный перевал {request_num}",
            "add_time": "2024-01-15 10:30:00",
            "user": {
                "email": f"concurrent{request_num}@test.com",
                "fam": "Тест",
                "name": "Тест",
                "phone": "+7 999 999 99 99"
            },
            "coords": {
                "latitude": "45.1234",
                "longitude": "7.5678",
                "height": "1500"
            },
            "level": {
                "summer": "1А"
            }
        }
        
        try:
            response = client.post("/submitData", json=data)
            results.put((request_num, response.status_code))
        except Exception as e:
            results.put((request_num, str(e)))
    
    # Запускаем несколько потоков
    threads = []
    num_threads = 3
    
    for i in range(num_threads):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Проверяем результаты
    successful_requests = 0
    while not results.empty():
        request_num, result = results.get()
        if result == 200:
            successful_requests += 1
    
    assert successful_requests == num_threads, "Не все конкурентные запросы завершились успешно"

if __name__ == "__main__":
    # Запуск тестов напрямую
    import sys
    pytest.main([__file__, "-v"])