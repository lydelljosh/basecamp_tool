import requests
from utils.utils import print_error

BASE_URL = "https://3.basecampapi.com"

def fetch_todo_detail(account_id: str, bucket_id: str, todo_id: int, headers: dict) -> dict | None:
    try:
        url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/todos/{todo_id}.json"
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print_error(f"[TODO FETCH FAIL] {todo_id}: {e}")
        return None

def fetch_comments(account_id: str, bucket_id: str, todo_id: int, headers: dict) -> list[dict]:
    try:
        url = f"{BASE_URL}/{account_id}/buckets/{bucket_id}/recordings/{todo_id}/comments.json"
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print_error(f"[COMMENTS FETCH FAIL] {todo_id}: {e}")
        return []   