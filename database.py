import os
import psycopg2
from psycopg2.extras import RealDictCursor, DictCursor
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class Database:
    """
    Класс для работы с базой данных PostgreSQL.
    Использует паттерн Singleton.
    """
    
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
        logger.info("Database instance created")
    
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
            logger.info("✅ Подключение к БД установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
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
                data.get('beauty_title', ''),
                data['title'],
                data.get('other_titles', ''),
                data.get('connect', ''),
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
            logger.info(f"✅ Перевал добавлен с ID: {pereval_id}")
            return pereval_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка при добавлении перевала: {e}")
            return None
        finally:
            cursor.close()
    
    def get_pereval_by_id(self, pereval_id: int) -> Optional[Dict]:
        """
        Получить запись о перевале по ID.
        
        Args:
            pereval_id: ID перевала
            
        Returns:
            Словарь с данными перевала или None если не найден
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    pa.*,
                    u.email as user_email,
                    u.fam as user_fam,
                    u.name as user_name,
                    u.otc as user_otc,
                    u.phone as user_phone,
                    c.latitude,
                    c.longitude,
                    c.height
                FROM pereval_added pa
                JOIN users u ON pa.user_id = u.id
                JOIN coords c ON pa.coords_id = c.id
                WHERE pa.id = %s
            """, (pereval_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Получаем изображения
            cursor.execute("""
                SELECT pi.id, pi.title, pi.data
                FROM pereval_images pi
                JOIN pereval_added_images pai ON pi.id = pai.image_id
                WHERE pai.pereval_id = %s
            """, (pereval_id,))
            
            images = cursor.fetchall()
            
            # Форматируем результат
            formatted_data = {
                'id': result['id'],
                'beauty_title': result['beauty_title'] or '',
                'title': result['title'],
                'other_titles': result['other_titles'] or '',
                'connect': result['connect'] or '',
                'add_time': result['add_time'].isoformat() if result['add_time'] else None,
                'date_added': result['date_added'].isoformat() if result['date_added'] else None,
                'status': result['status'],
                'user': {
                    'email': result['user_email'],
                    'fam': result['user_fam'],
                    'name': result['user_name'],
                    'otc': result['user_otc'] or '',
                    'phone': result['user_phone']
                },
                'coords': {
                    'latitude': str(result['latitude']),
                    'longitude': str(result['longitude']),
                    'height': str(result['height'])
                },
                'level': {
                    'winter': result['level_winter'] or '',
                    'summer': result['level_summer'] or '',
                    'autumn': result['level_autumn'] or '',
                    'spring': result['level_spring'] or ''
                },
                'images': [
                    {
                        'id': img['id'],
                        'title': img['title'] or '',
                        'data': img['data']
                    } for img in images
                ]
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении перевала: {e}")
            return None
        finally:
            cursor.close()
    
    def update_pereval(self, pereval_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновить запись о перевале.
        
        Args:
            pereval_id: ID перевала
            data: Новые данные
            
        Returns:
            Словарь с результатом: {'state': 0/1, 'message': 'сообщение'}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем, существует ли запись и её статус
            cursor.execute("""
                SELECT status FROM pereval_added WHERE id = %s
            """, (pereval_id,))
            
            record = cursor.fetchone()
            if not record:
                return {'state': 0, 'message': 'Запись не найдена'}
            
            if record['status'] != 'new':
                return {'state': 0, 'message': f'Редактирование запрещено. Статус записи: {record["status"]}'}
            
            # 1. Обновляем координаты (если есть в данных)
            if 'coords' in data:
                coords = data['coords']
                cursor.execute("""
                    UPDATE coords c
                    SET latitude = %s, longitude = %s, height = %s
                    FROM pereval_added pa
                    WHERE pa.id = %s AND pa.coords_id = c.id
                """, (
                    float(coords['latitude']),
                    float(coords['longitude']),
                    int(coords['height']),
                    pereval_id
                ))
            
            # 2. Обновляем основные данные перевала
            update_fields = []
            update_values = []
            
            field_mappings = {
                'beauty_title': 'beauty_title',
                'title': 'title',
                'other_titles': 'other_titles',
                'connect': 'connect',
                'add_time': 'add_time'
            }
            
            for field, db_field in field_mappings.items():
                if field in data:
                    update_fields.append(f"{db_field} = %s")
                    update_values.append(data[field])
            
            # Обновляем уровень сложности
            if 'level' in data:
                level = data['level']
                level_mappings = {
                    'winter': 'level_winter',
                    'summer': 'level_summer',
                    'autumn': 'level_autumn',
                    'spring': 'level_spring'
                }
                
                for field, db_field in level_mappings.items():
                    if field in level:
                        update_fields.append(f"{db_field} = %s")
                        update_values.append(level.get(field, ''))
            
            if update_fields:
                update_values.append(pereval_id)
                query = f"""
                    UPDATE pereval_added 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """
                cursor.execute(query, update_values)
            
            # 3. Обновляем изображения (если есть в данных)
            if 'images' in data and data['images']:
                # Удаляем старые связи и изображения
                cursor.execute("""
                    DELETE FROM pereval_images pi
                    USING pereval_added_images pai
                    WHERE pai.pereval_id = %s 
                    AND pai.image_id = pi.id
                """, (pereval_id,))
                
                cursor.execute("""
                    DELETE FROM pereval_added_images 
                    WHERE pereval_id = %s
                """, (pereval_id,))
                
                # Добавляем новые изображения
                for img in data['images']:
                    img_data = img['data']
                    if img_data.startswith('data:image'):
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
            logger.info(f"✅ Перевал {pereval_id} успешно обновлен")
            return {'state': 1, 'message': 'Запись успешно обновлена'}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка при обновлении перевала {pereval_id}: {e}")
            return {'state': 0, 'message': f'Ошибка при обновлении: {str(e)}'}
        finally:
            cursor.close()
    
    def get_pereval_by_email(self, email: str) -> List[Dict]:
        """
        Получить все перевалы по email пользователя.
        
        Args:
            email: Email пользователя
            
        Returns:
            Список перевалов
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    pa.*,
                    u.email as user_email,
                    u.fam as user_fam,
                    u.name as user_name,
                    u.otc as user_otc,
                    u.phone as user_phone,
                    c.latitude,
                    c.longitude,
                    c.height
                FROM pereval_added pa
                JOIN users u ON pa.user_id = u.id
                JOIN coords c ON pa.coords_id = c.id
                WHERE u.email = %s
                ORDER BY pa.date_added DESC
            """, (email,))
            
            results = cursor.fetchall()
            perevals = []
            
            for row in results:
                # Получаем изображения для каждого перевала
                cursor.execute("""
                    SELECT pi.id, pi.title, pi.data
                    FROM pereval_images pi
                    JOIN pereval_added_images pai ON pi.id = pai.image_id
                    WHERE pai.pereval_id = %s
                """, (row['id'],))
                
                images = cursor.fetchall()
                
                pereval_data = {
                    'id': row['id'],
                    'beauty_title': row['beauty_title'] or '',
                    'title': row['title'],
                    'other_titles': row['other_titles'] or '',
                    'connect': row['connect'] or '',
                    'add_time': row['add_time'].isoformat() if row['add_time'] else None,
                    'date_added': row['date_added'].isoformat() if row['date_added'] else None,
                    'status': row['status'],
                    'user': {
                        'email': row['user_email'],
                        'fam': row['user_fam'],
                        'name': row['user_name'],
                        'otc': row['user_otc'] or '',
                        'phone': row['user_phone']
                    },
                    'coords': {
                        'latitude': str(row['latitude']),
                        'longitude': str(row['longitude']),
                        'height': str(row['height'])
                    },
                    'level': {
                        'winter': row['level_winter'] or '',
                        'summer': row['level_summer'] or '',
                        'autumn': row['level_autumn'] or '',
                        'spring': row['level_spring'] or ''
                    },
                    'images': [
                        {
                            'id': img['id'],
                            'title': img['title'] or '',
                            'data': img['data']
                        } for img in images
                    ]
                }
                perevals.append(pereval_data)
            
            logger.info(f"✅ Найдено {len(perevals)} перевалов для email: {email}")
            return perevals
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении перевалов по email {email}: {e}")
            return []
        finally:
            cursor.close()
    
    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Соединение с БД закрыто")
