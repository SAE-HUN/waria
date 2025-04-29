from datetime import datetime
from typing import List

from supabase import create_client

from app.repository.models import Chat


class ChatRepository:
    def __init__(self, supabase_url, supabase_key, table_name: str) -> None:
        self.supabase = create_client(supabase_url, supabase_key)
        self.table_name = table_name

    def get_chats(self, user_id: str, limit: int = 10) -> List[Chat]:
        result = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        # Convert ISO timestamp strings to datetime objects
        for item in result.data:
            if item.get('created_at'):
                item['created_at'] = datetime.fromisoformat(
                    item['created_at'].replace('Z', '+00:00')
                )

        return [Chat(**item) for item in result.data]

    def get_chat(self, chat_id: str) -> Chat:
        result = (
            self.supabase.table(self.table_name).select("*").eq("id", chat_id).execute()
        )

        return Chat(**result.data[0])

    def update_chat_response(self, chat_id: str, response: str):
        data = {"response": response}
        self.supabase.table(self.table_name).update(data).eq("id", chat_id).execute()

    def save_chat(self, chat: Chat):
        data = chat.model_dump(exclude={'response', 'created_at'})
        response = self.supabase.table(self.table_name).insert(data).execute()

        return response
