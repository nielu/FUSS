"""
Routes and views for the flask application.
"""
#region imports
from datetime import datetime
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, make_response
from FUSS import app, models
from timeit import default_timer as timer
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

@app.route('/cleanup')
def cleanup():
    from FUSS import backgroundWorkers as bg
    bg.start_db_smoother()
    return 'OK', 201