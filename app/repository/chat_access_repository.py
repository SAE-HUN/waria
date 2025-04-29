from app.repository.models import ChatAccess
from supabase import create_client

class ChatAccessRepository:
    def __init__(self, supabase_url, supabase_key, table_name: str) -> None:
        self.supabase = create_client(supabase_url, supabase_key)
        self.table_name = table_name

    def save_chat_access(self, chat_access: ChatAccess):
        return self.supabase.table(self.table_name).insert(chat_access.model_dump()).execute()
