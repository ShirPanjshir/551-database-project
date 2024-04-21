import tabula
import warnings
import pandas as pd
import numpy as np
import requests
import re

warnings.simplefilter(action='ignore', category=FutureWarning)

DB_URLS = ("https://fir-tutorial-dbda2-default-rtdb.firebaseio.com/",
           "https://trojan-force-default-rtdb.firebaseio.com/")

TIME_FORMAT = '%Y-%m-%d %H:%M'
DATE_FORMAT = "%Y-%m-%d"
ERROR_CODE = 7700
SUCCESS = 200


def hash_func(event):
    """Uses the report's EventID, which will vary depending on the time submitted (down to seconds). Users have a 50%
    chance of submitting on an even or odd numbered second. Rapid submissions will cross multiple seconds and also be
    evenly hashed"""
    return int(event[-1]) % 2


def batch_process_pdf(pdf_path):
    """This function uses the USC Crime Report PDF as an input and will input the reports into the database
     as a batch"""
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

    for i in ['Offense', 'Initial Incident', 'Final Incident']:
        df[(i.replace(' ', '_')+'_Category')] = df[i].str.split(' -', n=1).str[0]
        df[(i.replace(' ', '_')+'_Description')] = df[i].str.split(' -', n=1).str[1]
    for i in ['Offense_Description', 'Initial_Incident_Description', 'Final_Incident_Description']:
        df[i] = df[i].str.strip()
        df[i] = df[i].str.replace(r"([^ ])(- )", r"\1 - ", regex=True)
        df[i] = df[i].str.replace("Skateboar d", "Skateboard")

    df['Location_Type'] = df.Location.str.split(' - ', n=1).str[1]
    df.Location = df.Location.str.split(' - ', n=1).str[0]
    df.Location = df.Location.str.strip()
    df.Location_Type = df.Location_Type.str.replace(r"([^ ])(- )", r"\1-", regex=True)

    cols = list(df.columns)
    df = df[cols[0:3] + cols[10:16] + cols[6:9] + cols[16:] + cols[9:10]]
    df = df.rename(columns={"Date Reported": "Date_Reported", "Date From": "Date_From", "Date To": "Date_To"})
    df = df.rename(columns={"Case #": "CaseID", "Event #": "EventID"})

    for i in ['Date_Reported', 'Date_From', 'Date_To']:
        df[i] = df[i].str.replace(r" - [A-Z]{3} at ", " ", regex=True)
        df[i] = df[i].str.replace(r"\..*", "", regex=True)
        df[i] = pd.to_datetime(df[i], format="%m/%d/%y %H:%M")
        df[i] = df[i].dt.strftime(TIME_FORMAT)

    df.CaseID = df.CaseID.replace(r"[^0-9\.]*", np.nan, regex=True)
    df.CaseID = df.CaseID.astype(str).str.replace(r"\.[0-9]+", "", regex=True)
    df = df.replace(r"[ ]{2,}", " ", regex=True)
    df = df.replace('nan', np.nan)
    df = df.set_index('EventID').to_dict(orient='index')

    for k, v in df.items():
        url = DB_URLS[hash_func(k)]
        data = {i: j for i, j in v.items() if j == j}
        r = requests.put(f"{url}crimes/{k}.json", json=data)

    if r.status_code != 200:
        return f"Upload error. Status code {r.status_code}"
    elif error:
        return f"Upload Complete. Failed to process page {error}. Please enter manually."
    else:
        return "Upload Complete."


