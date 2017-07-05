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

TEMP_FUNC = 0
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

@device_blueprint.route('/all.png')
def graph_all():
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import date2num
    import io
    
    cnt = 15
    y = get_all_data()[0]
    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.plot(y)
    ax.set_ylabel('Temp: *C')
    ax.set_xticklabels([])
    png_output = io.BytesIO()
    fig.tight_layout()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    logging.debug('Graphed all entries in MCP9808. Entry count {}'.format(len(y)))
    return response

@device_blueprint.route('/graph.png')
def temp_graph():
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import date2num
    import io
    
    cnt = 15
    if 'mcp_limit' in session:
        cnt = session['mcp_limit']
    x,y = get_data(None, None, cnt)
    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.plot(range(0,len(x)),y[0])
    ax.set_xticks(range(0,len(x)))
    ax.set_xticklabels(x, rotation=45)
    ax.set_xlabel('Date')
    ax.set_ylabel('Temp: *C')
    png_output = io.BytesIO()
    fig.tight_layout()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

@device_blueprint.route('/update', methods=['POST'])
def update_settings():
    if request.method == 'POST':
        if 'entry_count' in request.form:
            session['mcp_limit'] = int(request.form['entry_count'])
            logging.debug('set mcp_limit to ' + session['mcp_limit'])
    return main_view()


def get_all_data():
    sensorID = get_sensor_id(TEMP_FUNC)[0]

    res = SensorEntry.query.filter(SensorEntry.sensor_id == sensorID).order_by(asc(SensorEntry.date)).all()
    y = [[]]
    for e in res:
        y[0].append(e.reading)
    return y


def get_data(d1, d2, sample_count=10):
    import datetime
    tformat = '%Y-%m-%d'
    """gets sensor readings from d1 to d2 """
    sensorID = get_sensor_id(TEMP_FUNC)[0]
    if d1 == None:
        startDate = SensorEntry.query.filter(SensorEntry.sensor_id == sensorID) \
        .order_by(asc(SensorEntry.date)).first().date
    else:
        startDate = d1

    if d2 == None:
        endDate = SensorEntry.query.filter(SensorEntry.sensor_id == sensorID) \
            .order_by(desc(SensorEntry.date)).first().date
    else:
        endDate = d2
    delta = endDate - startDate
    separator = delta / sample_count
    x = []
    y = [[]]
    d1 = startDate
    d2 = startDate + separator
    for i in range(0, sample_count):
        avg = db.session.query(func.avg(SensorEntry.reading)) \
            .filter((SensorEntry.sensor_id == sensorID) & ((SensorEntry.date >= d1) & (SensorEntry.date < d2))).first()[0]

        y[0].append(avg)
        x.append((d1.strftime(tformat)))
        d1 += separator
        d2 += separator
    return x,y

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

@mqtt.on_topic(device_topic + '0/temperature')
def handle_temp(client, userdata, message):
    with app.app_context():
        logging.debug('Got MQTT message {}/{}/{}'.format(client,userdata,message))
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