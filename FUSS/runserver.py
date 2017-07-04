"""
This script runs the FUSS application using a development server.
"""

from os import environ, path
from FUSS import app, host, port, debug, backgroundWorkers as bg




if __name__ == '__main__':
    #bg.start_runner()
    #bg.start_db_smoother()
    app.run(host, port, debug=debug)