from dump import dump_projects
from fetch import fetch_all_todos_from_dump
from jira_formatter import format_for_jira_live

def main():
    # Step 1 - Fetch projects
    run_dir, projects_path, projects = dump_projects(output_root="results")

    # Step 2 - Fetch todos metadata (with URLs and IDs)
    todos_path, todos = fetch_all_todos_from_dump(projects, run_dir)

    # Step 3 - Export live to Jira CSV (fetches comments inline)
    format_for_jira_live(todos, run_dir)

if __name__ == "__main__":
    main()