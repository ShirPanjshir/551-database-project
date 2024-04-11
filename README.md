# 551-database-project
551 semester project
http://3.216.130.143

project file will render with Flask
database will host database interaction commands and datacleaning
html pages to be rendered by project.py

Needs: Partial Match????? (maybe not), 
Concerns: 


13FEB24- search by CaseID and Event# are working on the page. Need to fix function for search_by_location. 
14FEB24- Location working
17FEB24- UPLOAD, PDF_UPLOAD, and ALL SEARCH functions working (****very nice***), report_crime swapped report_case: deleted manual event# input and adjusted other parameters to ensure funcitonality- converts to pd.Timestap as function runs.
22FEB24- UPDATE and DELETE functions working, html now has separate boxes for each function.

10APR24 update log:
  overall
    - removed ugly underscores
    - reordered fields
  search by case number
    - emtpy field error message
    - wrong format error message
  search by event number
    - emtpy field error message
    - wrong format error message
  advanced search
    - emtpy field error message if all == ''
    - change date format from yy-mm-dd to YYYY-MM-DD (same as the admin page)  
    - wrong date format error message
    - check date inconsistency (start > end)
  report
    - emtpy field error message (at least one field)
    - wrong date format error message
    - check date inconsistency (start > end)
  update
    - emtpy field error message (at least one field)
    - wrong date format error message
    - check date inconsistency (start > end)
    - checks if caseID has been used
    - caseID format error message (if caseID)
  delete
    - emtpy field error message
    - wrong format error message
    - not found error message (shown on the same page. only show the red page if successful)
    

Current considerations:
  -consider a .lower() on query results so that "CLOSED" and "closed" both have same results
  -explore options for date window entry field pop up thing
  -report a case is running on PATCH function vs PUT. we could use the base_url and include the event as part of the PUT call, so the entire db will not be overwritten. It works fine as is, but we could lose         points for using the wrong function to 'create' something, though functionally there is no difference.
  

update crime workflow:   this would be nice but its complicated, would have to use the search function and all that. probably a bit much for this project. PASS
enter event id -> if event id == valid -> show original data side by side -> show a new block that says something like "enter text into columns you want to update" -> print the entire updated case with the confirmation message !!!CASEID cannot be modified!!!

MIDPOINT FEEDBACK: Regarding distributed storing: Use some hash function to distribute the data. Categorizing is not a good option.
Reason: What if dataset grows enormously huge. Using only 2 table is not a good option in your scenario.
Hash function based on time entered implemented and works a/o 11MAR24
