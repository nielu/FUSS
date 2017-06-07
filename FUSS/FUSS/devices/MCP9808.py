from flask.views import View
from flask import render_template, session, Blueprint, make_response
from FUSS import models
from sys import modules

device_blueprint = Blueprint('MCP9808', __name__, template_folder='templates')


@device_blueprint.route('/')
def main_view():
    return render_template('dummy_page.html', objects=get_objects())

def get_objects():
    return {'device_name' : __name__, 'device_type': 'Temperature-sensor'}

@device_blueprint.route('/graph.png')
def temp_graph():
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import date2num
    import io
    import datetime
    tformat = '%Y-%m-%d'
    db = models.get_db()
    x = []
    y = []
    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    entryCount = 30
    sensorID = db.execute("SELECT id FROM sensors WHERE instr(name, 'MCP')").fetchone()[0]
    startDate = db.execute('SELECT date FROM entries WHERE sensor_type == ? ORDER BY date ASC LIMIT 1',
                           [sensorID]).fetchone()[0]

    startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    endDate = db.execute('SELECT date FROM entries WHERE sensor_type == ? ORDER BY date DESC LIMIT 1',
                           [sensorID]).fetchone()[0]

    endDate = datetime.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')
    delta = endDate - startDate
    separator = delta/entryCount
    d1 = startDate
    d2 = startDate + separator
    for i in range(0, entryCount):
        avg = db.execute('SELECT avg(reading) FROM entries WHERE sensor_type == ? AND date > ? AND date <= ?',
                         [sensorID,d1.strftime(tformat), d2.strftime(tformat)]).fetchone()[0]
        y.append(avg)
        x.append((d1.strftime(tformat)))
        d1 += separator
        d2 += separator
    ax.plot(range(0,len(x)),y)
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
