# dump.py
import os
import json
import requests
from datetime import datetime
from auth import get_auth_headers
from utils.utils import print_success, print_error, BASE_URL

def dump_projects(output_root: str = "results") -> tuple[str, str, list]:
    """
    Fetch all projects (with dock) and save to results/run_{ts}/projects_dump.json.
    Returns: (run_dir, projects_json_path, projects_list)
    """
    headers = get_auth_headers()
    account_id = headers.get("Account-ID")
    if not account_id:
        raise RuntimeError("Account-ID missing in headers. Check config.json/auth.py")

    projects_url = f"{BASE_URL}/{account_id}/projects.json"

    # Always create run directory first, even if projects fetch fails
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(output_root, f"run_{ts}")
    os.makedirs(run_dir, exist_ok=True)

    try:
        resp = requests.get(projects_url, headers=headers)
        resp.raise_for_status()
        projects = resp.json()
        if not isinstance(projects, list):
            raise RuntimeError("Unexpected response for projects.json (not a list).")
    except Exception as e:
        print_error(f"Failed to fetch projects: {e}")
        return run_dir, "", []

    projects_path = os.path.join(run_dir, "projects_dump.json")
    with open(projects_path, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)

    print_success(f"Saved {len(projects)} projects to {projects_path}")
    return run_dir, projects_path, projects
