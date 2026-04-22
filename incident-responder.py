import sqlite3
import time
from datetime import datetime
import requests

api_dict = {
    "GitHub": {
        "url": "https://api.github.com",
        "expected_status": [200],
        "timeout": 3,
        "check_interval": 5,
        "alert_threshold": 3,
        "headers": {"Accept": "application/json"},
        "retry_count": 2
    },
    "httpBin": {
        "url": "https://httpbin.org/get",
        "expected_status": [200],
        "timeout": 3,
        "check_interval": 5,
        "alert_threshold": 3,
        "headers": {"Accept": "application/json"},
        "retry_count": 2
    },
    "CatFacts": {
        "url": "https://catfact.ninja/fact",
        "expected_status": [200],
        "timeout": 3,
        "check_interval": 5,
        "alert_threshold": 3,
        "headers": {"Accept": "application/json"},
        "retry_count": 2
    },
    "ipAddress": {
        "url": "https://api.ipify.org",
        "expected_status": [200],
        "timeout": 3,
        "check_interval": 5,
        "alert_threshold": 3,
        "headers": {"Accept": "application/json"},
        "retry_count": 2
    },
    "DetroitTime": {
        "url": "https://worldtimeapi.org/api/timezone/America/Detroit",
        "expected_status": [200],
        "timeout": 3,
        "check_interval": 5,
        "alert_threshold": 3,
        "headers": {"Accept": "application/json"},
        "retry_count": 2
    }
    
}

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
def check_for_incident(service_name, expected_status, threshold=3):
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
        if status is not None and status in expected_status:
            return False

    return True

success_count = 0

#loops the check
for service_name, config in api_dict.items():
    url = config["url"]
    timeout = config["timeout"]
    expected_status = config["expected_status"]
    retry_count = config["retry_count"]
    headers = config["headers"]
 
    response = None
    last_error = None
 
    for attempt in range(retry_count):
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            break  # success — stop retrying
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"Attempt {attempt + 1} failed for {service_name}: {e}")
 
    if response is not None:
        response_time = response.elapsed.total_seconds()
 
        print(f"[{service_name}] Status: {response.status_code} | Response time: {response_time:.3f}s")
 
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

        if response.status_code in expected_status:
            success_count += 1

        print(f"[{service_name}] Saved to database.")

    else:
        print(f"[{service_name}] All {retry_count} attempts failed.")
        print(f"[{service_name}] Last error: {last_error}")

        cursor.execute(
            "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                service_name,
                url,
                None,
                None,
                str(last_error)
            )
        )
        print(f"[{service_name}] Failure saved to database.")

    if check_for_incident(service_name, expected_status, threshold=config["alert_threshold"]):
        incident_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        incident_details = f"{service_name} failed {config['alert_threshold']} checks in a row."

        print(f"INCIDENT DETECTED: {incident_details}")

        cursor.execute(
            "INSERT INTO incidents VALUES (?, ?, ?, ?)",
            (
                incident_time,
                service_name,
                "Consecutive Failures",
                incident_details
            )
        )
    time.sleep(config["check_interval"])

con.commit()
con.close()
 
print(f"\nSuccessful checks: {success_count} / {len(api_dict)}")
