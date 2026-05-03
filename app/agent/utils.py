"""
Utility helpers for the agent layer.
"""

import json
import re


def safe_parse(output: str) -> dict:
    """
    Safely parse an LLM output string into a Python dict.

    Handles:
      • Clean JSON strings
      • JSON wrapped in markdown code fences  ```json … ```
      • Partial / malformed JSON (falls back to error dict)
    """
    if not output:
        return _fallback("Empty output")

    # Strip markdown fences if present
    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)```", output)
    candidate = fence_match.group(1).strip() if fence_match else output.strip()

    # Try direct JSON parse
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Last-resort: find first {...} block
    brace_match = re.search(r"\{[\s\S]+\}", candidate)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return _fallback(f"Could not parse: {output[:120]}")


def _fallback(reason: str) -> dict:
    return {
        "intent": "unknown",
        "action": "fallback",
        "result": reason,
        "ticket_id": None,
    }
