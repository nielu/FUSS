"""
This script runs the FUSS application using a development server.
"""

from os import environ, path
from FUSS import app, host, port, debug


def start_runner():
    import threading
    import requests
    import time
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('http://127.0.0.1:{}/'.format(port))
                if r.status_code == 200:
                    print('Server started, quiting start_loop')
                    not_started = False
                print(r.status_code)
            except:
                print('Server not yet started')
            time.sleep(2)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()

if __name__ == '__main__':
    start_runner()
    app.run(host, port, debug=debug)