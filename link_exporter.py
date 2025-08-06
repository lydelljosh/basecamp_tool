import json
import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils.basecamp_api import fetch_todo_detail, fetch_message_detail, fetch_comments

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

ACCESS_TOKEN = config.get("access_token")
ACCOUNT_ID = str(config.get("account_id"))

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Basecamp Link Exporter (you@example.com)"
}

# Create timestamped output folder
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = os.path.join("results", f"run_{timestamp}")
os.makedirs(output_dir, exist_ok=True)


def determine_link_type(url):
    if re.search(r'/buckets/\d+/todos/\d+', url):
        return "todo"
    elif re.search(r'/buckets/\d+/messages/\d+', url):
        return "message"
    return "unknown"


def parse_ids(url, link_type):
    match = re.search(r'/buckets/(\d+)/(?:todos|messages)/(\d+)', url)
    if not match:
        raise ValueError(f"URL must contain /buckets/{{id}}/{link_type}/{{id}}")
    return match.group(1), match.group(2)


def clean_html(raw_html):
    soup = BeautifulSoup(raw_html or "", "html.parser")
    return re.sub(r'\s+', ' ', soup.get_text()).strip()


def format_comments(comments):
    formatted = []
    for c in comments:
        author = c.get("creator", {}).get("name", "Unknown")
        created_at = c.get("created_at", "")[:19].replace("T", " ")
        text = clean_html(c.get("content", ""))
        if text:
            block = f"{author} [{created_at}]\n{text}\n"
            formatted.append(block)
    return "\n\n".join(formatted).strip()


def export_to_csv(data, comments, output_csv, is_todo=True):
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Project Name", "Container Name", "Title", "Assignee", "Description", "Comments"])

        project_name = data.get("bucket", {}).get("name", "")
        container = data.get("parent", {}).get("title", "") if is_todo else data.get("title", "")
        title = data.get("title", "")
        description = clean_html(data.get("description", "") if is_todo else data.get("content", ""))

        assignees = [a.get("name", "") for a in data.get("assignees", [])] if is_todo else []
        assignee_str = ", ".join(assignees)

        comments_str = format_comments(comments)

        writer.writerow([project_name, container, title, assignee_str, description, comments_str])


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def should_skip_download(url):
    return "avatar" in url or "/people/" in url


def extract_and_download(html, save_dir, prefix=""):
    soup = BeautifulSoup(html or "", "html.parser")
    img_tags = soup.find_all("img")

    for i, tag in enumerate(img_tags):
        url = tag.get("src")
        if not url:
            continue

        filename = f"{prefix}_img_{i+1}.png"
        if should_skip_download(url):
            print(f"[SKIP] Ignored (avatar or preview): {filename} ({url})")
            continue

        try:
            response = requests.get(url, headers=HEADERS, stream=True)
            content_type = response.headers.get("Content-Type", "")
            print(f"[INFO] Attempting to download: {filename} ({url}) — {content_type}")

            if response.status_code == 200 and "html" not in content_type.lower():
                os.makedirs(save_dir, exist_ok=True)
                with open(os.path.join(save_dir, filename), "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"[OK] Saved to: {os.path.join(save_dir, filename)}")
            else:
                print(f"[WARN] Skipped (non-binary or failed): {filename} ({response.status_code})")

        except Exception as e:
            print(f"[ERROR] Exception downloading {url}: {e}")


def download_attachments(body_html, comments, root_dir):
    os.makedirs(root_dir, exist_ok=True)

    # From main body
    desc_dir = os.path.join(root_dir, "description")
    extract_and_download(body_html, desc_dir, "description")

    # From comments
    for c in comments:
        cid = c.get("id")
        comment_html = c.get("content", "")
        comment_dir = os.path.join(root_dir, f"comment_{cid}")
        extract_and_download(comment_html, comment_dir, f"comment_{cid}")


def handle_todo(bucket_id, todo_id):
    print(f"[INFO] Fetching To-do {todo_id}...")
    todo_data = fetch_todo_detail(ACCOUNT_ID, bucket_id, int(todo_id), HEADERS)
    comments = fetch_comments(ACCOUNT_ID, bucket_id, int(todo_id), HEADERS)

    if not todo_data:
        print("[ERROR] Failed to fetch To-do.")
        return

    save_json({"todo": todo_data, "comments": comments}, os.path.join(output_dir, f"todo_{todo_id}.json"))
    export_to_csv(todo_data, comments, os.path.join(output_dir, f"todo_{todo_id}_jira.csv"), is_todo=True)
    download_attachments(todo_data.get("description", ""), comments, os.path.join(output_dir, "attachments"))


def handle_message(bucket_id, message_id):
    print(f"[INFO] Fetching Message {message_id}...")
    message_data = fetch_message_detail(ACCOUNT_ID, bucket_id, int(message_id), HEADERS)
    comments = fetch_comments(ACCOUNT_ID, bucket_id, int(message_id), HEADERS)

    if not message_data:
        print("[ERROR] Failed to fetch Message.")
        return

    save_json({"message": message_data, "comments": comments}, os.path.join(output_dir, f"message_{message_id}.json"))
    export_to_csv(message_data, comments, os.path.join(output_dir, f"message_{message_id}_jira.csv"), is_todo=False)
    download_attachments(message_data.get("content", ""), comments, os.path.join(output_dir, "attachments"))


def main():
    url = input("Enter full Basecamp To-do or Message URL: ").strip()
    link_type = determine_link_type(url)

    if link_type == "unknown":
        print("[ERROR] Unsupported URL format.")
        return

    try:
        bucket_id, item_id = parse_ids(url, link_type)
    except ValueError as e:
        print(f"[ERROR] {e}")
        return

    if link_type == "todo":
        handle_todo(bucket_id, item_id)
    elif link_type == "message":
        handle_message(bucket_id, item_id)

    print(f"[SUCCESS] Export complete: {output_dir}")


if __name__ == "__main__":
    main()
