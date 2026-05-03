import json

def safe_parse(output: str):
    """
    Safely parse LLM output into JSON.
    Falls back to default structure if parsing fails.
    """
    try:
        print("Raw LLM Output:", output)
        return json.loads(output)
    except Exception as e:
        print("Error parsing LLM output:", e)
        return {
            "action": "fallback",
            "reason": "Failed to parse LLM output"
        }