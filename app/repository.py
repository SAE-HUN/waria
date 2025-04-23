import time
from datetime import datetime
from typing import List

from supabase import create_client

from app.models import ChatHistory


class Repository:
    def __init__(self, supabase_url, supabase_key) -> None:
        self.supabase = create_client(supabase_url, supabase_key)

    def get_chat_history(self, user_id: str, limit: int = 10) -> List[ChatHistory]:
        result = (
            self.supabase.table("chat_history")
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

        return [ChatHistory(**item) for item in result.data]

    def save_chat_log(self, log: ChatHistory):
        start_time = time.time()
        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"\nSaving chat log start: {current_time}")

        # Convert to dict and remove created_at to use Supabase default
        data = log.model_dump(exclude={'created_at'})
        response = self.supabase.table("chat_history").insert(data).execute()

        end_time = time.time()
        elapsed = end_time - start_time
        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"Saving chat log end: {current_time} (took {elapsed:.3f}s)")

        return response

    def get_model_name(self):
        result = self.supabase.table("models").select("*").execute()
        return result.data[0]["name"]
