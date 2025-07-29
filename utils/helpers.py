import re

def parse_todo_url(url):
    """
    Extracts project_id and todo_id from a Basecamp To-do URL.
    Supports both /projects/ and /buckets/ format.
    """
    match = re.search(r'/(?:projects|buckets)/(\d+)/todos/(\d+)', url)
    if not match:
        raise ValueError("URL must contain /projects|buckets/{project_id}/todos/{todo_id}")
    return match.group(1), match.group(2)
