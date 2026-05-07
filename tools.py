import os
import subprocess
import warnings
import re

# Suppress library warnings (like the renaming notice) to keep terminal output clean
# We do this BEFORE importing the library that triggers it
warnings.filterwarnings("ignore", message=".*renamed to `ddgs`.*")
warnings.filterwarnings("ignore", category=RuntimeWarning)

from ddgs import DDGS
from config import BASE_PATH

def resolve_path(path: str) -> str:
    """
    Resolves a given path. If it's relative or starts with '/', 
    it's joined with BASE_PATH to ensure it targets the user's home.
    """
    # If path starts with / or \, it's treated as relative to the drive root on Windows.
    # We want to redirect it to BASE_PATH if it's not an absolute Windows path (e.g. C:\)
    if not os.path.isabs(path) or (path.startswith('/') or path.startswith('\\')):
        # Remove leading slash/backslash to join correctly
        clean_path = path.lstrip('/\\')
        return os.path.join(BASE_PATH, clean_path)
    return path

def read_file(path: str) -> str:
    """
    Reads the content of a file and returns it as a string.
    Handles FileNotFoundError, PermissionError, and encoding issues.
    """
    try:
        path = resolve_path(path)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at '{path}'"
    except PermissionError:
        return f"Error: Permission denied to read '{path}'"
    except UnicodeDecodeError:
        return f"Error: Could not decode '{path}' using utf-8"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(path: str, content: str) -> str:
    """
    Writes content to a file, creating parent directories if they don't exist.
    Returns a success message with the path.
    """
    try:
        path = resolve_path(path)
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: File written to '{path}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_files(directory: str = ".") -> str:
    """
    Lists the contents of a directory, differentiating folders and files with icons.
    Returns 'Directory is empty' if no contents are found.
    """
    try:
        directory = resolve_path(directory)
        if not os.path.exists(directory):
            return f"Error: Directory '{directory}' not found"
            
        items = os.listdir(directory)
        if not items:
            return "Directory is empty"
        
        formatted_items = []
        for item in sorted(items):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                formatted_items.append(f"📁 {item}")
            else:
                formatted_items.append(f"📄 {item}")
                
        return "\n".join(formatted_items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def create_folder(name: str) -> str:
    """
    Creates a folder with the given name, including parent directories if necessary.
    Uses exist_ok=True to avoid errors if the folder already exists.
    """
    try:
        name = resolve_path(name)
        os.makedirs(name, exist_ok=True)
        return f"Success: Folder '{name}' created"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def strip_ansi(text: str) -> str:
    """Removes ANSI escape sequences (colors, cursor movements) from a string."""
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def run_command(command: str) -> str:
    """
    Runs a shell command and returns the clean text output.
    Blocks dangerous commands and has a 15-second timeout.
    """
    dangerous_commands = ["rm -rf /", "format c:", "del /f /s /q c:\\", "shutdown", "mkfs"]
    
    if any(danger in command.lower() for danger in dangerous_commands):
        return "Error: Dangerous command blocked for safety."
        
    try:
        # We specify encoding='utf-8' and errors='replace' to prevent crashes 
        # when commands (like weather reports) return non-standard characters.
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace',
            timeout=15
        )
        
        raw_output = result.stdout.strip() if result.stdout else result.stderr.strip()
        if not raw_output:
            return "Command completed with no output"
            
        # Strip ANSI escape codes to prevent terminal corruption/glitches
        return strip_ansi(raw_output)
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 15 seconds"
    except Exception as e:
        return f"Error running command: {str(e)}"

