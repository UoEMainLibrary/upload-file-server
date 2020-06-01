# ! /usr/bin/env python

import sys
sys.path.insert(0, '/home/lib/lacddt/py2libs')

from datetime import date
import email.message
import email.utils
import json
import os
import re
import requests
import smtplib

from flask import Flask, jsonify, request, abort
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
# UPLOAD_PATH='/home/lib/lacddt/collectingcovidserver/cc/upload/'
UPLOAD_PATH = '/backup/lac-store/cov19coll/'


def send_email(uid, depositor_address):
    # Create a text/plain message

    archivist_address = "crc-duty-archivist@ed.ac.uk"
    depositor_message = "Thank you for your submission to the University of Edinburgh Covid-19 Collecting" \
                        " Initiative. We appreciate and recognize that by getting in touch, you are helping" \
                        " us to document life in our University communities at a very significant time in" \
                        " our history. Creating this archive plays a vital role in providing a memory of" \
                        " this time for future reflection and use. \n \n Your reference number (UID) is:" \
                        " %s \n\n If you have any questions or issues regarding your submission, please email" \
                        " crc-duty-archivist@ed.ac.uk, quoting your reference number (UID) and we will" \
                        " be in touch." % uid

    depositor_mail = email.message.Message()
    depositor_mail['From'] = archivist_address
    depositor_mail['To'] = depositor_address
    depositor_mail['Subject'] = "Receipt for depositing to The University of Edinburgh Collecting Covid-19"

    depositor_mail.set_payload(depositor_message)

    notification = email.message.Message()
    notification['From'] = archivist_address
    notification['To'] = archivist_address
    notification['Subject'] = "Collecting Covid-19: new deposit"
    notification.set_payload("A new deposit: " + uid + " has been made")
    
    # Send the message
    s = smtplib.SMTP('bulkmailrelay.ucs.ed.ac.uk')

    if email.utils.parseaddr(depositor_address) != ('', ''):
        s.sendmail(archivist_address, depositor_address, depositor_mail.as_string())

    s.sendmail(archivist_address, archivist_address, notification.as_string())
    s.quit()


# Make sure a recursive path hasn't been passed
# Bad people do bad things
def validate_filenames(upload_path):
    for f in request.files:
        uploaded_file = request.files[f]
        dest_path = os.path.abspath(os.path.join(upload_path, uploaded_file.filename))
        if not dest_path.startswith(upload_path):
            return False

    return True


# Assume it is sufficient to validate as a sequence of numbers
def validate_uid(uid):
    return re.match(r'\d{4}-\d{2}-\d{2}_\d{1,4}$', uid) is not None


def get_uid(form):
    # If we are passed a 'uid' value then we will use that.
    if form['uid'] and validate_uid(form['uid']):
        return form['uid']

    today = date.today().strftime("%Y-%m-%d") + '_'

    # Collect all sub-directories of upload path as a generator
    gen = (x[0] for x in os.walk(UPLOAD_PATH))

    # Filter out those that don't belong to today
    sub_directories = [x for x in gen if today in x]

    # If there's been an upload today increment by one
    if len(sub_directories):
        # narrow down to a list of the running count and get biggest number
        last_number = max([int(x[x.rfind(today) + len(today):]) for x in sub_directories])

        return today + str(last_number + 1)

    # This is today's first upload
    return today + '1'


# Allow post and get methods as well as options for 'pre-flight' browser checks.
@app.route('/api/', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def api():
    # Only action if there's files being uploaded
    if request.method == 'POST':
        if len(request.files):
            dest_folder = get_uid(request.form)
            upload_path = os.path.abspath(os.path.join(UPLOAD_PATH, dest_folder))

            # Stop if there's an invalid filename
            if not validate_filenames(upload_path):
                return jsonify(success=False)

            # Create the directory to save the file
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)

            # Save each file
            for f in request.files:
                uploaded_file = request.files[f]
                uploaded_file.save(os.path.join(upload_path, uploaded_file.filename))

            return jsonify(dest_folder=dest_folder)
        else:
            # form_data = json.loads(json.dumps(request.form.to_dict(flat=False)))
            form_data = json.loads(request.data)

            dest_folder = get_uid(form_data)

            upload_path = os.path.abspath(os.path.join(UPLOAD_PATH, dest_folder))

            # Create the directory to save the file
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)

            # If files are not being sent then we've just left to write the form data
            if upload_path.startswith(os.path.abspath(UPLOAD_PATH)):
                with open(os.path.join(upload_path, 'form.json'), 'w') as f:
                    f.write(json.dumps(form_data))

                send_email(dest_folder, form_data['email'])
            else:
                abort(302)

        return jsonify(success=True)  # response content doesn't really matter as long as there is a response
    return abort(400)  # jsonify(success=False)


@app.route('/recaptcha/<recaptcha>', methods=['GET', 'OPTIONS'])
@cross_origin()
def recaptcha(recaptcha='0'):
    url = 'https://www.google.com/recaptcha/api/siteverify?'
    resp = requests.get(url + 'secret=' +
                 '&response=' + recaptcha)
    return resp.content


# This will validate 'pre-flight' browser options requests (I think)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0')
