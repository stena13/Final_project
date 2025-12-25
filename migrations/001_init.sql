-- migrations/001_init.sql
-- Создание новой структуры БД

-- Удаляем старые таблицы если они существуют
DROP TABLE IF EXISTS pereval_added_images CASCADE;
DROP TABLE IF EXISTS pereval_images CASCADE;
DROP TABLE IF EXISTS pereval_added CASCADE;
DROP TABLE IF EXISTS coords CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS pereval_areas CASCADE;
DROP TABLE IF EXISTS spr_activities_types CASCADE;

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    fam VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    otc VARCHAR(255),
    phone VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица координат
CREATE TABLE IF NOT EXISTS coords (
    id SERIAL PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    height INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица перевалов
CREATE TABLE IF NOT EXISTS pereval_added (
    id SERIAL PRIMARY KEY,
    beauty_title VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    other_titles VARCHAR(255),
    connect TEXT,
    add_time TIMESTAMP NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    coords_id INTEGER NOT NULL REFERENCES coords(id),
    level_winter VARCHAR(10),
    level_summer VARCHAR(10),
    level_autumn VARCHAR(10),
    level_spring VARCHAR(10),
    status VARCHAR(20) DEFAULT 'new' 
        CHECK (status IN ('new', 'pending', 'accepted', 'rejected')),
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица изображений
CREATE TABLE IF NOT EXISTS pereval_images (
    id SERIAL PRIMARY KEY,
    data TEXT NOT NULL,  -- Храним base64
    title VARCHAR(255),
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица связи перевал-изображение
CREATE TABLE IF NOT EXISTS pereval_added_images (
    id SERIAL PRIMARY KEY,
    pereval_id INTEGER NOT NULL REFERENCES pereval_added(id) ON DELETE CASCADE,
    image_id INTEGER NOT NULL REFERENCES pereval_images(id) ON DELETE CASCADE,
    UNIQUE(pereval_id, image_id)
);

-- Сохраняем старые таблицы для справочников
CREATE TABLE IF NOT EXISTS pereval_areas (
    id BIGSERIAL PRIMARY KEY,
    id_parent BIGINT NOT NULL,
    title TEXT
);

CREATE TABLE IF NOT EXISTS spr_activities_types (
    id SERIAL PRIMARY KEY,
    title TEXT
);