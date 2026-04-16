import sqlite3
import time
from datetime import datetime
import requests

test_url = "https://api.github.com"

try:
    # We added timeout=3 so it gives up after 3 seconds
    response = requests.get(test_url, timeout=3)

    print("Status Code:", response.status_code)
    print("Response Time (seconds):", response.elapsed.total_seconds())

except requests.exceptions.RequestException as e:
    # If the network fails or times out, it runs this instead of crashing
    print("Alert: The network crashed or timed out")
    print("Error Details:", e)