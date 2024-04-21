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
from database import SUCCESS


app = Flask(__name__)

CATEGORIES = ('', 'ADMINISTRATIVE', 'ALARM RESPONSE', 'ALCOHOL', 'ARSON', 'ASSAULT', 'ASSAULT-OTHER',
              'BATTERY', 'BURGLARY', 'BURGLARY-MOTOR VEHICLE', 'CRIMINAL THREATS', 'DEATH', 'DISORDERLY CONDUCT',
              'DISTURBANCE', 'DOMESTIC VIOLENCE', 'EH&S', 'EXTORTION', 'FIRE', 'FRAUD', 'HARASSMENT', 'HATE',
              'HOMELAND SECURITY', 'HOSPITAL', 'INCIDENT', 'LA MUNICIPAL CODE', 'MOTOR VEHICLE THEFT', 'NARCOTICS',
              'OBSCENE ACTIVITY', 'OBSERVATIONS', 'OFFICER STATUS', 'PROPERTY', 'ROBBERY', 'SERVICE', 'SEX OFFENSE',
              'SUICIDE', 'THEFT-GRAND', 'THEFT-MOTOR VEHICLE', 'THEFT-PETTY', 'THEFT-TRICK', 'TRAFFIC', 'TRESPASS',
              'VANDALISM', 'VEHICLE CODE', 'WARRANT', 'WEAPONS')

DISPOSITIONS = ('', 'ADVISED & COMPLIED', 'ADVISED OF 602 PC & RELEASED', 'CANCELLED EVENT', 'CLOSED',
                'Cleared Arrest', 'Cleared Other', 'Cleared by Exceptional Means', 'FIELD INTERVIEW & RELEASE',
                'Hold Over', 'Inactive Investigation', 'Investigation Continued', 'LAFD RESPONDING & WILL HANDLE',
                'LAPD ON SCENE & WILL HANDLE', 'NO CRIME OCCURRED; NO REPORT TAKEN', 'Open', 'PENDING INVESTIGATION',
                'REPORT TAKEN', 'REQUEST COMPLETED', 'RESOLVED UPON ARRIVAL', 'TRANSPORTED BY LAFD PARAMEDICS',
                'UNABLE TO LOCATE - GONE ON ARRIVAL', 'Void')

LOCATION_TYPES = ('', 'Non-campus building or property', 'Non-reportable location', 'On Campus',
                  'On Campus - Residential Facility', 'Public property')

DROP_DOWNS = {'categories': CATEGORIES, 'dispositions': DISPOSITIONS, 'loc_types': LOCATION_TYPES}

PARAS = ('date_rep', 'start_dt', 'end_dt', 'off_cat', 'off_des', 'disp',
         'ii_cat', 'ii_des', 'fi_cat', 'fi_des', 'loc', 'loc_type')

MESSAGE = {'IDERROR': 'Incorrect input format - Case ID must be a seven-digit number.',
           'IDCONFLICT': 'This Case ID has already been used.',
           'CASEID_NULL': 'Please enter a CaseID.',
           'EVENT': 'Incorrect input format - Event Number must follow this format: NN-NN-NN-NNNNNN.',
           'EVENT_NULL': "Please enter an Event Number.",
           'ADV_EMPTY': 'Please fill in at least one field.',
           'DTERROR': 'Incorrect date format or invalid date.',
           'DTCONFLICT': 'Date From must be earlier than Date To.',
           'WARNING': 'Incorrect input format - please adjust',
           'CONNECTIONERROR': "Connection error - Please contact admins.",
           'NOMATCH': 'Event Number %s not in Database, no entries %s.',
           'SUCCESS': "Case with Event Number %s %s."}

PWD = 'PLEASE'


@app.route("/")
def landing_site():
    return render_template('home.html')


@app.route("/crime/<id>")
def show_crime_data(id):
    """calls a function from database.py that lists all crimes matching the unique event number"""
    crime_info, status = search_event(id)
    if status != SUCCESS:
        crime_info = MESSAGE[crime_info]
    return jsonify(crime_info)


@app.route("/search")
def search_index():
    return render_template('search.html', results='', **DROP_DOWNS)


@app.route('/results')
def results_index():
    page = 'search.html'
    caseid = request.args.get('caseid')
    event = request.args.get('event')

    if caseid is not None:
        result, status = search_case_id(caseid)
    elif event is not None:
        result, status = search_event(event)
    else:
        search_filters = {p: request.args.get(p) for p in PARAS}
        if all(not v for v in search_filters.values()):
            return render_template(page, results='', warning=MESSAGE['ADV_EMPTY'], **DROP_DOWNS)
        result, status = search(**search_filters)

    if status != SUCCESS:
        message = MESSAGE.get(result, "Unexpected Error.")
        return render_template(page, results='', warning=message, **DROP_DOWNS)
    number_found = len(result)
    return render_template(page, results=result, number_found=number_found, **DROP_DOWNS)


@app.route("/reportacrime")
def crime_report_page():
    return render_template('reportacrime.html', password='')


@app.route('/reportacrimeadmin')
def crime_report_page_admin():
    input_password = request.args.get('password')
    if input_password == PWD:
        return render_template('reportacrime.html', password=input_password, **DROP_DOWNS)
    else:
        return render_template('magicword.html')


@app.route("/crime/inputs/<id>")  # uploads data from site to proper database
def report_a_crime(id):
    page = 'reportacrime.html'
    fields = {p: request.args.get(p) for p in PARAS[1:]}
    if all(not v for v in fields.values()):
        return render_template(page, password=PWD, warning=MESSAGE['ADV_EMPTY'], **DROP_DOWNS)
    fields['caseid'] = request.args.get('decision')

    result, status = report_case(**fields)
    if status == SUCCESS:
        return render_template('crimes_submitted.html', eventid=result)
    else:
        message = MESSAGE.get(result, "Unexpected Error.")
        return render_template(page, password=PWD, warning=message, **DROP_DOWNS)


@app.route("/deletecase")
def delete_a_case():
    page = 'reportacrime.html'
    event = request.args.get('Event')
    if not event:
        return render_template(page, password=PWD, warning=MESSAGE['EVENT_NULL'], **DROP_DOWNS)

    result, status = delete_case(event)
    if status == SUCCESS:
        message = MESSAGE[result] % (event, "deleted")
        return render_template('crimes_updated.html', message=message)
    else:
        if result == "NOMATCH":
            message = MESSAGE[result] % (event, "deleted")
        else:
            message = MESSAGE.get(result, "Unexpected Error.")
        return render_template(page, password=PWD, warning=message, **DROP_DOWNS)


@app.route("/updateevent")
def update_event_info():
    page = 'reportacrime.html'
    fields = {p: request.args.get(p) for p in (list(PARAS[1:]) + ['event', 'caseid'])}
    if all(not v for v in fields.values()):
        return render_template(page, password=PWD, warning=MESSAGE['ADV_EMPTY'], **DROP_DOWNS)

    result, status = update_event(**fields)
    if status == SUCCESS:
        message = MESSAGE[result] % (fields['event'], "updated")
        return render_template('crimes_updated.html', message=message)
    else:
        if result == "NOMATCH":
            message = MESSAGE[result] % (fields['event'], "updated")
        else:
            message = MESSAGE.get(result, "Unexpected Error.")
        return render_template(page, password=PWD, warning=message, **DROP_DOWNS)


if __name__ == "__main__":
    app.run()
