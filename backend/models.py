from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    telegram_id = db.Column(db.BigInteger)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)

class Zone(db.Model):
    __tablename__ = 'zones'
    zone_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    location = db.Column(db.String(50))
    responsible = db.Column(db.String(32))

class SensorType(db.Model):
    __tablename__ = 'sensor_types'
    type_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

class Sensor(db.Model):
    __tablename__ = 'sensors'
    sensor_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.zone_id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('sensor_types.type_id'), nullable=False)
    serial_number = db.Column(db.String(50))
    status = db.Column(db.String(32), nullable=False)
    last_inspection_date = db.Column(db.DateTime, default=datetime.utcnow)

class SensorHistory(db.Model):
    __tablename__ = 'sensor_history'
    event_id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.sensor_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    event_type = db.Column(db.String(32), nullable=False)
    event_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class SensorSubscription(db.Model):
    __tablename__ = 'sensor_subscriptions'
    sub_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.zone_id'), nullable=False)