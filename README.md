# Basecamp Tool

This Python-based utility extracts To-dos, comments, and attachments from Basecamp 3 projects and exports the data into a structured CSV format (Jira-compatible). It supports retrieving:

- All projects and their todo lists (including grouped lists)
- Full todo details including:
  - Description with HTML content parsed to clean text
  - Assignees and creators
  - Completion status and due dates
  - Comments (cleanly formatted with names, emails, and timestamps)
  - Attachments (with direct download links)
  - Group organization within todo lists

---

## 🔧 Features

- ✅ **Group-aware todo fetching** - Handles grouped todo lists with proper organization
- ✅ **Completed todo/todolist support** - Optional fetching of archived/completed todolists and todos
- ✅ **Token refresh handling** - Automatic access token refresh using refresh tokens
- ✅ **Robust error handling** - Automatic retries with exponential backoff for server errors (525, 502, 503, 504)
- ✅ **Special character cleaning** - Converts Unicode characters to ASCII-compatible equivalents
- ✅ **HTML content parsing** - Cleans HTML descriptions and comments to readable text
- ✅ **Jira-ready CSV export** - Properly formatted for Jira import
- ✅ **OAuth authentication flow** - Automated browser-based authentication setup
- ✅ **Session-based attachment downloads** - Downloads bc-attachments, images, and files using authenticated sessions
- ✅ **Automatic token refresh** - Automatically refreshes expired OAuth tokens at startup
- ✅ **Cross-platform compatibility** - Windows and macOS support with platform-specific fixes
- ✅ **Comprehensive logging** - Detailed progress tracking and error reporting
- ✅ **Attachment mapping** - Direct todo ID mapping for reliable attachment correlation
- ✅ **Enhanced error handling** - Improved validation and graceful error recovery
- ✅ **Configuration validation** - Validates required fields and warns about missing credentials
- ✅ **Jira API integration** - Automated attachment uploads and status management via Jira REST API
- ✅ **Status synchronization** - Update Jira issue status based on Basecamp completion status

---

## 🆕 Recent Improvements

### Attachment Download System
- ✅ **Session authentication** - Direct email/password login for downloading authenticated attachments
- ✅ **Comprehensive attachment detection** - Finds bc-attachment elements, images, and main attachments in todos and comments
- ✅ **Organized file structure** - Downloads to `results/run_*/attachments/todo_*/` with clear naming
- ✅ **Windows compatibility** - Fixed path handling and encoding issues for Windows systems

### Authentication Enhancements  
- ✅ **Automatic token refresh at startup** - Prevents 401 errors by refreshing tokens before API calls
- ✅ **Cross-environment sync** - Updates config.json automatically to keep macOS/Windows tokens in sync
- ✅ **Standalone refresh utility** - Added `refresh_token.py` for manual token refresh
- ✅ **Enhanced error messaging** - Clear instructions for re-authentication when refresh fails

### Core Improvements
- ✅ **Completed todos support** - Added configurable option to include archived/completed todolists and todos
- ✅ **Enhanced error handling** - Better handling of 404 errors for completed todos endpoints
- ✅ **Improved run directory creation** - Creates output directory even when projects fetch fails
- ✅ **Added group support** - Now properly fetches and organizes todos within grouped lists
- ✅ **Debug logging** - Comprehensive attachment detection and processing logs
- ✅ **Basecamp Todo ID mapping** - Each CSV row includes unique todo ID for attachment correlation
- ✅ **Robust error handling** - Fixed bare except clauses and added detailed error messages
- ✅ **Configuration validation** - Validates required config fields at startup

### Jira Integration
- ✅ **Automated attachment uploads** - Upload files from todo folders to Jira issues via API
- ✅ **Label-based mapping** - Use Basecamp Todo IDs as Jira labels for precise issue targeting
- ✅ **Status synchronization** - Automatically update Jira issue status for completed todos
- ✅ **Dry-run capabilities** - Preview operations before executing for safe testing
- ✅ **Flexible status mapping** - Support custom Jira status transitions (Done, Closed, etc.)

---

## 📂 Project Structure

```bash
basecamp_tool/
├── main.py                  # Entry script with automatic token refresh
├── auth.py                  # OAuth authentication flow
├── session_auth.py          # Session-based authentication for file downloads
├── refresh_token.py         # Standalone token refresh utility
├── dump.py                  # Dumps all project metadata
├── fetch.py                 # Fetches todo and list data with group support
├── jira_formatter.py        # Formats data into Jira-compatible CSV with attachment downloads
├── upload_attachments_to_jira.py  # Jira API integration for attachments and status updates
├── utils/
│   ├── basecamp_api.py      # API wrappers with retry logic
│   ├── utils.py             # Utility functions (logging, text cleaning, constants)
│   └── helpers.py           # URL parsing helpers
├── config.json              # OAuth tokens and Jira API configuration
├── .gitignore               # Git exclusions
└── results/
    └── run_YYYYMMDD_HHMMSS/ # Timestamped output folders
        ├── projects_dump.json
        ├── todos_deep.json
        ├── todos_jira.csv
        └── attachments/     # Downloaded attachment files
            └── todo_*/      # Organized by todo ID
```

