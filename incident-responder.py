import sqlite3
import time
from datetime import datetime
import requests

test_url = "https://api.github.com"

con = sqlite3.connect("ping_log.db")
cursor = conn.cursor()

#create table and error column
cursor.execute("""CREATE TABLE IF NOT EXISTS results 
(date TEXT,
    url TEXT,
    status INTEGER,
    response_time REAL,
    error TEXT)""")

success_count = 0

try:
    # We added timeout=3 so it gives up after 3 seconds
    response = requests.get(test_url, timeout=3)
    response_time = response.elapsed.total_seconds()


    print("Status Code:", response.status_code)
    print("Response Time (seconds):", response.elapsed.total_seconds())
        
        
        #saves successful request data into database
        cursor.execute(
        "INSERT INTO results VALUES (?, ?, ?, ?, ?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            test_url,
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
        "INSERT INTO results VALUES (?, ?, ?, ?, ?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            test_url,
            None,
            None,
            str(e)
        )
    )

    print("failure saved to database.")

con.commit()
con.close()