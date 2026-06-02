import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Sensor, Zone, SensorType, SensorHistory, SensorSubscription
from sqlalchemy import or_
from datetime import datetime, timedelta
import requests
from telegram_utils import send_alert_to_subscribers

app = Flask(__name__)
TELEGRAM_TOKEN = "8956916107:AAHExSI6ZnyT4RvCyg8qYwvaBqy-Kdvawbc"
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

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
        return jsonify({"error": "Пользователь существует"}), 400
    new_user = User(username=data['username'], password_hash=generate_password_hash(data['password']), role_id=2)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Успех"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        res = jsonify({"login": True, "username": user.username})
        set_access_cookies(res, create_access_token(identity=str(user.user_id)))
        return res, 200
    return jsonify({"error": "Неверный логин или пароль"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    res = jsonify({"logout": True})
    unset_jwt_cookies(res)
    return res, 200

@app.route('/api/profile', methods=['GET', 'PATCH'])
@jwt_required()
def handle_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    if request.method == 'GET':
        return jsonify({"username": user.username, "telegram_id": user.telegram_id or ""})
    user.telegram_id = request.get_json().get('telegram_id')
    db.session.commit()
    return jsonify({"message": "Профиль обновлен"}), 201

@app.route('/api/profile/change-password', methods=['POST'])
@jwt_required()
def update_password():
    user = db.session.get(User, int(get_jwt_identity()))
    data = request.get_json()
    if not check_password_hash(user.password_hash, data['old_password']):
        return jsonify({"error": "Неверный старый пароль"}), 400
    user.password_hash = generate_password_hash(data['new_password'])
    db.session.commit()
    return jsonify({"message": "Пароль изменен"}), 201

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
    return jsonify({"status": "ok"}), 201

@app.route('/api/zones/<int:zone_id>/sensors', methods=['GET'])
@jwt_required()
def zone_sensors(zone_id):
    sensors = Sensor.query.filter_by(zone_id=zone_id).all()
    # ДОБАВИЛИ last_date ТУТ
    return jsonify([{
        "id":s.sensor_id,
        "name":s.name,
        "status":s.status,
        "sn":s.serial_number,
        "last_date": s.last_inspection_date.strftime("%d.%m.%Y %H:%M") if s.last_inspection_date else "Нет данных"
    } for s in sensors])

@app.route('/api/sensors', methods=['GET', 'POST'])
@jwt_required()
def sensors_main():
    if request.method == 'GET':
        return jsonify([{"id":s.sensor_id,"name":s.name,"status":s.status} for s in Sensor.query.all()])
    d = request.get_json()
    s = Sensor(name=d['name'], zone_id=int(d['zone_id']), type_id=int(d['type_id']), serial_number=d.get('serial_number'), status='active', last_inspection_date=datetime.now())
    db.session.add(s); db.session.commit(); return jsonify({"ok":True}), 201

@app.route('/api/sensors/<int:id>', methods=['GET', 'DELETE', 'PUT']) # ДОБАВИЛИ GET
@jwt_required()
def sensor_one(id):
    s = db.session.get(Sensor, id)
    if not s: 
        return jsonify({"error": "Датчик не найден"}), 404
        
    if request.method == 'GET':
        return jsonify({
            "id": s.sensor_id,
            "name": s.name,
            "sn": s.serial_number,
            "zone_id": s.zone_id,
            "type_id": s.type_id,
            "status": s.status
        }), 200

    # ЕСЛИ УДАЛЯЕМ
    if request.method == 'DELETE':
        db.session.delete(s)
        db.session.commit()
        return jsonify({"ok": True}), 200
        
    d = request.get_json()
    s.name = d.get('name', s.name)
    s.serial_number = d.get('serial_number', s.serial_number)
    s.last_inspection_date = datetime.now()
    db.session.commit()
    return jsonify({"ok": True}), 200

@app.route('/api/sensors/faulty', methods=['GET'])
@jwt_required()
def get_faulty():
    f = Sensor.query.filter_by(status='failure').all()
    return jsonify([{"id":s.sensor_id,"name":s.name,"zone_id":s.zone_id} for s in f])

@app.route('/api/sensors/urgent', methods=['GET'])
@jwt_required()
def get_urgent():
    faulty = Sensor.query.filter_by(status='failure').all()
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    need_service = Sensor.query.filter(Sensor.last_inspection_date < thirty_days_ago).all()
    
    return jsonify({
        "faults": [{"id": s.sensor_id, "name": s.name, "zone_id": s.zone_id} for s in faulty],
        "service": [{"id": s.sensor_id, "name": s.name, "date": s.last_inspection_date.strftime("%d.%m.%Y")} for s in need_service]
    })

@app.route('/api/sensors/report', methods=['POST'])
@jwt_required()
def sensor_report():
    d = request.get_json()
    s = db.session.get(Sensor, d['sensor_id'])
    if s:
        old_status = s.status
        s.status = d['status']
        s.last_inspection_date = datetime.now() # ОБНОВЛЯЕМ ДАТУ ПРИ СМЕНЕ СТАТУСА
        
        if d['status'] == 'failure' and old_status != 'failure':
            event = SensorHistory(sensor_id=s.sensor_id, user_id=int(get_jwt_identity()), event_type='FAILURE', notes="Сбой")
            db.session.add(event)
            try:
                zone = db.session.get(Zone, s.zone_id)
                send_alert_to_subscribers(s, zone.name if zone else "Система")
            except: pass
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify({"err": 404}), 404

@app.route('/api/subscriptions', methods=['GET'])
@jwt_required()
def get_subs():
    try:
        user_id = int(get_jwt_identity())
        subs = db.session.query(SensorSubscription).filter_by(user_id=user_id).all()
        return jsonify([s.zone_id for s in subs]), 200
    except Exception as e:
        print(f"SUBS GET ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/subscriptions/toggle', methods=['POST'])
@jwt_required()
def toggle_sub():
    try:
        user_id = int(get_jwt_identity())
        zone_id = int(request.get_json().get('zone_id'))
        
        existing = SensorSubscription.query.filter_by(user_id=user_id, zone_id=zone_id).first()
        if existing:
            db.session.delete(existing)
            msg = "Отписались"
        else:
            new_sub = SensorSubscription(user_id=user_id, zone_id=zone_id)
            db.session.add(new_sub)
        
        db.session.commit()
        return jsonify({"message": "OK"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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