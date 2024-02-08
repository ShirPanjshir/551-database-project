from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from database import report_crime
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
def landing_site():
    return render_template('home.html', crimes=crimes)

@app.route("/crime/<location>")    # delete - nest all searches into /search route with results_index() func
def list_crimes(location):
    """should a call function from database.py that lists all crimes matching that location"""
    crime_locations = search_location(location) # not built yet
    return jsonify(crime_locations)


@app.route("/crime/<id>")
def show_crime_data(id):
    """calls a function from database.py that lists all crimes matching the unique event number"""
    crime_info = search_event(id)
    return jsonify(crime_info)


@app.route("/search")
def search_index():
    return render_template('search.html', results='')


@app.route('/results')
def results_index():
    query = request.args.get('query')  # this pulls the query value
    category = request.args.get('category')  # this pulls the selected category and can feed into logic for querying
    print(category)
    crime_match = search_event(query)
    return render_template('search.html', results=crime_match)


@app.route("/reportacrime")
def crime_report_page():
    return render_template('reportacrime.html', password='')

@app.route('/reportacrimeadmin')
def crime_report_page_admin():
    input_password = request.args.get('password')
    print(input_password)
    if input_password == 'PLEASE':
        return render_template('reportacrime.html', password=input_password)
    else:
        return render_template('magicword.html')

@app.route("/crime/inputs/<id>")  # uploads data from site to proper database
def report_a_crime(id):
    data = request.args
    crime_string = json.dumps(data)
    report_crime(crime_string)
    return render_template('crimes_submitted.html', crimes=data)

# @app.route("/crime/report/<id>")   # returns matching data from database to site
# def report_results(id):
#     data = request.argsHow
#     print(data)
#     # crime_data = json.dumps(data)
#     crime_event_number = data.get('event')
#     found_event = search_event(crime_event)
#     return render_template('databasereport.html', crimes=found_event)


if __name__ == "__main__":
    app.run()
