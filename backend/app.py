import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Sensor, Zone, SensorType, SensorHistory
from sqlalchemy import or_
from datetime import datetime
import requests

app = Flask(__name__)
TELEGRAM_TOKEN = "8956916107:AAHExSI6ZnyT4RvCyg8qYwvaBqy-Kdvawbc"
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1@postgres:5432/buildsafe_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'dev-secret-key'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False 
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
app.config['JWT_COOKIE_SECURE'] = False 

db.init_app(app)
jwt = JWTManager(app)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Пользователь уже существует"}), 400
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password_hash=hashed_pw, role_id=2)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Успешная регистрация"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=str(user.user_id))
        response = jsonify({"login": True, "username": user.username})
        set_access_cookies(response, access_token)
        return response, 200
    return jsonify({"error": "Неверный логин или пароль"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    response = jsonify({"logout": True})
    unset_jwt_cookies(response)
    return response, 200

@app.route('/api/profile', methods=['GET', 'PATCH'])
@jwt_required()
def handle_profile():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user: return jsonify({"error": "Пользователь не найден"}), 404

    if request.method == 'GET':
        return jsonify({"username": user.username, "telegram_id": user.telegram_id or ""})
    
    data = request.get_json()
    user.telegram_id = data.get('telegram_id')
    db.session.commit()
    return jsonify({"message": "Профиль обновлен"})

@app.route('/api/profile/change-password', methods=['POST'])
@jwt_required()
def update_password():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    data = request.get_json()
    if not check_password_hash(user.password_hash, data['old_password']):
        return jsonify({"error": "Старый пароль неверен"}), 400
    user.password_hash = generate_password_hash(data['new_password'])
    db.session.commit()
    return jsonify({"message": "Пароль успешно изменен"})

@app.route('/api/zones', methods=['GET', 'POST'])
@jwt_required()
def handle_zones():
    if request.method == 'GET':
        zones = Zone.query.all()
        return jsonify([{"id": z.zone_id, "name": z.name, "location": z.location, "responsible": z.responsible} for z in zones])
    
    data = request.get_json()
    new_zone = Zone(name=data['name'], location=data['location'], responsible=data.get('responsible'))
    db.session.add(new_zone)
    db.session.commit()
    return jsonify({"message": "Зона создана"}), 201

@app.route('/api/zones/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_zone(id):
    zone = db.session.get(Zone, id)
    if zone:
        db.session.delete(zone)
        db.session.commit()
        return jsonify({"message": "Зона удалена"}), 200
    return jsonify({"error": "Зона не найдена"}), 404

@app.route('/api/zones/<int:zone_id>/sensors', methods=['GET'])
@jwt_required()
def get_zone_sensors(zone_id):
    sensors = Sensor.query.filter_by(zone_id=zone_id).all()
    return jsonify([{"id": s.sensor_id, "name": s.name, "status": s.status, "sn": s.serial_number} for s in sensors])

@app.route('/api/sensors', methods=['GET', 'POST'])
@jwt_required()
def handle_sensors():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        per_page = 5

        query = Sensor.query
        if search:
            query = query.filter(or_(
                Sensor.name.ilike(f'%{search}%'),
                Sensor.serial_number.ilike(f'%{search}%')
            ))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "sensors": [{"id": s.sensor_id, "name": s.name, "status": s.status, "sn": s.serial_number} for s in pagination.items],
            "total_pages": pagination.pages,
            "current_page": pagination.page
        })

    if request.method == 'POST':
        data = request.get_json()
        try:
            new_sensor = Sensor(
                name=data['name'],
                zone_id=data['zone_id'],
                type_id=data['type_id'],
                serial_number=data.get('serial_number'),
                status='active'
            )
            db.session.add(new_sensor)
            db.session.commit()
            return jsonify({"message": "Датчик добавлен"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

@app.route('/api/sensors/faulty', methods=['GET'])
@jwt_required()
def get_faulty():
    faulty = Sensor.query.filter_by(status='failure').all()
    return jsonify([{"id": s.sensor_id, "name": s.name, "status": s.status, "zone_id": s.zone_id} for s in faulty])

@app.route('/api/sensor/report', methods=['POST'])
@jwt_required()
def report_state():
    data = request.get_json()
    sensor = db.session.get(Sensor, data['sensor_id'])
    if sensor:
        if data['status'] == 'failure' and sensor.status != 'failure':
            event = SensorHistory(sensor_id=sensor.sensor_id, user_id=int(get_jwt_identity()), event_type='FAILURE', notes="Сигнал сбоя")
            db.session.add(event)
        sensor.status = data['status']
        db.session.commit()
        return jsonify({"status": "ok"}), 200
    return jsonify({"error": "not found"}), 404

@app.route('/api/sensors/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_sensor(id):
    sensor = db.session.get(Sensor, id)
    if sensor:
        db.session.delete(sensor)
        db.session.commit()
        return jsonify({"message": "Удалено"}), 200
    return jsonify({"error": "Не найден"}), 404

@app.route('/api/reports/create', methods=['POST'])
@jwt_required()
def create_report():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user.telegram_id:
        return jsonify({"error": "В профиле не указан Telegram ID!"}), 400

    faulty_sensors = Sensor.query.filter_by(status='failure').all()
    report_text = "*ОТЧЕТ О СОСТОЯНИИ СИСТЕМЫ*\n\n"
    report_text += f"Диспетчер: {user.username}\n"
    report_text += f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"

    if not faulty_sensors:
        report_text += "✅ Все системы работают в штатном режиме."
    else:
        report_text += f"⚠️ Обнаружено неисправностей: {len(faulty_sensors)}\n\n"
        for s in faulty_sensors:
            zone = db.session.get(Zone, s.zone_id)
            report_text += f"*Зона:* {zone.name if zone else 'N/A'}\n"
            report_text += f"*Устройство:* {s.name}\n"
            report_text += f"SerialNumber: `{s.serial_number}`\n"
            report_text += "--------------------------------\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": user.telegram_id, "text": report_text, "parse_mode": "Markdown"}

    try:
        tg_res = requests.post(url, json=payload)
        if tg_res.status_code == 200:
            return jsonify({"message": "Отчет отправлен в Telegram!"}), 200
        return jsonify({"error": "Бот вас не нашел. Нажмите START в боте."}), 400
    except:
        return jsonify({"error": "Ошибка связи с Telegram"}), 500

@app.route('/api/sensor_types', methods=['GET'])
@jwt_required()
def get_types():
    types = SensorType.query.all()
    return jsonify([{"id": t.type_id, "name": t.name} for t in types])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5252)