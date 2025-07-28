# Basecamp Tool

This Python-based utility extracts To-dos, comments, and attachments from Basecamp 3 projects and exports the data into a structured CSV format (Jira-compatible). It supports retrieving:

- All projects and their todo lists
- Full todo details including:
  - Description
  - Assignees
  - Completion status
  - Comments (cleanly formatted with names and timestamps)
  - Attachments (with direct links)

---

## 🔧 Features

- ✅ Retrieves full To-do details per list
- ✅ Fetches comments with readable formatting
- ✅ Downloads and links attachments
- ✅ Jira-ready CSV output
- ✅ Custom configuration via `config.json`
- 🧪 Handles most project formats

---

## 🚫 Known Limitations

- ❌ **Grouped To-do Lists (e.g. sections like "In Progress", "Bugs") are not accessible** with standard OAuth tokens.
  - These require **elevated privileges (admin access)** to access the `recordings.json` or `todosets.json` endpoints where group data is exposed.

---

## 📂 Project Structure

```bash
basecamp_tool/
├── main.py                  # Entry script to fetch and export data
├── dump.py                  # Dumps all project metadata
├── fetch.py                 # Fetches todo and list data
├── jira_formatter.py        # Formats data into a Jira-style CSV
├── download_attachments.py  # Optional: Downloads attached files (WIP)
├── utils/
│   ├── basecamp_api.py      # API wrappers
│   ├── utils.py             # Utility functions (save/load, logging)
│   └── __init__.py
├── config.json              # User tokens and flags
├── .gitignore               # Git exclusions (includes .DS_Store, /results/)
└── results/
    └── run_*/               # Timestamped folders with outputs
```

---

## 📝 Setup

1. Clone the repository
2. Set up a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Fill in your `config.json` with the following:

```json
{
  "client_id": "your-client-id",
  "client_secret": "your-secret",
  "redirect_uri": "http://localhost:8888/callback",
  "access_token": "your-oauth-access-token",
  "refresh_token": "",
  "account_id": 12345678,
  "project_filter": "",
  "include_completed": false
}
```

---

## 🚀 Usage

```bash
python main.py
```

- This runs the full dump → fetch → export flow
- Output files will be saved in a new folder inside `results/` with timestamped naming

---

## 🗂 Output

Each run generates:

- `projects_dump.json`: Project metadata
- `todos_deep.json`: Detailed todos + metadata
- `todos_jira.csv`: Final CSV, ready for Jira import

---

## ❗ Admin Access Requirement

To support **grouped to-do list** structures (e.g. lists with sections like "Backlog", "Completed", etc.), this script **requires an admin token** with elevated permissions. Without it, only top-level (ungrouped) todo lists are retrievable.

---

## ✅ Git Ignore

This repo excludes:
- `.DS_Store`
- `.venv`
- `__pycache__`
- `results/` output directory

---

## 📌 Notes

- This repo is generalized and **does not reference any company or internal Basecamp account**
- All code is designed to be reusable for any Basecamp 3 instance with OAuth access

---

## 📄 License

MIT — Free to use and modify.