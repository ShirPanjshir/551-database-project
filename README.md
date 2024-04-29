# 551-database-project
USC DSCI 551 Semester Project
The BDK Distributed Database for USC Public Safety
*hosted at the link below*
http://3.216.130.143

Or Clone Repository and run **project.py**
>database.py contains functions to support project.py
>templates directory contains html files
>static directory contains images

This database was built with Python Flask, HTML, and Google Firebase.
    
Web interface users are able to query the database via simple or advanced search methods and download their results into a CSV/Excel allowing for subsequent crime analysis.
Simple: Retrieve a specific entry aia unique case ID number or unique event number.
Advanced: Via any other feature (12 further available) pertaining to reports, such as: location or disposition.
Advanced queries are able to be sorted by feature and subsequent filtering via a search bar to fine-tune requests.
Drop-down menus are available in several fields to allow faster and more efficient searching.

Authorized users (password protected) are also able to create, update+(upsert), and delete individual records. 
All alterations to the database return the event number to be copied and searched for rapid confirmation of adjustments.

Database Administrator has ability to bulk upload PDF-type reports to the databases, as well as an option to delete all entries, both via the CLI*.
    *Requires tabula-py, JPype1, and Java to be installed.

Hashing into the databases is conducted upon time-derived, event number to ensure unique entries.
User-assigned Case numbers are simple increment, based on the most recently used case number, preventing duplicate entries.

Error handling is specific to each action, informing user of specific alteration required to fix improper queries or adjustments, e.g. "Use proper YYYY-MM-DD HH:MM format for query".
Strict input formatting ensures data integrity, resulting in clean and uniform downloads that facilate advanced analytics immediately after download.

For questions and comments, please contact Kyle W. Parker at kwparker@usc.edu
FIGHT ON!
