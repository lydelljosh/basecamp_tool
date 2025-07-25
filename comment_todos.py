import os
import requests
from utils import get_account_id, save_to_json, print_error, print_success
from auth import get_auth_headers

BASE_URL = "https://3.basecampapi.com"
ACCOUNT_ID = get_account_id()


def comment_todos(todos_data, run_dir):
    headers = get_auth_headers()
    enriched_data = {}

    for project, lists in todos_data.items():
        enriched_data[project] = {}

        for list_title, todos in lists.items():
            enriched_list = []

            for todo in todos:
                todo_id = todo.get("id")
                if not todo_id or "url" not in todo:
                    continue

                try:
                    bucket_id = todo["url"].split("/buckets/")[1].split("/")[0]
                except IndexError:
                    print_error(f"Invalid URL format in todo: {todo.get('url')}")
                    continue

                todo_url = f"{BASE_URL}/{ACCOUNT_ID}/buckets/{bucket_id}/todos/{todo_id}.json"
                comments_url = f"{BASE_URL}/{ACCOUNT_ID}/buckets/{bucket_id}/recordings/{todo_id}/comments.json"

                try:
                    # Fetch full todo details
                    todo_res = requests.get(todo_url, headers=headers)
                    todo_res.raise_for_status()
                    detail = todo_res.json()

                    # Fetch comments
                    comments = []
                    try:
                        comments_res = requests.get(comments_url, headers=headers)
                        comments_res.raise_for_status()
                        comments_data = comments_res.json()

                        for c in comments_data:
                            comments.append({
                                "id": c.get("id"),
                                "created_at": c.get("created_at"),
                                "updated_at": c.get("updated_at"),
                                "author": c.get("creator", {}).get("name"),
                                "author_email": c.get("creator", {}).get("email_address"),
                                "content_html": c.get("content"),  # <- reliable field
                                "attachments": c.get("attachments", [])
                            })
                    except Exception as e:
                        print_error(f"Failed to fetch comments for todo {todo_id}: {e}")

                    enriched_list.append({
                        "id": todo_id,
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
                        "comments": comments,
                        "app_url": detail.get("app_url"),
                        "url": detail.get("url")
                    })

                except Exception as e:
                    print_error(f"Failed to enrich todo {todo_id}: {e}")
                    continue

            enriched_data[project][list_title] = enriched_list

    # Save enriched version
    output_path = os.path.join(run_dir, "todos_deep.json")
    save_to_json(enriched_data, output_path)
    print_success(f"Saved enriched todos to {output_path}")