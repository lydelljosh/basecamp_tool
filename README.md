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
- ✅ **Attachment support** - Downloads and links file attachments
- ✅ **Comprehensive logging** - Detailed progress tracking and error reporting

---

## 🆕 Recent Improvements

- ✅ **Completed todos support** - Added configurable option to include archived/completed todolists and todos
- ✅ **Token refresh mechanism** - Automatic refresh of expired access tokens using refresh tokens
- ✅ **Enhanced error handling** - Better handling of 404 errors for completed todos endpoints
- ✅ **Improved run directory creation** - Creates output directory even when projects fetch fails
- ✅ **Added group support** - Now properly fetches and organizes todos within grouped lists
- ✅ **Code consolidation** - Removed duplicate code and centralized utilities

---

## 📂 Project Structure

```bash
basecamp_tool/
├── main.py                  # Entry script to fetch and export data
├── auth.py                  # OAuth authentication flow
├── dump.py                  # Dumps all project metadata
├── fetch.py                 # Fetches todo and list data with group support
├── jira_formatter.py        # Formats data into Jira-compatible CSV
├── download_attachments.py  # Downloads file attachments
├── link_exporter.py         # Link and message export utilities
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
        └── todos_jira.csv
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
  "include_completed": false
}
```

**Configuration Options:**
- `include_completed`: Set to `true` to fetch archived/completed todolists and todos (default: `false`)

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
1. **Dump projects** - Fetches all project metadata
2. **Fetch todos** - Retrieves todos with group organization and details (includes completed items if configured)
3. **Export to Jira CSV** - Creates a formatted CSV file for import

### Output Location
Files are saved in timestamped folders: `results/run_YYYYMMDD_HHMMSS/`

### Authentication Setup
If you need to re-authenticate or set up for the first time:
```bash
python auth.py
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
- App URL (link back to Basecamp)

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

**"525 Server Error"**: The tool now automatically retries these temporary Basecamp server errors.

**"Missing Account-ID"**: Run the authentication setup again:
```bash
python -c "from auth import get_token; get_token()"
```

**Empty or missing todos**: Verify your Basecamp account has access to the projects and todo lists.

**Import issues with special characters**: The tool automatically cleans Unicode characters to ASCII equivalents for better Jira compatibility.

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