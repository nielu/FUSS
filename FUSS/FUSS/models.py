#region imports
from FUSS import app, bcrypt
from flask import Flask, request, session, g, redirect, url_for, abort, \
   flash, make_response, config, _app_ctx_stack
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
    from io import StringIO
    if (app.config['DB_IN_MEM']):
        print('Loading db to memory')
        #create temporary file to store in memory
        file_db = sqlite3.connect(app.config['DATABASE'])
        tempfile = StringIO()
        for line in file_db.iterdump():
            tempfile.write('%s\n' % line)
        file_db.close()
        tempfile.seek(0)
    
        #create db in memory from file
        rv = sqlite3.connect(':memory:')
        rv.cursor().executescript(tempfile.read())
        rv.commit()
    else:
        rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    #if 'sqlite_db' not in app.config
    #    app.config.update(dict(sqlite_db=connect_db()))
    #return app.config['sqlite_db']
    #if not hasattr(flask.g, 'sqlite_db'):
    #    g.sqllite_db = connect_db()
    #return g.sqllite_db
    if not hasattr(app, 'sqlite_db'):
        app.sqlite_db = connect_db()
    return app.sqlite_db;

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
    devices = []
    for m in modules:
        print('Loading device module {}'.format(m))
        moduleName = 'FUSS.devices.{}'.format(m)
        devModule = importlib.import_module(moduleName)
        devices.append(m)
        app.register_blueprint(devModule.device_blueprint, url_prefix=('/dev/' + m))
    app.config.update(dict(DEVICES=devices))

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
    if (account == None or bcrypt.check_password_hash(account[1], password) == False):
        return False, 'Invalid username or password'
    session['logged_in'] = True
    return True, 'Logged in'
