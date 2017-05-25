"""
Routes and views for the flask application.
"""
#region imports
from datetime import datetime
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, make_response
from FUSS import app
from FUSS import models
from timeit import default_timer as timer
#endregion

@app.route('/simple.png')
def simple():
    return models.createGraph()

@app.route('/graph.png')
def graph():
    return models.createAnotherGraph()


@app.route('/show_temp')
def show_temp():
    start_time = timer()
    db = models.get_db()
    if not 'count_limit' in session:
        session['count_limit'] = 25;
    limit = session['count_limit']

    sensorMac = int('a020a61783c3', 16)
    sensorMac2 = int('a020a617878c', 16)
    sensorsId = db.execute('SELECT id, name from sensors WHERE mac_address == ? OR mac_address == ?',
                          [ sensorMac2,sensorMac]).fetchall()
    if len(sensorsId) == 0:
        abort(401)
    entrycount = dict()
    for s in sensorsId:
        entrycount[s[1]] = db.execute('SELECT COUNT(*) FROM entries WHERE sensor_type == ?',
                            [sensorsId[0][0]]).fetchone()[0]
    separator = entrycount[sensorsId[0][1]] / limit

    #labels = db.execute('SELECT date FROM entries WHERE sensor_type == ? ',
    #                    [sensorsId[0][0]]).fetchall()[::separator]
    labels = db.execute('SELECT date FROM entries WHERE sensor_type == ? AND ROWID % ? == 0',
                        [sensorsId[0][0], separator]).fetchall()
    entries = list()
    for s in sensorsId:
        separator = entrycount[s[1]] / limit
        q = db.execute('SELECT reading FROM entries WHERE sensor_type == ? AND ROWID % ? == 0',
                       [s[0], separator]).fetchall()
        entries.append({'name': s[1], 'values': q})
    end_time = timer()
    misc = {'time': (end_time-start_time)}
    return render_template('show_temp.html', labels=labels, entries=entries, misc=misc)


@app.route('/')
def show_entries():
    return render_template('show_entries.html')


@app.route('/add', methods=['POST'])
def add_entry():
    db = models.get_db()
    mac = int(request.form['MAC'], 16)
    sensorid = db.execute('SELECT id FROM sensors WHERE mac_address == ? AND function_number == ?',
                          [mac, request.form['FUNC_ID']]).fetchone()
    if not sensorid:
        abort(401)
    db.execute('insert into entries (sensor_type, date, reading) values (?, ?, ?)',
                 [sensorid[0],datetime.strftime('%Y-%m-%d %H:%M:%S'), request.form['VALUE']])
    db.commit()
    return '', 201


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if (request.method == 'POST'):
        success, error = models.login(request.form['username'], request.form['password'])
        if (success):
            session['logged_in'] = True
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    error = None
    if (request.method == 'POST'):
        login = request.form['username']
        pass1 = request.form['password']
        pass2 = request.form['password2']
        if (pass1 != pass2):
            return render_template('register.html', error='Passwords dont match')
        if (len(pass1) < 8):
            return render_template('register.html', error='Password is too short')
        success, error = models.registerUser(login, pass1)
        if (success):
            session['logged_in'] = True
            return redirect(url_for('show_entries'))
    return render_template('register.html', error=error)

@app.route('/set_options', methods=['POST'])
def set_options():
    if request.method == 'POST':
        if 'entryCount' in request.form:
            limit = int(request.form['entryCount'])
            session['count_limit'] = limit
    return 'OK',201


@app.route('/register_sensor', methods=['POST'])
def register_sensor():
    if request.method == 'POST':
        mac = int(request.form['MAC'], 16)

        funcid = request.form['FUNC_ID']
        name = request.form['NAME']
        db = models.get_db()
        sensors = db.execute('SELECT name FROM sensors WHERE mac_address == ? AND function_number == ?',
                             [mac, funcid]).fetchall()
        if len(sensors) == 0:
            db.execute('INSERT INTO sensors (name, mac_address, function_number, sensor_category) VALUES (?,?,?,0)',
            [name, mac, funcid])
            db.commit()
        return 'OK', 201
    return 'NA', 403
#endregion