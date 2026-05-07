from langchain_core.tools import tool
import json
from pathlib import Path


@tool
def query_logs(user_id: str) -> dict:
    """
    Retrieve the most recent access or error log for a user from
    data/access_logs.json.

    Args:
        user_id: The ID of the user whose logs to fetch.

    Returns:
        The most recent log entry for the user (dict), or an error
        dict with keys `error` and `reason` when something fails.
    """
    # Candidate locations for data/access_logs.json
    package_root = Path(__file__).resolve().parents[2]
    candidates = [
        package_root / "data" / "access_logs.json",
        Path.cwd() / "data" / "access_logs.json",
    ]

    for path in candidates:
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception as e:
                return {"error": "FILE_READ_ERROR", "reason": str(e)}

            # data can be a list of log entries or a mapping from user_id -> list
            if isinstance(data, dict):
                logs = data.get(str(user_id)) or data.get(user_id) or []
            else:
                logs = [entry for entry in data if str(entry.get("user_id")) == str(user_id)]

            if not logs:
                return {"error": "NOT_FOUND", "reason": "NO_LOGS_FOR_USER"}

            # Choose most recent by 'timestamp' when available
            if isinstance(logs, list):
                try:
                    most_recent = max(logs, key=lambda x: x.get("timestamp", ""))
                except Exception:
                    most_recent = logs[-1]
                return most_recent

            return logs

    return {"error": "NO_DATA_FILE", "reason": "data/access_logs.json not found"}
