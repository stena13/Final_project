import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def init_database():
    """Инициализация базы данных"""
    conn = None
    try:
        # Подключаемся к БД
        conn = psycopg2.connect(
            host=os.getenv("FSTR_DB_HOST"),
            port=os.getenv("FSTR_DB_PORT"),
            user=os.getenv("FSTR_DB_LOGIN"),
            password=os.getenv("FSTR_DB_PASS"),
            database="pereval"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Читаем SQL файл
        with open('migrations/001_init.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Выполняем SQL
        cursor.execute(sql_script)
        print("✅ База данных успешно инициализирована!")
        
        # Импортируем исходные данные
        with open('pereval1.sql', 'r', encoding='utf-8') as f:
            original_data = f.read()
        
        # Выполняем только INSERT запросы из оригинального файла
        lines = original_data.split('\n')
        insert_queries = [line for line in lines if line.strip().upper().startswith('INSERT')]
        
        for query in insert_queries:
            try:
                cursor.execute(query)
            except Exception as e:
                print(f"⚠️ Ошибка при импорте данных: {e}")
                continue
        
        print("✅ Исходные данные импортированы!")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_database()