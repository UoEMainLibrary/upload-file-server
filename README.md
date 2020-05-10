# HTTP upload file server in Flask

This is a simple (62 line) Flask server that accepts http requests to `http://[hostname]/api`
and save the file(s) in the formdata in a subdirectory of `UPLOAD_PATH` with a named
`"%d-%m-%y_%uid"` where: %d: day of the month, %m: month, %y: year and %uid is a value
passed in the submitted form to uniquely identify the submission. An example would be
`home/hrafn/PycharmProjects/upload-file-server/upload/08-05-2020_5801`.

Flask-Cors is added to allowed cross-origin requests and responses.

This runs on Python 3. The only dependency aside from
[Flask](https://flask.palletsprojects.com/en/1.1.x/) is
[Flask-Cors](https://flask-cors.readthedocs.io/en/latest/).

## Installation
1. Clone the repo.
2. Activate virtualenv (`source venv/bin/activate`)
3. Install requirements (`pip install -r requirements.txt`) 
4. Run the server (`python3 main.py`)

## Notes
I might have been hurrying but it seems to me that if you **start** by trying to access anything in
`request.files` ([see manual](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Request.files))
other than using the key `"file"` then Flask will respond with a 400. If so, this is a Flask bug,
but I can't be bothered with reproducing it. Therefore, the assumption that I go by is that the
request will contain the first file under the key `"file"`.

