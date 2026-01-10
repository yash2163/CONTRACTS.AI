import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")

    # validation
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing in .env")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is missing in .env")