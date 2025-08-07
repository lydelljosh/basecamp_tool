import os
import csv
from bs4 import BeautifulSoup
from auth import get_auth_headers
from utils.utils import print_success, clean_special_characters
from utils.basecamp_api import fetch_todo_detail, fetch_comments

def format_for_jira_live(todos_data: dict, run_dir: str):
    headers = get_auth_headers()
    account_id = headers.get("Account-ID")
    if not account_id:
        raise ValueError("Missing Account-ID in headers.")

    output_path = os.path.join(run_dir, "todos_jira.csv")
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "Project", "List", "Group", "Todo Title", "Description", "Assignees",
            "Created By", "Due Date", "Completed", "Comments",
            "Attachments", "App URL"
        ])
        writer.writeheader()

        for project, lists in todos_data.items():
            for list_title, list_block in lists.items():
                for todo in list_block.get("todos", []):
                    todo_id = todo.get("id")
                    url = todo.get("url", "")
                    try:
                        bucket_id = url.split("/buckets/")[1].split("/")[0]
                    except Exception:
                        continue

                    detail = fetch_todo_detail(account_id, bucket_id, todo_id, headers)
                    if not detail:
                        continue

                    raw_description = detail.get("description") or detail.get("description_html", "")
                    soup = BeautifulSoup(raw_description, "html.parser")
                    clean_description = soup.get_text(separator=" ", strip=True)

                    comments = fetch_comments(account_id, bucket_id, todo_id, headers)
                    comment_blocks = []
                    for c in comments:
                        name = c.get("creator", {}).get("name", "Unknown")
                        email = c.get("creator", {}).get("email_address", "")
                        created = c.get("created_at", "")
                        raw_text = c.get("content") or c.get("content_html", "")
                        text = BeautifulSoup(raw_text, "html.parser").get_text(separator=" ", strip=True)
                        if text:
                            comment_blocks.append(f"{name} ({email}) at {created}:\n> {text}")
                    formatted_comments = "\n\n".join(comment_blocks)

                    attachments = detail.get("attachments", [])
                    attachment_lines = []
                    for a in attachments:
                        name = a.get("filename") or a.get("name") or "unnamed"
                        url = a.get("url") or a.get("href")
                        if url:
                            attachment_lines.append(f"{name}: {url}")

                    # Extract group from list_title if it follows the "List - Group" format
                    # (Updated format from the new fetch logic)
                    group_name = todo.get("group", "Ungrouped")
                    list_name = list_title
                    if " - " in list_title:
                        parts = list_title.split(" - ", 1)
                        list_name = parts[0]  # Original list name
                        group_name = parts[1]  # Group name from list title takes precedence
                    
                    writer.writerow({
                        "Project": clean_special_characters(project),
                        "List": clean_special_characters(list_name),
                        "Group": clean_special_characters(group_name),
                        "Todo Title": clean_special_characters(detail.get("title", "")),
                        "Description": clean_special_characters(clean_description),
                        "Assignees": clean_special_characters(", ".join([p.get("name") for p in detail.get("assignees", [])])),
                        "Created By": clean_special_characters(detail.get("creator", {}).get("name") or ""),
                        "Due Date": detail.get("due_on") or "",
                        "Completed": detail.get("completed", False),
                        "Comments": clean_special_characters(formatted_comments),
                        "Attachments": clean_special_characters(" | ".join(attachment_lines)),
                        "App URL": detail.get("app_url", "")
                    })

    print_success(f"Exported Jira CSV to {output_path}")
