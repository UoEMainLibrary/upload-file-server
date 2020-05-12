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


# Bad people do bad things
def validate_filenames():
    for f in request.files:
        if '../' in f.filename:
            return False

    return True


# If we are not supplied with a proper uid then we won't try to use it
def validate_uid():
    if request.form['uid']:
        try:
            return '_' + str(int(request.form['uid']))
        except ValueError:
            pass
    return None

# Allow post and get methods as well as options for 'pre-flight' browser checks.
@app.route('/api/', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def api():
    # Only action if there's files being uploaded
    if request.method == 'POST':
        # defensive check for uid
        uid = validate_uid()

        # Stop if not supplied with valid uid
        if not uid:
            return jsonify(success=False)

        if len(request.files):
            # Stop if there's an invalid filename
            if not validate_filenames():
                return jsonify(success=False)

            # We've done checks and can carry on
            upload_path = UPLOAD_PATH + date.today().strftime("%d-%m-%Y") + uid

            # Create the directory to save the file
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)

            # Save each file
            for f in request.files:
                uploaded_file = request.files[f]
                uploaded_file.save(os.path.join(upload_path, uploaded_file.filename))
        else:
            print(request.headers)
            print(request.form)
            #print(request.get_json())
            #print(request.form)

        return jsonify(success=True)  # response content doesn't really matter as long as there is a response
    return jsonify(success=False)


# This will validate 'pre-flight' browser options requests (I think)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0')