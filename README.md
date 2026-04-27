# Incident Responder

A Python-based monitoring tool that pings web services and logs their uptime and response times to an SQLite database. Includes visualization tools to track reliability over time.

## Team Members
* Amadou
* Joseph Jajawie
* Youssef Kamal


## Joseph Jajawie:
* Commit 1 - initialized the project and implemented the SQL Database, including but not limited to creating tables and attributes of each table for each ping to be stored. About 5 hours
* Commit 10 - Transformed the storing of APIs in the code from simple strings of URL to Dictionaries that stored general information of APIs. Additionally updated the visualization to a heatmap to demonstrate uptime over several days. About 9-10 hours
* Team Eval - Amadou and Youssef are both great teammates. Both of them were very clear in communication and timely with contribution to the project.


## Amadou Ba:
* April 16: Built the core API pinger engine with the `requests` library and built-in timeout error handling. 4 hours
* April 21 Developed `visualize.py` using the `matplotlib` library to pull SQLite data and generate graphical uptime line charts. 6 ish hours 
* April 21:Initialized the project README structure and documentation. 30 min at most 
* Team eval - Joeseph and Youssef were great projects partners, they communicated clearly and did their fair share, they also helped me out on some of my parts too.

## Youssef Kamal:
* April 17: added sqlite logging and error handling- 2 hr
* April 19: added sqlite logging and service_name column - 1 hr
* April 22: added incident detection and logging- 3 hr
* April 22: added currents status and incident count- 2 hr
* April 25 added continous monitoring with adjustable timing, added demo_api for live testing and incident simulation - 3 hr
* April 25: Improved gui to supporr multiple types, added start stop buttons for monitoring, added check interval input, added uptime graph to show uptime over time, added demo_api buttons, added live log - 6hr
* April 27: added individual api graphs, ptime summary and incident viewer to gui - 3 hr
* April 27: added comments- 15 min
Team eval: Amadou and Joseph were good groupmates, they submitted work on time and did their fair share. Communication could be a little better, although to be fair I was also not communicating as well as I should have either.
