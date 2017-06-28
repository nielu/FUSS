"""
The flask application package.
"""

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_mqtt import Mqtt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

host = 'localhost'
port = 5000
secret_key = 'SUPER_SECRET_DEV_KEY'
debug = True

mqtt_broker = '127.0.0.1'
mqtt_port = 1883

db_uri = 'db_engine://db_user:db_password@db_address/db_name'

try:
    from config import *
except ImportError:
    pass

app.config['MQTT_BROKER_URL'] = mqtt_broker
app.config['MQTT_BROKER_PORT'] = mqtt_port

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

app.config['SECRET_KEY'] = secret_key

bcrypt = Bcrypt(app)
mqtt = Mqtt(app)
db = SQLAlchemy(app)

import FUSS.views
import FUSS.models

#models.init_devices()