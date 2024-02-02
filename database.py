import json
import requests

database_urls = {0: "https://fir-tutorial-dbda2-default-rtdb.firebaseio.com/",
                 1: "https://trojan-force-default-rtdb.firebaseio.com/"}

#the list below is provided for testing. individual string works as well as in loop with list of strings

crime_string = '{"date": 112923, "event": 340790, "case": 2306474, "offense": "assault", "location": "1100 Block of 37th PL", "disposition": "cleared arrest"}'

crimes = ['{"date": 112923, "event": 340790, "case": 2306474, "offense": "assault", "location": "1100 Block of 37th PL", "disposition": "cleared arrest"}',
          '{"date": 113023, "event": 340791, "case": 2306475, "offense": "theft", "location": "1200 Block of 37th PL", "disposition": "open"}',
          '{"date": 113023, "event": 340792, "offense": "larceny", "location": "1100 Block of 37th PL", "disposition": "open"}',
          '{"date": 113123, "event": 340793, "case": 2306476, "offense": "assault", "location": "1500 Block of 37th PL", "disposition": "cleared arrest"}',
          ]

crime_strings = ['{"date": 123563, "event": 123456, "offense": "bad stuff"}', '{"date": 127763, "event": 123477, '
                                                                              '"offense": "really bad stuff"}']


def batch_process_pdf(batch):
    """This should be the function that inputs a pdf, reads the content into a dictionary or list of strings that can
    then be uploaded all at once. The data cleaning and pdf conversion into an object(s) that can be fed into the
    report_crime() function"""


def report_crime_string(crime):
    """This should be the function that allows a DBA to manually upload a new crime to the db. It can also be used
    in a loop to process an inputted batch. The input should be structured as a string version of a JSON with all
    standard parameters complete. The "event" from the pdf should be extracted and used as the primary key"""
    crime_record = json.loads(crime)
    primary_key = crime_record.get("event")
    try:
        if crime_record.get("case") > 1:
            url = database_urls.get(1)
    except:
        url = database_urls.get(0)
    url = f"{url}/crimes/{primary_key}/.json"
    response = requests.put(url, json=crime_record)
    status_code = response.status_code
    return status_code, print(f'Crime {primary_key} submitted to database!')

# this works, tested 2feb24 by kwp

def report_crime_json(crime):
    """This should be the function that allows a DBA to manually upload a new crime to the db. It can also be used
    in a loop to process an inputted batch. The input should be structured as a string version of a JSON with all
    standard parameters complete. The "event" from the pdf should be extracted and used as the primary key"""
    crime_record = json.load(crime)
    primary_key = crime_record.get("event")
    try:
        if crime_record.get("case") > 1:
            url = database_urls.get(1)
    except:
        url = database_urls.get(0)
    url = f"{url}/crimes/{primary_key}/.json"
    response = requests.put(url, json=crime_record)
    status_code = response.status_code
    return status_code, print(f'Crime {primary_key} submitted to database!')

def search_event(event):
    event_match = {}
    db1_url = database_urls.get(0)
    db1_url = f'{db1_url}/crimes.json?orderBy=\"event\"&equalTo={event}'
    db1_response = requests.get(db1_url)
    db1_data = db1_response.json()
    db2_url = database_urls.get(1)  # parameter logic
    db2_url = f'{db2_url}/crimes.json?orderBy=\"event\"&equalTo={event}'
    db2_response = requests.get(db2_url)
    db2_data = db2_response.json()
    event_match.update(db1_data)
    event_match.update(db2_data)
    return event_match

# this works, tested 2feb24 by kwp

def search_location(location):
    """This will search the databases for events that match on location"""
    location_matches = {}
    return location_matches

print(search_event(123477))
