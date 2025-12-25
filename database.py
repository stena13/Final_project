# database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import base64

load_dotenv()

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.host = os.getenv("FSTR_DB_HOST", "localhost")
        self.port = os.getenv("FSTR_DB_PORT", "5432")
        self.login = os.getenv("FSTR_DB_LOGIN", "postgres")
        self.password = os.getenv("FSTR_DB_PASS", "")
        self.database = os.getenv("DATABASE_NAME", "pereval")
        self.conn = None
        self.connect()
        self._initialized = True
    
    def connect(self):
        """Установка соединения с БД"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.login,
                password=self.password,
                database=self.database,
                cursor_factory=RealDictCursor
            )
            print("✅ Подключение к БД установлено")
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            raise
    
    def get_connection(self):
        """Получение активного соединения"""
        if self.conn and not self.conn.closed:
            return self.conn
        else:
            self.connect()
            return self.conn
    
    def add_pereval(self, data: Dict[str, Any]) -> Optional[int]:
        """
        Добавляет новый перевал в БД.
        
        Args:
            data: Словарь с данными перевала
            
        Returns:
            id вставленной записи или None при ошибке
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Добавляем/обновляем пользователя
            user = data['user']
            cursor.execute("""
                INSERT INTO users (email, fam, name, otc, phone)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    fam = EXCLUDED.fam,
                    name = EXCLUDED.name,
                    otc = EXCLUDED.otc,
                    phone = EXCLUDED.phone
                RETURNING id
            """, (
                user['email'], 
                user['fam'], 
                user['name'],
                user.get('otc'), 
                user['phone']
            ))
            user_id = cursor.fetchone()['id']
            
            # 2. Добавляем координаты
            coords = data['coords']
            cursor.execute("""
                INSERT INTO coords (latitude, longitude, height)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                float(coords['latitude']), 
                float(coords['longitude']), 
                int(coords['height'])
            ))
            coords_id = cursor.fetchone()['id']
            
            # 3. Добавляем перевал
            cursor.execute("""
                INSERT INTO pereval_added 
                (beauty_title, title, other_titles, connect, 
                 add_time, user_id, coords_id,
                 level_winter, level_summer, level_autumn, level_spring)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data.get('beauty_title'),
                data['title'],
                data.get('other_titles'),
                data.get('connect'),
                data['add_time'],
                user_id,
                coords_id,
                data['level'].get('winter', ''),
                data['level'].get('summer', ''),
                data['level'].get('autumn', ''),
                data['level'].get('spring', '')
            ))
            pereval_id = cursor.fetchone()['id']
            
            # 4. Добавляем изображения
            for img in data.get('images', []):
                # Декодируем base64 если нужно
                img_data = img['data']
                if img_data.startswith('data:image'):
                    # Убираем префикс data:image/...
                    img_data = img_data.split(',')[1]
                
                cursor.execute("""
                    INSERT INTO pereval_images (data, title)
                    VALUES (%s, %s)
                    RETURNING id
                """, (img_data, img.get('title')))
                image_id = cursor.fetchone()['id']
                
                cursor.execute("""
                    INSERT INTO pereval_added_images (pereval_id, image_id)
                    VALUES (%s, %s)
                """, (pereval_id, image_id))
            
            conn.commit()
            print(f"✅ Перевал добавлен с ID: {pereval_id}")
            return pereval_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка при добавлении перевала: {e}")
            return None
        finally:
            cursor.close()
    
    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()
            print("🔌 Соединение с БД закрыто")