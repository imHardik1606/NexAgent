import os
import warnings
from dotenv import load_dotenv

# Forcefully suppress all library warnings (like the duckduckgo-search notice)
# globally before any other modules are imported.
os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")

# Load environment variables from .env file
load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Model and evaluation parameters. Prices intentionally remain user-supplied.
ROUTING_MODE = os.getenv("ROUTING_MODE", "all_cloud")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "llama3.2:3b")
CLOUD_MODEL = os.getenv("CLOUD_MODEL", "openai/gpt-oss-20b")
MODEL_NAME = CLOUD_MODEL
ESCALATE_TOOLS = {
    name.strip() for name in os.getenv("ESCALATE_TOOLS", "run_command,write_file").split(",") if name.strip()
}
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))
SHELL_TIMEOUT_S = float(os.getenv("SHELL_TIMEOUT_S", "15"))
CLOUD_PRICE_PER_M_INPUT = float(os.getenv("CLOUD_PRICE_PER_M_INPUT", "0.0"))  # TODO: fill from Groq pricing.
CLOUD_PRICE_PER_M_OUTPUT = float(os.getenv("CLOUD_PRICE_PER_M_OUTPUT", "0.0"))  # TODO: fill from Groq pricing.

# Path Configuration
# Automatically detects the user's home directory (Windows: C:\Users\Name, Linux/Mac: /home/name)
# Can be overridden by setting NEXAGENT_BASE_PATH in the .env file
BASE_PATH = os.getenv("NEXAGENT_BASE_PATH", os.path.expanduser("~"))

# Memory Path: Persistent data stored in a hidden folder in the user's home directory
MEMORY_PATH = os.path.join(BASE_PATH, ".nexagent", "memory.json")


