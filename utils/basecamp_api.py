import requests
import re
import time
from utils.utils import print_error, BASE_URL

def fetch_todo_detail(account_id: str, bucket_id: str, todo_id: int, headers: dict) -> dict | None:
    url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todos/{todo_id}.json"
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=30)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [525, 502, 503, 504] and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"[RETRY] {todo_id}: Server error {e.response.status_code}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                print_error(f"[TODO FETCH FAIL] {todo_id}: {e}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"[RETRY] {todo_id}: {e}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                print_error(f"[TODO FETCH FAIL] {todo_id}: {e}")
                return None
    
    return None

def fetch_comments(account_id: str, bucket_id: str, item_id: int, headers: dict) -> list[dict]:
    all_comments = []
    base_url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/recordings/{item_id}/comments.json"
    url = base_url

    while url:
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            all_comments.extend(res.json())

            # Handle pagination using the Link header
            link_header = res.headers.get("Link", "")
            match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
            url = match.group(1) if match else None
        except Exception as e:
            print_error(f"[COMMENTS FETCH FAIL] {item_id}: {e}")
            break

    return all_comments
    
def fetch_message_detail(account_id: str, bucket_id: str, message_id: int, headers: dict) -> dict | None:
    try:
        url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/messages/{message_id}.json"
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print_error(f"[MESSAGE FETCH FAIL] {message_id}: {e}")
        return None