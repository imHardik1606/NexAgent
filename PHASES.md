# NexAgent — Project Plan

## Project Overview
A CLI-based AI agent that executes real OS-level actions
from plain English commands using LLM tool use.

## Tech Stack
- Python 3.11
- Groq API (Llama 3.1 8B)
- DuckDuckGo Search
- Docker

---

## Phase 1: Project Setup and Environment
**Aim:** Establish project structure and verify LLM connectivity
**Status:** ✅ Complete
**What I did:**
- Created the project scaffold including `main.py`, `agent.py`, `tools.py`, `config.py`, and `logger.py`.
- Set up a Python virtual environment and initialized `requirements.txt` with core dependencies.
- Implemented environment variable management in `config.py` using `python-dotenv`.
- Created a `test_connection.py` script to verify Groq API connectivity and model response handling.
- Configured project hygiene with `.gitignore` and a dedicated `logs/` directory.
**What I learned:**
- Best practices for structuring an AI agent project for modularity and scalability.
- Securely managing API keys and configuration across different environments.
- Using the Groq Python SDK to interact with Llama 3 models efficiently.

---

## Phase 2: Core Tool Functions
**Aim:** Build all OS-level tools the agent will use
**Status:** ✅ Complete
**What I did:**
- Implemented file system tools: `read_file`, `write_file`, `list_files`, and `create_folder` with robust error handling.
- Added system automation tool: `run_command` with a 15s timeout and safety filters for dangerous operations.
- Integrated web search capability: `search_web` using the DuckDuckGo search API.
- Created `TOOL_DEFINITIONS` and `AVAILABLE_FUNCTIONS` for seamless LLM integration.
- Developed an integrated test suite within `tools.py` to verify all tool functionality.
**What I learned:**
- Implementing idempotent file operations and handling cross-platform encoding issues (UTF-8).
- Designing safety-first shell command execution with command blacklisting.
- Structuring OpenAI-style tool definitions for function calling.

---

## Phase 3: Agent Logic
**Aim:** Build the brain that connects LLM to tools
**Status:** ✅ Complete
**What I did:**
- Developed the `Agent` class in `agent.py` using the Groq SDK for high-speed inference.
- Implemented recursive tool-calling logic that enables the LLM to execute local functions.
- Designed a persistent conversation history system for multi-turn interactions.
- Added error handling and truncation logic for tool outputs to maintain token efficiency and clean logs.
**What I learned:**
- Managing state in conversational AI using a structured message history.
- Handling the two-step completion cycle required for OpenAI-style function calling.
- Debugging complex LLM-to-tool integration flows and parsing dynamic arguments.

---

## Phase 4: CLI Interface
**Aim:** Build clean terminal interface for user interaction
**Status:** 🔲 Not Started

---

## Phase 5: Logging System
**Aim:** Add production-grade logging to every operation
**Status:** ✅ Complete
**What I did:**
- Built a centralized `logger.py` module with both `FileHandler` and `StreamHandler`.
- Configured automated directory creation for `logs/` and UTF-8 encoding support for cross-platform emojis.
- Integrated logging throughout the Agent's lifecycle, including user inputs, tool calls, and final responses.
**What I learned:**
- Best practices for structuring logs in a production AI application.
- Managing encoding challenges when logging unicode characters (emojis) in Windows environments.

---

## Phase 6: Docker + README
**Aim:** Containerize and document the project
**Status:** 🔲 Not Started