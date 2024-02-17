# 551-database-project
551 semester project

project file will render with Flask
database will host database interaction commands and datacleaning
html pages to be rendered by project.py

Needs: Partial Match????? (maybe not), multiple field search (combine and step filter), 
Concerns: Special characters


13FEB24- search by CaseID and Event# are working on the page. Need to fix function for search_by_location. 
14FEB24- Location working
17FEB24- UPLOAD, PDF_UPLOAD, and ALL SEARCH functions working (****very nice***) 
Current considerations:
  -consider a .lower() on query results so that "CLOSED" and "closed" both have same results
  -consider drop down list for categories/dispositions? might be long- a separate page with a read out might be easier to read and could be dynamic/automated (like an index page)
  -explore options for date window entry field pop up thing
  -drop down selections for categories/dispositions? categories makes sense, dispositions seems less categorical
  -UPDATE feature    (patch vs post vs put... current report crime has PUT and batch report has PATCH....)
  -DELETE feature.... should be an easy swap... rather than return matches, just delete them.
  -report_crime swap to report_case, delete manual event# input and adjust other parameters to ensure funcitonality
