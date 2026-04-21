import sqlite3
import matplotlib.pyplot as plt

con = sqlite3.connect("log.db")
cursor = con.cursor()

cursor.execute("SELECT DISTINCT service_name FROM results")
services = [row[0] for row in cursor.fetchall()]

uptimes = []

for service in services:
    cursor.execute("SELECT COUNT(*) FROM results WHERE service_name = ?", (service,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM results WHERE service_name = ? AND status = 200", (service,))
    successes = cursor.fetchone()[0]

    uptime_pct = (successes / total) * 100 if total > 0 else 0
    uptimes.append(uptime_pct)

con.close()

plt.plot(services, uptimes, marker='o', linestyle='-', color='blue')
plt.title("Uptime Percentage by Service")
plt.ylabel("Uptime (%)")
plt.ylim(0, 110)
plt.grid(True)
plt.show()