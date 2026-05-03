import os
import subprocess
from ddgs import DDGS

def read_file(path: str) -> str:
    """
    Reads the content of a file and returns it as a string.
    Handles FileNotFoundError, PermissionError, and encoding issues.
    """
    try:
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
        os.makedirs(name, exist_ok=True)
        return f"Success: Folder '{name}' created"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def run_command(command: str) -> str:
    """
    Runs a shell command and returns the output.
    Blocks dangerous commands and has a 15-second timeout.
    """
    dangerous_commands = ["rm -rf /", "format c:", "del /f /s /q c:\\", "shutdown", "mkfs"]
    
    if any(danger in command.lower() for danger in dangerous_commands):
        return "Error: Dangerous command blocked for safety."
        
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=15
        )
        
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        if not output:
            return "Command completed with no output"
        return output
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 15 seconds"
    except Exception as e:
        return f"Error running command: {str(e)}"

def search_web(query: str) -> str:
    """
    Searches the web using DuckDuckGo and returns the top 4 results.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
            
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
            "name": "search_web",
            "description": "Searches the web using DuckDuckGo and returns the top 4 results.",
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
    "search_web": search_web
}

if __name__ == "__main__":
    print("--- Running Tools Tests ---")
    
    # 1. Test create_folder
    folder_test = create_folder("test_vault")
    print(f"Test create_folder: {'PASS' if 'Success' in folder_test else 'FAIL'} ({folder_test})")
    
    # 2. Test write_file
    write_test = write_file("test_vault/test.txt", "NexAgent Tool Test Content")
    print(f"Test write_file: {'PASS' if 'Success' in write_test else 'FAIL'} ({write_test})")
    
    # 3. Test read_file
    read_test = read_file("test_vault/test.txt")
    print(f"Test read_file: {'PASS' if read_test == 'NexAgent Tool Test Content' else 'FAIL'} (Content: {read_test})")
    
    # 4. Test list_files
    list_test = list_files("test_vault")
    print(f"Test list_files: {'PASS' if '📄 test.txt' in list_test else 'FAIL'}")
    try:
        print(f"Directory Contents:\n{list_test}")
    except UnicodeEncodeError:
        # Fallback for terminals that don't support the emojis
        print("Directory Contents: [Icons hidden due to terminal encoding constraints]")
    
    # 5. Test error handling (read non-existent file)
    error_test = read_file("missing_file.txt")
    print(f"Test error handling (FileNotFound): {'PASS' if 'Error' in error_test else 'FAIL'} ({error_test})")

    # 6. Test run_command
    cmd_test = run_command("echo Hello from Shell")
    print(f"Test run_command: {'PASS' if 'Hello' in cmd_test else 'FAIL'} ({cmd_test})")
    
    # 7. Test run_command (dangerous)
    danger_test = run_command("shutdown /s")
    print(f"Test run_command (danger): {'PASS' if 'blocked' in danger_test else 'FAIL'} ({danger_test})")

    # 8. Test search_web
    search_test = search_web("Python programming")
    print(f"Test search_web: {'PASS' if 'Result 1' in search_test or 'No results found' in search_test else 'FAIL'}")
    # print(search_test) # Uncomment to see full results

    # Cleanup (Optional, but good practice)
    try:
        os.remove("test_vault/test.txt")
        os.rmdir("test_vault")
        print("--- Cleanup complete ---")
    except:
        pass
