import os
import csv
from bs4 import BeautifulSoup
from auth import get_auth_headers
from utils.utils import print_success, clean_special_characters, print_error, sanitize_csv_field
from utils.basecamp_api import fetch_todo_detail, fetch_comments
from session_auth import BasecampSessionAuth

def format_for_jira_live(todos_data: dict, run_dir: str, download_attachments: bool = True):
    headers = get_auth_headers()
    account_id = headers.get("Account-ID")
    if not account_id:
        raise ValueError("Missing Account-ID in headers.")


    # Initialize session authentication for attachment downloads
    session_auth = None
    if download_attachments:
        print_success("Initializing session authentication for attachment downloads...")
        session_auth = BasecampSessionAuth()
        if not session_auth.login():
            print_error("Failed to authenticate with session login. Attachments will not be downloaded.")
            session_auth = None
        else:
            print_success("Session authentication successful!")

    # Create attachments directory
    attachments_dir = os.path.join(run_dir, "attachments")
    if download_attachments:
        os.makedirs(attachments_dir, exist_ok=True)

    # Count total todos to process
    total_todos = sum(len(list_block.get("todos", [])) for lists in todos_data.values() for list_block in lists.values())
    print_success(f"Processing {total_todos} todos for attachment downloads...")
    
    processed_todos = 0
    attachment_candidates = 0

    output_path = os.path.join(run_dir, "todos_jira.csv")
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "Project", "List", "Group", "Todo Title", "Description", "Assignees",
            "Created By", "Due Date", "Completed", "Comments",
            "Attachments", "Downloaded Files", "App URL"
        ])
        writer.writeheader()

        for project, lists in todos_data.items():
            for list_title, list_block in lists.items():
                for todo in list_block.get("todos", []):
                    processed_todos += 1
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

                    # Download attachments if session auth available
                    downloaded_files = []
                    todo_attachments_dir = os.path.join(attachments_dir, f"todo_{todo_id}") if download_attachments else None
                    
                    if session_auth and download_attachments:
                        os.makedirs(todo_attachments_dir, exist_ok=True)
                        print(f"DEBUG: Processing todo {todo_id} for attachments...")
                        
                        # Check if this todo has any potential attachments
                        has_attachments = bool(raw_description) or len(detail.get("attachments", [])) > 0
                        if has_attachments:
                            attachment_candidates += 1
                            print(f"DEBUG: Todo {todo_id} has attachments - description: {bool(raw_description)}, main attachments: {len(detail.get('attachments', []))}")
                        
                        # Download attachments from description
                        if raw_description:
                            soup = BeautifulSoup(raw_description, "html.parser")
                            print(f"DEBUG: Description length: {len(raw_description)} chars")
                            
                            # Download bc-attachment elements
                            bc_attachments = soup.find_all("bc-attachment")
                            print(f"DEBUG: Found {len(bc_attachments)} bc-attachment elements in description")
                            for i, bc_att in enumerate(bc_attachments):
                                filename = bc_att.get("filename", f"attachment_{i}")
                                download_url = bc_att.get("href")
                                
                                if download_url:
                                    local_path = os.path.join(todo_attachments_dir, filename)
                                    if session_auth.download_file(download_url, local_path):
                                        downloaded_files.append({
                                            "filename": filename,
                                            "local_path": local_path,
                                            "source": "description_bc_attachment"
                                        })
                            
                            # Download images from description
                            images = soup.find_all("img")
                            print(f"DEBUG: Found {len(images)} images in description")
                            for i, img in enumerate(images):
                                src = img.get("src")
                                if src and not any(skip in src.lower() for skip in ['avatar', 'profile', 'people']):
                                    filename = f"image_{i}.png"
                                    if "/" in src:
                                        potential_name = src.split("/")[-1].split("?")[0]
                                        if "." in potential_name:
                                            filename = potential_name
                                    
                                    local_path = os.path.join(todo_attachments_dir, filename)
                                    if session_auth.download_file(src, local_path):
                                        downloaded_files.append({
                                            "filename": filename,
                                            "local_path": local_path,
                                            "source": "description_image"
                                        })

                    comments = fetch_comments(account_id, bucket_id, todo_id, headers)
                    comment_blocks = []
                    for c_idx, c in enumerate(comments):
                        name = c.get("creator", {}).get("name", "Unknown")
                        email = c.get("creator", {}).get("email_address", "")
                        created = c.get("created_at", "")
                        raw_text = c.get("content") or c.get("content_html", "")
                        text = BeautifulSoup(raw_text, "html.parser").get_text(separator=" ", strip=True)
                        if text:
                            comment_blocks.append(f"{name} ({email}) at {created}: > {text}")
                            
                        # Download attachments from comments
                        if session_auth and download_attachments and raw_text:
                            comment_soup = BeautifulSoup(raw_text, "html.parser")
                            
                            # Download bc-attachments in comments
                            comment_bc_attachments = comment_soup.find_all("bc-attachment")
                            for i, bc_att in enumerate(comment_bc_attachments):
                                filename = bc_att.get("filename", f"comment_{c_idx}_attachment_{i}")
                                download_url = bc_att.get("href")
                                
                                if download_url:
                                    local_path = os.path.join(todo_attachments_dir, filename)
                                    if session_auth.download_file(download_url, local_path):
                                        downloaded_files.append({
                                            "filename": filename,
                                            "local_path": local_path,
                                            "source": f"comment_{c_idx}_attachment"
                                        })
                            
                            # Download images in comments
                            comment_images = comment_soup.find_all("img")
                            for i, img in enumerate(comment_images):
                                src = img.get("src")
                                if src and not any(skip in src.lower() for skip in ['avatar', 'profile', 'people']):
                                    filename = f"comment_{c_idx}_image_{i}.png"
                                    if "/" in src:
                                        potential_name = src.split("/")[-1].split("?")[0]
                                        if "." in potential_name:
                                            filename = potential_name
                                    
                                    local_path = os.path.join(todo_attachments_dir, filename)
                                    if session_auth.download_file(src, local_path):
                                        downloaded_files.append({
                                            "filename": filename,
                                            "local_path": local_path,
                                            "source": f"comment_{c_idx}_image"
                                        })
                                        
                    formatted_comments = "\n\n".join(comment_blocks)

                    # Process main todo attachments
                    attachments = detail.get("attachments", [])
                    print(f"DEBUG: Todo {todo_id} has {len(attachments)} main attachments")
                    attachment_lines = []
                    for attachment in attachments:
                        name = attachment.get("filename") or attachment.get("name") or "unnamed"
                        url = attachment.get("download_url") or attachment.get("url") or attachment.get("href")
                        
                        if url:
                            attachment_lines.append(f"{name}: {url}")
                            
                            # Download main attachments
                            if session_auth and download_attachments:
                                local_path = os.path.join(todo_attachments_dir, name)
                                if session_auth.download_file(url, local_path):
                                    downloaded_files.append({
                                        "filename": name,
                                        "local_path": local_path,
                                        "source": "main_attachment"
                                    })

                    # Extract group from list_title if it follows the "List - Group" format
                    # (Updated format from the new fetch logic)
                    group_name = todo.get("group", "Ungrouped")
                    list_name = list_title
                    if " - " in list_title:
                        parts = list_title.split(" - ", 1)
                        list_name = parts[0]  # Original list name
                        group_name = parts[1]  # Group name from list title takes precedence

                    # Create downloaded files info for CSV
                    downloaded_info = []
                    for file_info in downloaded_files:
                        downloaded_info.append(f"{file_info['filename']} -> {file_info['local_path']} (from {file_info['source']})")
                    
                    writer.writerow({
                        "Project": sanitize_csv_field(clean_special_characters(project)),
                        "List": sanitize_csv_field(clean_special_characters(list_name)),
                        "Group": sanitize_csv_field(clean_special_characters(group_name)),
                        "Todo Title": sanitize_csv_field(clean_special_characters(detail.get("title", ""))),
                        "Description": sanitize_csv_field(clean_special_characters(clean_description)),
                        "Assignees": sanitize_csv_field(clean_special_characters(", ".join([p.get("name") for p in detail.get("assignees", [])]))),
                        "Created By": sanitize_csv_field(clean_special_characters(detail.get("creator", {}).get("name") or "")),
                        "Due Date": detail.get("due_on") or "",
                        "Completed": detail.get("completed", False),
                        "Comments": sanitize_csv_field(clean_special_characters(formatted_comments)),
                        "Attachments": sanitize_csv_field(clean_special_characters(" | ".join(attachment_lines))),
                        "Downloaded Files": sanitize_csv_field(clean_special_characters(" | ".join(downloaded_info))),
                        "App URL": detail.get("app_url", "")
                    })

    print_success(f"Exported Jira CSV to {output_path}")
    
    # Print processing summary
    print_success(f"Processed {processed_todos} todos, {attachment_candidates} had potential attachments")
    
    # Print attachment download summary
    if download_attachments and session_auth:
        total_files = 0
        if os.path.exists(attachments_dir):
            for root, dirs, files in os.walk(attachments_dir):
                total_files += len(files)
        print_success(f"Downloaded {total_files} attachment files to {attachments_dir}")
    elif download_attachments:
        print_error("Attachment downloading was requested but session authentication failed")
