from flask.views import View
from flask import render_template, session, Blueprint
from FUSS import models
from sys import modules

device_blueprint = Blueprint('test_device', __name__, template_folder='templates')


@device_blueprint.route('/')
@device_blueprint.route('/dupa')
def main_view():
    objects={'device_name' : 'test_device', 'device_type': 'None'}
    return render_template('dummy_page.html', objects=objects)

