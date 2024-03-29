'''
    This function will create first request to page so that flask can preload modules etc.
'''
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

'''
    This function will perform scan over last 1000 entries in DB to verify
    date continuity. Every gap will be filled with new entry with None as reading
    Whole task will run in background task, which should probably be handled by celery (WIP)
'''
def start_db_smoother():
    import threading
    import time
    from datetime import datetime
    import sys
    from FUSS import DBModels, db, app
    from sqlalchemy import asc, desc
    from sqlalchemy.sql import and_, or_, func
    import logging

    def loop():
        with app.app_context():
            print('starting db smoother job')
            time.sleep(2)
            entryCount = 1000
            correctedEntries = 0
            logging.info('performing db scan')
        
            sensors = DBModels.Sensors.query.all()
            logging.debug('got {} sensors'.format(len(sensors)))
            for s in sensors:
                entries = DBModels.SensorEntry.query.filter \
                    (DBModels.SensorEntry.sensor_id == s.id) \
                    .order_by(desc(DBModels.SensorEntry.date)).limit(entryCount).all()
                logging.debug('got {} entries'.format(len(entries)))
                entryCount = len(entries)
                if len(entries) < 100:
                    break
                avgTime = None
                i = 0
                for i in range(10):
                    if avgTime is None:
                        avgTime = (entries[i].date - entries[i+1].date)
                    else:
                        avgTime += (entries[i].date - entries[i+1].date)
                avgTime = avgTime/i
                threshold = avgTime * 1.01
                logging.debug('average time difference between entries is {}, threshold {}' \
                    .format(avgTime, threshold))
                for i in range(entryCount - 1):
                    e1 = entries[i]
                    e2 = entries[i+1]
                    timeDifference = e1.date - e2.date
                    tempTime = e1.date
                    while (timeDifference > threshold):
                        tempTime -= avgTime
                        logging.debug('time difference is {}, adding new value at {}' \
                            .format(timeDifference, tempTime))

                        e = DBModels.SensorEntry(s.id, None, tempTime)
                        print('t1: {} t2: {} t: {}'.format(e1.date, e2.date, e.date))
                        db.session.add(e)
                        timeDifference = e.date - e2.date
                        logging.debug('new time difference {}'.format(timeDifference))
                        correctedEntries += 1
                    db.session.commit()

            logging.info('Db smoother finished running')
            logging.info('Corrected {} entries'.format(correctedEntries))

    thread = threading.Thread(target=loop)
    thread.start()
    logging.info('Started db smoother thread')

