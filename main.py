from dump import dump_projects
from fetch import fetch_all_todos_from_dump
from jira_formatter import format_for_jira_live
from auth import refresh_access_token
from utils.utils import load_config, save_config, print_success, print_error

def ensure_valid_token():
    """Ensure we have a valid access token by refreshing it."""
    config = load_config()
    
    refresh_token = config.get("refresh_token")
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    
    if not refresh_token or not client_id or not client_secret:
        print_error("Missing refresh_token, client_id, or client_secret in config.json")
        print_error("Please run: python -c \"from auth import get_token; get_token()\"")
        return False
    
    print_success("Refreshing access token to ensure it's valid...")
    token_data = refresh_access_token(refresh_token, client_id, client_secret)
    
    if not token_data:
        print_error("Failed to refresh token. Please re-authenticate:")
        print_error("Run: python -c \"from auth import get_token; get_token()\"")
        return False
    
    new_access_token = token_data.get("access_token")
    new_refresh_token = token_data.get("refresh_token")
    
    if not new_access_token:
        print_error("No access_token in refresh response")
        return False
    
    # Update config with new tokens
    config["access_token"] = new_access_token
    if new_refresh_token:  # Some OAuth providers rotate refresh tokens
        config["refresh_token"] = new_refresh_token
    
    save_config(config)
    print_success("✅ Access token refreshed and saved to config.json")
    return True

def main():
    # Step 0 - Ensure we have a valid access token
    if not ensure_valid_token():
        print_error("Cannot proceed without valid access token. Exiting.")
        return
    
    # Step 1 - Fetch projects
    run_dir, projects_path, projects = dump_projects(output_root="results")

    # Step 2 - Fetch todos metadata (with URLs and IDs)
    todos_path, todos = fetch_all_todos_from_dump(projects, run_dir)

    # Step 3 - Export live to Jira CSV (fetches comments inline) + Download attachments
    format_for_jira_live(todos, run_dir, download_attachments=True)

if __name__ == "__main__":
    main()