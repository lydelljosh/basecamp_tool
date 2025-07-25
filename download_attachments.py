# download_attachments.py
import os
import json
import requests
from datetime import datetime
from auth import get_auth_headers
from utils.utils import save_config, load_config, print_success, print_error

def sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in (name or ""))[:180]

def download_all_attachments(todos_json_path: str,
                             output_root: str = "results") -> str:
    """
    Read todos_deep.json, download all attachments from todos & comments.
    Returns the attachments output folder path.
    """
    # Load todos_deep.json
    with open(todos_json_path, "r", encoding="utf-8") as f:
        todos_data = json.load(f)

    headers = get_auth_headers()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    attachments_root = os.path.join(output_root, f"run_{ts}", "attachments")
    os.makedirs(attachments_root, exist_ok=True)

    total = 0
    for project_name, lists in todos_data.items():
        for list_title, todos in lists.items():
            for todo in todos:
                # Todo-level attachments
                for att in todo.get("attachments", []):
                    total += _download_one(att, headers, attachments_root, project_name, list_title, todo["title"])

                # Comment-level attachments (if you also stored them)
                for comment in todo.get("comments", []):
                    for att in comment.get("attachments", []):
                        total += _download_one(att, headers, attachments_root, project_name, list_title, todo["title"])

    print_success(f"Downloaded {total} file(s) into: {attachments_root}")
    return attachments_root


def _download_one(att: dict, headers: dict, root: str,
                  project: str, list_title: str, todo_title: str) -> int:
    url = att.get("url") or att.get("download_url")
    filename = att.get("filename") or att.get("name") or f"{att.get('id', 'file')}.bin"
    if not url:
        return 0

    folder = os.path.join(root, sanitize(project), sanitize(list_title), sanitize(todo_title))
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, sanitize(filename))

    try:
        resp = requests.get(url, headers=headers, stream=True)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(1024 * 32):
                f.write(chunk)
        print_success(f"Downloaded: {dest}")
        return 1
    except Exception as e:
        print_error(f"Failed to download {filename}: {e}")
        return 0
