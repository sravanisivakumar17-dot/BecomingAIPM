import os
from dotenv import load_dotenv

from extract import extract_action_items
from google_docs import append_action_items

# adding a comment for testing purposes.

def read_minutes(path: str) -> str:
    print(f"[main] Reading minutes from: {path}", flush=True)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Minutes file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    print("[main] START", flush=True)

    load_dotenv()
    print("[main] Loaded .env", flush=True)

    doc_id = os.getenv("GOOGLE_DOC_ID", "").strip()
    minutes_path = os.getenv("MINUTES_PATH", "Data/mins.txt").strip()
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()

    if not doc_id:
        raise RuntimeError("Missing GOOGLE_DOC_ID in .env")

    print(f"[main] Model: {model}", flush=True)
    print(f"[main] Doc ID set: {bool(doc_id)}", flush=True)

    minutes_text = read_minutes(minutes_path)
    if not minutes_text.strip():
        raise RuntimeError(f"Minutes file is empty: {minutes_path}")

    print(f"[main] Minutes length: {len(minutes_text)} chars", flush=True)

    print("[main] Calling OpenRouter to extract action items...", flush=True)
    result = extract_action_items(minutes_text, model=model)

    items = result.get("action_items", [])
    print(f"[main] Extracted {len(items)} action items", flush=True)

    print("[main] Appending to Google Doc...", flush=True)
    append_action_items(doc_id, items)

    print(f"[main] DONE. Appended {len(items)} action items to Google Doc.", flush=True)


if __name__ == "__main__":
    main()