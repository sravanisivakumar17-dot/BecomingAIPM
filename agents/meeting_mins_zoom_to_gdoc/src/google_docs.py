from __future__ import print_function

import os
from typing import List, Dict

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Full access to read/write Google Docs
SCOPES = ["https://www.googleapis.com/auth/documents"]


def get_docs_service():
    """
    Creates/returns an authenticated Google Docs API service.
    Requires:
      - credentials.json in project root (OAuth Desktop client)
      - token.json will be created after first auth
    """
    creds = None
    token_path = "token.json"
    creds_path = "credentials.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    "credentials.json not found in project root. "
                    "Download OAuth Desktop credentials from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("docs", "v1", credentials=creds)


def append_action_items(doc_id: str, items: List[Dict]) -> None:
    service = get_docs_service()

    # Find end of doc so we can insert text there
    doc = service.documents().get(documentId=doc_id).execute()
    end_index = doc["body"]["content"][-1]["endIndex"] - 1

    lines = []
    lines.append("\n\n=== Action Items (Auto-generated) ===\n")

    if not items:
        lines.append("- (No action items found)\n")
    else:
        for i, it in enumerate(items, 1):
            action = (it.get("action") or "").strip()
            owner = (it.get("owner") or "").strip()
            timeline = (it.get("timeline") or "").strip()

            if not action:
                continue

            # Formatting rule:
            # owner exists -> Owner — Action — Timeline (timeline optional)
            # else -> Action
            if owner:
                if timeline:
                    lines.append(f"{i}. {owner} — {action} — {timeline}\n")
                else:
                    lines.append(f"{i}. {owner} — {action}\n")
            else:
                lines.append(f"{i}. {action}\n")

    text = "".join(lines)

    requests = [
        {
            "insertText": {
                "location": {"index": end_index},
                "text": text
            }
        }
    ]

    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests}
    ).execute()