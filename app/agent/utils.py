import json

def safe_parse(output: str):
    """
    Safely parse LLM output into JSON.
    Falls back to default structure if parsing fails.
    """
    try:
        return json.loads(output)
    except Exception:
        return {
            "action": "fallback",
            "reason": "Failed to parse LLM output"
        }