def report_case(caseid=False, start_dt=None, end_dt=None, off_cat=None, off_des=None, disp=None,
                ii_cat=None, ii_des=None, fi_cat=None, fi_des=None, loc_type=None, loc=None):
    """ This is the main CREATE function allowing the user to fill fields present in the standard report format
    dt_from and df_to must be pd.Timestamps!!!
    """
    data = {'Disposition': disp, 'Final_Incident_Category': fi_cat, 'Final_Incident_Description': fi_des,
            'Initial_Incident_Category': ii_cat, 'Initial_Incident_Description': ii_des,
            'Location': loc, 'Location_Type': loc_type, 'Offense_Category': off_cat, 'Offense_Description': off_des}

    # moving timestamp process up first to generate eventID that is fed to hashfunction
    time = pd.Timestamp.now(tz='US/Pacific')
    data['Date_Reported'] = time.strftime(TIME_FORMAT)
    sec = time.hour * 3600 + time.minute * 60 + time.second
    eventID = f"{time.strftime('%y-%m-%d')}-{sec:06}"

    url = DB_URLS[hash_func(eventID)]

    if caseid == "yes":   # caseid, if selected, can put into either db now
        result, status = ez_download({'orderBy': '"CaseID"', 'limitToLast': '1'})
        if status != 200:
            return result, status
        latest = max([int(v['CaseID']) for v in result.values()])
        data['CaseID'] = str(latest + 1)

    if start_dt:
        try:
            start_dt = pd.to_datetime(start_dt, format=TIME_FORMAT)
            data['Date_From'] = start_dt.strftime(TIME_FORMAT)
        except ValueError:
            return "DTERROR", ERROR_CODE
    if end_dt:
        try:
            end_dt = pd.to_datetime(end_dt, format=TIME_FORMAT)
            data['Date_To'] = end_dt.strftime(TIME_FORMAT)
        except ValueError:
            return "DTERROR", ERROR_CODE
    if start_dt and end_dt:
        if end_dt < start_dt:
            return "DTCONFLICT", ERROR_CODE
    data = {k: v for k, v in data.items() if v}
    case = {eventID: data}
    try:
        r = requests.patch(f"{url}crimes.json", json=case)
        if r.status_code == 200:
            return eventID, SUCCESS
    except requests.exceptions.RequestException:
        pass
    return "CONNECTIONERROR", ERROR_CODE


def ez_download(p=None):
    """Quick download function to save space"""
    try:
        r0 = requests.get(f"{DB_URLS[0]}crimes.json", params=p)
        r1 = requests.get(f"{DB_URLS[1]}crimes.json", params=p)
        if r0.status_code == 200 and r1.status_code == 200:
            data = r0.json()
            data.update(r1.json())
            return data, SUCCESS
    except requests.exceptions.RequestException:
        pass
    return "CONNECTIONERROR", ERROR_CODE


def search(start_dt=None, end_dt=None, date_rep=None, off_cat=None, off_des=None, ii_cat=None,
           ii_des=None, fi_cat=None, fi_des=None, loc_type=None, loc=None, disp=None):
    """Main function used to READ database inventory. Can do partial match and
    search upon any parameter in the report"""
    #  test for empty input done on project.py
    if start_dt:
        try:
            start_dt = pd.to_datetime(start_dt, format=DATE_FORMAT)
            start_dt = start_dt.strftime(DATE_FORMAT)
        except ValueError:
            return "DTERROR", ERROR_CODE
    if end_dt:
        try:
            end_dt = pd.to_datetime(end_dt, format=DATE_FORMAT)
            end_dt = end_dt + pd.Timedelta(days=1)
            end_dt = end_dt.strftime(DATE_FORMAT)
        except ValueError:
            return "DTERROR", ERROR_CODE
    if date_rep:
        try:
            date_rep = pd.to_datetime(date_rep, format=DATE_FORMAT)
            next = date_rep + pd.Timedelta(days=1)
            date_rep = date_rep.strftime(DATE_FORMAT)
            next = next.strftime(DATE_FORMAT)
        except ValueError:
            return "DTERROR", ERROR_CODE
    if start_dt and end_dt:
        if start_dt >= end_dt:
            return "DTCONFLICT", ERROR_CODE
    # Pick one filter and download data
    map1 = {'Disposition': disp, 'Final_Incident_Category': fi_cat,
            'Initial_Incident_Category': ii_cat, 'Location_Type': loc_type, 'Offense_Category': off_cat}
    map2 = {'Final_Incident_Description': fi_des, 'Initial_Incident_Description': ii_des,
            'Location': loc, 'Offense_Category': off_cat, 'Offense_Description': off_des}
    map1 = {k: v for k, v in map1.items() if v}
    map2 = {k: v for k, v in map2.items() if v}
    if date_rep:
        result, status = ez_download({'orderBy': '"Date_Reported"', 'startAt': f'"{date_rep}"', 'endAt': f'"{next}"'})
    elif start_dt:
        result, status = ez_download({'orderBy': '"Date_From"', 'startAt': f'"{start_dt}"'})
    elif end_dt:
        result, status = ez_download({'orderBy': '"Date_To"', 'endAt': f'"{end_dt}"'})
    elif map1:
        for k, v in map1.items():
            result, status = ez_download({'orderBy': f'"{k}"', 'equalTo': f'"{v}"'})
            break
    else:
        result, status = ez_download()

    if status != 200:
        return result, status

    df = pd.DataFrame.from_dict(result, orient='index').sort_index()

    if start_dt and ("Date_From" in df):
        df = df[df.Date_From >= start_dt]
    if end_dt and ("Date_To" in df):
        df = df[df.Date_To <= end_dt]
    # Categorical filters
    for k, v in map1.items():
        if k in df:
            df = df[df[k] == v]

    # case insentitive partial match
    for k, v in map2.items():
        if k in df:
            df = df[df[k].str.contains(v, regex=False, na=False, case=False)]

    df = df.fillna('N/A')
    return df.to_dict(orient='index'), SUCCESS


