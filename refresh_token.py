#!/usr/bin/env python3
"""
Simple script to refresh the OAuth access token when it expires.
Run this when you get 401 Unauthorized errors.
"""

from auth import refresh_access_token
from utils.utils import load_config, save_config, print_success, print_error

def main():
    config = load_config()
    
    refresh_token = config.get("refresh_token")
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    
    if not refresh_token:
        print_error("No refresh_token found in config.json. You need to run the full OAuth flow again.")
        print("Run: python -c \"from auth import get_token; get_token()\"")
        return
    
    if not client_id or not client_secret:
        print_error("Missing client_id or client_secret in config.json")
        return
    
    print("Refreshing access token...")
    token_data = refresh_access_token(refresh_token, client_id, client_secret)
    
    if not token_data:
        print_error("Failed to refresh token. You may need to re-authenticate.")
        print("Run: python -c \"from auth import get_token; get_token()\"")
        return
    
    new_access_token = token_data.get("access_token")
    new_refresh_token = token_data.get("refresh_token")
    
    if not new_access_token:
        print_error("No access_token in refresh response")
        return
    
    # Update config with new tokens
    config["access_token"] = new_access_token
    if new_refresh_token:  # Some OAuth providers rotate refresh tokens
        config["refresh_token"] = new_refresh_token
    
    save_config(config)
    print_success("Access token refreshed successfully!")
    print("You can now run main.py again.")

if __name__ == "__main__":
    main()