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


@app.route('/')
def show_entries():
    return render_template('layout.html')


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
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return render_template('layout.html')


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