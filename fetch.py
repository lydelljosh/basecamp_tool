import os
import requests
from auth import get_auth_headers
from utils.utils import save_to_json, print_success, print_error

BASE_URL = "https://3.basecampapi.com"

def fetch_all_todos_from_dump(projects, output_dir):
    headers = get_auth_headers()
    account_id = headers.get("Account-ID")
    all_data = {}

    for project in projects:
        bucket_id = project.get("id")
        name = project.get("name")
        print(f"\n=== Processing project: {name} ===")
        dock = project.get("dock", [])
        todoset_link = next((item for item in dock if item.get("name") == "todoset"), None)

        if not todoset_link:
            print_error(f"No todoset found for {name}")
            continue

        todosets_url = todoset_link.get("url").replace(".json", "/todolists.json")

        try:
            sets_res = requests.get(todosets_url, headers=headers)
            sets_res.raise_for_status()
            sets_data = sets_res.json()
        except Exception as e:
            print_error(f"Failed to fetch todolists for {name}: {e}")
            continue

        all_data[name] = {}

        # CASE 1: Proper grouped response
        if isinstance(sets_data, dict) and "groups" in sets_data:
            print(f"[DEBUG] Grouped todolists found for: {name}")
            for group in sets_data["groups"]:
                group_name = group.get("name", "Ungrouped")
                print(f"  > Group: {group_name}")
                for tlist in group.get("todolists", []):
                    list_title = f"{group_name} - {tlist.get('title')}"
                    print(f"    - Fetching list: {list_title}")
                    fetch_and_append_todos(account_id, bucket_id, tlist, list_title, all_data[name], headers)

        # CASE 2: Flat response containing groups and todolists
        elif isinstance(sets_data, list):
            print(f"[DEBUG] Flat list format for: {name}")
            current_group = None
            for item in sets_data:
                if item.get("type") == "Group":
                    current_group = item.get("name", "Ungrouped")
                    print(f"  > Group: {current_group}")
                elif item.get("type") == "Todolist":
                    list_title = item.get("title")
                    if current_group:
                        list_title = f"{current_group} - {list_title}"
                    print(f"    - Fetching list: {list_title}")
                    fetch_and_append_todos(account_id, bucket_id, item, list_title, all_data[name], headers)
        else:
            print_error(f"Unrecognized todolist format for {name}")

    output_path = os.path.join(output_dir, "todos_deep.json")
    save_to_json(all_data, output_path)
    print_success(f"Saved deep todos to {output_path}")
    return output_path, all_data

def fetch_and_append_todos(account_id, bucket_id, tlist, list_title, output_dict, headers):
    list_id = tlist.get("id")
    todos_url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todolists/{list_id}/todos.json"

    try:
        todos_res = requests.get(todos_url, headers=headers)
        todos_res.raise_for_status()
        todos = todos_res.json()
    except Exception as e:
        print_error(f"Failed to fetch todos for list {list_title}: {e}")
        return

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

    print(f"      ↳ Added {len(enriched_todos)} todos to: {list_title}")
    output_dict[list_title] = enriched_todos