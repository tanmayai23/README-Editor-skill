import os
from flask import Flask
app = Flask(__name__)
SECRET = os.environ.get('FLASK_SECRET_KEY')

@app.get('/')
def index():
    return 'ok'
