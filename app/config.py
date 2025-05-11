import os
from dotenv import load_dotenv

load_dotenv()

API_LIMIT = os.environ.get("API_LIMIT")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPEN_ROUTER_URL = os.environ.get("OPEN_ROUTER_URL")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY") 