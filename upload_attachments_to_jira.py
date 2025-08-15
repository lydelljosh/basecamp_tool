#!/usr/bin/env python3
"""
Automated Jira attachment uploader using labels and Todo IDs.
Uploads attachments from todo folders to corresponding Jira issues based on labels.
"""

import os
import csv
import json
import requests
import base64
from typing import Dict, List, Optional
from utils.utils import load_config, print_success, print_error

class JiraAttachmentUploader:
    """Upload attachments to Jira issues based on labels and Todo IDs"""
    
    def __init__(self):
        self.config = load_config()
        self.jira_config = self.config.get('jira', {})
        
        if not self.jira_config:
            raise ValueError("No Jira configuration found in config.json")
        
        self.base_url = self.jira_config.get('url', '').rstrip('/')
        self.email = self.jira_config.get('email')
        self.api_token = self.jira_config.get('api_token')
        self.project_key = self.jira_config.get('project_key')
        
        if not all([self.base_url, self.email, self.api_token, self.project_key]):
            raise ValueError("Missing required Jira configuration: url, email, api_token, project_key")
        
        # Create authentication header
        auth_string = f"{self.email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {auth_b64}',
            'Accept': 'application/json'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self) -> bool:
        """Test the Jira API connection"""
        try:
            print_success("Testing Jira API connection...")
            
            url = f"{self.base_url}/rest/api/3/myself"
            response = self.session.get(url)
            
            if response.status_code == 200:
                user_data = response.json()
                print_success(f"Connected as: {user_data.get('displayName', 'Unknown')}")
                return True
            else:
                print_error(f"Connection failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Connection test failed: {e}")
            return False
    
    def search_issues_by_label(self, label: str) -> List[Dict]:
        """Search for Jira issues by label"""
        try:
            # JQL query to find issues by label in the project
            jql = f'project = {self.project_key} AND labels = "{label}"'
            
            url = f"{self.base_url}/rest/api/3/search"
            params = {
                'jql': jql,
                'fields': 'key,summary,labels',
                'maxResults': 100
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                result = response.json()
                issues = result.get('issues', [])
                print_success(f"Found {len(issues)} issues with label '{label}'")
                return issues
            else:
                print_error(f"Failed to search issues: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print_error(f"Failed to search issues by label '{label}': {e}")
            return []
    
    def upload_attachment(self, issue_key: str, file_path: str) -> bool:
        """Upload a single attachment to a Jira issue"""
        try:
            if not os.path.exists(file_path):
                print_error(f"File not found: {file_path}")
                return False
            
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/attachments"
            
            # Remove Content-Type header for file upload and add required header
            headers = {
                'Authorization': self.headers['Authorization'],
                'X-Atlassian-Token': 'no-check'  # Required for file uploads
            }
            
            filename = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                response = self.session.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                attachments = response.json()
                if attachments:
                    print_success(f"Uploaded: {filename} to {issue_key}")
                    return True
                else:
                    print_error(f"Upload response empty for {filename}")
                    return False
            else:
                print_error(f"Failed to upload {filename}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Exception uploading {file_path}: {e}")
            return False
    
    def upload_attachments_for_issue(self, issue_key: str, todo_id: str, attachments_dir: str) -> int:
        """Upload all attachments for a specific issue based on Todo ID"""
        todo_folder = os.path.join(attachments_dir, f"todo_{todo_id}")
        
        if not os.path.exists(todo_folder):
            print_error(f"No attachment folder found: {todo_folder}")
            return 0
        
        if not os.path.isdir(todo_folder):
            print_error(f"Path exists but is not a directory: {todo_folder}")
            return 0
        
        uploaded_count = 0
        files = [f for f in os.listdir(todo_folder) if os.path.isfile(os.path.join(todo_folder, f))]
        
        if not files:
            print_success(f"No files to upload in {todo_folder}")
            return 0
        
        print_success(f"Uploading {len(files)} files from {todo_folder} to {issue_key}")
        
        for filename in files:
            file_path = os.path.join(todo_folder, filename)
            if self.upload_attachment(issue_key, file_path):
                uploaded_count += 1
            else:
                print_error(f"Failed to upload {filename}")
        
        print_success(f"Uploaded {uploaded_count}/{len(files)} files to {issue_key}")
        return uploaded_count
    
    def get_todo_label_mapping(self, csv_path: str) -> Dict[str, str]:
        """Extract Todo ID to todolist ID (label) mapping from CSV"""
        mapping = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    todo_id = row.get('Basecamp Todo ID', '').strip()
                    
                    # You mentioned todolist ID = jira label
                    # We need to extract todolist ID from the CSV data
                    # This might be in the URL or we need to add it to the CSV
                    
                    app_url = row.get('App URL', '').strip()
                    if app_url and todo_id:
                        # Extract todolist ID from Basecamp URL
                        # URL format: https://3.basecamp.com/ACCOUNT/buckets/BUCKET/todolists/TODOLIST_ID/todos/TODO_ID
                        try:
                            parts = app_url.split('/todolists/')
                            if len(parts) > 1:
                                todolist_id = parts[1].split('/')[0]
                                mapping[todo_id] = todolist_id
                            else:
                                print_error(f"Could not extract todolist ID from URL: {app_url}")
                        except Exception as e:
                            print_error(f"Failed to parse URL for todo {todo_id}: {e}")
                        
            print_success(f"Loaded {len(mapping)} Todo ID to Todolist ID (label) mappings from CSV")
            return mapping
            
        except Exception as e:
            print_error(f"Failed to read CSV mapping: {e}")
            return {}
    
    def upload_all_attachments(self, csv_path: str, attachments_dir: str, dry_run: bool = False) -> bool:
        """Main function to upload all attachments based on CSV and labels"""
        
        if not self.test_connection():
            print_error("Cannot proceed - Jira connection failed")
            return False
        
        # Get Todo ID to label mapping from CSV
        mapping = self.get_todo_label_mapping(csv_path)
        if not mapping:
            print_error("No valid Todo ID mappings found")
            return False
        
        total_uploaded = 0
        total_issues_processed = 0
        
        # Process each Todo ID
        for todo_id, todolist_id in mapping.items():
            print_success(f"\nProcessing Todo ID {todo_id} (todolist ID/label: {todolist_id})")
            
            # Search for Jira issues with this label (todolist ID)
            issues = self.search_issues_by_label(todolist_id)
            
            if not issues:
                print_error(f"No Jira issues found with label '{todolist_id}' for Todo ID {todo_id}")
                continue
            
            if len(issues) > 1:
                print_error(f"Multiple issues found with label '{todolist_id}': {[issue['key'] for issue in issues]}")
                print_error(f"Using first issue: {issues[0]['key']}")
            
            issue = issues[0]
            issue_key = issue['key']
            
            if dry_run:
                print_success(f"DRY RUN: Would upload attachments from todo_{todo_id} to {issue_key}")
                continue
            
            # Upload attachments for this issue
            uploaded_count = self.upload_attachments_for_issue(issue_key, todo_id, attachments_dir)
            total_uploaded += uploaded_count
            total_issues_processed += 1
        
        if dry_run:
            print_success(f"\nDRY RUN COMPLETE: Would process {len(mapping)} todos")
        else:
            print_success(f"\nUPLOAD COMPLETE:")
            print_success(f"Processed {total_issues_processed} Jira issues")
            print_success(f"Uploaded {total_uploaded} attachment files")
        
        return True

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload attachments to Jira issues based on labels and Todo IDs")
    parser.add_argument('--csv', help='Path to todos_jira.csv file')
    parser.add_argument('--attachments', help='Path to attachments directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be uploaded without actually uploading')
    parser.add_argument('--test-connection', action='store_true', help='Test Jira connection and exit')
    
    args = parser.parse_args()
    
    try:
        uploader = JiraAttachmentUploader()
        
        if args.test_connection:
            if uploader.test_connection():
                print_success("Jira connection test passed!")
            else:
                print_error("Jira connection test failed!")
            return
        
        # Validate required arguments for upload operations
        if not args.csv:
            print_error("--csv argument is required for upload operations")
            return
        
        if not args.attachments:
            print_error("--attachments argument is required for upload operations")
            return
        
        if not os.path.exists(args.csv):
            print_error(f"CSV file not found: {args.csv}")
            return
        
        if not os.path.exists(args.attachments):
            print_error(f"Attachments directory not found: {args.attachments}")
            return
        
        success = uploader.upload_all_attachments(args.csv, args.attachments, args.dry_run)
        
        if success:
            print_success("Attachment upload process completed successfully!")
        else:
            print_error("Attachment upload process failed!")
            
    except Exception as e:
        print_error(f"Failed to initialize uploader: {e}")
        print_error("Please check your Jira configuration in config.json")

if __name__ == "__main__":
    main()