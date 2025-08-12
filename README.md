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
├── utils/
│   ├── basecamp_api.py      # API wrappers with retry logic
│   ├── utils.py             # Utility functions (logging, text cleaning, constants)
│   └── helpers.py           # URL parsing helpers
├── config.json              # OAuth tokens and configuration
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
  "include_completed": false,
  "username": "your-basecamp-email@example.com",
  "password": "your-basecamp-password"
}
```

**Configuration Options:**
- `include_completed`: Set to `true` to fetch archived/completed todolists and todos (default: `false`)
- `username` & `password`: Required for session-based attachment downloads (used only for file authentication, not stored elsewhere)

5. Get your OAuth tokens:
```bash
python -c "from auth import get_token; get_token()"
```
This will:
- Open your browser for Basecamp authentication
- Automatically save your access token and account ID to `config.json`

---

## 🚀 Usage

### Basic Export
```bash
python main.py
```

This runs the complete workflow:
1. **Refresh token** - Automatically refreshes expired OAuth tokens
2. **Dump projects** - Fetches all project metadata
3. **Fetch todos** - Retrieves todos with group organization and details (includes completed items if configured)
4. **Export to Jira CSV** - Creates a formatted CSV file for import
5. **Download attachments** - Downloads bc-attachments, images, and files using session authentication

### Output Location
Files are saved in timestamped folders: `results/run_YYYYMMDD_HHMMSS/`

### Manual Token Refresh
If you need to manually refresh your OAuth token:
```bash
python refresh_token.py
```

### Authentication Setup
If you need to re-authenticate or set up for the first time:
```bash
python -c "from auth import get_token; get_token()"
```

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

### `attachments/`
Downloaded attachment files organized by todo ID:
- `todo_{id}/` - Individual folders for each todo's attachments
- Files include bc-attachments, images, and main todo attachments
- Preserves original filenames where possible
- Source tracking in CSV shows origin (description, comment, main attachment)

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