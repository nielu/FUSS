from flask.views import View
from flask import render_template, session, Blueprint, make_response
from FUSS import models
from sys import modules

device_blueprint = Blueprint('test_device', __name__, template_folder='templates')


@device_blueprint.route('/')
def main_view():
    return render_template('devices/dummy_page.html', objects=get_objects())

def get_objects():
    return {'device_name' : 'test_device', 'device_type': 'None'}

@device_blueprint.route('/graph.png')
def simple_graph():
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    import io
    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.plot([1, 3, 2, 5, 9,8,12,15,10, 25])
    ax.set_title('WIENCEJ RDZENIUF')
    ax.grid(True)
    ax.set_xlabel('RDZENIE')
    ax.set_ylabel('RDZENIE')
    png_output = io.BytesIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

