import os
import requests
from auth import get_auth_headers
from utils.utils import save_config, load_config, print_success, print_error, save_to_json

BASE_URL = "https://3.basecampapi.com"

def fetch_all_todos_from_dump(projects, output_dir):
    headers = get_auth_headers()
    account_id = headers.get("Account-ID")
    all_data = {}

    for project in projects:
        bucket_id = project.get("id")
        name = project.get("name")
        dock = project.get("dock", [])
        todoset_link = next((item for item in dock if item.get("name") == "todoset"), None)

        if not todoset_link:
            print_error(f"No todoset found for {name}")
            continue

        todosets_url = todoset_link.get("url").replace(".json", "/todolists.json")

        try:
            sets_res = requests.get(todosets_url, headers=headers)
            sets_res.raise_for_status()
            todolists = sets_res.json()
        except Exception as e:
            print_error(f"Failed to fetch todolists for {name}: {e}")
            continue

        all_data[name] = {}

        for tlist in todolists:
            list_id = tlist.get("id")
            list_title = tlist.get("title")
            todos_url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todolists/{list_id}/todos.json"

            try:
                todos_res = requests.get(todos_url, headers=headers)
                todos_res.raise_for_status()
                todos = todos_res.json()
            except Exception as e:
                print_error(f"Failed to fetch todos for list {list_title}: {e}")
                continue

            enriched_todos = []
            for todo in todos:
                todo_id = todo.get("id")
                todo_url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todos/{todo_id}.json"

                try:
                    detail_res = requests.get(todo_url, headers=headers)
                    detail_res.raise_for_status()
                    detail = detail_res.json()

                    enriched_todos.append({
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
                        "attachments": [],
                        "comments": [],
                        "app_url": detail.get("app_url"),
                        "url": detail.get("url")
                    })

                except Exception as e:
                    print_error(f"Failed to fetch full todo detail: {e}")
                    continue

            all_data[name][list_title] = enriched_todos

    output_path = os.path.join(output_dir, "todos_deep.json")
    save_to_json(all_data, output_path)
    print_success(f"Saved deep todos to {output_path}")
    return output_path, all_data