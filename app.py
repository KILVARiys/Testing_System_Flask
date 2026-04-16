import sqlite3
import os

from flask import Flask, redirect, render_template, request, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import json

load_dotenv()

app = Flask(__name__)
# Секретный ключ берём из .env (см. файл .env в репозитории)
app.secret_key = os.getenv('SECRET_KEY')

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'

# Модель User
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    @staticmethod
    def get(user_id):
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'database.db'))
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        return None
    
    @staticmethod
    def find_by_username(username):
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'database.db'))
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        return None
    
    @staticmethod
    def find_by_email(email):
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'database.db'))
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        return None

    @staticmethod
    def find_by_login(login):
        """Find a user by email or username."""
        # try email first
        user = User.find_by_email(login)
        if user:
            return user
        # try username
        return User.find_by_username(login)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Функция инициализации БД
def init_db():
    db_path = os.getenv('DATABASE_PATH', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Таблица тестов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            time_limit INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            question_order INTEGER NOT NULL,
            FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
        )
    ''')

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            score INTEGER NOT NULL,        -- набранные баллы
            max_score INTEGER NOT NULL,    -- максимально возможные баллы
            start_time TIMESTAMP NOT NULL, -- когда начал тест
            end_time TIMESTAMP,            -- когда закончил (NULL пока не завершён)
            timed_out INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (test_id) REFERENCES tests (id)
        )
    ''')
    
    conn.commit()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE user_attempts ADD COLUMN timed_out INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Если в БД нет тестов — добавим демо-данные
    seed_test_data(db_path)


