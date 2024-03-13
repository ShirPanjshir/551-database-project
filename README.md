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
  
Dan's wishlist:
Search By Case Number: show something like "case not found" if caseID not found DONE (this is default return)
Add a "Search By Event ID" section. Proposed layoout: Search By Case Number, Search By Event ID, and Advanced Search (without evenID row) DONE
Advanced Search: move Date_Reported above Date_From (it's more logical) DONE
search crime: add drop down menus for categorical variables DONE
ADD drop down menus for Location_Type DONE
!!!! FOR ALL DROP DOWN MENUS: add a default BLANK category that returns NONE or "" !!!!! DONE, blank '' option is at top, results in  N/A value on returns DONE
report crime: show assigned event id in the confirmation page DONE
update crime: find a way to separate Event from other text boxes DONE

update crime workflow:   this would be nice but its complicated, would have to use the search function and all that. probably a bit much for this project. PASS
enter event id -> if event id == valid -> show original data side by side -> show a new block that says something like "enter text into columns you want to update" -> print the entire updated case with the confirmation message !!!CASEID cannot be modified!!!

MIDPOINT FEEDBACK: Regarding distributed storing: Use some hash function to distribute the data. Categorizing is not a good option.
Reason: What if dataset grows enormously huge. Using only 2 table is not a good option in your scenario.
Hash function based on time entered implemented and works a/o 11MAR24
