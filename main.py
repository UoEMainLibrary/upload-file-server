# ! /usr/bin/env python
import os
from datetime import date

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from logging.config import dictConfig

# Configuration for logging
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
CORS(app)
UPLOAD_PATH = 'upload/'


# Allow post and get methods as well as options for 'pre-flight' browser checks.
@app.route('/api/', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def api():
    # Only action if there's files being uploaded
    if request.method == 'POST' and len(request.files):
        # defensive check for uid
        uid = '' if request.form['uid'] is None else '_' + request.form['uid']

        upload_path = UPLOAD_PATH + date.today().strftime("%d-%m-%Y") + uid

        if not os.path.exists(upload_path):
            os.mkdir(upload_path)

        for f in request.files:
            uploaded_file = request.files[f]
            uploaded_file.save(os.path.join(upload_path, uploaded_file.filename))
        return jsonify(success=True)  # response content doesn't really matter as long as there is a response
    return jsonify(success=False)


# This will validate 'pre-flight' browser options requests (I think)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0')