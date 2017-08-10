"""
Routes and views for the flask application.
"""
#region imports
from datetime import datetime
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, make_response
from FUSS import app, models
from timeit import default_timer as timer
import logging
#endregion


@app.route('/')
def show_entries():
    return render_template('layout.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if (request.method == 'POST'):
        success, error = models.login(request.form['username'], request.form['password'])
        if (success):
            flash('You were logged in')
            logging.debug('User {} was logged in'.format(request.form['username']))
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('isAdmin', None)
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
            session['isAdmin'] = False
            return redirect(url_for('show_entries'))
    return render_template('register.html', error=error)

@app.route('/set_options', methods=['POST'])
def set_options():
    if request.method == 'POST':
        if 'entryCount' in request.form:
            limit = int(request.form['entryCount'])
            session['count_limit'] = limit
    return 'OK',201

@app.route('/cleanup')
def cleanup():
    from FUSS import backgroundWorkers as bg
    logging.info('Got db smoother request')
    bg.start_db_smoother()
    return 'OK', 201

@app.route('/view_all')
def view_all():
    return render_template('show_all.html', data=models.getAllData())

@app.route('/json')
def return_json():
    return models.getJSON()

def unauthorizedAccess():
    flash('You are not authorized for this action!')
    return render_template('layout.html', error='Not authorized')

@app.route('/admin')
def admin_panel():
    access = 'isAdmin' in session and session['isAdmin']
    if not access:
        return unauthorizedAccess()
    return render_template('adminPanel.html')

@app.route('/admin/users')
def user_panel():
    access = 'isAdmin' in session and session['isAdmin']
    if not access:
        return unauthorizedAccess()
    return render_template('adminPanel.html', users=models.getUsers())

@app.route('/admin/devices')
def device_panel():
    access = 'isAdmin' in session and session['isAdmin']
    if not access:
        return unauthorizedAccess()
    return render_template('adminPanel.html', sensors=models.getSensors(), types=models.getSensorTypes())

@app.route('/admin/system')
def system_panel():
    access = 'isAdmin' in session and session['isAdmin']
    if not access:
        return unauthorizedAccess()
    return render_template('adminPanel.html')

@app.route('/admin/alarms')
def alarm_panel():
    access = 'isAdmin' in session and session['isAdmin']
    if not access:
        return unauthorizedAccess()
    return render_template('adminPanel.html')

@app.route('/admin/users/set', methods=['POST'])
def modify_user():
    access = 'isAdmin' in session and session['isAdmin']
    if not access or not request.method == 'POST':
        return unauthorizedAccess()
    if 'userID' in request.form and 'newLevel' in request.form:
        res, msg = models.updateUserAccessLevel(request.form['userID'], request.form['newLevel'])
        flash(msg)
    else:
        flash('Invalid parameters')
    return user_panel()

@app.route('/admin/devices/set', methods=['POST'])
def modify_sensor():
    access = 'isAdmin' in session and session['isAdmin']
    if not access or not request.method == 'POST':
        return unauthorizedAccess()
    if 'sensorID' in request.form and 'newName' in request.form:
        res, msg = models.updateSensorName(request.form['sensorID'], request.form['newName'])
        flash(msg)
    else:
        flash('Invalid parameters')
    return device_panel()
