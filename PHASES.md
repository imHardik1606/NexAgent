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
**Status:** ⏳ In Progress

---

## Phase 3: Agent Logic
**Aim:** Build the brain that connects LLM to tools
**Status:** 🔲 Not Started

---

## Phase 4: CLI Interface
**Aim:** Build clean terminal interface for user interaction
**Status:** 🔲 Not Started

---

## Phase 5: Logging System
**Aim:** Add production-grade logging to every operation
**Status:** 🔲 Not Started

---

## Phase 6: Docker + README
**Aim:** Containerize and document the project
**Status:** 🔲 Not Started