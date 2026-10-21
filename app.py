from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, template_folder='.')
app.secret_key = 'fitzone_secret_key_123'

DB_CONFIG = {
    'dbname': 'fitzone_db',
    'user': 'postgres',
    'password': '28112008DNM',  
    'host': 'localhost',
    'port': '5432'
}

def get_db():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    conn.set_client_encoding('UTF8')
    return conn

@app.route('/')
def home():
    user = session.get('user')
    return render_template('index.html', user=user)

# Вход
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    login_val = data.get('login', '').strip()
    password = data.get('password', '').strip()

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, fullname, role FROM clients WHERE phone = %s AND password = %s", (login_val, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user'] = {
                'id': user['id'],
                'fullname': user['fullname'],
                'role': user['role']
            }
            return jsonify({'status': 'success', 'role': user['role']}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Неверный логин/телефон или пароль'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Выход
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# Регистрация
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    fullname = data.get('fullname')
    phone = data.get('phone')
    tariff = data.get('tariff')
    trainer_note = data.get('trainer_note', '')
    password = data.get('password')

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clients (fullname, phone, tariff, trainer_note, password, role) VALUES (%s, %s, %s, %s, %s, 'client')",
            (fullname, phone, tariff, trainer_note, password)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Админка (Страница)
@app.route('/admin')
def admin():
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return "<h1>403 Доступ запрещен. Войдите под аккаунтом администратора!</h1><a href='/'>На главную</a>", 403

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients ORDER BY id DESC")
        clients = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin.html', clients=clients, user=user)
    except Exception as e:
        return f"Ошибка: {e}"

# --- API ДЛЯ РАБОТЫ С РАСПИСАНИЕМ ---

# 1. Чтение расписания
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, trainer, room, event_time, free_seats FROM schedule ORDER BY event_time ASC;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 2. Добавление тренировки
@app.route('/api/admin/schedule', methods=['POST'])
def add_schedule():
    data = request.get_json()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO schedule (title, trainer, room, event_time, free_seats) 
               VALUES (%s, %s, %s, %s, %s);""",(data['title'], data['trainer'], data['room'], data['event_time'], data['free_seats'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 3. Удаление тренировки
@app.route('/api/admin/schedule/<int:item_id>', methods=['DELETE'])
def delete_schedule(item_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedule WHERE id = %s;", (item_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'deleted'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    # host='0.0.0.0' делает сайт доступным для всех устройств в твоем Wi-Fi
    app.run(host='0.0.0.0', port=5000, debug=True)