---

## 📝 Setup

### Prerequisites
- Python 3.8+
- Basecamp 3 account with API access

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd basecamp_tool
```

2. Install required dependencies:
```bash
pip install requests beautifulsoup4
```

3. Create your Basecamp 3 app:
   - Go to https://launchpad.37signals.com/integrations
   - Create a new app to get your `client_id` and `client_secret`

4. Set up authentication - Create `config.json`:

```json
{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "redirect_uri": "http://localhost:8888/callback",
  "include_completed": true,
  "username": "your-basecamp-email@example.com",
  "password": "your-basecamp-password",
  "jira": {
    "url": "https://your-domain.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "YOUR_JIRA_API_TOKEN",
    "project_key": "YOUR_PROJECT_KEY",
    "project_name": "Your Project Name",
    "default_issue_type": "Bug",
    "default_priority": "Medium",
    "test_mode": true,
    "test_limit": 5
  }
}
```

**Configuration Options:**
- `include_completed`: Set to `false` to exclude archived/completed todolists and todos (default: `true`)
- `username` & `password`: Required for session-based attachment downloads (used only for file authentication, not stored elsewhere)
- `jira`: Jira Cloud API configuration for automated integration (optional)

5. Get your OAuth tokens:
```bash
python -c "from auth import get_token; get_token()"
```
This will:
- Open your browser for Basecamp authentication
- Automatically save your access token and account ID to `config.json`

### Jira Setup (Optional)

For automated Jira integration, you'll need:

1. **Jira Cloud instance** with admin access
2. **API Token**: Generate at https://id.atlassian.com/manage-profile/security/api-tokens
3. **Project Key**: The key of your target Jira project (e.g., "BMT")

**Jira Configuration Steps:**
1. Add your Jira details to the `jira` section in `config.json`
2. Create a test project or use existing project
3. During CSV import, map `Basecamp Todo ID` column to Labels field
4. This enables the automated attachment and status sync features

---

## 🚀 Usage

### Basic Export
```bash
python main.py
```

This runs the complete workflow:
1. **Validate configuration** - Checks required fields and warns about missing credentials
2. **Refresh token** - Automatically refreshes expired OAuth tokens
3. **Dump projects** - Fetches all project metadata
4. **Fetch todos** - Retrieves todos with group organization and details (includes completed items if configured)
5. **Export to Jira CSV** - Creates a formatted CSV file with Basecamp Todo IDs for import
6. **Download attachments** - Downloads bc-attachments, images, and files using session authentication

### Jira Integration Commands

After running the basic export, use these commands for Jira automation:

#### **Test Jira API Connection**
```bash
python upload_attachments_to_jira.py --test-connection
```

#### **Upload Attachments to Jira Issues**
```bash
# Dry run first (recommended)
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --attachments results/run_*/attachments --dry-run

# Actual upload
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --attachments results/run_*/attachments
```

#### **Update Status for Completed Todos**
```bash
# Test what would be updated
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --update-completed --dry-run

# Update completed todos to "Done" status
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --update-completed

# Update to custom status (e.g., "Closed")
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --update-completed --target-status "Closed"
```

### Manual Token Management
```bash
# Manual token refresh
python refresh_token.py

