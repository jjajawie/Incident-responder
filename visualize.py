import sqlite3
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from collections import defaultdict
 
con = sqlite3.connect("log.db")
cursor = con.cursor()
 
cursor.execute("""
    SELECT service_name,
           substr(date, 1, 10) as day,
           COUNT(*) as total,
           SUM(CASE WHEN status = 200 THEN 1 ELSE 0 END) as successes
    FROM results
    GROUP BY service_name, day
    ORDER BY day
""")

rows = cursor.fetchall()
con.close()

heat_data = defaultdict(dict)
for service_name, day, total, successes in rows:
    pct = (successes / total * 100) if total > 0 else 0
    heat_data[service_name][day] = pct

all_days = sorted({row[1] for row in rows})
heat_services = list(heat_data.keys())

matrix = np.full((len(heat_services), len(all_days)), np.nan)
for i, service in enumerate(heat_services):
    for j, day in enumerate(all_days):
        if day in heat_data[service]:
            matrix[i][j] = heat_data[service][day]
 
cmap = mcolors.LinearSegmentedColormap.from_list(
    "uptime", ["#ff0d00", "#dbbd6a", "#09a14b"]
)
cmap.set_bad(color="#cccccc")
 
fig, ax = plt.subplots(figsize=(10, 5))
 
im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=100)
 
ax.set_title("Uptime Heatmap (% per day)")
ax.set_xticks(range(len(all_days)))
ax.set_xticklabels(all_days, rotation=90, ha="right", fontsize=8)
ax.set_yticks(range(len(heat_services)))
ax.set_yticklabels(heat_services, fontsize=9)

for i in range(len(heat_services)):
    for j in range(len(all_days)):
        val = matrix[i][j]
        if not np.isnan(val):
            ax.text(
                j, i, f"{val:.0f}%",
                ha="center", va="center",
                fontsize=8,
                color="white" if val < 50 else "black"
            )

plt.colorbar(im, ax=ax, label="Uptime %", orientation="vertical", pad=0.02)
plt.tight_layout()
plt.show()