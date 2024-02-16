import tabula # must install java
import pandas as pd
import numpy as np
import requests
import json
import PyPDF2

# Kyle's links
database_urls = {0: "https://fir-tutorial-dbda2-default-rtdb.firebaseio.com/",
                 1: "https://trojan-force-default-rtdb.firebaseio.com/"}

# Dan's links
db = ("https://fir-tutorial-dbda2-default-rtdb.firebaseio.com/crimes.json",
      "https://trojan-force-default-rtdb.firebaseio.com/crimes.json")

# Time to remove test cases

crime_string = '{"date": 112923, "event": 340790, "case": 2306474, "offense": "assault", "location": "1100 Block of 37th PL", "disposition": "cleared arrest"}'

crimes = ['{"date": 112923, "event": 340790, "case": 2306474, "offense": "assault", "location": "1100 Block of 37th PL", "disposition": "cleared arrest"}',
          '{"date": 113023, "event": 340791, "case": 2306475, "offense": "theft", "location": "1200 Block of 37th PL", "disposition": "open"}',
          '{"date": 113023, "event": 340792, "offense": "larceny", "location": "1100 Block of 37th PL", "disposition": "open"}',
          '{"date": 113123, "event": 340793, "case": 2306476, "offense": "assault", "location": "1500 Block of 37th PL", "disposition": "cleared arrest"}',
          ]

crime_strings = ['{"date": 123563, "event": 123456, "offense": "bad stuff"}', '{"date": 127763, "event": 123477, '
                                                                              '"offense": "really bad stuff"}']