# Re-authenticate completely
python -c "from auth import get_token; get_token()"
```

### Complete Workflow Example

**1. Export data from Basecamp:**
```bash
python main.py
```

**2. Import CSV to Jira (manual step):**
- Use the generated `todos_jira.csv` file
- Import via Jira's CSV import feature
- Ensure Basecamp Todo IDs are added as labels during import

**3. Upload attachments automatically:**
```bash
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --attachments results/run_*/attachments --dry-run
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --attachments results/run_*/attachments
```

**4. Update completed todo status:**
```bash
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --update-completed --dry-run
python upload_attachments_to_jira.py --csv results/run_*/todos_jira.csv --update-completed
```

### Output Location
Files are saved in timestamped folders: `results/run_YYYYMMDD_HHMMSS/`

---

## 🗂 Output Files

Each run generates timestamped files in `results/run_YYYYMMDD_HHMMSS/`:

### `projects_dump.json`
Raw project metadata from Basecamp API

### `todos_deep.json`  
Comprehensive todo data including:
- Todo details (title, description, assignees, due dates)
- Group organization and hierarchy
- Attachment metadata
- Creator and completion information
- Archived/completed todolists and todos (if configured)

### `todos_jira.csv`
Jira-compatible CSV with columns:
- Project, List, Group, Todo Title
- Description (HTML cleaned to text)
- Assignees, Created By, Due Date, Completed
- Comments (formatted with author and timestamp)
- Attachments (with download URLs)
- Downloaded Files (local paths of downloaded attachments)
- App URL (link back to Basecamp)
- **Basecamp Todo ID** (for reliable attachment mapping)

### `attachments/`
Downloaded attachment files organized by todo ID:
- `todo_{id}/` - Individual folders for each todo's attachments
- Files include bc-attachments, images, and main todo attachments
- Preserves original filenames where possible
- Source tracking in CSV shows origin (description, comment, main attachment)
- **Direct mapping** via Basecamp Todo ID enables reliable import to external systems

---

## 🔧 Error Handling

The tool includes robust error handling:

- **Automatic retries** - 3 attempts with exponential backoff for server errors (525, 502, 503, 504)
- **Request timeouts** - 30-second timeout prevents hanging
- **Detailed logging** - Progress tracking and error reporting
- **Graceful degradation** - Continues processing other todos if individual requests fail

---

## 🚨 Troubleshooting

### Common Issues

**"401 Unauthorized" errors**: The OAuth token has expired. The script automatically refreshes tokens, but if it fails:
```bash
python refresh_token.py
```
Or re-authenticate completely:
```bash
python -c "from auth import get_token; get_token()"
```

**"0 attachment files downloaded"**: Check that:
- Username and password are correct in `config.json` 
- Todos actually contain attachments (bc-attachment elements, images, or main attachments)
- Session authentication succeeded (look for "Session authentication successful!" message)

**"525 Server Error"**: The tool automatically retries these temporary Basecamp server errors.

**"Missing Account-ID"**: Run the authentication setup again:
```bash
python -c "from auth import get_token; get_token()"
```

**Empty or missing todos**: Verify your Basecamp account has access to the projects and todo lists.

**Windows path/encoding issues**: The tool includes Windows-specific fixes, but ensure your Python installation supports UTF-8.

**Cross-platform token sync**: Tokens are automatically refreshed and synced across different machines running the script.

### Jira Integration Issues

**"Failed to connect to Jira API"**: Check your Jira configuration:
```bash
python upload_attachments_to_jira.py --test-connection
```
- Verify API token is correct and not expired
- Ensure email address matches your Jira account
- Check Jira URL format (https://domain.atlassian.net)

**"No Jira issues found with label"**: The label mapping failed:
- Ensure you imported CSV with Basecamp Todo ID as labels
- Check that labels were properly created during Jira import
- Verify project key matches your target project

**"Status not available"**: The target status doesn't exist or isn't accessible:
- Check available status transitions in your Jira workflow
- Use `--target-status "Status Name"` to specify exact status name
- Ensure your account has permission to transition issues

**"Multiple issues found with label"**: One Todo ID matches multiple Jira issues:
- Check for duplicate labels in your Jira project
- The script will use the first match found

---

## 🔒 Security Considerations

### Configuration Security
- **config.json contains sensitive data** - OAuth tokens, account IDs, session credentials, and Jira API tokens
- **Already gitignored** - The file is excluded from version control by default
- **Keep credentials private** - Never commit config.json or share tokens publicly
- **Regular token refresh** - OAuth tokens are automatically refreshed to limit exposure
- **Jira API token security** - Store API tokens securely, rotate regularly

### Best Practices
- ✅ **Use environment variables** for CI/CD deployments instead of config.json
- ✅ **Limit account access** - Use dedicated Basecamp accounts with minimal required permissions
- ✅ **Regular credential rotation** - Periodically regenerate API tokens and passwords
- ✅ **Secure storage** - Store config.json in encrypted directories on shared systems

### Authentication Methods
- **OAuth tokens** - Primary authentication method for Basecamp API, automatically managed
- **Session credentials** - Username/password for attachment downloads only
- **Jira API tokens** - For Jira Cloud integration, generate at Atlassian Account Security
- **API tokens** - All tokens stored securely in config.json, refresh when possible

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📌 Notes

- This tool is generalized and does not reference any specific company or internal accounts
- Designed to work with any Basecamp 3 instance with proper OAuth access
- All sensitive data (tokens, account IDs) should be kept in `config.json` and never committed

---

## 📄 License

MIT License - Free to use and modify.