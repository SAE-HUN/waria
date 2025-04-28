from datetime import datetime

from pydantic import BaseModel


class ChatHistory(BaseModel):
    user_id: str
    utterance: str
    response: str | None = None
    is_user_friend: bool
    created_at: datetime | None = None


class Block(BaseModel):
    id: str
    name: str


class UserProperties(BaseModel):
    isFriend: bool


class User(BaseModel):
    id: str
    type: str
    properties: UserProperties


class UserRequest(BaseModel):
    block: Block
    utterance: str
    user: User


class KakaoRequest(BaseModel):
    userRequest: UserRequest
