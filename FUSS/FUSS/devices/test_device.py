from flask.views import View
from flask import render_template, session, Blueprint, make_response
from FUSS import models, app
from sys import modules

device_blueprint = Blueprint('test_device', __name__, template_folder='templates')

def init():
    pass

@device_blueprint.route('/')
def main_view():
    return render_template('devices/dummy_page.html', objects=get_objects())

def get_objects():
    return {'device_name' : 'test_device', 'device_type': 'None'}

@device_blueprint.route('/graph.png')
def simple_graph():
    return graph_all()

@device_blueprint.route('/all.png')
def graph_all():
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import date2num
    import io
    
    cnt = 15
    y = get_all_data()
    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    for subList in y:
        for d in subList:
            ax.plot(d)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.axis('off')
    png_output = io.BytesIO()
    fig.tight_layout()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

def get_all_data():
    with app.app_context():
        import importlib

        y = []
        dev_mods = app.config['DEVICES']
        for dev in dev_mods:
            modName = 'FUSS.devices.{}'.format(dev)
            if modName == __name__:
                continue

            devModule = importlib.import_module(modName)

            if hasattr(devModule, 'get_all_data'):
                y.append(devModule.get_all_data())

        return y

        

