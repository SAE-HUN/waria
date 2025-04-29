from datetime import datetime

from pydantic import BaseModel


class Chat(BaseModel):
    user_id: str
    utterance: str
    response: str | None = None
    created_at: datetime | None = None
