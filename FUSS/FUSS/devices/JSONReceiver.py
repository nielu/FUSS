from flask.views import View
from flask import render_template, session, Blueprint, make_response
from FUSS import models, app, db, mqtt
from FUSS.DBModels import *
from sys import modules
import logging
import json

device_blueprint = Blueprint('JSONReceiver', __name__, template_folder='templates')
device_topic = 'sensor/JSON'
def init():
    logging.info('JSON MQTT receiver loaded')
    mqtt.subscribe(device_topic)

@device_blueprint.route('/')
def main_view():
    return render_template('devices/JSONReceiver.html', objects=get_objects())

def get_objects():
    return {'telemetry': SensorTelemetry.query.limit(10).all()}

@mqtt.on_topic(device_topic)
def handleMQTTMessage(client, userdata, message):
    message = message.payload
    logging.info('got {}'.format(message))
    try:
        msg = json.loads(message)
    except ValueError as err:
        logging.ERROR('Failed to parse json message! Error: "{}"\nMessage: "{}"'.
                      format(err, message))
        return
    if 'sensor' not in msg or 'MAC' not in msg:
        logging.ERROR('JSON lacks required fields! {}'.format(msg))
        return
    devType = msg['sensor']
    try:
        mac = int(msg['MAC'], 16)
    except ValueError as err:
        logging.ERROR('Could not parse MAC address. {}'.format(err))
        return
    with app.app_context():
        if 'temp' in msg:
            func_id = 1
            insert_data(devType, mac, func_id, float(msg['temp']))
        if 'hum' in msg:
            func_id = 2
            insert_data(devType, mac, func_id, float(msg['hum'])).id
        if 'vcc' in msg and 'heap' in msg:
            t = SensorTelemetry(mac, date=datetime.now(), voltage=float(msg['vcc'])/1000.0, free_heap=msg['heap'], json_data=message)
            db.session.add(t)
            db.session.commit()


def new_sensor(name, sensorID, category):
    '''Adds new sensor to sensors table'''
    '''sensorID - mac address in hex'''
    '''funcID - 0 for temp, 1 for humidity'''
    s = Sensors(name, sensorID, category)
    db.session.add(s)
    db.session.commit()
    logging.debug('New SI7021 sensor {}'.format(s))
    return s

def insert_data(name, sensorMAC, function_number, value):
    '''Adds reading into DB'''
    id = get_sensor_id(function_number, sensorMAC)
    if len(id) == 0:
        id = new_sensor(name, sensorMAC, function_number).id
    else:
        id = id[0]
    e = SensorEntry(id, value)
    db.session.add(e)
    db.session.commit()
    logging.debug('New SI7021 reading {}'.format(e))
    return e

def get_sensor_id(function_number, macAddress):
    '''Gets id of devices with following mac address and func number'''
    ids = Sensors.query.filter((Sensors.mac_address == macAddress) &
                                (Sensors.function_number == function_number)).all()
    
    retVal = []
    for s in ids:
        retVal.append(int(s.id))
    return retVal

def get_sensor_type_id(type):
    ids = SensorType.query.filter((SensorType.type == type)).first()