import requests
from models import db, User, SensorSubscription

TELEGRAM_TOKEN = "8956916107:AAHExSI6ZnyT4RvCyg8qYwvaBqy-Kdvawbc"

def send_alert_to_subscribers(sensor, zone_name):
    subs = SensorSubscription.query.filter_by(zone_id=sensor.zone_id).all()
    
    text = f" *ОПОВЕЩЕНИЕ*\n\n" \
           f"Зона: {zone_name}\n" \
           f"Устройство: {sensor.name}\n" \
           f"SN: `{sensor.serial_number}`\n" \
           f"Состояние: Обнаружен сбой"

    for sub in subs:
        user = db.session.get(User, sub.user_id)
        if user and user.telegram_id:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": user.telegram_id, "text": text, "parse_mode": "Markdown"}
            try:
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                print(f"Ошибка отправки: {e}")