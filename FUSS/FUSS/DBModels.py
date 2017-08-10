from FUSS import app, db
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from flask import json
import logging

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))
    level = db.Column(db.Integer)

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.level = 0
    def __repr__(self):
        return 'User {}'.format(self.username)

    def isAdmin(self):
        return self.level > 0

class Sensors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    mac_address = db.Column(db.BigInteger)
    function_number = db.Column(db.Integer)

    def __init__(self, name, mac_address, function_number):
        if (type(mac_address) is str):
            mac_address = int(mac_address, 16)
        self.name = name
        self.mac_address = mac_address
        self.function_number = function_number
    def __repr__(self):
        return 'Sensor {}:{} MAC:{}'.format(self.name, self.function_number, self.mac_address)

    def __json__(self):
        return ['name', 'mac_address', 'function_number']

class SensorEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'))
    date = db.Column(db.DateTime)
    reading = db.Column(db.Text)

    def __init__(self, sensor_id, reading, date = None):
        self.sensor_id = sensor_id
        self.reading = reading
        if date is None:
            self.date = datetime.now()
        else:
            self.date = date

    def __repr__(self):
        return '{} : {}'.format(self.date, self.reading)

    def __json__(self):
        return ['date', 'reading']

class SensorTelemetry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    voltage = db.Column(db.Text)
    error = db.Column(db.Text)
    json_data = db.Column(db.Text)

    def __init__(self, sensor_id, date, voltage=None, uptime=None, error=None, json_data=None):
        self.sensor_id = sensor_id
        self.date = date
        self.voltage = voltage
        self.uptime = uptime
        self.error = error
        self.json_data = json_data

class SensorType(db.Model):
    __tablename__ = 'sensortype'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80))
    unit = db.Column(db.String(80))
    description = db.Column(db.Text)

    def __init__(self, type, unit, description=None):
        self.type = type
        self.unit = unit
        self.description = description

    def __repr__(self):
       return 'Sensor {} type: {} [{}].\n{}'.format(self.id, self.type, self.unit, self.description)

