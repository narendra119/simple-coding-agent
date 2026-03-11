import os
import subprocess

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace an exact string in a file with new text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string", "description": "Exact text to replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "delete_file",
        "description": "Delete a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "List files in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (defaults to '.')"},
            },
            "required": [],
        },
    },
    {
        "name": "run_shell",
        "description": "Run a shell command and return its stdout and stderr. Use for executing code, running tests, installing packages, git operations, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"},
                "cwd": {"type": "string", "description": "Working directory for the command (defaults to '.')"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (defaults to 30)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "search_files",
        "description": "Recursively search for a string within files in a directory. Returns matching file paths, line numbers, and line content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "String to search for"},
                "directory": {"type": "string", "description": "Directory to search in (defaults to '.')"},
                "extension": {"type": "string", "description": "Only search files with this extension, e.g. '.py' (optional)"},
            },
            "required": ["query"],
        },
    },
]


def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w") as f:
        f.write(content)
    return f"Written to {path}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    with open(path) as f:
        content = f.read()
    if old_string not in content:
        raise ValueError(f"String not found in {path}")
    with open(path, "w") as f:
        f.write(content.replace(old_string, new_string, 1))
    return f"Edited {path}"


def delete_file(path: str) -> str:
    os.remove(path)
    return f"Deleted {path}"


def list_files(path: str = ".") -> str:
    entries = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        level = root.replace(path, "").count(os.sep)
        indent = "  " * level
        entries.append(f"{indent}{os.path.basename(root)}/")
        for file in files:
            entries.append(f"{indent}  {file}")
    return "\n".join(entries)


def search_files(query, directory=".", extension=None):
    """
    Recursively searches for a string within files in a directory.
    Returns a list of matches with file paths and line numbers.
    """
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            if extension and not file.endswith(extension):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if query in line:
                            results.append({
                                "file": file_path,
                                "line": i,
                                "content": line.strip()
                            })
            except (UnicodeDecodeError, PermissionError):
                continue
    return results


def run_shell(command: str, cwd: str = ".", timeout: int = 30) -> str:
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        timeout=timeout,
        text=True,
        capture_output=True,
    )
    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += result.stderr
    if result.returncode != 0:
        output += f"\n[exit code {result.returncode}]"
    return output or "(no output)"


def execute_tool(name: str, inputs: dict) -> str:
    try:
        match name:
            case "read_file":   return read_file(**inputs)
            case "write_file":  return write_file(**inputs)
            case "edit_file":   return edit_file(**inputs)
            case "delete_file": return delete_file(**inputs)
            case "run_shell":     return run_shell(**inputs)
            case "list_files":    return list_files(**inputs)
            case "search_files":  return str(search_files(**inputs))
            case _:               return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {e}"
