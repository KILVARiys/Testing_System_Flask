# 📝 Testing System

> Полноценная веб-система для создания и прохождения тестов с аутентификацией пользователей, таймером, историей попыток и визуализацией прогресса.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-lightgrey.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0%2B-brightgreen.svg)](https://www.sqlite.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-3.0%2B-orange.svg)](https://www.chartjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Возможности

### 🔐 Аутентификация и пользователи
- ✅ Регистрация с валидацией (email, username, пароль)
- ✅ Вход по email или username
- ✅ Хэширование паролей (Werkzeug)
- ✅ Защищённые маршруты (Flask-Login)
- ✅ Flash-сообщения об ошибках и успехах

### 📋 Управление тестами
- ✅ Создание тестов через динамическую форму
- ✅ Добавление вопросов с вариантами ответов
- ✅ Отметка правильных ответов
- ✅ Установка ограничения по времени
- ✅ Адаптивный интерфейс создания тестов

### ⏱️ Прохождение тестов
- ✅ Список доступных тестов с информацией
- ✅ Отображение количества вопросов и лучшего результата
- ✅ JavaScript-таймер с авто-отправкой
- ✅ Проверка правильности ответов
- ✅ Подсчёт и сохранение результатов

### 📊 Личный кабинет
- ✅ История всех попыток в таблице
- ✅ Процент правильных ответов
- ✅ График прогресса (Chart.js)
- ✅ Отслеживание улучшения результатов

### 🎨 Интерфейс
- ✅ Современный минималистичный дизайн
- ✅ Адаптивная вёрстка (mobile-friendly)
- ✅ CSS-переменные для кастомизации
- ✅ Интуитивная навигация

## 🚀 Быстрый старт

### Предварительные требования
- Python 3.8 или выше
- pip (менеджер пакетов Python)
- Git (опционально)

### Установка

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/yourusername/testing-system.git
cd testing-system
```

2. **Создайте виртуальное окружение**
```bash
python -m venv venv
```
```bash
# Windows
venv\Scripts\activate
```
```bash
# Linux/MacOS
source venv/bin/activate
```
3. **Установите зависимости**
```bash
pip install -r requirements.txt
```
4. **Настройте переменные окружения**
```bash
# Создайте файл .env в корне проекта
cp .env.example .env

# Отредактируйте .env файл

Пример .env файла:
# Секретный ключ Flask (обязательно измените!)
SECRET_KEY=your-super-secret-random-string-here

# Путь к базе данных
DATABASE_PATH=database.db

# Режим отладки (True для разработки)
FLASK_DEBUG=True
```
5. **Запустите приложение**
```bash
python app.py
```
6. **Откройте в браузере**
```bash
http://127.0.0.1:5000
```

## 📦 Структура проекта
```
testing-system/
│
├── app.py                 # Основной файл приложения
├── requirements.txt       # Зависимости Python
├── .env                   # Переменные окружения
├── .env.example          # Пример конфигурации
├── README.md             # Документация
│
├── static/               # Статические файлы
│   └── style.css        # Стили приложения
│
├── templates/            # HTML шаблоны
│   ├── index.html       # Главная страница
│   ├── login.html       # Страница входа
│   ├── register.html    # Страница регистрации
│   ├── tests.html       # Список тестов
│   ├── test_detail.html # Прохождение теста
│   ├── create_test.html # Создание теста
│   └── profile.html     # Профиль пользователя
│
└── database.db           # База данных SQLite (создаётся автоматически)
```

## 🗄️ Схема базы данных

### Таблица `users` - Пользователи системы

| Поле           | Тип данных     | Ограничения                  | Описание                    |
|----------------|----------------|------------------------------|-----------------------------|
| id             | INTEGER        | PRIMARY KEY, AUTOINCREMENT   | Уникальный идентификатор    |
| username       | TEXT           | NOT NULL, UNIQUE             | Имя пользователя            |
| email          | TEXT           | NOT NULL, UNIQUE             | Электронная почта           |
| password_hash  | TEXT           | NOT NULL                     | Хэшированный пароль         |

**Индексы:**
- `username` (UNIQUE)
- `email` (UNIQUE)

---

### Таблица `tests` - Тесты

| Поле           | Тип данных     | Ограничения                  | Описание                    |
|----------------|----------------|------------------------------|-----------------------------|
| id             | INTEGER        | PRIMARY KEY, AUTOINCREMENT   | Уникальный идентификатор    |
| title          | TEXT           | NOT NULL                     | Название теста              |
| description    | TEXT           | NOT NULL                     | Описание теста              |
| time_limit     | INTEGER        | NOT NULL                     | Лимит времени (в минутах)   |

---

### Таблица `questions` - Вопросы тестов

| Поле           | Тип данных     | Ограничения                  | Описание                    |
|----------------|----------------|------------------------------|-----------------------------|
| id             | INTEGER        | PRIMARY KEY, AUTOINCREMENT   | Уникальный идентификатор    |
| test_id        | INTEGER        | NOT NULL, FOREIGN KEY        | Ссылка на тест              |
| question_text  | TEXT           | NOT NULL                     | Текст вопроса               |
| question_order | INTEGER        | NOT NULL                     | Порядковый номер вопроса    |

**Внешние ключи:**
- `test_id` → `tests(id)` ON DELETE CASCADE

**Индексы:**
- `test_id, question_order` (для сортировки)

---

### Таблица `answers` - Варианты ответов

| Поле           | Тип данных     | Ограничения                  | Описание                    |
|----------------|----------------|------------------------------|-----------------------------|
| id             | INTEGER        | PRIMARY KEY, AUTOINCREMENT   | Уникальный идентификатор    |
| question_id    | INTEGER        | NOT NULL, FOREIGN KEY        | Ссылка на вопрос            |
| answer_text    | TEXT           | NOT NULL                     | Текст ответа                |
| is_correct     | BOOLEAN        | NOT NULL                     | Флаг правильного ответа     |

**Внешние ключи:**
- `question_id` → `questions(id)` ON DELETE CASCADE

---

### Таблица `user_attempts` - Попытки прохождения тестов

| Поле           | Тип данных     | Ограничения                  | Описание                    |
|----------------|----------------|------------------------------|-----------------------------|
| id             | INTEGER        | PRIMARY KEY, AUTOINCREMENT   | Уникальный идентификатор    |
| user_id        | INTEGER        | NOT NULL, FOREIGN KEY        | Ссылка на пользователя      |
| test_id        | INTEGER        | NOT NULL, FOREIGN KEY        | Ссылка на тест              |
| score          | INTEGER        | NOT NULL                     | Набранные баллы             |
| max_score      | INTEGER        | NOT NULL                     | Максимально возможный балл  |
| start_time     | TIMESTAMP      | NOT NULL                     | Время начала попытки        |
| end_time       | TIMESTAMP      | NULL                         | Время завершения попытки    |

**Внешние ключи:**
- `user_id` → `users(id)`
- `test_id` → `tests(id)`

**Индексы:**
- `user_id, test_id` (для быстрого поиска попыток)
- `user_id, start_time` (для сортировки истории)




## 🔄 Связи между таблицами

| Связь                    | Тип           | Описание                                           |
|--------------------------|---------------|----------------------------------------------------|
| users → user_attempts    | One-to-Many   | Один пользователь может иметь много попыток         |
| tests → user_attempts    | One-to-Many   | Один тест может быть пройден много раз              |
| tests → questions        | One-to-Many   | Один тест содержит много вопросов                   |
| questions → answers      | One-to-Many   | Один вопрос имеет несколько вариантов ответа        |


## 📝 Пример SQL-запроса для создания всех таблиц

```sql
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Таблица тестов
CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    time_limit INTEGER NOT NULL
);

-- Таблица вопросов
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_order INTEGER NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
);

-- Таблица ответов
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
);

-- Таблица попыток пользователей
CREATE TABLE IF NOT EXISTS user_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    max_score INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (test_id) REFERENCES tests (id)
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_questions_test_order ON questions(test_id, question_order);
CREATE INDEX IF NOT EXISTS idx_attempts_user_test ON user_attempts(user_id, test_id);
CREATE INDEX IF NOT EXISTS idx_attempts_user_time ON user_attempts(user_id, start_time);
```

## 🛠️ Технологии

### Backend
* Flask - Веб-фреймворк

* Flask-Login - Управление сессиями

* Werkzeug - Хэширование паролей

* SQLite3 - База данных

* Python-dotenv - Конфигурация

### Frontend
* HTML5 - Структура страниц

* CSS3 - Стилизация (Flexbox, Grid, переменные)

* JavaScript (Vanilla) - Интерактивность

* Chart.js - Визуализация данных