def batch_process_pdf(pdf_path):
    page = len(PyPDF2.PdfReader(pdf_path).pages)
    pdf = []
    error = []
    for i in range(1, page+1):
        try:
            pdf.extend(tabula.read_pdf(pdf_path, pages=i))
        except:
            error.append(i)
    header = ('Date Reported', 'Event #', 'Case #', 'Offense', 'Initial Incident', 'Final Incident',
              'Date From', 'Date To', 'Location', 'Disposition')
    for i, v in enumerate(pdf):
        if tuple(v.columns) != header:
            v = v.T.reset_index().T.reset_index(drop=True)  # send column names back to the first row
            v.columns = header  # rename column names
            pdf[i] = v
    df = pd.concat(pdf).reset_index(drop=True)
    df = df.replace(r'\r+|\n+|\t+', ' ', regex=True)
    df['Offense_Category'] = df.Offense.str.split(' -', n=1).str[0]
    df['Offense_Description'] = df.Offense.str.split(' -', n=1).str[1]    
    df.Offense_Description = df.Offense_Description.str.strip()
    df.Offense_Description = df.Offense_Description.str.replace(r"([^ ])(- )", r"\1 - ", regex=True)
    df.Offense_Description = df.Offense_Description.str.replace("Skateboar d", "Skateboard")

    df['Initial_Incident_Category'] = df['Initial Incident'].str.split(' -', n=1).str[0]
    df['Initial_Incident_Description'] = df['Initial Incident'].str.split(' -', n=1).str[1]
    df.Initial_Incident_Description = df.Initial_Incident_Description.str.strip()
    df.Initial_Incident_Description = df.Initial_Incident_Description.str.replace(r"([^ ])(- )", r"\1 - ", regex=True)
    df.Initial_Incident_Description = df.Initial_Incident_Description.str.replace("Skateboar d", "Skateboard")

    df['Final_Incident_Category'] = df['Final Incident'].str.split(' -', n=1).str[0]
    df['Final_Incident_Description'] = df['Final Incident'].str.split(' -', n=1).str[1]
    df.Final_Incident_Description = df.Final_Incident_Description.str.strip()
    df.Final_Incident_Description = df.Final_Incident_Description.str.replace(r"([^ ])(- )", r"\1 - ", regex=True)
    df.Final_Incident_Description = df.Final_Incident_Description.str.replace("Skateboar d", "Skateboard")

    df['Location_Type'] = df.Location.str.split(' - ', n=1).str[1]
    df.Location = df.Location.str.split(' - ', n=1).str[0]
    df.Location = df.Location.str.strip()
    df.Location_Type = df.Location_Type.str.replace(r"([^ ])(- )", r"\1-", regex=True)

    cols = list(df.columns)
    df = df[cols[0:3] + cols[10:16] + cols[6:9] + cols[16:] + cols[9:10]]
    df = df.rename(columns={"Date Reported": "Date_Reported", "Date From": "Date_From", "Date To": "Date_To"})
    df = df.rename(columns={"Case #": "CaseID", "Event #": "EventID"})

    df.Date_Reported = df.Date_Reported.str.replace(r" - [A-Z]{3} at ", " ", regex=True)
    df.Date_Reported = pd.to_datetime(df.Date_Reported, format="%m/%d/%y %H:%M")
    df.Date_Reported = df.Date_Reported.dt.strftime('%Y-%m-%d %H:%M')

    df.Date_From = df.Date_From.str.replace(r" - [A-Z]{3} at ", " ", regex=True)
    df.Date_From = df.Date_From.str.replace(r"\..*", "", regex=True)
    df.Date_From = pd.to_datetime(df.Date_From, format="%m/%d/%y %H:%M")
    df.Date_From = df.Date_From.dt.strftime('%Y-%m-%d %H:%M')

    df.Date_To = df.Date_To.str.replace(r" - [A-Z]{3} at ", " ", regex=True)
    df.Date_To = df.Date_To.str.replace(r"\..*", "", regex=True)
    df.Date_To = pd.to_datetime(df.Date_To, format="%m/%d/%y %H:%M")
    df.Date_To = df.Date_To.dt.strftime('%Y-%m-%d %H:%M')

    df.CaseID = df.CaseID.replace(r"[^0-9\.]*", np.nan, regex=True)
    df.CaseID = df.CaseID.astype(str).str.replace(r"\.[0-9]+", "", regex=True)
    df = df.replace(r"[ ]{2,}", " ", regex=True)
    df = df.replace('nan', np.nan)

    df0 = df[df.CaseID.isnull()].drop(columns='CaseID')
    dic0 = df0.set_index('EventID').to_dict(orient='index')
    for i in dic0:
        dic0[i] = {k: v for k, v in dic0[i].items() if v == v}
    r0 = requests.patch(f"{db[0]}", json=dic0)

    df1 = df[~df.CaseID.isnull()]
    dic1 = df1.set_index('EventID').to_dict(orient='index')
    for i in dic1:
        dic1[i] = {k: v for k, v in dic1[i].items() if v == v}
    r1 = requests.patch(f"{db[1]}", json=dic1)

    if r0.status_code != 200 or r1.status_code != 200:
        return f"Upload error. DB0 status code {r0.status_code}, DB1 status code {r1.status_code}"
    elif error:
        return f"Upload Complete. Failed to process page {error}. Please enter manually."
    else:
        return "Upload Complete."


def report_crime(crime):
    """This should be the function that allows a DBA to manually upload a new crime to the db. It can also be used
    in a loop to process an inputted batch. The input should be structured as a string version of a JSON with all
    standard parameters complete. The "event" from the pdf should be extracted and used as the primary key"""
    crime_record = json.loads(crime)
    del crime_record['SUBMIT']
    primary_key = crime_record.get("Event")
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


