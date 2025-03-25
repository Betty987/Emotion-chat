# config.py
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the API key from the environment
API_KEY = os.getenv("GROK_API_KEY")

if not API_KEY:
    raise ValueError("GROK_API_KEY not found in .env file. Please set it.")