import os
import json
import subprocess

def tool_list_directory(path="."):
    """Lists files in the target directory to allow exploration."""
    try:
        return json.dumps(os.listdir(path))
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_read_file_lines(filename):
    """Reads a file and returns its line count to analyze length."""
    try:
        with open(filename, 'r') as f:
            return json.dumps({"lines": len(f.readlines())})
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_read_file_contents(filename):
    """Reads and returns the actual text contents of a file."""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        return json.dumps({"content": content})
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_append_log(text):
    """Appends an analytical conclusion string to a local file."""
    try:
        with open("agent_output.log", "a") as f:
            f.write(text + "\n")
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_open_app(app_name):
    """Opens a local application by name."""
    try:
        subprocess.Popen([app_name])
        return json.dumps({"status": "opened", "app": app_name})
    except Exception as e:
        return json.dumps({"error": str(e)})

AVAILABLE_TOOLS = {
    "list_directory": tool_list_directory,
    "read_file_lines": tool_read_file_lines,
    "read_file_contents": tool_read_file_contents,
    "append_log": tool_append_log,
    "open_app": tool_open_app,
}

TOOLS_SCHEMA = [
    {
        "name": "list_directory",
        "description": "Lists all file and folder names in a target directory to explore what files are available.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The relative path to the directory. Use '.' for the current working folder."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "read_file_lines",
        "description": "Reads a specific text file and returns the total number of lines it contains. Use this when the user asks HOW MANY LINES a file has.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The exact name or relative path of the file to inspect."}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "read_file_contents",
        "description": "Reads a specific text file and returns its actual text content. Use this when the user asks WHAT IS IN a file or wants to know the file's contents.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The exact name or relative path of the file to read."}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "append_log",
        "description": "Appends a final analytical conclusion or status report line to the local 'agent_output.log' file.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text string statement to write into the permanent log file."}
            },
            "required": ["text"]
        }
    },
    {
        "name": "open_app",
        "description": "Opens a local application by its executable name (e.g. 'firefox', 'code').",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "The executable name of the application to open."}
            },
            "required": ["app_name"]
        }
    }
]