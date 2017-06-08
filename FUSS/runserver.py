"""
This script runs the FUSS application using a development server.
"""

from os import environ, path
from FUSS import app

if __name__ == '__main__':
    host = 'localhost'
    port = 5000
    secret_key = ''
    username = ''
    password = ''
    db_name = ''
    debug = False
    try:
        from config import *
    except ImportError:
        pass
    app.config.update(dict(
    DATABASE=path.join(app.root_path, db_name),
    SECRET_KEY=secret_key,
    USERNAME=username,
    PASSWORD=password
    ))
    app.run(host, port, debug=debug)