def seed_test_data(db_path):
    """Insert a demo test if no tests exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tests')
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    try:
        cursor.execute('INSERT INTO tests (title, description, time_limit) VALUES (?, ?, ?)', ('Демо-тест', 'Пример теста, созданного автоматически', 5))
        test_id = cursor.lastrowid

        # Question 1
        cursor.execute('INSERT INTO questions (test_id, question_text, question_order) VALUES (?, ?, ?)', (test_id, 'Какой язык мы используем?', 0))
        q1 = cursor.lastrowid
        cursor.execute('INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)', (q1, 'Python', 1))
        cursor.execute('INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)', (q1, 'Java', 0))

        # Question 2
        cursor.execute('INSERT INTO questions (test_id, question_text, question_order) VALUES (?, ?, ?)', (test_id, 'HTML это язык разметки?', 1))
        q2 = cursor.lastrowid
        cursor.execute('INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)', (q2, 'Да', 1))
        cursor.execute('INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)', (q2, 'Нет', 0))

        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Простая валидация и проверка уникальности
        if not username or not email or not password or not confirm_password:
            flash('Пожалуйста, заполните все поля', 'error')
            return redirect(url_for('register'))

        # Минимальная длина пароля
        if len(password) < 8:
            flash('Пароль должен быть не менее 8 символов', 'error')
            return redirect(url_for('register'))

        # Подтверждение пароля
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))

        # Проверяем, существует ли уже пользователь с таким username или email
        if User.find_by_username(username):
            flash('Имя пользователя уже занято', 'error')
            return redirect(url_for('register'))

        if User.find_by_email(email):
            flash('Пользователь с таким email уже зарегистрирован', 'error')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        db_path = os.getenv('DATABASE_PATH', 'database.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', (username, email, password_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            # На случай гонки или если уникальность нарушена в БД
            flash('Невозможно зарегистрировать пользователя — данные уже существуют', 'error')
            return redirect(url_for('register'))
        finally:
            conn.close()

        flash('Регистрация прошла успешно. Введите данные для входа.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_value = request.form.get('login') or request.form.get('email')
        password = request.form['password']
        user = User.find_by_login(login_value)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # После успешного входа отправляем пользователя на список тестов
            return redirect(url_for('tests'))
        else:
            flash('Неверный email или пароль', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/tests')
@login_required
def tests():
    # Получаем список тестов с числом вопросов и лучшим результатом текущего пользователя
    db_path = os.getenv('DATABASE_PATH', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = '''
        SELECT 
            t.id, t.title, t.description, t.time_limit,
            COUNT(DISTINCT q.id) as question_count,
            MAX(ua.score) as best_score
        FROM tests t
        LEFT JOIN questions q ON t.id = q.test_id
        LEFT JOIN user_attempts ua ON t.id = ua.test_id AND ua.user_id = ?
        GROUP BY t.id
        ORDER BY t.id
    '''

    cursor.execute(query, (current_user.id,))
    rows = cursor.fetchall()

    tests_list = []
    for row in rows:
        test = {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'time_limit': row[3],
            'question_count': row[4] or 0,
            'best_score': row[5] if row[5] is not None else None,
        }
        tests_list.append(test)

    return render_template('tests.html', tests=tests_list)

@app.route('/test/<int:test_id>')
@login_required
def test_detail(test_id):
    # Загружаем данные теста
    db_path = os.getenv('DATABASE_PATH', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем сам тест
    cursor.execute('SELECT id, title, description, time_limit FROM tests WHERE id = ?', (test_id,))
    test_row = cursor.fetchone()
    if not test_row:
        conn.close()
        flash('Тест не найден', 'error')
        return redirect(url_for('tests'))

    test = {
        'id': test_row[0],
        'title': test_row[1],
        'description': test_row[2],
        'time_limit': test_row[3],
    }

    # Загружаем вопросы и ответы (одним запросом)
    cursor.execute('''
        SELECT q.id as qid, q.question_text, a.id as aid, a.answer_text
        FROM questions q
        LEFT JOIN answers a ON q.id = a.question_id
        WHERE q.test_id = ?
        ORDER BY q.question_order, a.id
    ''', (test_id,))

    rows = cursor.fetchall()

    # Группируем ответы по вопросам
    questions = []
    q_map = {}
    for qid, qtext, aid, atext in rows:
        if qid not in q_map:
            q = {'id': qid, 'text': qtext, 'answers': []}
            q_map[qid] = q
            questions.append(q)
        else:
            q = q_map[qid]

        if aid is not None:
            q['answers'].append({'id': aid, 'text': atext})

    # Создаём запись попытки для этого пользователя и теста (фиксируем start_time)
    total_questions = len(questions)
    start_time_str = datetime.now(timezone.utc).isoformat()
    try:
        cursor.execute('INSERT INTO user_attempts (user_id, test_id, score, max_score, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)', (current_user.id, test_id, 0, total_questions, start_time_str, None))
        attempt_id = cursor.lastrowid
        conn.commit()
    except Exception:
        # В случае ошибки не блокируем отображение теста — просто не передаём attempt_id
        attempt_id = None
        conn.rollback()
    finally:
        conn.close()

    return render_template('test_detail.html', test=test, questions=questions, attempt_id=attempt_id)


@app.route('/create_test', methods=['GET', 'POST'])
@login_required
def create_test():
    # Простая форма создания теста: данные приходят в поле 'payload' как JSON
    if request.method == 'POST':
        payload = request.form.get('payload')
        if not payload:
            flash('Нет данных для создания теста', 'error')
            return redirect(url_for('create_test'))
        try:
            data = json.loads(payload)
        except Exception:
            flash('Неверный формат данных', 'error')
            return redirect(url_for('create_test'))

        title = data.get('title')
        description = data.get('description', '')
        time_limit = int(data.get('time_limit') or 0)
        questions = data.get('questions', [])

        if not title or not questions:
            flash('Требуется название и хотя бы один вопрос', 'error')
            return redirect(url_for('create_test'))

        db_path = os.getenv('DATABASE_PATH', 'database.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO tests (title, description, time_limit) VALUES (?, ?, ?)', (title, description, time_limit))
            test_id = cursor.lastrowid

            for idx, q in enumerate(questions):
                qtext = q.get('text')
                if not qtext:
                    continue
                cursor.execute('INSERT INTO questions (test_id, question_text, question_order) VALUES (?, ?, ?)', (test_id, qtext, idx))
                qid = cursor.lastrowid
                for a in q.get('answers', []):
                    atext = a.get('text')
                    is_correct = 1 if a.get('is_correct') else 0
                    if not atext:
                        continue
                    cursor.execute('INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)', (qid, atext, is_correct))

            conn.commit()
        except Exception as e:
            conn.rollback()
            flash('Ошибка при сохранении теста: ' + str(e), 'error')
            return redirect(url_for('create_test'))
        finally:
            conn.close()

        flash('Тест успешно создан', 'success')
        return redirect(url_for('tests'))

    return render_template('create_test.html')

@app.route('/profile')
@login_required
def profile():
    # Получаем историю попыток текущего пользователя
    db_path = os.getenv('DATABASE_PATH', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ua.id, ua.test_id, t.title, ua.score, ua.max_score, ua.start_time, ua.end_time
        FROM user_attempts ua
        LEFT JOIN tests t ON ua.test_id = t.id
        WHERE ua.user_id = ?
        ORDER BY ua.start_time ASC
    ''', (current_user.id,))

    attempts = []
    labels = []
    data = []
    for aid, test_id, title, score, max_score, start_time, end_time in cursor.fetchall():
        ts = end_time or start_time
        percent = None
        try:
            if max_score and max_score > 0:
                percent = round((score / max_score) * 100, 2)
            else:
                percent = 0
        except Exception:
            percent = 0

        display_date = ts.split('T')[0] if ts else ''
        attempts.append({
            'id': aid,
            'test_id': test_id,
            'title': title,
            'score': score,
            'max_score': max_score,
            'percent': percent,
            'date': display_date,
        })
        labels.append(display_date)
        data.append(percent)

    conn.close()

    chart_data = {
        'labels': labels,
        'datasets': [{
            'label': 'Результаты тестов (%)',
            'data': data,
            'fill': False,
            'borderColor': 'rgb(75, 192, 192)',
            'tension': 0.1
        }]
    }

    return render_template('profile.html', attempts=attempts, chart_data=chart_data)


@app.route('/test/<int:test_id>/submit', methods=['POST'])
@login_required
def submit_test(test_id):
    attempt_id = request.form.get('attempt_id')
    db_path = os.getenv('DATABASE_PATH', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Список вопросов для теста
    cursor.execute('SELECT id FROM questions WHERE test_id = ?', (test_id,))
    q_rows = cursor.fetchall()
    question_ids = [r[0] for r in q_rows]
    total_questions = len(question_ids)

    # Правильные ответы mapping question_id -> set(answer_id)
    correct_map = {}
    if question_ids:
        placeholders = ','.join('?' for _ in question_ids)
        sql = f'SELECT question_id, id FROM answers WHERE question_id IN ({placeholders}) AND is_correct = 1'
        cursor.execute(sql, question_ids)
        for qid, aid in cursor.fetchall():
            # setdefault is correct: it returns the set for the key or inserts a new one
            correct_map.setdefault(qid, set()).add(aid)

    # Получаем start_time из attempt (если есть)
    start_time = None
    if attempt_id:
        cursor.execute('SELECT id, user_id, test_id, start_time, end_time FROM user_attempts WHERE id = ?', (attempt_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            flash('Попытка не найдена', 'error')
            return redirect(url_for('tests'))
        if row[1] != current_user.id:
            conn.close()
            flash('Попытка не принадлежит вам', 'error')
            return redirect(url_for('tests'))
        # Если попытка уже была завершена — не позволяем повторно отправлять
        if row[4] is not None:
            conn.close()
            flash('Эта попытка уже завершена', 'error')
            return redirect(url_for('profile'))
        try:
            start_time = datetime.fromisoformat(row[3])
        except Exception:
            start_time = None

    # Проверка времени
    cursor.execute('SELECT time_limit FROM tests WHERE id = ?', (test_id,))
    trow = cursor.fetchone()
    time_limit = trow[0] if trow else None
    # use timezone-aware UTC now to match stored start_time which is timezone-aware
    now = datetime.now(timezone.utc)
    timed_out = False
    if start_time and time_limit:
        deadline = start_time + timedelta(minutes=time_limit)
        if now > deadline:
            timed_out = True

    # Подсчёт балла
    score = 0
    for qid in question_ids:
        field = f'q_{qid}'
        val = request.form.get(field)
        if not val:
            continue
        try:
            selected = int(val)
        except ValueError:
            continue
        if qid in correct_map and selected in correct_map[qid]:
            score += 1

    end_time_str = now.isoformat()
    try:
        # Если таймаут — обнулим балл и пометим timed_out
        if timed_out:
            score_to_store = 0
            timed_flag = 1
        else:
            score_to_store = score
            timed_flag = 0

        if attempt_id:
            cursor.execute('UPDATE user_attempts SET score = ?, max_score = ?, end_time = ?, timed_out = ? WHERE id = ?', (score_to_store, total_questions, end_time_str, timed_flag, attempt_id))
        else:
            cursor.execute('INSERT INTO user_attempts (user_id, test_id, score, max_score, start_time, end_time, timed_out) VALUES (?, ?, ?, ?, ?, ?, ?)', (current_user.id, test_id, score_to_store, total_questions, now.isoformat(), end_time_str, timed_flag))
        conn.commit()
    finally:
        conn.close()

    if timed_out:
        flash(f'Время истекло. Результат: {score}/{total_questions}', 'warning')
    else:
        flash(f'Результат: {score}/{total_questions}', 'success')

    return redirect(url_for('profile'))

if __name__ == '__main__':
    init_db()
    app.run(debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true')