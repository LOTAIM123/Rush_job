import json
import os
import threading
import urllib.request

API_URL = os.environ.get("RUSHJOB_API", "http://127.0.0.1:8000")
TIMEOUT = 3


def _request(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API_URL + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def submit_score(name, score, seconds):
    """Sends the score in the background. Returns the thread."""
    def work():
        try:
            _request("/api/scores", {"name": name, "score": score, "seconds": round(seconds, 1)})
        except Exception:
            pass
    t = threading.Thread(target=work, daemon=True)
    t.start()
    return t


class Leaderboard:
    """Loads the top list in the background; `rows` is always safe to read."""

    def __init__(self):
        self.rows = []
        self.error = False

    def refresh(self, limit=5):
        def work():
            try:
                self.rows = _request(f"/api/scores?limit={limit}")
                self.error = False
            except Exception:
                self.error = True
        threading.Thread(target=work, daemon=True).start()
