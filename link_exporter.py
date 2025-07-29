import json
import os
import re
import csv
from bs4 import BeautifulSoup
from datetime import datetime
from utils.basecamp_api import fetch_todo_detail, fetch_comments

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

ACCESS_TOKEN = config.get("access_token")
ACCOUNT_ID = str(config.get("account_id"))  # must be string for URL formatting

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Basecamp Link Exporter (you@example.com)"
}

# Create timestamped output folder
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = os.path.join("results", f"run_{timestamp}")
os.makedirs(output_dir, exist_ok=True)


def parse_todo_url(url):
    match = re.search(r'/(?:projects|buckets)/(\d+)/todos/(\d+)', url)
    if not match:
        raise ValueError("URL must contain /projects|buckets/{project_id}/todos/{todo_id}")
    return match.group(1), match.group(2)


def clean_html(raw_html):
    soup = BeautifulSoup(raw_html or "", "html.parser")
    text = soup.get_text()
    return re.sub(r'\s+', ' ', text).strip()  # normalize all whitespace


def format_comments(comments):
    formatted = []
    for c in comments:
        author = c.get("creator", {}).get("name", "Unknown")
        created_at = c.get("created_at", "")[:19].replace("T", " ")
        text = clean_html(c.get("content", ""))
        if text:
            line = f"[{author} - {created_at}]: {text}"
            formatted.append(line.replace('\n', ' ').replace('\r', ' ').strip())
    return "\n".join(formatted)


def export_to_csv(todo_data, comments, output_csv):
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Project Name", "Todolist Name", "Todo Title", "Assignee", "Description", "Comments"])

        project_name = todo_data.get("bucket", {}).get("name", "")
        todolist_name = todo_data.get("parent", {}).get("title", "")
        title = todo_data.get("title", "")
        description = clean_html(todo_data.get("description", ""))

        assignees = [a.get("name", "") for a in todo_data.get("assignees", [])]
        assignee_str = ", ".join(assignees)

        comments_str = format_comments(comments)

        writer.writerow([project_name, todolist_name, title, assignee_str, description, comments_str])


def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    todo_url = input("Enter full Basecamp To-do URL: ").strip()

    try:
        project_id, todo_id = parse_todo_url(todo_url)
    except ValueError as e:
        print(f"[ERROR] Invalid URL format: {e}")
        return

    print(f"Fetching To-do {todo_id} from project {project_id}...")

    todo_data = fetch_todo_detail(ACCOUNT_ID, project_id, int(todo_id), HEADERS)
    comments_data = fetch_comments(ACCOUNT_ID, project_id, int(todo_id), HEADERS)

    if not todo_data:
        print("[ERROR] Failed to fetch To-do. Aborting.")
        return

    result = {
        "todo": todo_data,
        "comments": comments_data
    }

    json_path = os.path.join(output_dir, f"todo_{todo_id}.json")
    csv_path = os.path.join(output_dir, f"todo_{todo_id}_jira.csv")

    save_json(result, json_path)
    export_to_csv(todo_data, comments_data, csv_path)

    print(f"[SUCCESS] Exported JSON: {json_path}")
    print(f"[SUCCESS] Exported CSV : {csv_path}")


if __name__ == "__main__":
    main()