def report_case(caseid=False, dt_from=None, dt_to=None, off_cat=None, off_des=None, disp=None,
                ii_cat=None, ii_des=None, fi_cat=None, fi_des=None, loc_type=None, loc=None):
    '''
    dt_from and df_to must be pd.Timestamps!!!
    '''
    url = db[0]
    data = {'Disposition': disp, 'Final_Incident_Category': fi_cat, 'Final_Incident_Description': fi_des,
            'Initial_Incident_Category': ii_cat,'Initial_Incident_Description': ii_des,
            'Location': loc, 'Location_Type': loc_type, 'Offense_Category': off_cat, 'Offense_Description': off_des}
    if caseid:
        url = db[1]
        r = requests.get(f'{db[1]}?orderBy="CaseID"&limitToLast=1')
        data['CaseID'] = int(list(json.loads(r.text).values())[0]['CaseID']) + 1

    time = pd.Timestamp.now(tz='US/Pacific')  
    data['Date_Reported'] = time.strftime('%Y-%m-%d %H:%M')
    eventID = f"{time.strftime('%y-%m-%d')}-{time.hour*3600 + time.minute*60 + time.second:06}" 

    if dt_from:
        data['Date_From'] = dt_from.strftime('%Y-%m-%d %H:%M')
    if dt_to:
        data['Date_To'] = dt_to.strftime('%Y-%m-%d %H:%M')
    data = {k: v for k, v in data.items() if v is not None}
    case = {eventID: data}
    r = requests.patch(url, json=case)
    # FYI the primary key is eventID (automatically generated based on time reported)
    return r.status_code


def report_crime_json(crime):
    """This should be the function that allows a DBA to manually upload a new crime to the db. It can also be used
    in a loop to process an inputted batch. The input should be structured as a string version of a JSON with all
    standard parameters complete. The "event" from the pdf should be extracted and used as the primary key"""
    #need to convert case, date, and event from string to int, this will allow for simpler queries!!!!
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
    db1_url = f'{db1_url}/crimes.json?orderBy="$key"&equalTo="{event}"'
    db1_response = requests.get(db1_url)
    db1_data = db1_response.json()
    db2_url = database_urls.get(1)  # parameter logic
    db2_url = f'{db2_url}/crimes.json?orderBy="$key"&equalTo="{event}"'  #{db2_url}/crimes.json?orderBy=\"event\"&equalTo={event}
    db2_response = requests.get(db2_url)
    db2_data = db2_response.json()
    event_match.update(db1_data)
    event_match.update(db2_data)
    return event_match


# this works, tested 12feb, must quote out the numbers with dashes or will return error

def search_by_id(caseid):
    '''
    caseid should be a  seven-digit nuemeric string
    '''
    r = requests.get(db[1], params={'orderBy': '"CaseID"', 'equalTo': f'"{caseid}"'})
    # Use pd.DataFrame.from_dict(json.loads(r.text), orient='index').sort_index() to convert to df
    return json.loads(r.text)


