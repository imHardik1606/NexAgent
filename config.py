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
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY or GROQ_API_KEY == "your_key_here":
    raise ValueError("GROQ_API_KEY not found in .env file. Please add your actual Groq API key.")

# Model Parameters
MODEL_NAME = "llama-3.1-8b-instant"
TEMPERATURE = 0.1

# Path Configuration
# Automatically detects the user's home directory (Windows: C:\Users\Name, Linux/Mac: /home/name)
# Can be overridden by setting NEXAGENT_BASE_PATH in the .env file
BASE_PATH = os.getenv("NEXAGENT_BASE_PATH", os.path.expanduser("~"))

