#region imports
from FUSS import app, bcrypt, db
from FUSS.DBModels import *
from sqlalchemy import asc,desc
from sqlalchemy.sql import and_, or_, func, select
from flask import Flask, request, session, g, redirect, url_for, abort, \
   flash, make_response, config, _app_ctx_stack
from timeit import default_timer as timer
import sqlite3
import os
import datetime
import pkgutil
import logging
import json
from datetime import datetime, date
#endregion


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):

        if isinstance(o, (datetime, date)):
            return js_date_utc(o)
        return json.JSONEncoder.default(self, o)


#region Database

#endregion
@app.before_first_request
def init_devices():
    import pkgutil
    import importlib
    modules = [name for _, name, _ in pkgutil.iter_modules(['FUSS/devices'])]
    logging.info('Got {} module(s)'.format(len(modules)))
    devices = []
    for m in modules:
        logging.info('Loading device module {}'.format(m))
        moduleName = 'FUSS.devices.{}'.format(m)
        devModule = importlib.import_module(moduleName)
        devices.append(m)
        app.register_blueprint(devModule.device_blueprint, url_prefix=('/dev/' + m))
        devModule.init()
    app.config.update(dict(DEVICES=devices))

def registerUser(name, password):
    exist = User.query.filter_by(username=name).first()
    if (exist is not None):
        return False, 'User already exists'
    hash = bcrypt.generate_password_hash(password).decode('utf-8')
    newUser = User(name, hash)
    db.session.add(newUser)
    db.session.commit()
    return True, 'Account created'

def login(name, password):
    user = User.query.filter_by(username=name).first()
    if (user is None or bcrypt.check_password_hash(user.password, password) == False):
        return False, 'Invalid username or password'
    session['logged_in'] = True
    session['isAdmin'] = user.isAdmin()
    session['userID'] = user.id
    return True, 'Logged in'

def floatify(reading):
    import math
    if reading is None:
        return None
    try:
        return float(reading)
    except:
        logging.info('exception with {}'.format(reading))
        return math.nan

def js_date_utc(date : datetime) -> str:
    return 'Date.UTC({}, {}, {}, {}, {}, {})' \
        .format(date.year, date.month - 1, date.day, date.hour, date.minute, date.second)

def getSensorID(function_number):
    '''Gets id of devices with following func number'''
    return Sensors.query.filter(Sensors.function_number == function_number).all()

def getSensor(id):
    return Sensors.query.filter(Sensors.id == id).first()

def getSensorReadings(sensor_id):
    return SensorEntry.query.filter(SensorEntry.sensor_id == sensor_id) \
                .order_by(asc(SensorEntry.date)).with_entities(SensorEntry.reading).all()

def getStartDate(sensor_id):
    return SensorEntry.query.filter(SensorEntry.sensor_id == sensor_id) \
                .order_by(asc(SensorEntry.date)).with_entities(SensorEntry.date).first()[0],

def getJSON():
    tempID = getSensorID(1)
    humID = getSensorID(2)
    y = []

    for i in range(len(tempID)):
        y.append({
            'data' : [floatify(r[0]) for r in getSensorReadings(tempID[i].id)]
          })
    for i in range(len(humID)):
        y.append({
            'data' : [floatify(r[0]) for r in getSensorReadings(humID[i].id)]
            })
    
    return json.dumps(y, cls=DateTimeEncoder)

def getAllData():

    tempID = getSensorID(1)
    humID = getSensorID(2)
    y = []

    for i in range(len(tempID)):
        y.append({
            'id': i,
            'name': tempID[i].name,
            'axis': 0,
            'pointstart': js_date_utc(getStartDate(tempID[i].id)[0]),
            'pointinterval' : get_average_interval(tempID[i].id)
           })
    for i in range(len(humID)):
        y.append({
            'id' : len(tempID) + i,
            'name': humID[i].name,
            'axis': 1,
            'pointstart' : js_date_utc(getStartDate(humID[i].id)[0]),
            'pointinterval' : get_average_interval(humID[i].id)
            })
    
    return y

def get_average_interval(sensorID, sampleCount=10000):
    entries = SensorEntry.query.filter(SensorEntry.sensor_id == sensorID) \
                .order_by(desc(SensorEntry.date)).limit(sampleCount).all()
    avg = None
    for i in range(sampleCount - 1):
        if avg is None:
            avg = entries[i].date - entries[i+1].date
        else:
            avg +=entries[i].date - entries[i+1].date
    avg = avg / (sampleCount - 1)
    return avg.total_seconds() * 1000

def updateSensorName(sensorID, newName):
    msg = ''
    if (len(newName) < 3 or len(newName) > 25):
        msg = 'Invalid name length!'
    else:
        sensor = getSensor(sensorID)
        if sensor is None:
            msg = 'Did not found sensor with id: ' + str(sensorID)
        elif sensor.name == newName:
            msg = 'New name is same as old'
        elif len(Sensors.query.filter(Sensors.name == newName).all()) > 0:
            msg = 'Name already in use!'
        else:
            sensor.name = newName
            db.session.commit()
            logging.info('Updated sensor name ' + newName)
            return True, 'Name updated'
    logging.error(msg)
    return False, msg

def updateUserAccessLevel(userID, newLevel):
    msg = ''
    try:
        newLevel = int(newLevel)
    except ValueError:
        newLevel = None
    if (newLevel is None or newLevel < 0 or newLevel > 100):
        msg = 'Invalid access level!'
    else:
        user = User.query.filter(User.id == userID).first()
        if user is None:
            msg = 'Did not found user with id: ' + str(userID)
        elif user.level == newLevel:
            msg = 'Current access is the same'
        else:
            user.level = newLevel
            db.session.commit()
            logging.info('Updated user {} level to {}'.format(user, newLevel))
            return True, 'Level updated'
    logging.error(msg)
    return False, msg

def updateUserPassword(userID, oldPassword, newPassword):
    msg = ''
    usr = getUser(userID)
    if usr is None:
        return False, 'User does not exist!'
    if not bcrypt.check_password_hash(usr.password, oldPassword):
        return False, 'Old password is invalid!'
    hash = bcrypt.generate_password_hash(newPassword).decode('utf-8')
    usr.password = hash
    db.session.commit()
    return True, 'Updated password'


def getUsers():
    return User.query.all()

def getSensors():
    return Sensors.query.all()

def getSensorTypes():
    return SensorType.query.all()

def getUser(userID):
    return User.query.filter(User.id == userID).first()