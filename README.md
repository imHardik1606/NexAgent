# NexAgent — AI-Powered OS Assistant

NexAgent is a CLI-based AI agent that bridges natural language and OS-level execution. By leveraging Llama 3.1 via the Groq API, it interprets complex user intent and safely executes local file system operations, shell commands, and web searches.

## 🧠 Why I Built This
I built NexAgent to explore the transition from traditional CLIs to **AI-native operating environments**. Instead of memorizing syntax, users interact with their system through high-level intent. This project demonstrates how an LLM can act as a reasoning engine for an OS, chaining multiple tools to solve non-trivial automation tasks while maintaining safety and auditability.

## ✨ Features
NexAgent is equipped with six core tools that enable it to manage your environment:
- **`list_files`**: Recursively explore directory structures.
- **`read_file`**: Extract content from local files for context or analysis.
- **`write_file`**: Generate or update documents, scripts, or logs.
- **`create_folder`**: Organize project structures on the fly.
- **`run_command`**: Execute arbitrary shell commands (with safety filtering).
- **`search_web`**: Retrieve real-time information from the internet via DuckDuckGo.

## 🛠 Tech Stack
| Technology | Purpose |
| :--- | :--- |
| **Python 3.11** | Core logic and tool implementation |
| **Groq (Llama 3.1 8B)** | High-speed LLM reasoning and function calling |
| **Click** | Robust CLI argument parsing and interactive REPL |
| **Docker** | Containerization for consistent environments |
| **DuckDuckGo API** | Live web search integration |
| **Logging** | Production-grade UTF-8 session tracking |

## 🏗 Project Architecture
```text
      +-------------+        +-------------+        +-----------------+
      |    User     | <----> |     CLI     | <----> |      Agent      |
      | (English)   |        |  (main.py)  |        |    (agent.py)   |
      +-------------+        +-------------+        +--------+--------+
                                                             |
                                           +-----------------+-----------------+
                                           |                                   |
                                   +-------v-------+                   +-------v-------+
                                   |  LLM (Groq)   |                   |  Local Tools  |
                                   | (Reasoning)   |                   |  (tools.py)   |
                                   +---------------+                   +---------------+
```

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **Groq API Key**: Obtain one from the [Groq Console](https://console.groq.com/).

### Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/imHardik1606/NexAgent.git
   cd NexAgent
   ```
2. **Setup environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure API Key**:
   Create a `.env` file in the root:
   ```env
   GROQ_API_KEY=your_key_here
   ```

### Running Locally
```bash
python main.py
```

### Running with Docker
```bash
# Build the image
docker build -t nexagent .

# Run interactively with your .env
docker run -it --env-file .env nexagent
```

## 🎮 Example Interactions
- **File Management**: `Create a folder called 'src' and inside it create 'app.py' with a hello world print.`
- **System Intel**: `How many files are in the current directory and what is their total size?`
- **Web-to-Local**: `Search for the latest Python release version and write it to VERSION.txt.`
- **Command execution**: `List the active network connections using a system command.`

## 📁 Project Structure
```text
NexAgent/
├── agent.py          # LLM orchestration and tool calling logic
├── main.py           # CLI entry point and interactive loop
├── tools.py          # OS and Web tool implementations
├── logger.py         # Session logging and formatting
├── config.py         # Environment and global configuration
├── requirements.txt  # Project dependencies
├── Dockerfile        # Container configuration
└── PHASES.md         # Detailed development roadmap
```

## 💡 What I Learned
1. **The Function Calling Paradox**: I learned that LLMs are excellent at choosing tools but require strict output schemas. Implementing recursive tool loops taught me how to handle multi-step reasoning where the output of one tool serves as the input for the next.
2. **Safety as a First-Class Citizen**: Building the `run_command` tool required a "deny-list" approach to prevent destructive actions (like `rm -rf /`). I realized that an AI-native OS is only as good as its security sandbox.
3. **Interactive UI in CLI**: Integrating `Click` with an LLM-driven REPL highlighted the importance of user feedback (like "Thinking..." indicators) to manage the latency of remote inference calls.
4. **State Persistence**: Managing conversation history while preventing token overflow taught me how to balance context retention with API efficiency.
