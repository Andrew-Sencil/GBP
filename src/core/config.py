import os
from dotenv import load_dotenv

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")

if not SERP_API_KEY:
    raise ValueError("SERP_API_KEY is not found. Make sure it's set in your .env file.")
