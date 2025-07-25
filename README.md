# 🧰 Basecamp Tool – Project To-dos & Attachments Extractor

This tool allows you to fetch **Basecamp 3 projects**, extract **to-do lists** with full details (assignees, attachments, comments), and **download all related files** into timestamped result folders for audit or offline review.

---

## 📦 Features

- ✅ Fetch all **active projects** in your account.
- ✅ Extract **To-do lists** (including title, notes, status, assignees, due dates).
- ✅ Include **full comment threads** with authors, timestamps, and content.
- ✅ Download **attachments** from both to-dos and comments.
- ✅ Output organized in `results/run_YYYYMMDD_HHMMSS/` for every execution.
- ✅ Modular structure – easy to extend or adapt.

---

## 📁 Folder Structure

```
basecamp_tool/
│
├── auth.py                    # Authentication loader from config.json
├── config.json                # 🔒 Contains your account and token info (add to .gitignore)
├── dump.py                    # Step 1: Fetch & dump projects (with todoset links)
├── fetch.py                   # Step 2: Extract todos, comments, attachments (metadata only)
├── download_attachments.py    # Step 3: Download all files into /results/
├── main.py                    # Master runner: executes dump → fetch → download
├── utils.py                   # Common print, sanitize, and helper functions
│
├── results/
│   └── run_20250725_173000/   # Timestamped output folder
│       ├── projects_dump.json     # Raw project + dock metadata
│       ├── todos_deep.json        # Enriched todos + comments + attachment metadata
│       └── attachments/           # Actual downloaded files
│
├── .gitignore                 # Ignores config.json, results/, etc.
└── README.md
```

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install requests
```

### 2. Create your `config.json`

```json
{
  "Account-ID": "YOUR_ACCOUNT_ID",
  "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}
```

> ⚠️ Keep this file **secure** and **never commit** it. Add it to your `.gitignore`.

---

## ▶️ How to Run

From the root folder, simply run:

```bash
python main.py
```

This will:

1. Save project metadata → `results/run_*/projects_dump.json`
2. Save enriched todos + comments → `results/run_*/todos_deep.json`
3. Download attachments to → `results/run_*/attachments/...`

---

## 📑 JSON Outputs

### `projects_dump.json`
Raw project list with dock sections, including `todoset` URLs.

### `todos_deep.json`
Each project → todolist → todos (with comments & attachments):

```json
{
  "Project A": {
    "Development": [
      {
        "title": "Fix Login Bug",
        "created_by": "John Doe",
        "assignees": ["Dev Team"],
        "completed": false,
        "attachments": [...],
        "comments": [...]
      }
    ]
  }
}
```

---

## 📁 Attachments Folder

Downloaded files will be stored by:

```
attachments/<Project>/<Todolist>/<Todo Title>/<filename>
```

---

## 🧼 To Do / Suggestions

- [ ] Clean HTML from comment content (`utils/html_cleaner.py`)
- [ ] Export report to CSV/Excel
- [ ] Add CLI flags for selective fetch/download
- [ ] Support HTML summary output

---