"""
The flask application package.
"""

from flask import Flask
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
import FUSS.views
import FUSS.models

models.init_devices()
