from flask.views import View
from flask import render_template, session, Blueprint, make_response
from FUSS import models, app
from sys import modules
import logging
device_blueprint = Blueprint('test_device', __name__, template_folder='templates')

def init():
    logging.info('Dummy module loaded')
    pass

@device_blueprint.route('/')
def main_view():
    return render_template('devices/dummy_page.html', objects=get_objects())

def get_objects():
    return {'device_name' : 'test_device', 'device_type': 'None'}


