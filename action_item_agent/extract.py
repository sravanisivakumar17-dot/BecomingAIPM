import os
import json
import re
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You extract action items from meeting minutes.

The input will be plain English paragraphs/bullets.

Return ONLY valid JSON (no markdown, no commentary) matching this schema:
{
  "action_items": [
    {
      "action": "string",
      "owner": "string or empty",
      "timeline": "string or empty"
    }
  ]
}

Rules:
- "action" must be a clear, standalone task phrased as an imperative (e.g., "Send the deck to the team").
- If an owner is not explicitly stated, set owner to "".
- If a timeline/due date is not explicitly stated, set timeline to "".
- Deduplicate near-duplicate items.
- Do not invent owners or timelines.
"""

def _extract_json_object(text: str) -> dict:
    """
    Tries to parse JSON even if the model wraps it in extra text.
    """
    text = text.strip()

    # Best case: pure JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the first {...} block
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"Could not find JSON in model output:\n{text}")

    json_text = match.group(0)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Found JSON-like block but failed to parse:\n{json_text}") from e

def extract_action_items(minutes_text: str, model: str) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY in environment/.env")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": minutes_text},
        ],
        "temperature": 0.2,
        # If supported by the model/provider, this strongly nudges JSON-only output:
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "ActionItemAgent",
    }

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text}")

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return _extract_json_object(content)