#region imports
from FUSS import app, bcrypt, db
from FUSS.DBModels import *
from flask import Flask, request, session, g, redirect, url_for, abort, \
   flash, make_response, config, _app_ctx_stack
from timeit import default_timer as timer
import sqlite3
import os
import datetime
import pkgutil
#endregion


#region Database

#endregion
@app.before_first_request
def init_devices():
    import pkgutil
    import importlib
    modules = [name for _, name, _ in pkgutil.iter_modules(['FUSS/devices'])]
    print('Got {} module(s)'.format(len(modules)))
    devices = []
    for m in modules:
        print('Loading device module {}'.format(m))
        moduleName = 'FUSS.devices.{}'.format(m)
        devModule = importlib.import_module(moduleName)
        devices.append(m)
        app.register_blueprint(devModule.device_blueprint, url_prefix=('/dev/' + m))
        devModule.init()
    app.config.update(dict(DEVICES=devices))

def registerUser(name, password):
    exist = User.query.filter_by(username=name).first()
    if (exist is not None):
        return False, 'User already exists'
    hash = bcrypt.generate_password_hash(password).decode('utf-8')
    newUser = User(name, hash)
    db.session.add(newUser)
    db.session.commit()
    return True, 'Account created'

def login(name, password):
    user = User.query.filter_by(username=name).first()
    if (user is None or bcrypt.check_password_hash(user.password, password) == False):
        return False, 'Invalid username or password'
    session['logged_in'] = True
    return True, 'Logged in'


