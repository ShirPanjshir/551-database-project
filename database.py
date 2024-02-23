import tabula  # must install java
import warnings
import pandas as pd
import numpy as np
import requests
import json

warnings.simplefilter(action='ignore', category=FutureWarning)

# Kyle's links
database_urls = {0: "https://fir-tutorial-dbda2-default-rtdb.firebaseio.com/",
                 1: "https://trojan-force-default-rtdb.firebaseio.com/"}

# Dan's links
db = ("https://fir-tutorial-dbda2-default-rtdb.firebaseio.com/crimes.json",
      "https://trojan-force-default-rtdb.firebaseio.com/crimes.json")


def batch_process_pdf(pdf_path):
    # 22FEB24 by Dan
    error = []
    pdf = tabula.read_pdf(pdf_path, pages='all')
    header = ('Date Reported', 'Event #', 'Case #', 'Offense', 'Initial Incident', 'Final Incident',
              'Date From', 'Date To', 'Location', 'Disposition')
    for i, v in enumerate(pdf):
        if v.iloc[:, 0].isnull().any() or len(v.columns) != 10:
            error.append(i)
        elif tuple(v.columns) != header:
            v = v.T.reset_index().T.reset_index(drop=True)  # send column names back to the first row
            v.columns = header  # rename column names
            pdf[i] = v
    pdf = [v for i, v in enumerate(pdf) if i not in error]
    error = [i+1 for i in error]
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


def report_case(caseid=False, dt_from=None, dt_to=None, off_cat=None, off_des=None, disp=None,
                ii_cat=None, ii_des=None, fi_cat=None, fi_des=None, loc_type=None, loc=None):
    '''
    dt_from and df_to must be pd.Timestamps!!!
    '''
    url = db[0]
    data = {'Disposition': disp, 'Final_Incident_Category': fi_cat, 'Final_Incident_Description': fi_des,
            'Initial_Incident_Category': ii_cat, 'Initial_Incident_Description': ii_des,
            'Location': loc, 'Location_Type': loc_type, 'Offense_Category': off_cat, 'Offense_Description': off_des}
    if caseid == 'yes':
        url = db[1]
        r = requests.get(f'{url}?orderBy="CaseID"&limitToLast=1')
        data['CaseID'] = str(int(list(json.loads(r.text).values())[0]['CaseID']) + 1)
    else:
        url = db[0]

    time = pd.Timestamp.now(tz='US/Pacific')
    data['Date_Reported'] = time.strftime('%Y-%m-%d %H:%M')
    sec = time.hour * 3600 + time.minute * 60 + time.second
    eventID = f"{time.strftime('%y-%m-%d')}-{sec:06}"

    if dt_from:
        dt_from = pd.to_datetime(dt_from, format='%Y-%m-%d %H:%M')
        data['Date_From'] = dt_from.strftime('%Y-%m-%d %H:%M')
    if dt_to:
        dt_to = pd.to_datetime(dt_to, format='%Y-%m-%d %H:%M')
        data['Date_To'] = dt_to.strftime('%Y-%m-%d %H:%M')
    data = {k: v for k, v in data.items() if v}
    case = {eventID: data}
    r = requests.patch(url, json=case)
    return r.status_code


def ez_download(p):
    r0 = requests.get(db[0], params=p)
    r1 = requests.get(db[1], params=p)
    return r0, r1


