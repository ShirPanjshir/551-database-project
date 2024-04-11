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

PARAS = ('date_rep', 'start_dt', 'end_dt', 'off_cat', 'off_des', 'disp',
         'ii_cat', 'ii_des', 'fi_cat', 'fi_des', 'loc', 'loc_type')

DROP_DOWNS = {'categories': CATEGORIES, 'dispositions': DISPOSITIONS, 'loc_types': LOCATION_TYPES}

MESSAGE_CASEID = 'Incorrect input format - Case ID must be a seven-digit number.'
MESSAGE_CASEID_CONFLICT = 'This Case ID has already been used.'
MESSAGE_CASEID_NULL = "Please enter a CaseID."
MESSAGE_EVENT = 'Incorrect input format - Event Number must follow this format: NN-NN-NN-NNNNNN.'
MESSAGE_EVENT_NULL = "Please enter an Event Number."
MESSAGE_ADV_EMPTY = 'Please fill in at least one field.'
MESSAGE_DT = 'Incorrect date format or invalid date.'
MESSAGE_DT_CONFLICT = 'Date From must be earlier than Date To.'
WARNING = 'Incorrect input format - please adjust'


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
    return render_template('search.html', results='', **DROP_DOWNS)


@app.route('/results')
def results_index():
    caseid = request.args.get('caseid')
    event = request.args.get('event')

    if caseid is not None:
        if not caseid:
            message = MESSAGE_CASEID_NULL
            return render_template('search.html', results="", warning=message, **DROP_DOWNS)
        else:
            try:
                crime_match = search_case_id(caseid)
            except ValueError:
                return render_template('search.html', results="", warning=MESSAGE_CASEID, **DROP_DOWNS)
    elif event is not None:
        if not event:
            message = MESSAGE_EVENT_NULL
            return render_template('search.html', results="", warning=message, **DROP_DOWNS)
        else:
            try:
                crime_match = search_event(event)
            except ValueError:
                return render_template('search.html', results="", warning=MESSAGE_EVENT, **DROP_DOWNS)
    else:
        search_filters = {}
        for p in PARAS:
            search_filters[p] = request.args.get(p)
        if all(not v for v in search_filters.values()):
            return render_template('search.html', results="", warning=MESSAGE_ADV_EMPTY, **DROP_DOWNS)
        try:
            crime_match = search(**search_filters)
        except ValueError:
            return render_template('search.html', results="", warning=MESSAGE_DT, **DROP_DOWNS)
        if crime_match == "DTCONFLICT":
            return render_template('search.html', results="", warning=MESSAGE_DT_CONFLICT, **DROP_DOWNS)

    number_found = len(crime_match)
    return render_template('search.html', results=crime_match, number_found=number_found, **DROP_DOWNS)


@app.route("/reportacrime")
def crime_report_page():
    return render_template('reportacrime.html', password='')


@app.route('/reportacrimeadmin')
def crime_report_page_admin():
    input_password = request.args.get('password')
    print(input_password)
    if input_password == 'PLEASE':
        return render_template('reportacrime.html', password=input_password, **DROP_DOWNS)
    else:
        return render_template('magicword.html')


@app.route("/crime/inputs/<id>")  # uploads data from site to proper database
def report_a_crime(id):
    data = request.args
    fields = {}
    for p in PARAS[1:]:
        fields[p] = data[p]
    if all(not v for v in fields.values()):
        return render_template('reportacrime.html', password='PLEASE', **DROP_DOWNS, warning=MESSAGE_ADV_EMPTY)
    fields['caseid'] = data['decision']
    status = report_case(**fields)
    if status == "DTERROR":
        return render_template('reportacrime.html', password='PLEASE', **DROP_DOWNS, warning=MESSAGE_DT)
    elif status == "DTCONFLICT":
        return render_template('reportacrime.html', password='PLEASE', **DROP_DOWNS, warning=MESSAGE_DT_CONFLICT)
    elif isinstance(status, int):
        message = f"Connection Issue. Status code {status}."
        return render_template('reportacrime.html', password='PLEASE', **DROP_DOWNS, warning=message)
    else:
        return render_template('crimes_submitted.html', eventid=status)


@app.route("/deletecase")
def delete_a_case():
    error = False
    event = request.args['Event']

    if not event:
        message, error = MESSAGE_EVENT_NULL, True
    else:
        try:
            match = search_event(event)
        except ValueError:
            message, error = MESSAGE_EVENT, True

    if not error:
        if match:
            delete_case(event)
            message = f'Case with Event Number {event} deleted.'
        else:
            message, error = f'Event Number {event} not in Database, no entries removed.', True

    if not error:
        return render_template('crimes_deleted.html', message=message)
    else:
        return render_template('reportacrime.html', password='PLEASE', warning=message, **DROP_DOWNS)


@app.route("/updateevent")
def update_event_info():
    empty = False
    error = False
    data = request.args
    fields = {}
    for p in PARAS[1:]:
        fields[p] = data[p]
    if all(not v for v in fields.values()):
        empty = True

    fields['event'] = data['Event']
    fields['caseid'] = data['CaseID']

    if not fields['event']:
        message, error = MESSAGE_EVENT_NULL, True
    else:
        try:
            match = search_event(fields['event'])
            if not match:
                message, error = f"Event Number {fields['event']} not in Database, no entries updated.", True
        except ValueError:
            message, error = MESSAGE_EVENT, True
    if empty:
        message, error = MESSAGE_ADV_EMPTY, True

    if not error:
        status = update_event(**fields)
        if status == 200:
            message = f"Case with Event Number {fields['event']} updated."
        elif status == "DTERROR":
            message, error = MESSAGE_DT, True
        elif status == "DTCONFLICT":
            message, error = MESSAGE_DT_CONFLICT, True
        elif status == "IDERROR":
            message, error = MESSAGE_CASEID, True
        elif status == "IDCONFLICT":
            message, error = MESSAGE_CASEID_CONFLICT, True
        else:
            message, error = "Unexpected Error.", True

    if error:
        return render_template('reportacrime.html', password='PLEASE', warning=message, **DROP_DOWNS)
    else:
        return render_template('crimes_updated.html', message=message)


if __name__ == "__main__":
    app.run()