def search_case_id(caseid):
    """Simple search function accepting only CaseID as input"""
    if not caseid:
        return 'CASEID_NULL', ERROR_CODE
    if re.match("^[0-9]{7}$", caseid):
        return ez_download({'orderBy': '"CaseID"', 'equalTo': f'"{caseid}"'})
    else:
        return 'IDERROR', ERROR_CODE


def search_event(event):
    """Simple search function accepting only Event Number as input"""
    if not event:
        return 'EVENT_NULL', ERROR_CODE
    if re.match("^[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{6}$", event):
        url = DB_URLS[hash_func(event)]
        try:
            r = requests.get(f"{url}crimes.json", params={'orderBy': '"$key"', 'equalTo': f'"{event}"'})
            if r.status_code == 200:
                return r.json(), SUCCESS
        except requests.exceptions.RequestException:
            pass
        return "CONNECTIONERROR", ERROR_CODE
    else:
        return 'EVENT', ERROR_CODE


def delete_case(event):
    """Main function to DELETE content from the database"""
    result, status = search_event(event)
    if status != 200:
        return result, status
    url = DB_URLS[hash_func(event)]
    if not result:
        return "NOMATCH", ERROR_CODE
    try:
        r = requests.delete(f'{url}crimes/{event}.json')
        if r.status_code == 200:
            return "SUCCESS", SUCCESS
    except requests.exceptions.RequestException:
        pass
    return "CONNECTIONERROR", ERROR_CODE


def update_event(event, caseid=None, start_dt=None, end_dt=None, disp=None, fi_cat=None, fi_des=None, ii_cat=None,
                 ii_des=None, loc=None, loc_type=None, off_cat=None, off_des=None):
    """Main function to UPDATE content"""
    data = {'CaseID': caseid, 'Disposition': disp, 'Location': loc, 'Location_Type': loc_type,
            'Final_Incident_Category': fi_cat, 'Final_Incident_Description': fi_des,
            'Initial_Incident_Category': ii_cat, 'Initial_Incident_Description': ii_des,
            'Offense_Category': off_cat, 'Offense_Description': off_des}
    data = {k: v for k, v in data.items() if v}   # filter out Nones and empty strings

    result, status = search_event(event)
    if status != 200:
        return result, status
    if not result:
        return "NOMATCH", ERROR_CODE
    result = list(result.values())[0]
    old_from = result.get('Date_From', '')
    old_to = result.get('Date_To', '')

    if caseid:
        result, status = search_case_id(caseid)
        if status != 200:
            return result, ERROR_CODE
        if result:
            return "IDCONFLICT", ERROR_CODE

    time = pd.Timestamp.now(tz='US/Pacific')
    data['Date_Reported'] = time.strftime(TIME_FORMAT)

    if start_dt:
        try:
            start_dt = pd.to_datetime(start_dt, format=TIME_FORMAT)  # this lets it work on hmtl input
            data['Date_From'] = start_dt.strftime(TIME_FORMAT)
        except ValueError:
            return "DTERROR", ERROR_CODE
    elif old_from:
        start_dt = pd.to_datetime(old_from, format=TIME_FORMAT)

    if end_dt:
        try:
            end_dt = pd.to_datetime(end_dt, format=TIME_FORMAT)     # this lets it work on hmtl input
            data['Date_To'] = end_dt.strftime(TIME_FORMAT)
        except ValueError:
            return "DTERROR", ERROR_CODE
    elif old_to:
        end_dt = pd.to_datetime(old_to, format=TIME_FORMAT)

    if start_dt and end_dt:
        if end_dt < start_dt:
            return "DTCONFLICT", ERROR_CODE
    url = DB_URLS[hash_func(event)]
    try:
        r = requests.patch(f'{url}crimes/{event}/.json', json=data)
        if r.status_code == 200:
            return "SUCCESS", SUCCESS
    except requests.exceptions.RequestException:
        pass
    return "CONNECTIONERROR", ERROR_CODE


def delete_all():
    user_input = input('Provide authorization code: ')
    if user_input == '8675309':
        for i in range(len(DB_URLS)):
            try:
                r = requests.delete(f'{DB_URLS[i]}.json')
                if r.status_code != 200:
                    return 'Connection issue.'
            except requests.exceptions.RequestException:
                return 'Connection issue.'
        return 'Databases deleted!'
    else:
        print("Code not accepted.")
