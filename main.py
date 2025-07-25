from dump import dump_projects
from fetch import fetch_all_todos_from_dump
from comment_todos import comment_todos

def main():
    # Step 1 - Fetch projects
    run_dir, projects_path, projects = dump_projects(output_root="results")

    # Step 2 - Fetch todos with metadata
    todos_path, todos = fetch_all_todos_from_dump(projects, run_dir)

    # Step 3 - Attach comments and files
    comment_todos(todos, run_dir)

if __name__ == "__main__":
    main()