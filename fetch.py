# fetch.py
import os
import json
import requests
from typing import Dict, List
from auth import get_auth_headers
from utils import print_success, print_error

BASE_URL = "https://3.basecampapi.com"

def fetch_all_todos_from_dump(projects_dump_path: str, run_dir: str) -> str:
    """
    Using the projects_dump.json, follow each project's todoset url -> todolists -> todos -> details/comments.
    Save everything to {run_dir}/todos_deep.json and return that path.
    """
    headers = get_auth_headers()
    account_id = headers.get("Account-ID")

    with open(projects_dump_path, "r", encoding="utf-8") as f:
        projects = json.load(f)

    result: Dict[str, Dict[str, List[dict]]] = {}

    for project in projects:
        bucket_id = project.get("id")
        project_name = project.get("name")
        dock = project.get("dock", [])

        # Find the todoset dock entry (you already saw this in the dump)
        todoset_entry = next((d for d in dock if d.get("name") == "todoset" and d.get("enabled")), None)
        if not todoset_entry:
            print_error(f"[{project_name}] No todoset found/enabled.")
            continue

        # GET the todoset node to discover its 'todolists_url'
        try:
            todoset_url = todoset_entry["url"]  # e.g. /buckets/{bucket}/todosets/{id}.json
            r = requests.get(todoset_url, headers=headers)
            r.raise_for_status()
            todoset = r.json()
        except Exception as e:
            print_error(f"[{project_name}] Failed to fetch todoset: {e}")
            continue

        todolists_url = todoset.get("todolists_url")
        if not todolists_url:
            print_error(f"[{project_name}] todoset has no 'todolists_url'.")
            continue

        try:
            r = requests.get(todolists_url, headers=headers)
            r.raise_for_status()
            todolists = r.json()
        except Exception as e:
            print_error(f"[{project_name}] Failed to fetch todolists: {e}")
            continue

        result[project_name] = {}

        for tlist in todolists:
            list_id = tlist.get("id")
            list_title = tlist.get("title")
            if not list_id:
                continue

            todos_url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todolists/{list_id}/todos.json"

            try:
                r = requests.get(todos_url, headers=headers)
                r.raise_for_status()
                todos = r.json()
            except Exception as e:
                print_error(f"[{project_name}] Failed to fetch todos for list '{list_title}': {e}")
                continue

            enriched: List[dict] = []
            for todo in todos:
                try:
                    detail = _fetch_todo_detail(headers, account_id, bucket_id, todo["id"])
                    comments = _fetch_todo_comments(headers, account_id, bucket_id, todo["id"])
                    enriched.append(_shape_todo(detail, comments))
                except Exception as e:
                    print_error(f"[{project_name}] Failed to enrich todo {todo.get('id')}: {e}")

            result[project_name][list_title] = enriched

    # save
    todos_deep_path = os.path.join(run_dir, "todos_deep.json")
    with open(todos_deep_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print_success(f"Saved deep todos to {todos_deep_path}")
    return todos_deep_path


def _fetch_todo_detail(headers: dict, account_id: str, bucket_id: int, todo_id: int) -> dict:
    url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todos/{todo_id}.json"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def _fetch_todo_comments(headers: dict, account_id: str, bucket_id: int, todo_id: int) -> List[dict]:
    # Basecamp exposes comments via recordings
    url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/recordings/{todo_id}/comments.json"
    r = requests.get(url, headers=headers)
    if r.status_code == 404:
        # Some older items might be under /todos/{id}/comments.json — fallback gracefully
        fallback = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todos/{todo_id}/comments.json"
        r = requests.get(fallback, headers=headers)
    r.raise_for_status()
    return r.json()


def _shape_todo(detail: dict, comments: List[dict]) -> dict:
    return {
        "id": detail.get("id"),
        "title": detail.get("title"),
        "assignees": [p.get("name") for p in detail.get("assignees", [])],
        "due_on": detail.get("due_on"),
        "created_at": detail.get("created_at"),
        "completed": detail.get("completed"),
        "completed_at": detail.get("completed_at"),
        "created_by": detail.get("creator", {}).get("name"),
        "notes": detail.get("content"),
        "comments_count": detail.get("comments_count"),
        "attachments_count": len(detail.get("attachments", [])),
        "attachments": detail.get("attachments", []),
        "comments": [
            {
                "id": c.get("id"),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at"),
                "author": c.get("creator", {}).get("name"),
                "author_email": c.get("creator", {}).get("email_address"),
                "content_html": c.get("content_html"),
                "attachments": c.get("attachments", []),
            }
            for c in comments
        ],
        "app_url": detail.get("app_url"),
        "url": detail.get("url"),
    }
