import sqlite3
import matplotlib.pyplot as plt

con = sqlite3.connect("log.db")
cursor = con.cursor()

cursor.execute("SELECT DISTINCT service_name FROM results")
services = [row[0] for row in cursor.fetchall()]

uptimes = []
labels = []

for service in services:
    cursor.execute("SELECT COUNT(*) FROM results WHERE service_name = ?", (service,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM results WHERE service_name = ? AND status = 200", (service,))
    successes = cursor.fetchone()[0]

    uptime_pct = (successes / total) * 100 if total > 0 else 0
    uptimes.append(uptime_pct)

    cursor.execute(
        "SELECT COUNT(*) FROM incidents WHERE service_name = ?",
        (service,)
    )
    incident_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT status
        FROM results
        WHERE service_name = ?
        ORDER BY date DESC
        LIMIT 1
    """, (service,))

    latest_status = cursor.fetchone()

    if latest_status and latest_status[0] is not None:
        current_state = "UP"
    else:
        current_state = "DOWN"

    labels.append(f"{service}\n{current_state}\nIncidents: {incident_count}")

con.close()

plt.plot(labels, uptimes, marker='o', linestyle='-', color='blue')
plt.title("Service Monitoring Dashboard")
plt.ylabel("Uptime (%)")
plt.ylim(0, 110)
plt.grid(True)
plt.show()