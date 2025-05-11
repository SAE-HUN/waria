from app.config import (
    API_LIMIT,
    SUPABASE_URL,
    SUPABASE_KEY,
    OPEN_ROUTER_URL,
    OPENROUTER_API_KEY,
    LLM_MODEL,
    FINNHUB_API_KEY,
)
from app.repository.chat_repository import ChatRepository
from app.repository.chat_access_repository import ChatAccessRepository
from app.llm.chat_bot import ChatBot
from app.finance.fetcher import Fetcher

chat_repository = ChatRepository(SUPABASE_URL, SUPABASE_KEY, "chats")
chat_access_repository = ChatAccessRepository(
    SUPABASE_URL, SUPABASE_KEY, "chat_accesses"
)
chat_bot = ChatBot(OPEN_ROUTER_URL, OPENROUTER_API_KEY, LLM_MODEL)
fetcher = Fetcher(FINNHUB_API_KEY) 