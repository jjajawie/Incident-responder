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

def show_incidents():
    con = sqlite3.connect("log.db")
    cursor = con.cursor()

    cursor.execute("""
        SELECT date, service_name, incident_type, details
        FROM incidents
        ORDER BY date DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    con.close()

    if not rows:
        gui_log("No incidents recorded yet.")
        return

    gui_log("\nRecent Incidents")

    for date, service_name, incident_type, details in rows:
        gui_log(f"{date}")
        gui_log(f"Service: {service_name}")
        gui_log(f"Type: {incident_type}")
        gui_log(f"Details: {details}")

def show_uptime_summary():
    con = sqlite3.connect("log.db")
    cursor = con.cursor()

    cursor.execute("""
        SELECT 
            r.service_name,
            COUNT(*) as total_checks,
            SUM(CASE WHEN r.status = 200 THEN 1 ELSE 0 END) as successful_checks,
            SUM(CASE WHEN r.status != 200 OR r.status IS NULL THEN 1 ELSE 0 END) as failed_checks,
            AVG(r.response_time) as avg_response_time,
            COUNT(i.service_name) as incident_count
        FROM results r
        LEFT JOIN incidents i
            ON r.service_name = i.service_name
        GROUP BY r.service_name
    """)

    rows = cursor.fetchall()
    con.close()

    if not rows:
        gui_log("No uptime data available.")
        return

    gui_log("\n Uptime Summary")

    for service_name, total, successful, failed, avg_response, incidents in rows:
        uptime = (successful / total * 100) if total > 0 else 0
        avg_response = avg_response if avg_response is not None else 0

        gui_log(f"{service_name}")
        gui_log(f"Total checks: {total}")
        gui_log(f"Successful checks: {successful}")
        gui_log(f"Failed checks: {failed}")
        gui_log(f"Uptime: {uptime:.2f}%")
        gui_log(f"Average response time: {avg_response:.3f}s")
        gui_log(f"Incidents: {incidents}")

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
        gui_log("Invalid interval.")

    start_button.config(state="disabled")
    stop_button.config(state="normal")

    gui_log("Check started.")

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

    gui_log("Stop check")

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
        gui_log("No data.")
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

def show_selected_service_graph():
    clear_chart()

    service = selected_service.get()

    con = sqlite3.connect("log.db")
    cursor = con.cursor()

    cursor.execute("""
        SELECT substr(date, 1, 16) as minute_block,
            COUNT(*) as total,
            SUM(CASE WHEN status = 200 THEN 1 ELSE 0 END) as successes
            FROM results
            WHERE service_name = ?
            GROUP BY minute_block
            ORDER BY minute_block
    """, (service,))

    rows = cursor.fetchall()
    con.close()

    if not rows:
        gui_log(f"No data: {service}")
        return

    days = []
    percentages = []

    for time_block, total, successes in rows:
        uptime = (successes / total * 100) if total > 0 else 0
        days.append(time_block)
        percentages.append(uptime)

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(days, percentages, marker="o")

    ax.set_title(f"{service} Uptime Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Uptime %")
    ax.set_ylim(0, 105)
    ax.grid(True)
    ax.tick_params(axis="x", rotation=45)

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
        gui_log("No data")
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
    gui_log("DemoAPI UP.")


def set_demo_down():
    incident_responder.set_demo_api_status(False)
    gui_log("DemoAPI DOWN.")

root = tk.Tk()
root.title("Responder")
root.geometry("1000x700")
root.configure(bg="#1e1e1e")

title_label = tk.Label(
    root,
    text="Incident Responder",
    font=("Arial", 18, "bold"),
    bg="#1e1e1e",
    fg="white"
)
title_label.pack(pady=10)

control_frame = tk.Frame(root, bg="#2b2b2b", padx=10, pady=10)
control_frame.pack(fill=tk.X, padx=15, pady=5)


selected_service = tk.StringVar()
selected_service.set("GitHub")

service_dropdown = tk.OptionMenu(
    control_frame,
    selected_service,
    *incident_responder.api_dict.keys()
)
service_dropdown.pack(side=tk.LEFT, padx=5)

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

selected_graph_button = tk.Button(
    control_frame,
    text="Selected Graph",
    command=show_selected_service_graph,
    width=14
)
selected_graph_button.pack(side=tk.LEFT, padx=5)

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

summary_button = tk.Button(
    control_frame,
    text="Uptime Summary",
    command=show_uptime_summary,
    width=16
)
summary_button.pack(side=tk.LEFT, padx=5)

incidents_button = tk.Button(
    control_frame,
    text="Show Incidents",
    command=show_incidents,
    width=14
)
incidents_button.pack(side=tk.LEFT, padx=5)

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