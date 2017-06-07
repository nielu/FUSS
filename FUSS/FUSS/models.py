#region imports
from FUSS import app, bcrypt
from flask import Flask, request, session, g, redirect, url_for, abort, \
   flash, make_response
from timeit import default_timer as timer
import sqlite3
import os
import datetime
import pkgutil
#endregion

#region Database
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized database')


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqllite_db = connect_db()
    return g.sqllite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
#endregion

def init_devices():
    import pkgutil
    import importlib
    modules = [name for _, name, _ in pkgutil.iter_modules(['FUSS\devices'])]
    print('Got {} module(s)'.format(len(modules)))
    for m in modules:
        print('Loading device module {}'.format(m))
        devModule = importlib.import_module('FUSS.devices.{}'.format(m))
        app.register_blueprint(devModule.device_blueprint, url_prefix=m)

def createGraph():
    start_time = timer()
    import datetime
    import io
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter, date2num
    db = get_db()

    fig = Figure()
    ax = fig.add_subplot(111)
    fig.add_axes()
    x = []
    y = []
    y2 = []
    y3 = []
    entryCount = 5
    endDate = datetime.datetime.now()
    startDate = db.execute('SELECT date FROM entries ORDER BY date ASC LIMIT 1').fetchone()[0]
    startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    delta = endDate - startDate
    separator = delta / entryCount
    d1 = startDate
    d2 = startDate + separator
    loopavg = 0.0
    for i in range(0, entryCount):
        loopStart = timer()
        avg = db.execute('SELECT avg(reading) FROM entries WHERE sensor_type==1 AND date > ? AND date <= ?',
                         [d1.strftime('%Y-%m-%d %H:%M:%S'), d2.strftime('%Y-%m-%d %H:%M:%S')]).fetchone()[0]
        x.append(date2num(d1))
        y.append(avg)
        avg = db.execute('SELECT avg(reading) FROM entries WHERE sensor_type==2 AND date > ? AND date <= ?',
                         [d1.strftime('%Y-%m-%d %H:%M:%S'), d2.strftime('%Y-%m-%d %H:%M:%S')]).fetchone()[0]
        y2.append(avg)
        avg = db.execute('SELECT avg(reading) FROM entries WHERE sensor_type==3 AND date > ? AND date <= ?',
                         [d1.strftime('%Y-%m-%d %H:%M:%S'), d2.strftime('%Y-%m-%d %H:%M:%S')]).fetchone()[0]
        y3.append(avg)
        d1 += separator
        d2 += separator
        loopavg += (timer() - loopStart)
    loopavg /= entryCount
    plot = timer()
    ax.plot_date(x, y, '-')

    # ax.plot(y2)
    # ax.plot(y3)
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    png_output = io.BytesIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    end = timer()
    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'no-store,no-chache,must-revalidate'
    response.headers['whole_time'] = end - start_time
    response.headers['loop_avg'] = loopavg
    return response


def createAnotherGraph():
    start_time = timer()
    import datetime
    import io
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter, date2num
    db = get_db()

    fig = Figure()
    ax = fig.add_subplot(111)
    x = []
    y = []
    y2 = []
    y3 = []
    entryCount = 10
    endDate = datetime.datetime.now()
    startDate = db.execute('SELECT date FROM entries ORDER BY date ASC LIMIT 1').fetchone()[0]
    startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    delta = endDate - startDate
    separator = delta/entryCount
    d1 = startDate
    d2 = startDate + separator
    loopavg = 0.0
    for i in range(0, entryCount):
        loopStart = timer()
        avg = db.execute('SELECT avg(reading) FROM entries WHERE sensor_type==1 AND date > ? AND date <= ?',
                         [d1.strftime('%Y-%m-%d %H:%M:%S'),d2.strftime('%Y-%m-%d %H:%M:%S')]).fetchone()[0]
        x.append(date2num(d1))
        y.append(avg)
        avg = db.execute('SELECT avg(reading) FROM entries WHERE sensor_type==2 AND date > ? AND date <= ?',
                         [d1.strftime('%Y-%m-%d %H:%M:%S'), d2.strftime('%Y-%m-%d %H:%M:%S')]).fetchone()[0]
        y2.append(avg)
        avg = db.execute('SELECT avg(reading) FROM entries WHERE sensor_type==3 AND date > ? AND date <= ?',
                         [d1.strftime('%Y-%m-%d %H:%M:%S'), d2.strftime('%Y-%m-%d %H:%M:%S')]).fetchone()[0]
        y3.append(avg)
        d1 += separator
        d2 += separator
        loopavg+=(timer()-loopStart)
    loopavg /= entryCount
    plot = timer()
    ax.plot_date(x, y, '-')
    #ax.plot(y2)
    #ax.plot(y3)
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    png_output = io.BytesIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    end = timer()
    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'no-store,no-chache,must-revalidate'
    response.headers['whole_time'] = end-start_time
    response.headers['loop_avg'] = loopavg
    return response

def registerUser(name, password):
    db = get_db()
    exist = db.execute('SELECT * FROM users WHERE username == ?', [name]).fetchall()
    if (len(exist) > 0):
        return False, 'User already exists'
    hash = bcrypt.generate_password_hash(password).decode('utf-8')
    db.execute('INSERT INTO users (username, password) VALUES (?, ?)', [name, hash])
    db.commit()
    return True, 'Account created'

def login(name, password):
    db = get_db()
    account = db.execute('SELECT username, password FROM users WHERE username == ?', [name]).fetchone()
    if (account == None):
        return False, 'Invalid username'
    if (bcrypt.check_password_hash(account[1], password) == False):
        return False, 'Invalid password'
    return True, 'Logged in'
