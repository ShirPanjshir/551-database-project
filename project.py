from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from database import search_event
from database import search_case_id
from database import search
from database import report_case
from database import delete_case
from database import update_event


app = Flask(__name__)

CATEGORIES = {'', 'ADMINISTRATIVE', 'ALARM RESPONSE', 'ALCOHOL', 'ARSON', 'ASSAULT', 'ASSAULT-OTHER',
              'BATTERY', 'BURGLARY', 'BURGLARY-MOTOR VEHICLE', 'CRIMINAL THREATS', 'DEATH', 'DISORDERLY CONDUCT',
              'DISTURBANCE', 'DOMESTIC VIOLENCE', 'EH&S', 'EXTORTION', 'FIRE', 'FRAUD',
              'HARASSMENT', 'HATE', 'HOMELAND SECURITY', 'HOSPITAL', 'INCIDENT', 'LA MUNICIPAL CODE',
              'MOTOR VEHICLE THEFT', 'NARCOTICS', 'OBSCENE ACTIVITY', 'OBSERVATIONS', 'OFFICER STATUS', 'PROPERTY',
              'ROBBERY', 'SERVICE', 'SEX OFFENSE', 'SUICIDE', 'THEFT-GRAND', 'THEFT-MOTOR VEHICLE',
              'THEFT-PETTY', 'THEFT-TRICK', 'TRAFFIC', 'TRESPASS', 'VANDALISM', 'VEHICLE CODE', 'WARRANT', 'WEAPONS'}

DISPOSITIONS = {'', 'ADVISED & COMPLIED', 'ADVISED OF 602 PC & RELEASED', 'CANCELLED EVENT', 'CLOSED',
                'Cleared Arrest', 'Cleared Other', 'Cleared by Exceptional Means', 'FIELD INTERVIEW & RELEASE',
                'Hold Over', 'Inactive Investigation', 'Investigation Continued', 'LAFD RESPONDING & WILL HANDLE',
                'LAPD ON SCENE & WILL HANDLE', 'NO CRIME OCCURRED; NO REPORT TAKEN', 'Open', 'PENDING INVESTIGATION',
                'REPORT TAKEN', 'REQUEST COMPLETED', 'RESOLVED UPON ARRIVAL', 'TRANSPORTED BY LAFD PARAMEDICS',
                'UNABLE TO LOCATE - GONE ON ARRIVAL', 'Void'}

LOCATION_TYPES = {'', 'Non-campus building or property', 'Non-reportable location', 'On Campus',
                  'On Campus - Residential Facility', 'Public property'}


@app.route("/")
def landing_site():
    return render_template('home.html')


@app.route("/crime/<id>")
def show_crime_data(id):
    """calls a function from database.py that lists all crimes matching the unique event number"""
    crime_info = search_event(id)
    return jsonify(crime_info)


@app.route("/search")
def search_index():
    return render_template('search.html', results='', categories=CATEGORIES,
                           dispositions=DISPOSITIONS, loc_types=LOCATION_TYPES)


@app.route('/results')
def results_index():
    query = request.args.get('query')  # this pulls the query value
    event = request.args.get('Event')
    date_from = request.args.get('Date_From')
    date_reported = request.args.get('Date_Reported')
    date_to = request.args.get('Date_To')  # being used as endat rather than independent parameters
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
    return render_template('search.html', results=crime_match, number_found=number_found, categories=CATEGORIES,
                           dispositions=DISPOSITIONS, loc_types=LOCATION_TYPES)


@app.route("/reportacrime")
def crime_report_page():
    return render_template('reportacrime.html', password='')


@app.route('/reportacrimeadmin')
def crime_report_page_admin():
    input_password = request.args.get('password')
    print(input_password)
    if input_password == 'PLEASE':
        return render_template('reportacrime.html', password=input_password, categories=CATEGORIES,
                               dispositions=DISPOSITIONS, loc_types=LOCATION_TYPES)
    else:
        return render_template('magicword.html')


@app.route("/crime/inputs/<id>")  # uploads data from site to proper database
def report_a_crime(id):
    data = request.args
    decision = data['decision']
    date_from = data['Date_From']
    date_to = data['Date_To']
    disposition = data['Disposition']
    final_incident_category = data['Final_Incident_Category']
    final_incident_description = data['Final_Incident_Description']
    initial_incident_category = data['Initial_Incident_Category']
    initial_incident_description = data['Initial_Incident_Description']
    location = data['Location']
    location_type = data['Location_Type']
    offense_category = data['Offense_Category']
    offense_description = data['Offense_Description']
    eventid, status = report_case(decision, date_from, date_to, offense_category, offense_description, disposition,
                                  initial_incident_category, initial_incident_description, final_incident_category,
                                  final_incident_description, location_type, location)
    return render_template('crimes_submitted.html', crimes=data, eventid=eventid)


@app.route("/deletecase")
def delete_a_case():
    data = request.args
    event = data['Event']
    if search_event(event):
        delete_case(event)
        print(f'Case with Event Number {event} deleted')
        message = f'Case with Event Number {event} deleted.'
    else:
        print(f'Event Number {event} not in Database, no entries removed.')
        message = f'Event Number {event} not in Database, no entries removed.'
    return render_template('crimes_deleted.html', message=message)


@app.route("/updateevent")
def update_event_info():
    data = request.args
    event = data['Event']
    caseid = data['CaseID']
    date_from = data['Date_From']
    date_to = data['Date_To']
    disposition = data['Disposition']
    final_incident_category = data['Final_Incident_Category']
    final_incident_description = data['Final_Incident_Description']
    initial_incident_category = data['Initial_Incident_Category']
    initial_incident_description = data['Initial_Incident_Description']
    location = data['Location']
    location_type = data['Location_Type']
    offense_category = data['Offense_Category']
    offense_description = data['Offense_Description']
    if search_event(event):
        update_event(event, caseid, date_from, date_to, disposition, final_incident_category,
                     final_incident_description, initial_incident_category, initial_incident_description, location,
                     location_type, offense_category, offense_description)
        print(f'Case with Event Number {event} updated')
        message = f'Case with Event Number {event} updated.'
    else:
        print(f'Event Number {event} not in Database, no entries updated.')
        message = f'Event Number {event} not in Database, no entries updated.'
    return render_template('crimes_updated.html', message=message)


if __name__ == "__main__":
    app.run()
