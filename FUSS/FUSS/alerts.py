from smsapi.client import SmsAPI
from smsapi.responses import ApiError

from FUSS import app, DBModels, models
import logging

api = SmsAPI()
api.auth_token = app.config['SMS_API_KEY']
MAX_MSG_LEN = 160


def sendMessage(number, message):
    message = message.strip()
    asciiMessage = ''
    logging.info('Sending message to {}:"{}"'.format(number, message))
    try:
       asciiMessage = message #message.encode('ascii')
    except UnicodeEncodeError:
        logging.error('Message was not in ASCII!')
    try:
        if len(asciiMessage) > MAX_MSG_LEN:
            logging.error('Message was too long! ' + asciiMessage)
            return False

        api.service('sms').action('send')
        api.set_content(asciiMessage)
        api.set_to(number)

        res = api.execute()

        for r in res:
            logging.info('SMS returned {}: {} - {}'.format(r.id, r.points, r.status))
        return True
    except ApiError as e:
        logging.error('MSG thrown exception: {}-{}'.format(e.code, e.message))
        return False
