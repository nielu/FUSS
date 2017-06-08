"""
This script runs the FUSS application using a development server.
"""

from os import environ, path
from FUSS import app

if __name__ == '__main__':
    host = 'localhost'
    port = 5000
    secret_key = ''
    db_name = ''
    db_in_memeory = False
    debug = False
    try:
        from config import *
    except ImportError:
        pass
    app.config.update(dict(
    DATABASE=path.join(app.root_path, db_name),
    SECRET_KEY=secret_key,
    DB_IN_MEM=db_in_memeory
    ))
    app.run(host, port, debug=debug)