def get_weather(location: str) -> str:
    """
    Fetches the current weather for a specific location using wttr.in.
    Returns a clean, summarized weather report.
    """
    try:
        # Use v2 for a cleaner, more readable format
        url = f"https://wttr.in/{location}?format=%l:+%C+%t+(Feels+like+%f)+|+Wind:+%w+|+Humidity:+%h"
        result = subprocess.run(
            ["curl", "-s", url], 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout.strip()
        if not output or "weather data source" in output.lower():
            return f"Could not find weather for '{location}'. Please try a web search instead."
        return f"Weather Report: {output}"
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

def search_web(query: str) -> str:
    """
    Searches the web using DuckDuckGo and returns the top 8 results.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with DDGS() as ddgs:
                # Increased to 8 results to bypass irrelevant/blocked links
                results = list(ddgs.text(query, max_results=8))

        if not results:
            return "No results found"
            
        output = []
        for i, res in enumerate(results, 1):
            output.append(f"Result {i}:")
            output.append(f"Title: {res.get('title', 'N/A')}")
            output.append(f"Summary: {res.get('body', 'N/A')}\n")
            
        return "\n".join(output).strip()
    except Exception as e:
        return f"Error searching web: {str(e)}"


# Tool Definitions for LLM Integration
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a file and returns it as a string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to be read."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes content to a file, creating parent directories if they don't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file where content will be written."
                    },
                    "content": {
                        "type": "string",
                        "description": "The string content to write to the file."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists the contents of a directory with icons for files and folders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "The directory to list. Defaults to the current directory '.'."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Creates a folder with the given name, including parent directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name or path of the folder to create."
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Runs a shell command and returns the output (stdout or stderr). Has a 15s timeout and blocks dangerous commands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Fetches the current weather for a specific location (city, state, etc.) using a dedicated weather service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city or location to get the weather for."
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches the web using DuckDuckGo and returns the top 8 results. Use this if get_weather fails or for general info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Mapping function names to actual function objects
AVAILABLE_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "create_folder": create_folder,
    "run_command": run_command,
    "search_web": search_web,
    "get_weather": get_weather
}


if __name__ == "__main__":
    print("--- Running Tools Tests ---")
    
    # 0. Test resolve_path (The new core feature)
    print(f"Test resolve_path (relative): {resolve_path('test_dir')}")
    print(f"Test resolve_path (slash): {resolve_path('/Desktop/MyTest')}")
    
    # 1. Test create_folder (nested)
    folder_test = create_folder("agent_test/nested/deep")
    print(f"Test create_folder (nested): {'PASS' if 'Success' in folder_test else 'FAIL'} ({folder_test})")
    
    # 2. Test write_file (no emojis for console safety)
    write_test = write_file("agent_test/nested/deep/test.txt", "NexAgent Tool Test - Success")
    print(f"Test write_file: {'PASS' if 'Success' in write_test else 'FAIL'} ({write_test})")
    
    # 3. Test read_file
    read_test = read_file("agent_test/nested/deep/test.txt")
    print(f"Test read_file: {'PASS' if 'Success' in read_test else 'FAIL'} (Content: {read_test})")
    
    # 4. Test list_files
    list_test = list_files("agent_test/nested")
    print(f"Test list_files: {'PASS' if '📁 deep' in list_test else 'FAIL'}")
    
    # 5. Test error handling (read non-existent file)
    error_test = read_file("missing_file.txt")
    print(f"Test error handling (FileNotFound): {'PASS' if 'Error' in error_test else 'FAIL'} ({error_test})")

    # 6. Test run_command
    cmd_test = run_command("echo Hello from Shell")
    print(f"Test run_command: {'PASS' if 'Hello' in cmd_test else 'FAIL'} ({cmd_test})")
    
    # 7. Test run_command (danger)
    danger_test = run_command("shutdown /s")
    print(f"Test run_command (danger): {'PASS' if 'blocked' in danger_test else 'FAIL'} ({danger_test})")

    # 8. Test search_web
    search_test = search_web("Python programming")
    print(f"Test search_web: {'PASS' if 'Result 1' in search_test or 'No results found' in search_test else 'FAIL'}")

    # 9. Test run_command (timeout) - Should take 15s then fail
    print("Testing command timeout (expected wait: 15s)...")
    timeout_test = run_command("python -c \"import time; time.sleep(20)\"")
    print(f"Test timeout: {'PASS' if 'timed out' in timeout_test else 'FAIL'} ({timeout_test})")

    # Cleanup
    try:
        import shutil
        # Resolve the actual path for cleanup to be safe
        cleanup_path = resolve_path("agent_test")
        if os.path.exists(cleanup_path):
            shutil.rmtree(cleanup_path)
            print("--- Cleanup complete ---")
    except Exception as e:
        print(f"Cleanup failed: {e}")
    pass
