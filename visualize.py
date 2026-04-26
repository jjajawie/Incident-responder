import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.colors as mcolors
import numpy as np
from collections import defaultdict
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading
import importlib.util

spec = importlib.util.spec_from_file_location("incident_responder", "incident-responder.py")
incident_responder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(incident_responder)
 
#on = sqlite3.connect("log.db")
#cursor = con.cursor()
 
#cursor.execute("""
#    SELECT service_name,
#           substr(date, 1, 10) as day,
#           COUNT(*) as total,
#           SUM(CASE WHEN status = 200 THEN 1 ELSE 0 END) as successes
#    FROM results
#    GROUP BY service_name, day
#    ORDER BY day
#""")

#rows = cursor.fetchall()
#con.close()

#heat_data = defaultdict(dict)
#for service_name, day, total, successes in rows:
#    pct = (successes / total * 100) if total > 0 else 0
#    heat_data[service_name][day] = pct
#
#all_days = sorted({row[1] for row in rows})
#heat_services = list(heat_data.keys())
#
#matrix = np.full((len(heat_services), len(all_days)), np.nan)
#for i, service in enumerate(heat_services):
#    for j, day in enumerate(all_days):
#        if day in heat_data[service]:
#            matrix[i][j] = heat_data[service][day]
# 
#cmap = mcolors.LinearSegmentedColormap.from_list(
#    "uptime", ["#ff0d00", "#dbbd6a", "#09a14b"]
#)
#cmap.set_bad(color="#cccccc")
 
#fig, ax = plt.subplots(figsize=(10, 5))
 
#im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=100)
 
#ax.set_title("Uptime Heatmap (% per day)")
#ax.set_xticks(range(len(all_days)))
#ax.set_xticklabels(all_days, rotation=90, ha="right", fontsize=8)
#ax.set_yticks(range(len(heat_services)))
#ax.set_yticklabels(heat_services, fontsize=9)

#for i in range(len(heat_services)):
    #for j in range(len(all_days)):
       # val = matrix[i][j]
      #  if not np.isnan(val):
     #       ax.text(
    #            j, i, f"{val:.0f}%",
   #             ha="center", va="center",
  #              fontsize=8,
 #               color="white" if val < 50 else "black"
#            )

#plt.colorbar(im, ax=ax, label="Uptime %", orientation="vertical", pad=0.02)
#plt.tight_layout()
#plt.show()

def gui_log(message):
    log_box.config(state="normal")
    log_box.insert(tk.END, str(message) + "\n")
    log_box.see(tk.END)
    log_box.config(state="disabled")


def safe_log(message):
    root.after(0, lambda: gui_log(message))


def start_checks():
    try:
        interval = int(interval_entry.get())
        if interval < 1:
            interval = 1
    except ValueError:
        interval = 5
        gui_log("Invalid interval. Using 5 seconds instead.")

    start_button.config(state="disabled")
    stop_button.config(state="normal")

    gui_log("Monitoring started.")

    thread = threading.Thread(
        target=incident_responder.start_monitoring,
        args=(interval, safe_log),
        daemon=True
    )
    thread.start()


def stop_checks():
    incident_responder.stop_monitoring()

    start_button.config(state="normal")
    stop_button.config(state="disabled")

    gui_log("Stopping monitoring...")

def clear_chart():
    for widget in chart_frame.winfo_children():
        widget.destroy()


def show_heatmap():
    clear_chart()

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

    if not rows:
        gui_log("No data available for heatmap yet.")
        return

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

    fig, ax = plt.subplots(figsize=(8, 4))

    im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=100)

    ax.set_title("Uptime Heatmap (% per day)")
    ax.set_xticks(range(len(all_days)))
    ax.set_xticklabels(all_days, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(heat_services)))
    ax.set_yticklabels(heat_services, fontsize=9)

    for i in range(len(heat_services)):
        for j in range(len(all_days)):
            val = matrix[i][j]
            if not np.isnan(val):
                ax.text(
                    j, i, f"{val:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if val < 50 else "black"
                )

    plt.colorbar(im, ax=ax, label="Uptime %", orientation="vertical", pad=0.02)
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def show_uptime_graph():
    clear_chart()

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

    if not rows:
        gui_log("No data available for uptime graph yet.")
        return

    graph_data = defaultdict(list)

    for service_name, day, total, successes in rows:
        pct = (successes / total * 100) if total > 0 else 0
        graph_data[service_name].append((day, pct))

    fig, ax = plt.subplots(figsize=(8, 4))

    for service_name, values in graph_data.items():
        days = [item[0] for item in values]
        percentages = [item[1] for item in values]
        ax.plot(days, percentages, marker="o", label=service_name)

    ax.set_title("Uptime Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Uptime %")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(True)
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def set_demo_up():
    incident_responder.set_demo_api_status(True)
    gui_log("DemoAPI manually set to UP.")


def set_demo_down():
    incident_responder.set_demo_api_status(False)
    gui_log("DemoAPI manually set to DOWN.")

root = tk.Tk()
root.title("API Uptime Monitor / Incident Responder")
root.geometry("1000x700")
root.configure(bg="#1e1e1e")

title_label = tk.Label(
    root,
    text="API Uptime Monitor / Incident Responder",
    font=("Arial", 18, "bold"),
    bg="#1e1e1e",
    fg="white"
)
title_label.pack(pady=10)

control_frame = tk.Frame(root, bg="#2b2b2b", padx=10, pady=10)
control_frame.pack(fill=tk.X, padx=15, pady=5)

tk.Label(
    control_frame,
    text="Check every:",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", 10)
).pack(side=tk.LEFT, padx=5)

interval_entry = tk.Entry(control_frame, width=8)
interval_entry.insert(0, "5")
interval_entry.pack(side=tk.LEFT, padx=5)

tk.Label(
    control_frame,
    text="seconds",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", 10)
).pack(side=tk.LEFT, padx=5)

start_button = tk.Button(
    control_frame,
    text="Start Checks",
    command=start_checks,
    width=14
)
start_button.pack(side=tk.LEFT, padx=10)

stop_button = tk.Button(
    control_frame,
    text="Stop Checks",
    command=stop_checks,
    state="disabled",
    width=14
)
stop_button.pack(side=tk.LEFT, padx=5)

heatmap_button = tk.Button(
    control_frame,
    text="Show Heatmap",
    command=show_heatmap,
    width=14
)
heatmap_button.pack(side=tk.LEFT, padx=10)

demo_up_button = tk.Button(
    control_frame,
    text="Demo API Up",
    command=set_demo_up,
    width=14
)
demo_up_button.pack(side=tk.LEFT, padx=5)

demo_down_button = tk.Button(
    control_frame,
    text="Demo API Down",
    command=set_demo_down,
    width=14
)
demo_down_button.pack(side=tk.LEFT, padx=5)

graph_button = tk.Button(
    control_frame,
    text="Show Uptime Graph",
    command=show_uptime_graph,
    width=16
)
graph_button.pack(side=tk.LEFT, padx=5)

main_frame = tk.Frame(root, bg="#1e1e1e")
main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

log_frame = tk.LabelFrame(
    main_frame,
    text="Monitor Log",
    bg="#1e1e1e",
    fg="white",
    font=("Arial", 11, "bold")
)
log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

log_box = ScrolledText(
    log_frame,
    state="disabled",
    height=12,
    bg="#111111",
    fg="white",
    insertbackground="white"
)
log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

chart_frame = tk.LabelFrame(
    main_frame,
    text="Visualization",
    bg="#1e1e1e",
    fg="white",
    font=("Arial", 11, "bold")
)
chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
root.mainloop()