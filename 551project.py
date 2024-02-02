from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from database import report_crime_json
from database import search_event
from database import search_location
import json

app = Flask(__name__)

crimes = [{"date": 112923, "event": 340790, "case": 2306474, "offense": "assault", "location": "1100 Block of 37th PL"
           , "disposition": "cleared arrest"},
          {"date": 113023, "event": 340791, "case": 2306475, "offense": "theft", "location": "1200 Block of 37th PL"
              , "disposition": "open"},
          {"date": 113023, "event": 340792, "offense": "larceny", "location": "1100 Block of 37th PL"
              , "disposition": "open"},
          {"date": 113123, "event": 340793, "case": 2306476, "offense": "assault", "location": "1500 Block of 37th PL"
              , "disposition": "cleared arrest"},
          ]


@app.route("/")
def hello_world():
    return render_template('home.html', crimes=crimes)

@app.route("/crime/<location>")
def list_crimes(location):
    """should a call function from database.py that lists all crimes matching that location"""
    crime_locations = search_location(location) # not built yet
    return jsonify(crime_locations)


@app.route("/crime/<id>")
def show_crime_data(id):
    """calls a function from database.py that lists all crimes matching the unique event number"""
    crime_info = search_event(id)
    return jsonify(crime_info)


@app.route("/reportacrime")
def crime_report_page():
    return render_template('reportacrime.html')


@app.route("/crime/inputs/<id>")  #not working yet!!!!!
def report_a_crime(id):
    data = request.args
    crime_json = data.json()
    report_crime_json(crime_json)
    return render_template('crimes_submitted.html', crimes=data)


if __name__ == "__main__":
    app.run()