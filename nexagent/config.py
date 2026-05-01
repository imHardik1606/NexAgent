import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY or GROQ_API_KEY == "your_key_here":
    raise ValueError("GROQ_API_KEY not found in .env file. Please add your actual Groq API key.")

# Model Parameters
MODEL_NAME = "llama-3.1-8b-instant"
TEMPERATURE = 0.1
