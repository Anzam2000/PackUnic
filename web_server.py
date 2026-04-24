import os
import sqlite3
import json
import uuid
from datetime import timedelta, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
from pathlib import Path
import random
import base64

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

DB_NAME = 'unlock_system.db'
SESSIONS_DIR = 'active_sessions'
PHOTOS_DIR = 'user_photos'

Path(SESSIONS_DIR).mkdir(exist_ok=True)
Path(PHOTOS_DIR).mkdir(exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  name TEXT NOT NULL,
                  surname TEXT NOT NULL,
                  is_admin INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS unlock_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  name TEXT,
                  surname TEXT,
                  computer_serial TEXT,
                  session_code TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS work_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  name TEXT,
                  surname TEXT,
                  computer_serial TEXT,
                  session_start TIMESTAMP,
                  session_end TIMESTAMP,
                  duration_minutes INTEGER,
                  photo_path TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    if c.fetchone()[0] == 0:
        hashed_password = generate_password_hash('admin', method='pbkdf2:sha256')
        c.execute('''INSERT INTO users (username, password, name, surname, is_admin) 
                     VALUES (?, ?, ?, ?, ?)''',
                  ('admin', hashed_password, 'Admin', 'User', 1))
        print("✅ Создан админ: admin / admin")

    conn.commit()
    conn.close()


init_db()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def add_unlock_log(user_id, username, name, surname, computer_serial, session_code):
    query_db('''INSERT INTO unlock_logs (user_id, username, name, surname, computer_serial, session_code) 
                VALUES (?, ?, ?, ?, ?, ?)''',
             [user_id, username, name, surname, computer_serial, session_code])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return "Доступ запрещен", 403
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('scan_page'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['surname'] = user['surname']
            session['is_admin'] = bool(user['is_admin'])
            session.permanent = True
            return redirect(url_for('scan_page'))
        else:
            return render_template('login.html', error="Неверный логин или пароль")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/scan')
@login_required
def scan_page():
    return render_template('scan.html')


@app.route('/api/verify', methods=['POST'])
@login_required
def verify_unlock():
    data = request.json
    computer_serial = data.get('computer_serial')
    code = data.get('code')

    session_file = os.path.join(SESSIONS_DIR, f"{computer_serial}.json")
    if not os.path.exists(session_file):
        return jsonify({'success': False, 'message': 'Сессия не найдена'})

    with open(session_file, 'r') as f:
        session_data = json.load(f)

    if session_data.get('code') != code:
        return jsonify({'success': False, 'message': 'Неверный код'})

    if time.time() > session_data.get('expires_at', 0):
        return jsonify({'success': False, 'message': 'Код истек'})

    if session_data.get('verified'):
        return jsonify({'success': False, 'message': 'Уже подтверждено'})

    session_data['verified'] = True
    session_data['verified_by'] = session['username']
    session_data['verified_at'] = time.time()
    session_data['user_id'] = session['user_id']
    session_data['user_name'] = session['name']
    session_data['user_surname'] = session['surname']

    with open(session_file, 'w') as f:
        json.dump(session_data, f)

    add_unlock_log(
        session['user_id'],
        session['username'],
        session['name'],
        session['surname'],
        computer_serial,
        code
    )

    return jsonify({
        'success': True,
        'message': f'Компьютер разблокирован пользователем {session["name"]} {session["surname"]}',
        'user_id': session['user_id'],
        'username': session['username'],
        'name': session['name'],
        'surname': session['surname']
    })


@app.route('/api/check_session/<computer_serial>')
def check_session(computer_serial):
    session_file = os.path.join(SESSIONS_DIR, f"{computer_serial}.json")
    if not os.path.exists(session_file):
        return jsonify({'exists': False, 'verified': False})

    with open(session_file, 'r') as f:
        session_data = json.load(f)

    return jsonify({
        'exists': True,
        'code': session_data.get('code'),
        'verified': session_data.get('verified', False),
        'expires_at': session_data.get('expires_at'),
        'user_id': session_data.get('user_id'),
        'username': session_data.get('verified_by'),
        'name': session_data.get('user_name'),
        'surname': session_data.get('user_surname')
    })


@app.route('/api/create_session', methods=['POST'])
def create_session():
    data = request.json
    computer_serial = data.get('computer_serial')

    code = ''.join(random.choices('0123456789', k=8))

    session_data = {
        'computer_serial': computer_serial,
        'code': code,
        'created_at': time.time(),
        'expires_at': time.time() + 120,
        'verified': False
    }

    session_file = os.path.join(SESSIONS_DIR, f"{computer_serial}.json")
    with open(session_file, 'w') as f:
        json.dump(session_data, f)

    unlock_url = f"http://localhost:5000/scan?serial={computer_serial}&code={code}"

    return jsonify({
        'success': True,
        'code': code,
        'unlock_url': unlock_url,
        'expires_in': 120
    })


# ==================== НОВЫЕ API ДЛЯ СЕССИЙ ====================
@app.route('/api/session/start', methods=['POST'])
def start_work_session():
    """Начать сессию работы"""
    data = request.json
    computer_serial = data.get('computer_serial')

    # Получаем информацию о сессии
    session_file = os.path.join(SESSIONS_DIR, f"{computer_serial}.json")
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        user_id = session_data.get('user_id')
        username = session_data.get('verified_by')
        name = session_data.get('user_name')
        surname = session_data.get('user_surname')

        if user_id:
            # Создаем запись в БД
            query_db('''INSERT INTO work_sessions 
                        (user_id, username, name, surname, computer_serial, session_start) 
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     [user_id, username, name, surname, computer_serial, datetime.now()])

            return jsonify(
                {'success': True, 'session_id': query_db('SELECT last_insert_rowid() as id', one=True)['id']})

    return jsonify({'success': False})


@app.route('/api/session/end', methods=['POST'])
def end_work_session():
    """Завершить сессию работы"""
    data = request.json
    computer_serial = data.get('computer_serial')

    # Находим активную сессию
    active_session = query_db('''
        SELECT id, session_start 
        FROM work_sessions 
        WHERE computer_serial = ? AND session_end IS NULL 
        ORDER BY id DESC LIMIT 1
    ''', [computer_serial], one=True)

    if active_session:
        session_end = datetime.now()
        session_start = datetime.fromisoformat(active_session['session_start'])
        duration = int((session_end - session_start).total_seconds() / 60)

        query_db('''UPDATE work_sessions 
                    SET session_end = ?, duration_minutes = ? 
                    WHERE id = ?''',
                 [session_end, duration, active_session['id']])

        return jsonify({'success': True, 'duration': duration})

    return jsonify({'success': False})


@app.route('/api/session/photo', methods=['POST'])
def upload_photo():
    """Загрузить фото пользователя"""
    data = request.json
    computer_serial = data.get('computer_serial')
    photo_data = data.get('photo')  # base64

    if photo_data:
        # Декодируем фото
        photo_bytes = base64.b64decode(photo_data.split(',')[1] if ',' in photo_data else photo_data)

        # Создаем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{computer_serial}_{timestamp}.jpg"
        filepath = os.path.join(PHOTOS_DIR, filename)

        # Сохраняем фото
        with open(filepath, 'wb') as f:
            f.write(photo_bytes)

        # Обновляем запись в БД
        query_db('''UPDATE work_sessions 
                    SET photo_path = ? 
                    WHERE computer_serial = ? AND session_end IS NULL 
                    ORDER BY id DESC LIMIT 1''',
                 [filepath, computer_serial])

        return jsonify({'success': True, 'path': filepath})

    return jsonify({'success': False})


# ==================== АДМИН-ПАНЕЛЬ ====================
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = query_db('SELECT id, username, name, surname, is_admin FROM users ORDER BY id')
    return render_template('admin.html', users=users)


@app.route('/admin/logs')
@login_required
@admin_required
def view_logs():
    logs = query_db('''
        SELECT computer_serial, session_code, username, name, surname, timestamp 
        FROM unlock_logs 
        ORDER BY timestamp DESC 
        LIMIT 100
    ''')
    return render_template('logs.html', logs=logs)


@app.route('/admin/sessions')
@login_required
@admin_required
def view_sessions():
    """Просмотр сессий работы"""
    sessions = query_db('''
        SELECT ws.*, 
               datetime(ws.session_start, 'localtime') as start_time,
               datetime(ws.session_end, 'localtime') as end_time
        FROM work_sessions ws
        ORDER BY ws.session_start DESC 
        LIMIT 100
    ''')
    return render_template('sessions.html', sessions=sessions)


@app.route('/api/admin/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
@admin_required
def manage_users():
    if request.method == 'GET':
        users = query_db('SELECT id, username, name, surname, is_admin FROM users')
        return jsonify([dict(u) for u in users])

    elif request.method == 'POST':
        data = request.json
        hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')

        try:
            query_db('''INSERT INTO users (username, password, name, surname, is_admin) 
                        VALUES (?, ?, ?, ?, ?)''',
                     [data['username'], hashed_password, data['name'],
                      data['surname'], data.get('is_admin', 0)])
            return jsonify({'success': True, 'message': 'Пользователь создан'})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'message': 'Пользователь уже существует'})

    elif request.method == 'PUT':
        data = request.json
        if data.get('password'):
            hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
            query_db('''UPDATE users SET username=?, password=?, name=?, surname=?, is_admin=? 
                        WHERE id=?''',
                     [data['username'], hashed_password, data['name'],
                      data['surname'], data.get('is_admin', 0), data['id']])
        else:
            query_db('''UPDATE users SET username=?, name=?, surname=?, is_admin=? 
                        WHERE id=?''',
                     [data['username'], data['name'], data['surname'],
                      data.get('is_admin', 0), data['id']])
        return jsonify({'success': True, 'message': 'Пользователь обновлен'})

    elif request.method == 'DELETE':
        user_id = request.args.get('id')
        if user_id == str(session['user_id']):
            return jsonify({'success': False, 'message': 'Нельзя удалить себя'})

        query_db('DELETE FROM users WHERE id = ?', [user_id])
        return jsonify({'success': True, 'message': 'Пользователь удален'})


@app.route('/api/admin/change_password', methods=['POST'])
@login_required
@admin_required
def change_admin_password():
    data = request.json
    new_password = data.get('new_password')

    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
    query_db('UPDATE users SET password = ? WHERE id = ?',
             [hashed_password, session['user_id']])

    return jsonify({'success': True, 'message': 'Пароль изменен'})


# ==================== ОЧИСТКА СЕССИЙ ====================
def cleanup_sessions():
    while True:
        try:
            for session_file in Path(SESSIONS_DIR).glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)

                    if time.time() > data.get('expires_at', 0):
                        os.remove(session_file)
                except:
                    pass
        except:
            pass
        time.sleep(60)


threading.Thread(target=cleanup_sessions, daemon=True).start()

if __name__ == '__main__':
    print("=" * 60)
    print("🔐 UNLOCK SYSTEM WEB SERVER (LOCAL)")
    print("=" * 60)
    print("🌐 http://localhost:5000")
    print("👤 Админ: admin / admin")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)