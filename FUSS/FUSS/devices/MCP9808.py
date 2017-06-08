from flask.views import View
from flask import render_template, session, Blueprint, make_response, request
from FUSS import models
from sys import modules

device_blueprint = Blueprint('MCP9808', __name__, template_folder='templates')
data_axis = ["Date", ["Temp"]]

@device_blueprint.route('/')
def main_view():
    return render_template('devices/MCP_template.html', objects=get_objects())

def get_objects():
    return {'device_name' : __name__, 'device_type': 'Temperature-sensor'}

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
    return main_view()


def get_data(d1, d2, sample_count = 10):
    import datetime
    """gets sensor readings from d1 to d2 """
    tformat = '%Y-%m-%d'
    db = models.get_db()
    sensorID = get_sensor_id()
    if d1 == None:
        startDate = db.execute('SELECT date FROM entries WHERE sensor_type == ? ORDER BY date ASC LIMIT 1',
                           [sensorID]).fetchone()[0]
        startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    else:
        startDate = d1

    if d2 == None:
        endDate = db.execute('SELECT date FROM entries WHERE sensor_type == ? ORDER BY date DESC LIMIT 1',
                           [sensorID]).fetchone()[0]
        endDate = datetime.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')
    else:
        endDate = d2
    delta = endDate - startDate
    separator = delta/sample_count
    x = []
    y = [[]]
    d1 = startDate
    d2 = startDate + separator
    for i in range(0, sample_count):
        avg = db.execute('SELECT avg(reading) FROM entries WHERE sensor_type == ? AND date BETWEEN ? AND ?',
                         [sensorID,d1.strftime(tformat), d2.strftime(tformat)]).fetchone()[0]
        y[0].append(avg)
        x.append((d1.strftime(tformat)))
        d1 += separator
        d2 += separator
    return x,y


def get_sensor_id():
    db = models.get_db()
    return db.execute("SELECT id FROM sensors WHERE instr(name, 'MCP')").fetchone()[0]