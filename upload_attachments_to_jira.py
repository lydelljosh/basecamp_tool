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
    
    def update_issue_status(self, issue_key: str, status: str) -> bool:
        """Update the status of a Jira issue"""
        try:
            # First get available transitions for this issue
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
            response = self.session.get(url)
            
            if response.status_code != 200:
                print_error(f"Failed to get transitions for {issue_key}: {response.status_code}")
                return False
            
            transitions = response.json().get('transitions', [])
            
            # Find the transition to the desired status
            target_transition = None
            for transition in transitions:
                if transition['to']['name'].lower() == status.lower():
                    target_transition = transition
                    break
            
            if not target_transition:
                # List available transitions for debugging
                available = [t['to']['name'] for t in transitions]
                print_error(f"Status '{status}' not available for {issue_key}. Available: {available}")
                return False
            
            # Execute the transition
            transition_data = {
                "transition": {
                    "id": target_transition['id']
                }
            }
            
            response = self.session.post(url, json=transition_data)
            
            if response.status_code == 204:
                print_success(f"Updated {issue_key} status to '{status}'")
                return True
            else:
                print_error(f"Failed to update {issue_key} status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Exception updating {issue_key} status: {e}")
            return False

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
        """Extract Todo ID to Jira label mapping from CSV"""
        mapping = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    todo_id = row.get('Basecamp Todo ID', '').strip()
                    
                    # The Basecamp Todo ID itself is used as the Jira label
                    # So Todo ID 12345 maps to Jira label "12345"
                    if todo_id:
                        mapping[todo_id] = todo_id
                        
            print_success(f"Loaded {len(mapping)} Todo ID to Jira label mappings from CSV")
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
        for todo_id, jira_label in mapping.items():
            print_success(f"\nProcessing Todo ID {todo_id} (Jira label: {jira_label})")
            
            # Search for Jira issues with this label (same as Todo ID)
            issues = self.search_issues_by_label(jira_label)
            
            if not issues:
                print_error(f"No Jira issues found with label '{jira_label}' for Todo ID {todo_id}")
                continue
            
            if len(issues) > 1:
                print_error(f"Multiple issues found with label '{jira_label}': {[issue['key'] for issue in issues]}")
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

    def update_completed_todos(self, csv_path: str, target_status: str = "Done", dry_run: bool = False) -> bool:
        """Update Jira status for completed todos based on CSV"""
        
        if not self.test_connection():
            print_error("Cannot proceed - Jira connection failed")
            return False
        
        # Read CSV and find completed todos
        completed_todos = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    todo_id = row.get('Basecamp Todo ID', '').strip()
                    completed = row.get('Completed', '').strip().lower()
                    
                    # Check if todo is marked as completed
                    if todo_id and completed in ['true', '1', 'yes']:
                        completed_todos[todo_id] = todo_id  # Use Todo ID as Jira label
                        
            print_success(f"Found {len(completed_todos)} completed todos in CSV")
            
        except Exception as e:
            print_error(f"Failed to read CSV for completed todos: {e}")
            return False
        
        if not completed_todos:
            print_success("No completed todos found to update")
            return True
        
        total_updated = 0
        
        # Process each completed todo
        for todo_id, jira_label in completed_todos.items():
            print_success(f"\nProcessing completed Todo ID {todo_id} (Jira label: {jira_label})")
            
            # Search for Jira issues with this label
            issues = self.search_issues_by_label(jira_label)
            
            if not issues:
                print_error(f"No Jira issues found with label '{jira_label}' for completed Todo ID {todo_id}")
                continue
            
            if len(issues) > 1:
                print_error(f"Multiple issues found with label '{jira_label}': {[issue['key'] for issue in issues]}")
                print_error(f"Using first issue: {issues[0]['key']}")
            
            issue = issues[0]
            issue_key = issue['key']
            
            if dry_run:
                print_success(f"DRY RUN: Would update {issue_key} status to '{target_status}'")
                continue
            
            # Update the issue status
            if self.update_issue_status(issue_key, target_status):
                total_updated += 1
            else:
                print_error(f"Failed to update {issue_key} status")
        
        if dry_run:
            print_success(f"\nDRY RUN COMPLETE: Would update {len(completed_todos)} issues to '{target_status}'")
        else:
            print_success(f"\nSTATUS UPDATE COMPLETE:")
            print_success(f"Updated {total_updated}/{len(completed_todos)} issues to '{target_status}'")
        
        return True

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload attachments to Jira issues based on labels and Todo IDs")
    parser.add_argument('--csv', help='Path to todos_jira.csv file')
    parser.add_argument('--attachments', help='Path to attachments directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be uploaded without actually uploading')
    parser.add_argument('--test-connection', action='store_true', help='Test Jira connection and exit')
    parser.add_argument('--update-completed', action='store_true', help='Update status of completed todos in Jira')
    parser.add_argument('--target-status', default='Done', help='Target status for completed todos (default: Done)')
    
    args = parser.parse_args()
    
    try:
        uploader = JiraAttachmentUploader()
        
        if args.test_connection:
            if uploader.test_connection():
                print_success("Jira connection test passed!")
            else:
                print_error("Jira connection test failed!")
            return
        
        # Handle status update for completed todos
        if args.update_completed:
            if not args.csv:
                print_error("--csv argument is required for status update operations")
                return
            
            if not os.path.exists(args.csv):
                print_error(f"CSV file not found: {args.csv}")
                return
            
            success = uploader.update_completed_todos(args.csv, args.target_status, args.dry_run)
            
            if success:
                print_success("Status update process completed successfully!")
            else:
                print_error("Status update process failed!")
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