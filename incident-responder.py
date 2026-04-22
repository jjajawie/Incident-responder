import sqlite3
import time
from datetime import datetime
import requests

urls = [
    ("GitHub", "https://api.github.com"), #pairs, (service_name, url)
    #can add more urls later
]

con = sqlite3.connect("log.db")
cursor = con.cursor()

#create table and error column
cursor.execute("""CREATE TABLE IF NOT EXISTS results 
(date TEXT,
    service_name TEXT,
    url TEXT,
    status INTEGER,
    response_time REAL,
    error TEXT)""")

#create incident table
cursor.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    date TEXT,
    service_name TEXT,
    incident_type TEXT,
    details TEXT
)
""")
#checks for incidents and logs them
def check_for_incident(service_name, threshold=3):
    cursor.execute("""
        SELECT status
        FROM results
        WHERE service_name = ?
        ORDER BY date DESC
        LIMIT ?
    """, (service_name, threshold))

    recent_checks = cursor.fetchall()

    if len(recent_checks) < threshold:
        return False

    for (status,) in recent_checks:
        if status is not None and 200 <= status < 300:
            return False

    return True

success_count = 0

#loops the check
for service_name, url in urls:
    try:
        # We added timeout=3 so it gives up after 3 seconds
        response = requests.get(url, timeout=3)
        response_time = response.elapsed.total_seconds()


        print("Status Code:", response.status_code)
        print("Response Time (seconds):", response.elapsed.total_seconds())
            
            
            #saves successful request data into database
        cursor.execute(
            "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                service_name,
                url,
                response.status_code,
                response_time,
                None
            )
        )

        success_count += 1
        print("saved to database")

    except requests.exceptions.RequestException as e:
        # If the network fails or times out, it runs this instead of crashing
        print("Alert: The network crashed or timed out")
        print("Error Details:", e)

        #saves failed request data and error msg into database
        cursor.execute(
            "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                service_name,
                url,
                None,
                None,
                str(e)
            )
        )
        print("failure saved to database.")

    if check_for_incident(service_name, threshold=3):
        incident_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        incident_details = f"{service_name} failed 3 checks in a row."

        print("INCIDENT DETECTED:", incident_details)

        cursor.execute(
            "INSERT INTO incidents VALUES (?, ?, ?, ?)",
            (
                incident_time,
                service_name,
                "Consecutive Failures",
                incident_details
            )
        )
    
    time.sleep(5)

   

con.commit()
con.close()

print("Successful checks:", success_count, "/", len(urls))