# 551-database-project
551 semester project

project file will render with Flask
database will host database interaction commands and datacleaning
html pages to be rendered by project.py

Needs: Partial Match????? (maybe not), 
Concerns: 


13FEB24- search by CaseID and Event# are working on the page. Need to fix function for search_by_location. 
14FEB24- Location working
17FEB24- UPLOAD, PDF_UPLOAD, and ALL SEARCH functions working (****very nice***), report_crime swapped report_case: deleted manual event# input and adjusted other parameters to ensure funcitonality- converts to pd.Timestap as function runs.
22FEB24- UPDATE and DELETE functions working, html now has separate boxes for each function.

Current considerations:
  -consider a .lower() on query results so that "CLOSED" and "closed" both have same results
  -explore options for date window entry field pop up thing
  -report a case is running on PATCH function vs PUT. we could use the base_url and include the event as part of the PUT call, so the entire db will not be overwritten. It works fine as is, but we could lose         points for using the wrong function to 'create' something, though functionally there is no difference.
  