def search(start_dt=None, end_dt=None, off_cat=None, off_des=None, ii_cat=None,
           ii_des=None, fi_cat=None, fi_des=None, loc_type=None, loc=None, disp=None):
    '''
    Please check datatypes before passing values into this function
    start_dt, end_dt -> str "YY-MM-DD" 
    off_cat, ii_cat, fi_cat = str CATEGORIES in project.py
    loc_type = str LOCATION_TYPES in project.py
    disp = str DISPOSITIONS in project.py
    off_des, ii_des, fi_des = str
    '''
    # Pick one filter and download data
    if start_dt or end_dt:
        r0 = requests.get(db[0], params={'orderBy': '"$key"', 'startAt': f'"{start_dt}"', 'endAt': f'"{end_dt}"'})
        r1 = requests.get(db[1], params={'orderBy': '"$key"', 'startAt': f'"{start_dt}"', 'endAt': f'"{end_dt}"'})
    elif off_cat:
        r0 = requests.get(db[0], params={'orderBy': '"Offense_Category"', 'equalTo': f'"{off_cat}"'})
        r1 = requests.get(db[1], params={'orderBy': '"Offense_Category"', 'equalTo': f'"{off_cat}"'})
    elif ii_cat:
        r0 = requests.get(db[0], params={'orderBy': '"Initial_Incident_Category"', 'equalTo': f'"{ii_cat}"'})
        r1 = requests.get(db[1], params={'orderBy': '"Initial_Incident_Category"', 'equalTo': f'"{ii_cat}"'})
    elif fi_cat:
        r0 = requests.get(db[0], params={'orderBy': '"Final_Incident_Category"', 'equalTo': f'"{fi_cat}"'})
        r1 = requests.get(db[1], params={'orderBy': '"Final_Incident_Category"', 'equalTo': f'"{fi_cat}"'})
    elif loc_type:
        r0 = requests.get(db[0], params={'orderBy': '"Location_Type"', 'equalTo': f'"{loc_type}"'})
        r1 = requests.get(db[1], params={'orderBy': '"Location_Type"', 'equalTo': f'"{loc_type}"'})
    elif disp:
        r0 = requests.get(db[0], params={'orderBy': '"Disposition"', 'equalTo': f'"{disp}"'})
        r1 = requests.get(db[1], params={'orderBy': '"Disposition"', 'equalTo': f'"{disp}"'})
    else:
        r0 = requests.get(db[0])
        r1 = requests.get(db[1])

    # Merge jsons into one df
    data = json.loads(r0.text)
    data.update(json.loads(r1.text))
    df = pd.DataFrame.from_dict(data, orient='index').sort_index()

    # Categorical filters
    if off_cat:
        df = df[df.Offense_Category == off_cat]
    if ii_cat:
        df = df[df.Initial_Incident_Category == ii_cat]
    if fi_cat:
        df = df[df.Final_Incident_Category == fi_cat]
    if loc_type:
        df = df[df.Location_Type == loc_type]
    if disp:
        df = df[df.Disposition == disp]

    # case insentitive partial match
    if off_des:
        df = df[df.Offense_Description.str.lower().str.contains(off_des.lower())]
    if ii_des:
        df = df[df.Initial_Incident_Description.str.lower().str.contains(ii_des.lower())]
    if fi_des:
        df = df[df.Final_Incident_Description.str.lower().str.contains(fi_des.lower())]
    if loc:
        df = df[df.Location.str.lower().str.contains(loc.lower())]
    # use df.to_json(orient="index") or df.to_dict(orient="index") to convert to json string / dict
    return df


def search_location(location):
    """This will search the databases for events that match on location"""
    location_matches = {}
    db1_url = database_urls.get(0)
    db1_url = f'{db1_url}/crimes.json?orderBy=\"Location\"&equalTo=\"{location}\"'
    db1_response = requests.get(db1_url)
    print(db1_response)
    db1_data = db1_response.json()
    print(db1_data)
    db2_url = database_urls.get(1)  # parameter logic
    db2_url = f'{db2_url}/crimes.json?orderBy=\"Location\"&equalTo=\"{location}\"'
    db2_response = requests.get(db2_url)
    print(db2_response)
    db2_data = db2_response.json()
    print(db2_data)
    location_matches.update(db1_data)
    location_matches.update(db2_data)
    return location_matches
# {'error': 'Constraint index field must be a JSON primitive'}   or {}


def search_case_id(case_id):
    case_match = {}
    db1_url = database_urls.get(0)
    db1_url = f'{db1_url}/crimes.json?orderBy=\"CaseID\"&equalTo={case_id}'
    db1_response = requests.get(db1_url)
    db1_data = db1_response.json()
    db2_url = database_urls.get(1)  # parameter logic
    db2_url = f'{db2_url}/crimes.json?orderBy=\"CaseID\"&equalTo={case_id}'
    db2_response = requests.get(db2_url)
    db2_data = db2_response.json()
    case_match.update(db1_data)
    case_match.update(db2_data)
    return case_match
# works 12FEB24


print(search_location("3100 Block Of FIGUEROA ST"))

# print(search_case_id('2306606'))

# print(search_event('301215888777'))
#
# print(search_event('24-02-06-041188'))

# print(search_event('24-02-05-039645'))
#
# print(search_event('24-02-04-037848'))