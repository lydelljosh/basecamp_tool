import os
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from auth import get_auth_headers
from utils.utils import print_success, print_error, clean_special_characters
from utils.basecamp_api import fetch_todo_detail, fetch_comments
from session_auth import BasecampSessionAuth

def test_single_todo_with_attachments(todo_url: str):
    """Test processing a single todo with session-based attachment downloading."""
    
    # Parse the todo URL to extract bucket_id and todo_id
    try:
        # Expected format: https://3.basecamp.com/ACCOUNT_ID/buckets/BUCKET_ID/todos/TODO_ID
        # or https://3.basecampapi.com/ACCOUNT_ID/buckets/BUCKET_ID/todos/TODO_ID
        parts = todo_url.replace('3.basecampapi.com', '3.basecamp.com').split("/")
        account_id = parts[3]
        bucket_id = parts[parts.index("buckets") + 1]
        todo_id = parts[parts.index("todos") + 1]
    except (ValueError, IndexError):
        print_error("Invalid todo URL format. Expected: https://3.basecamp.com/ACCOUNT_ID/buckets/BUCKET_ID/todos/TODO_ID")
        return

    print_success(f"Testing todo ID: {todo_id} in bucket: {bucket_id}")

    # Create timestamped directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_dir = f"results/test_run_{timestamp}"
    attachments_dir = os.path.join(test_dir, "attachments")
    os.makedirs(attachments_dir, exist_ok=True)

    # Get API headers for fetching todo data
    headers = get_auth_headers()
    if not headers.get("Account-ID"):
        print_error("Missing Account-ID in headers.")
        return

    # Initialize session authentication
    print_success("Initializing session authentication...")
    session_auth = BasecampSessionAuth()
    
    if not session_auth.login():
        print_error("Failed to authenticate with session login")
        return
        
    print_success("Session authentication successful!")

    # Fetch todo details via API
    detail = fetch_todo_detail(account_id, bucket_id, todo_id, headers)
    if not detail:
        print_error("Failed to fetch todo details")
        return

    print_success(f"Todo Title: {detail.get('title', 'Unknown')}")

    # Process description for attachments
    raw_description = detail.get("description") or detail.get("description_html", "")
    clean_description = ""
    downloaded_files = []
    
    if raw_description:
        soup = BeautifulSoup(raw_description, "html.parser")
        clean_description = soup.get_text(separator=" ", strip=True)
        
        print_success(f"Description length: {len(raw_description)} chars")
        
        # Find bc-attachment elements
        bc_attachments = soup.find_all("bc-attachment")
        print_success(f"Found {len(bc_attachments)} bc-attachment elements")
        
        for i, bc_att in enumerate(bc_attachments):
            filename = bc_att.get("filename", f"attachment_{i}")
            download_url = bc_att.get("href")
            
            if download_url:
                print_success(f"Downloading: {filename} from {download_url}")
                local_path = os.path.join(attachments_dir, filename)
                
                if session_auth.download_file(download_url, local_path):
                    downloaded_files.append({
                        "filename": filename,
                        "local_path": local_path,
                        "source": "description_bc_attachment"
                    })
                    print_success(f"✅ Downloaded: {filename}")
                else:
                    print_error(f"❌ Failed to download: {filename}")
        
        # Find regular images
        images = soup.find_all("img")
        print_success(f"Found {len(images)} images")
        
        for i, img in enumerate(images):
            src = img.get("src")
            if src and not any(skip in src.lower() for skip in ['avatar', 'profile', 'people']):
                filename = f"image_{i}.png"
                if "/" in src:
                    potential_name = src.split("/")[-1].split("?")[0]
                    if "." in potential_name:
                        filename = potential_name
                
                print_success(f"Downloading image: {filename} from {src}")
                local_path = os.path.join(attachments_dir, filename)
                
                if session_auth.download_file(src, local_path):
                    downloaded_files.append({
                        "filename": filename,
                        "local_path": local_path,
                        "source": "description_image"
                    })
                    print_success(f"✅ Downloaded: {filename}")
                else:
                    print_error(f"❌ Failed to download: {filename}")

    # Process main todo attachments
    attachments = detail.get("attachments", [])
    attachment_lines = []
    
    for attachment in attachments:
        name = attachment.get("filename") or attachment.get("name") or "unnamed"
        url = attachment.get("download_url") or attachment.get("url") or attachment.get("href")
        
        if url:
            attachment_lines.append(f"{name}: {url}")
            
            print_success(f"Downloading main attachment: {name} from {url}")
            local_path = os.path.join(attachments_dir, name)
            
            if session_auth.download_file(url, local_path):
                downloaded_files.append({
                    "filename": name,
                    "local_path": local_path,
                    "source": "main_attachment"
                })
                print_success(f"✅ Downloaded: {name}")
            else:
                print_error(f"❌ Failed to download: {name}")

    # Fetch and process comments
    comments = fetch_comments(account_id, bucket_id, todo_id, headers)
    comment_blocks = []
    
    for c_idx, c in enumerate(comments):
        name = c.get("creator", {}).get("name", "Unknown")
        email = c.get("creator", {}).get("email_address", "")
        created = c.get("created_at", "")
        raw_text = c.get("content") or c.get("content_html", "")
        text = BeautifulSoup(raw_text, "html.parser").get_text(separator=" ", strip=True)
        
        if text:
            comment_blocks.append(f"{name} ({email}) at {created}:\n> {text}")
            
        # Check for attachments in comments
        if raw_text:
            comment_soup = BeautifulSoup(raw_text, "html.parser")
            
            # Find bc-attachments in comments
            comment_bc_attachments = comment_soup.find_all("bc-attachment")
            for i, bc_att in enumerate(comment_bc_attachments):
                filename = bc_att.get("filename", f"comment_{c_idx}_attachment_{i}")
                download_url = bc_att.get("href")
                
                if download_url:
                    print_success(f"Downloading comment attachment: {filename}")
                    local_path = os.path.join(attachments_dir, filename)
                    
                    if session_auth.download_file(download_url, local_path):
                        downloaded_files.append({
                            "filename": filename,
                            "local_path": local_path,
                            "source": f"comment_{c_idx}_attachment"
                        })
                        print_success(f"✅ Downloaded: {filename}")
                    else:
                        print_error(f"❌ Failed to download: {filename}")
            
            # Find images in comments
            comment_images = comment_soup.find_all("img")
            for i, img in enumerate(comment_images):
                src = img.get("src")
                if src and not any(skip in src.lower() for skip in ['avatar', 'profile', 'people']):
                    filename = f"comment_{c_idx}_image_{i}.png"
                    if "/" in src:
                        potential_name = src.split("/")[-1].split("?")[0]
                        if "." in potential_name:
                            filename = potential_name
                    
                    print_success(f"Downloading comment image: {filename}")
                    local_path = os.path.join(attachments_dir, filename)
                    
                    if session_auth.download_file(src, local_path):
                        downloaded_files.append({
                            "filename": filename,
                            "local_path": local_path,
                            "source": f"comment_{c_idx}_image"
                        })
                        print_success(f"✅ Downloaded: {filename}")
                    else:
                        print_error(f"❌ Failed to download: {filename}")

    formatted_comments = "\n\n".join(comment_blocks)

    # Create CSV output
    output_path = os.path.join(test_dir, f"test_todo_{todo_id}.csv")
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "Project", "List", "Group", "Todo Title", "Description", "Assignees",
            "Created By", "Due Date", "Completed", "Comments",
            "Attachments", "Downloaded Files", "App URL"
        ])
        writer.writeheader()

        # Create downloaded files info for CSV
        downloaded_info = []
        for file_info in downloaded_files:
            downloaded_info.append(f"{file_info['filename']} -> {file_info['local_path']} (from {file_info['source']})")

        writer.writerow({
            "Project": "Test Project",
            "List": "Test List", 
            "Group": "Test Group",
            "Todo Title": clean_special_characters(detail.get("title", "")),
            "Description": clean_special_characters(clean_description),
            "Assignees": clean_special_characters(", ".join([p.get("name") for p in detail.get("assignees", [])])),
            "Created By": clean_special_characters(detail.get("creator", {}).get("name") or ""),
            "Due Date": detail.get("due_on") or "",
            "Completed": detail.get("completed", False),
            "Comments": clean_special_characters(formatted_comments),
            "Attachments": clean_special_characters(" | ".join(attachment_lines)),
            "Downloaded Files": clean_special_characters(" | ".join(downloaded_info)),
            "App URL": detail.get("app_url", "")
        })

    print_success(f"Test results saved to {output_path}")
    
    # Print summary
    print_success("\n=== TEST SUMMARY ===")
    print_success(f"Todo: {detail.get('title', 'Unknown')}")
    print_success(f"Comments: {len(comments)}")
    print_success(f"Main attachments: {len(attachments)}")
    print_success(f"Downloaded files: {len(downloaded_files)}")
    
    if downloaded_files:
        print_success("\nDownloaded files:")
        for file_info in downloaded_files:
            file_size = "unknown"
            if os.path.exists(file_info['local_path']):
                file_size = f"{os.path.getsize(file_info['local_path'])} bytes"
            print_success(f"  ✅ {file_info['filename']} ({file_size}) from {file_info['source']}")
    else:
        print_error("No files were downloaded")

def main():
    """Main function for testing."""
    print("=== Basecamp Todo + Attachment Downloader Test ===")
    
    # Use the test URL directly
    todo_url = "https://3.basecamp.com/4146522/buckets/10338892/todos/8257859468"
    print(f"Testing with: {todo_url}")
    
    try:
        test_single_todo_with_attachments(todo_url)
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()