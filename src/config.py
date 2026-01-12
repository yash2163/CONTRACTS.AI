import os
import streamlit as st
from dotenv import load_dotenv

# Try loading .env (for local development)
load_dotenv()

class Config:
    # 1. Try to get key from Local Environment (.env)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # 2. If not found locally, try Streamlit Cloud Secrets
    if not GOOGLE_API_KEY and "GOOGLE_API_KEY" in st.secrets:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

    # 3. Repeat for Database URL
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL and "DATABASE_URL" in st.secrets:
        DATABASE_URL = st.secrets["DATABASE_URL"]

    # 4. Final Validation (Custom Error Message to help debug)
    if not GOOGLE_API_KEY:
        raise ValueError("CRITICAL ERROR: GOOGLE_API_KEY is missing. Check your .env file (Local) or Streamlit 'Secrets' settings (Cloud).")
    if not DATABASE_URL:
        raise ValueError("CRITICAL ERROR: DATABASE_URL is missing. Check your .env file (Local) or Streamlit 'Secrets' settings (Cloud).")