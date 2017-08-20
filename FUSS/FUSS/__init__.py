"""
The flask application package.
"""

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_mqtt import Mqtt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime, date
import logging
import json

class FUSSJsonEncoder(json.JSONEncoder):
    def default(self, o):
        '''
        This method will serialize only some of the SqlAlchemy table objects attributes
        Table objects should implemet __json__ field which will return attributes to serialize
        '''
        if isinstance(o.__class__, DeclarativeMeta):
                data = {}
                fields = o.__json__() if hasattr(o, '__json__') else dir(o)
                for field in [f for f in fields if not f.startswith('_') and f not in ['metadata', 'query', 'query_class']]:
                    value = o.__getattribute__(field)
                    try:
                        json.dumps(value)
                        data[field] = value
                    except TypeError:
                        data[field] = None
                return data
        if isinstance(o, (datetime, date)):
            return o.strftime("Date.UTC(%Y, %m, %d, %H, %M, %S)")
        return json.JSONEncoder.default(self, o)


app = Flask(__name__)
app.json_encoder = FUSSJsonEncoder

host = 'localhost'
port = 5000
secret_key = 'SUPER_SECRET_DEV_KEY'
debug = True

mqtt_broker = '127.0.0.1'
mqtt_port = 1883

sms_api_key = ''

db_uri = 'db_engine://db_user:db_password@db_address/db_name'


logging.basicConfig(filename='FUSS.log', level=logging.DEBUG, \
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', \
    datefmt='%m/%d/%Y %I:%M:%S %p')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

logging.getLogger('').addHandler(console)

try:
    from config import *
except ImportError:
    pass

app.config['MQTT_BROKER_URL'] = mqtt_broker
app.config['MQTT_BROKER_PORT'] = mqtt_port

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

app.config['SECRET_KEY'] = secret_key

app.config['SMS_API_KEY'] = sms_api_key

bcrypt = Bcrypt(app)
mqtt = Mqtt(app)
db = SQLAlchemy(app)


logging.info('Running on {}:{}. MQTT broker {}:{}'.format(host,port, mqtt_broker, mqtt_port))

import FUSS.models
import FUSS.controller
