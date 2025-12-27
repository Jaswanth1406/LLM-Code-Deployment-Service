import time
import requests
import datetime


def notify_evaluation(evaluation_url, payload, timeout_minutes=10):
    headers = {"Content-Type": "application/json"}
    deadline = datetime.datetime.utcnow() + datetime.timedelta(minutes=timeout_minutes)
    delay = 1
    while datetime.datetime.utcnow() < deadline:
        try:
            r = requests.post(evaluation_url, json=payload, headers=headers, timeout=10)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(delay)
        delay = min(delay * 2, 60)
    raise TimeoutError("Failed to notify evaluation URL within timeout")
