from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from database import report_crime
from database import search_event
from database import search_case_id
from database import search
import json

app = Flask(__name__)

CATEGORIES = {'ADMINISTRATIVE', 'ALARM RESPONSE', 'ALCOHOL', 'ARSON', 'ASSAULT', 'ASSAULT-OTHER',
              'BATTERY', 'BURGLARY', 'BURGLARY-MOTOR VEHICLE', 'CRIMINAL THREATS', 'DEATH', 'DISORDERLY CONDUCT',
              'DISTURBANCE', 'DOMESTIC VIOLENCE', 'EH&S', 'EXTORTION', 'FIRE', 'FRAUD',
              'HARASSMENT', 'HATE', 'HOMELAND SECURITY', 'HOSPITAL', 'INCIDENT', 'LA MUNICIPAL CODE',
              'MOTOR VEHICLE THEFT', 'NARCOTICS', 'OBSCENE ACTIVITY', 'OBSERVATIONS', 'OFFICER STATUS', 'PROPERTY',
              'ROBBERY', 'SERVICE', 'SEX OFFENSE', 'SUICIDE', 'THEFT-GRAND', 'THEFT-MOTOR VEHICLE',
              'THEFT-PETTY', 'THEFT-TRICK', 'TRAFFIC', 'TRESPASS', 'VANDALISM', 'VEHICLE CODE', 'WARRANT', 'WEAPONS'}

DISPOSITIONS = {'ADVISED & COMPLIED', 'ADVISED OF 602 PC & RELEASED', 'CANCELLED EVENT', 'CLOSED',
               'Cleared Arrest', 'Cleared Other', 'Cleared by Exceptional Means', 'FIELD INTERVIEW & RELEASE',
               'Hold Over', 'Inactive Investigation', 'Investigation Continued', 'LAFD RESPONDING & WILL HANDLE',
               'LAPD ON SCENE & WILL HANDLE', 'NO CRIME OCCURRED; NO REPORT TAKEN', 'Open', 'PENDING INVESTIGATION',
               'REPORT TAKEN', 'REQUEST COMPLETED', 'RESOLVED UPON ARRIVAL', 'TRANSPORTED BY LAFD PARAMEDICS',
               'UNABLE TO LOCATE - GONE ON ARRIVAL', 'Void'}

LOCATION_TYPES = {'Non-campus building or property', 'Non-reportable location', 'On Campus',
                  'On Campus - Residential Facility', 'Public property'}

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
    event = request.args.get('Event')
    date_from = request.args.get('Date_From')
    date_reported = request.args.get('Date_Reported')
    date_to = request.args.get('Date_To')
    disposition = request.args.get('Disposition')
    final_incident_category = request.args.get('Final_Incident_Category')
    final_incident_description = request.args.get('Final_Incident_Description')
    initial_incident_category = request.args.get('Initial_Incident_Category')
    initial_incident_description = request.args.get('Initial_Incident_Description')
    location = request.args.get('Location')
    location_type = request.args.get('Location_Type')
    offense_category = request.args.get('Offense_Category')
    offense_description = request.args.get('Offense_Description')
    print(date_from)
    if query:
        crime_match = search_case_id(query)
        print(crime_match)
    elif event:
        crime_match = search_event(event)
        print(crime_match)
    else:
        crime_match = search(date_from, date_to, date_reported, offense_category, offense_description,
                             initial_incident_category, initial_incident_description, final_incident_category,
                             final_incident_description, location_type, location, disposition)
    number_found = len(crime_match)
    return render_template('search.html', results=crime_match, number_found=number_found)


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
    event_number = data['Event']
    crime_string = json.dumps(data)
    report_crime(crime_string)
    return render_template('crimes_submitted.html', crimes=event_number)  #UPDATE REQUIRED on c_s.html


if __name__ == "__main__":
    app.run()
