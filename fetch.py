import os
import requests
from auth import get_auth_headers
from utils.utils import save_to_json, print_success, print_error, BASE_URL

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

        if isinstance(sets_data, list):
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

    # First get group ID-to-name mapping for individual todo group assignment
    group_map = {}
    groups_url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todolists/{list_id}/groups.json"
    
    try:
        groups_res = requests.get(groups_url, headers=headers)
        groups_res.raise_for_status()
        groups = groups_res.json()
        
        # Build group mapping for individual todos
        for group in groups:
            group_map[group["id"]] = group["name"]
        
        # If groups exist and have todos_url, fetch todos from each group separately
        if groups and any(group.get("todos_url") for group in groups):
            print(f"      Found {len(groups)} groups in {list_title}")
            for group in groups:
                group_name = group.get("name", "Unnamed Group")
                
                # Use the todos_url provided by the group response
                group_todos_url = group.get("todos_url")
                if not group_todos_url:
                    print(f"        ↳ No todos_url found for group: {group_name}")
                    continue
                
                group_enriched_todos = fetch_todos_from_url(group_todos_url, account_id, bucket_id, headers, f"{list_title} - {group_name}", group_map)
                
                # Store with group information
                group_key = f"{list_title} - {group_name}"
                output_dict[group_key] = {"todos": group_enriched_todos}
                print(f"        ↳ Added {len(group_enriched_todos)} todos to group: {group_name}")
            return
            
    except Exception as e:
        # If groups endpoint fails, fall back to fetching all todos from the list
        print(f"      No groups found in {list_title}, fetching all todos")
    
    # Fallback: fetch all todos from the list directly (no groups)
    todos_url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todolists/{list_id}/todos.json"
    enriched_todos = fetch_todos_from_url(todos_url, account_id, bucket_id, headers, list_title, group_map)
    
    print(f"      ↳ Added {len(enriched_todos)} todos to: {list_title}")
    output_dict[list_title] = {"todos": enriched_todos}

def fetch_todos_from_url(todos_url, account_id, bucket_id, headers, context_name, group_map=None):
    """Helper function to fetch and enrich todos from a given URL"""
    if group_map is None:
        group_map = {}
    try:
        todos_res = requests.get(todos_url, headers=headers)
        todos_res.raise_for_status()
        todos = todos_res.json()
    except Exception as e:
        print_error(f"Failed to fetch todos for {context_name}: {e}")
        return []

    enriched_todos = []
    for todo in todos:
        try:
            group_name = group_map.get(todo.get("group_id")) or "Ungrouped"
            enriched_todos.append({
                "id": todo.get("id"),
                "title": todo.get("title"),
                "assignees": [p.get("name") for p in todo.get("assignees", [])],
                "due_on": todo.get("due_on"),
                "created_at": todo.get("created_at"),
                "completed": todo.get("completed"),
                "completed_at": todo.get("completed_at"),
                "created_by": todo.get("creator", {}).get("name"),
                "notes": todo.get("content"),
                "comments_count": todo.get("comments_count"),
                "attachments_count": len(todo.get("attachments", [])),
                "attachments": [],
                "comments": [],
                "app_url": todo.get("app_url"),
                "url": todo.get("url"),
                "group": group_name,
                "parent_title": None
            })
        except Exception as e:
            print_error(f"Failed to enrich todo: {e}")
            continue

    return enriched_todos