def search(start_dt=None, end_dt=None, date_rep=None, off_cat=None, off_des=None, ii_cat=None,
           ii_des=None, fi_cat=None, fi_des=None, loc_type=None, loc=None, disp=None):

    if start_dt:
        start_dt = pd.to_datetime(start_dt, format="%y-%m-%d")
        start_dt = start_dt.strftime("%Y-%m-%d")
    if end_dt:
        end_dt = pd.to_datetime(end_dt, format="%y-%m-%d")
        end_dt = end_dt + pd.Timedelta(days=1)
        end_dt = end_dt.strftime("%Y-%m-%d")
    # Pick one filter and download data
    if date_rep:
        date_rep = pd.to_datetime(date_rep, format="%y-%m-%d")
        next = date_rep + pd.Timedelta(days=1)
        date_rep = date_rep.strftime("%Y-%m-%d")
        next = next.strftime("%Y-%m-%d")
        r0, r1 = ez_download({'orderBy': '"Date_Reported"', 'startAt': f'"{date_rep}"', 'endAt': f'"{next}"'})
    elif start_dt:
        r0, r1 = ez_download({'orderBy': '"Date_From"', 'startAt': f'"{start_dt}"'})
    elif end_dt:
        r0, r1 = ez_download({'orderBy': '"Date_To"', 'endAt': f'"{end_dt}"'})
    elif off_cat:
        r0, r1 = ez_download({'orderBy': '"Offense_Category"', 'equalTo': f'"{off_cat}"'})
    elif ii_cat:
        r0, r1 = ez_download({'orderBy': '"Initial_Incident_Category"', 'equalTo': f'"{ii_cat}"'})
    elif fi_cat:
        r0, r1 = ez_download({'orderBy': '"Final_Incident_Category"', 'equalTo': f'"{fi_cat}"'})
    elif loc_type:
        r0, r1 = ez_download({'orderBy': '"Location_Type"', 'equalTo': f'"{loc_type}"'})
    elif disp:
        r0, r1 = ez_download({'orderBy': '"Disposition"', 'equalTo': f'"{disp}"'})
    else:
        r0 = requests.get(db[0])
        r1 = requests.get(db[1])

    # Merge jsons into one df
    data = r0.json()
    data.update(r1.json())
    df = pd.DataFrame.from_dict(data, orient='index').sort_index()

    if start_dt and ("Date_From" in df):
        df = df[df.Date_From >= start_dt]
    if end_dt and ("Date_To" in df):
        df = df[df.Date_To <= end_dt]
    # Categorical filters
    if off_cat and ("Offense_Category" in df):
        df = df[df.Offense_Category == off_cat]
    if ii_cat and ("Initial_Incident_Category" in df):
        df = df[df.Initial_Incident_Category == ii_cat]
    if fi_cat and ("Final_Incident_Category" in df):
        df = df[df.Final_Incident_Category == fi_cat]
    if loc_type and ("Location_Type" in df):
        df = df[df.Location_Type == loc_type]
    if disp and ("Disposition" in df):
        df = df[df.Disposition == disp]

    # case insentitive partial match
    if off_des and ("Offense_Description" in df):
        df = df[df.Offense_Description.str.contains(off_des, regex=False, na=False, case=False)]
    if ii_des and ("Initial_Incident_Description" in df):
        df = df[df.Initial_Incident_Description.str.contains(ii_des, regex=False, na=False, case=False)]
    if fi_des and ("Final_Incident_Description" in df):
        df = df[df.Final_Incident_Description.str.contains(fi_des, regex=False, na=False, case=False)]
    if loc and ("Location" in df):
        df = df[df.Location.str.contains(loc, regex=False, na=False, case=False)]

    df = df.fillna('N/A')
    return df.to_dict(orient='index')


def search_case_id(case_id):
    r1 = requests.get(db[1], params={'orderBy': '"CaseID"', 'equalTo': f'"{case_id}"'})
    return r1.json()


def search_event(event):
    r0, r1 = ez_download({'orderBy': '"$key"', 'equalTo': f'"{event}"'})
    event_match = r0.json()
    event_match.update(r1.json())
    return event_match


def number_entries():
    db1 = len(requests.get(db[0]).json())
    db2 = len(requests.get(db[1]).json())
    return db1 + db2


def last_entry_date_time():
    db1last = requests.get(f'{db[0]}?orderBy="Date_Reported"')
    db1last = list(json.loads(db1last.text).values())[-1]['Date_Reported']
    db2last = requests.get(f'{db[1]}?orderBy="Date_Reported"')
    db2last = list(json.loads(db2last.text).values())[-1]['Date_Reported']
    if db1last > db2last:
        final_entry_time = db1last
    else:
        final_entry_time = db2last
    return final_entry_time


def delete_case(event):
    requests.delete(f'https://fir-tutorial-dbda2-default-rtdb.firebaseio.com/crimes/{event}.json')
    requests.delete(f'https://trojan-force-default-rtdb.firebaseio.com/crimes/{event}.json')
    return f'{event} deleted'


def update_event(event, caseid=None, dt_from=None, dt_to=None, disp=None, fi_cat=None, fi_des=None, ii_cat=None,
                 ii_des=None, loc=None, loc_type=None, off_cat=None, off_des=None):

    data = {'Disposition': disp, 'Final_Incident_Category': fi_cat, 'Final_Incident_Description': fi_des,
            'Initial_Incident_Category': ii_cat, 'Initial_Incident_Description': ii_des,
            'Location': loc, 'Location_Type': loc_type, 'Offense_Category': off_cat, 'Offense_Description': off_des}
    if caseid:
        url = database_urls[1]
    else:
        url = database_urls[0]

    time = pd.Timestamp.now(tz='US/Pacific')
    data['Date_Reported'] = time.strftime('%Y-%m-%d %H:%M')

    if dt_from:
        dt_from = pd.Timestamp(dt_from)  # this lets it work on hmtl input
        data['Date_From'] = dt_from.strftime('%Y-%m-%d %H:%M')
    if dt_to:
        dt_to = pd.Timestamp(dt_to)    # this lets it work on hmtl input
        data['Date_To'] = dt_to.strftime('%Y-%m-%d %H:%M')
    data = {k: v for k, v in data.items() if v}   # filter out Nones and empty strings
    print(data)
    url = url + f'crimes/{event}/.json'   # event cannot be in data dictionary for a PATCH update
    print(url)
    r = requests.patch(url, json=data)  # PATCH is for updates
    return r.status_code
# works on CLI


# update_event('23-12-06-348477', '5555555', None, None, 'CLOSED')
'''
OLD FUNCTIONS

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
'''