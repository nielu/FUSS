from flask.views import View
from flask import render_template, session, Blueprint, make_response, request
from FUSS import models,  mqtt, db, app
from FUSS.DBModels import *
from sys import modules
from datetime import datetime
from sqlalchemy import asc, desc
from sqlalchemy.sql import and_, or_, func

'''SI7021 device package'''
'''Two sensors available:'''
'''0. Temperature sensor, reads in *C'''
'''1. Humidity sensor, reads % of relative humidity'''
'''See /device_fw/SI7021 sketch'''

TEMP_FUNC = 0
HUM_FUNC = 1
SENSOR_NAME = 'si7021'
device_topic = 'sensor/si7021/'

device_blueprint = Blueprint(SENSOR_NAME, __name__, template_folder='templates/')
data_axis = ["Date", ["Temp", "Humidity"]]



def init():
    mqtt.subscribe(device_topic + '#')

@device_blueprint.route('/')
def main_view():
    return render_template('devices/SI_template.html', objects=get_objects())

def get_objects():
    return {'device_name' : __name__, 'device_type': 'Temperature-humidity-sensor'}

@device_blueprint.route('/graph.png')
def temp_graph():
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import date2num
    import io

    cnt = 15
    if 'si_limit' in session:
        cnt = session['si_limit']

    x,y = get_data(None,None, cnt)
    y_temp = y[0]
    y_hum = y[1]

    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(212)
    ax.plot(range(0,len(x)),y_temp, 'g-')
    ax.set_xticks(range(0,len(x)))
    ax.set_xticklabels(x, rotation=45)
    ax.set_xlabel('Date')
    ax.set_ylabel('temp *C')
    bx = fig.add_subplot(211)
    bx.plot(y_hum, 'b-')
    bx.set_ylabel('Hum %')
    bx.get_xaxis().set_visible(False)
    
    fig.tight_layout()
    png_output = io.BytesIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

@device_blueprint.route('/all.png')
def graph_all():
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import matplotlib.patches as mpatches
    from matplotlib.figure import Figure
    from matplotlib.dates import date2num
    import io
    
    cnt = 15
    y = get_all_data()
    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.plot(range(0, len(y[0])), y[0], 'g-', range(0, len(y[1])), y[1], 'b-')
    gLegend = mpatches.Patch(color='green', label='Temperature *C')
    bLegend = mpatches.Patch(color='blue', label='Humidity %RH')
    fig.legend(handles=[gLegend, bLegend], labels=['Temperature *C', 'Humidity %RH'])
    #ax.set_ylabel('Temp: *C')
    ax.set_xticklabels([])
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
            session['si_limit'] = int(request.form['entry_count'])
    return main_view()

@device_blueprint.route('/all.png')
def get_all_data():
    tempID = get_sensor_id(TEMP_FUNC)[0]
    humID = get_sensor_id(HUM_FUNC)[0]

    resTemp = SensorEntry.query.filter(SensorEntry.sensor_id == tempID).all()
    resHum = SensorEntry.query.filter(SensorEntry.sensor_id == humID).all()
    y = [[], []]
    for i in range(0, len(resTemp)):
        y[0].append(resTemp[i].reading)
        y[1].append(resHum[i].reading)
    return y

def get_data(d1, d2, sample_count = 10):
    import datetime
    tformat = '%Y-%m-%d'
    """gets sensor readings from d1 to d2 """
    humID = get_sensor_id(HUM_FUNC)[0]
    tempID = get_sensor_id(TEMP_FUNC)[0]
    if d1 == None:
        startDate = SensorEntry.query.filter(SensorEntry.sensor_id == tempID) \
        .order_by(asc(SensorEntry.date)).first().date
    else:
        startDate = d1

    if d2 == None:
        endDate = SensorEntry.query.filter(SensorEntry.sensor_id == tempID) \
            .order_by(desc(SensorEntry.date)).first().date
    else:
        endDate = d2
    delta = endDate - startDate
    separator = delta/sample_count
    x = []
    y = [[],[]]
    d1 = startDate
    d2 = startDate + separator
    for i in range(0, sample_count):
        avg = db.session.query(func.avg(SensorEntry.reading)) \
            .filter((SensorEntry.sensor_id == tempID) & ((SensorEntry.date >= d1 ) & (SensorEntry.date < d2))).first()[0]

        y[0].append(avg)
        
        avg = db.session.query(func.avg(SensorEntry.reading)) \
            .filter((SensorEntry.sensor_id == humID) & ((SensorEntry.date >= d1 ) & (SensorEntry.date < d2))).first()[0]

        y[1].append(avg)
        x.append((d1.strftime(tformat)))
        d1 += separator
        d2 += separator
    return x,y

def get_sensor_id(function_number, macAddress=None):
    '''Gets id of devices with following mac address and func number'''
    if macAddress is None:
        ids = Sensors.query.filter((Sensors.name == SENSOR_NAME) &
                               (Sensors.function_number == function_number)).all()
    else:
        if type(macAddress) is str:
            macAddress = int(macAddress,16)
        ids = Sensors.query.filter((Sensors.mac_address == macAddress) &
                                  (Sensors.function_number == function_number)).all()
    
    retVal = []
    for s in ids:
        retVal.append(int(s.id))
    return retVal

@mqtt.on_topic(device_topic + '0/temperature')
def handle_temp(client, userdata, message):
    with app.app_context():
        dev = message.topic.replace(device_topic, '').replace('/temperature', '')
        val = message.payload.decode()
        insert_data(dev, TEMP_FUNC, val)


@mqtt.on_topic(device_topic + '0/humidity')
def handle_hum(client, userdata, message):
    with app.app_context():
        dev = message.topic.replace(device_topic, '').replace('/humidity', '')
        val = message.payload.decode()
        insert_data(dev, HUM_FUNC, val)

def new_sensor(sensorID, category):
    '''Adds new sensor to sensors table'''
    '''sensorID - mac address in hex'''
    '''funcID - 0 for temp, 1 for humidity'''
    mac = int(sensorID, 16)
    s = Sensors(SENSOR_NAME, sensorID, category)
    db.session.add(s)
    db.session.commit()
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
    return e
