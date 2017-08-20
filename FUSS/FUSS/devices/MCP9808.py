from flask.views import View
from flask import render_template, session, Blueprint, make_response, request
from FUSS import models,  mqtt, db, app
from FUSS.DBModels import *
from sys import modules
from datetime import datetime
from sqlalchemy import asc, desc
from sqlalchemy.sql import and_, or_, func
import logging

'''MCP9808 device package'''
'''0. Temperature sensor, reads in *C'''
'''See /device_fw/MCP9808 sketch'''

TEMP_FUNC = 1
SENSOR_NAME = 'mcp9808'
device_topic = 'sensor/mcp9808/'

device_blueprint = Blueprint(SENSOR_NAME, __name__, template_folder='templates')
data_axis = ["Date", ["Temp"]]


def init():
    mqtt.subscribe(device_topic + '#')
    logging.info('Module MCP9808 loaded')

@device_blueprint.route('/')
def main_view():
    return render_template('devices/MCP_template.html', objects=get_objects())

def get_objects():
    return {'device_name' : __name__, 'device_type': 'Temperature-sensor'}

def get_sensor_id(function_number, macAddress=None):
    '''Gets id of devices with following mac address and func number'''
    if macAddress is None:
        ids = Sensors.query.filter((Sensors.name == SENSOR_NAME) & (Sensors.function_number == function_number)).all()
    else:
        if type(macAddress) is str:
            macAddress = int(macAddress,16)
        ids = Sensors.query.filter((Sensors.mac_address == macAddress) & (Sensors.function_number == function_number)).all()
    
    retVal = []
    for s in ids:
        retVal.append(int(s.id))
    return retVal

@mqtt.on_topic(device_topic + '+/temperature')
def handle_temp(client, userdata, message):
    with app.app_context():
        #logging.debug('Got MQTT message {}/{}/{}'.format(client,userdata,message))
        dev = message.topic.replace(device_topic, '').replace('/temperature', '')
        val = message.payload.decode()
        insert_data(dev, TEMP_FUNC, val)

def new_sensor(sensorID, category):
    '''Adds new sensor to sensors table'''
    '''sensorID - mac address in hex'''
    
    mac = int(sensorID, 16)
    s = Sensors(SENSOR_NAME, mac, category)
    db.session.add(s)
    db.session.commit()
    logging.debug('New MCP9808 sensor {}'.format(s))
    return s

def insert_data(sensorID, function_number, value):
    '''Adds reading into DB'''
    id = get_sensor_id(function_number, sensorID)
    if len(id) == 0:
        id = new_sensor(sensorID, function_number).id
    else:
        id = id[0]
    e = SensorEntry(id, value)
    db.session.add(e)
    db.session.commit()
    logging.debug('New MCP9808 reading {}'.format(e))
    return e