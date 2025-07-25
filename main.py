# main.py
from dump import dump_projects
from fetch import fetch_all_todos_from_dump
from download_attachments import download_all_attachments

def main():
    # 1) Dump all projects (with dock)
    run_dir, projects_path, _ = dump_projects(output_root="results")
    if not run_dir:
        return

    # 2) Fetch deep todos (lists, todos, comments, attachments meta)
    todos_deep_path = fetch_all_todos_from_dump(projects_path, run_dir)

    # 3) (Optional) Download all attachments
    #    Comment this out if you don't want to auto-download each run
    download_all_attachments(todos_deep_path, output_root="results")

if __name__ == "__main__":
    main()
