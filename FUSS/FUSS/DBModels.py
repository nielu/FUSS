from FUSS import app, db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))

    def __init__(self, username, password):
        self.username = username
        self.password = password
    def __repr__(self):
        return 'User {}'.format(self.username)

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


class SensorEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'))
    date = db.Column(db.DateTime)
    reading = db.Column(db.Text)

    def __init__(self, sensor_id, reading):
        self.sensor_id = sensor_id
        self.reading = reading
        self.date = datetime.now()

    def __repr__(self):
        return '{} : {}'.format(self.date, self.reading)





