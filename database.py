import tabula
import warnings
import pandas as pd
import numpy as np
import requests

warnings.simplefilter(action='ignore', category=FutureWarning)

database_urls = ("https://fir-tutorial-dbda2-default-rtdb.firebaseio.com/",
                 "https://trojan-force-default-rtdb.firebaseio.com/")


def hash_func(event):
    """Uses the report's EventID, which will vary depending on the time submitted (down to seconds). Users have a 50%
    chance of submitting on an even or odd numbered second. Rapid submissions will cross multiple seconds and also be
    evenly hashed"""
    event_hash = event[-1]
    return int(event_hash) % 2


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
    df = df.set_index('EventID').to_dict(orient='index')

    for k, v in df.items():
        url = database_urls[hash_func(k)]
        data = {i: j for i, j in v.items() if j == j}
        r = requests.put(f"{url}crimes/{k}.json", json=data)

    if r.status_code != 200:
        return f"Upload error. Status code {r.status_code}"
    elif error:
        return f"Upload Complete. Failed to process page {error}. Please enter manually."
    else:
        return "Upload Complete."


def report_case(caseid=False, dt_from=None, dt_to=None, off_cat=None, off_des=None, disp=None,
                ii_cat=None, ii_des=None, fi_cat=None, fi_des=None, loc_type=None, loc=None):
    """ This is the main CREATE function allowing the user to fill fields present in the standard report format
    dt_from and df_to must be pd.Timestamps!!!
    """
    data = {'Disposition': disp, 'Final_Incident_Category': fi_cat, 'Final_Incident_Description': fi_des,
            'Initial_Incident_Category': ii_cat, 'Initial_Incident_Description': ii_des,
            'Location': loc, 'Location_Type': loc_type, 'Offense_Category': off_cat, 'Offense_Description': off_des}

    # moving timestamp process up first to generate eventID that is fed to hashfunction
    time = pd.Timestamp.now(tz='US/Pacific')
    data['Date_Reported'] = time.strftime('%Y-%m-%d %H:%M')
    sec = time.hour * 3600 + time.minute * 60 + time.second
    eventID = f"{time.strftime('%y-%m-%d')}-{sec:06}"

    url = database_urls[hash_func(eventID)]

    if caseid == "yes":   # caseid, if selected, can put into either db now
        r0, r1 = ez_download({'orderBy': '"CaseID"', 'limitToLast': '1'})
        r0_latest = int(list(r0.json().values())[0]["CaseID"])
        r1_latest = int(list(r1.json().values())[0]["CaseID"])
        data['CaseID'] = str(max(r0_latest, r1_latest) + 1)

    if dt_from:
        dt_from = pd.to_datetime(dt_from, format='%Y-%m-%d %H:%M')
        data['Date_From'] = dt_from.strftime('%Y-%m-%d %H:%M')
    if dt_to:
        dt_to = pd.to_datetime(dt_to, format='%Y-%m-%d %H:%M')
        data['Date_To'] = dt_to.strftime('%Y-%m-%d %H:%M')
    data = {k: v for k, v in data.items() if v}
    case = {eventID: data}
    r = requests.patch(f"{url}crimes.json", json=case)
    return eventID, r.status_code


def ez_download(p=None):
    """Quick download function to save space"""
    r0 = requests.get(f"{database_urls[0]}crimes.json", params=p)
    r1 = requests.get(f"{database_urls[1]}crimes.json", params=p)
    return r0, r1


def search(start_dt=None, end_dt=None, date_rep=None, off_cat=None, off_des=None, ii_cat=None,
           ii_des=None, fi_cat=None, fi_des=None, loc_type=None, loc=None, disp=None):
    """Main function used to READ database inventory. Can do partial match and
    search upon any parameter in the report"""
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
        r0, r1 = ez_download()

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
    """Simple search function accepting only CaseID as input"""
    r0, r1 = ez_download({'orderBy': '"CaseID"', 'equalTo': f'"{case_id}"'})
    result = r0.json()
    result.update(r1.json())
    return result


def search_event(event):
    """Simple search function accepting only Event Number as input"""
    url = database_urls[hash_func(event)]
    event_match = requests.get(f"{url}crimes.json", params={'orderBy': '"$key"', 'equalTo': f'"{event}"'})
    return event_match.json()


def delete_case(event):
    """Main function to DELETE content from the database"""
    url = database_urls[hash_func(event)]
    requests.delete(f'{url}crimes/{event}.json')
    return f'{event} deleted'


def update_event(event, caseid=None, dt_from=None, dt_to=None, disp=None, fi_cat=None, fi_des=None, ii_cat=None,
                 ii_des=None, loc=None, loc_type=None, off_cat=None, off_des=None):
    """Main function to UPDATE content"""
    data = {'CaseID': caseid, 'Disposition': disp,
            'Final_Incident_Category': fi_cat, 'Final_Incident_Description': fi_des,
            'Initial_Incident_Category': ii_cat, 'Initial_Incident_Description': ii_des,
            'Offense_Category': off_cat, 'Offense_Description': off_des,
            'Location': loc, 'Location_Type': loc_type}
    # updated to find via hash

    url = database_urls[hash_func(event)]

    time = pd.Timestamp.now(tz='US/Pacific')
    data['Date_Reported'] = time.strftime('%Y-%m-%d %H:%M')

    if dt_from:
        dt_from = pd.Timestamp(dt_from)  # this lets it work on hmtl input
        data['Date_From'] = dt_from.strftime('%Y-%m-%d %H:%M')
    if dt_to:
        dt_to = pd.Timestamp(dt_to)    # this lets it work on hmtl input
        data['Date_To'] = dt_to.strftime('%Y-%m-%d %H:%M')

    data = {k: v for k, v in data.items() if v}   # filter out Nones and empty strings
    url = url + f'crimes/{event}/.json'   # event cannot be in data dictionary for a PATCH update
    r = requests.patch(url, json=data)  # PATCH is for updates
    return r.status_code
