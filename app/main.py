import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request

from app.finance.analyzer import Analyzer
from app.llm.chat_bot import LLM
from app.models import ChatHistory
from app.repository import Repository

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_LIMIT = os.environ.get("API_LIMIT")

app = FastAPI()
repository = Repository(SUPABASE_URL, SUPABASE_KEY)
llm = LLM()
analyzer = Analyzer()


@app.post("/analyze/request")
async def request_analysis(request: Request):
    try:
        request = await request.json()
        user_id = request["userRequest"]["user"]["id"]
        utterance = request["userRequest"]["utterance"]

        chat_history = repository.get_chat_history(user_id)
        today_chats = [
            chat
            for chat in chat_history
            if (time.time() - chat.created_at.timestamp()) < 24 * 60 * 60
        ]
        if len(today_chats) >= int(API_LIMIT):
            return {
                "message": "Daily usage limit (3) exceeded. Please try again tomorrow.",
                "status": 429,
            }
        
        new_chat = ChatHistory(
            user_id=user_id,
            utterance=utterance,
            is_user_friend=request["userRequest"]["user"]["properties"]["isFriend"],
        )
        result = repository.save_chat_history(new_chat)
        chat_id = result.data[0]["id"]

        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "basicCard": {
                            "title": utterance,
                            "description": "click below button to get analysis after 10 seconds",
                            "thumbnail": {
                                "imageUrl": "https://img1.daumcdn.net/thumb/C200x200.mplusfriend/?fname=http%3A%2F%2Fk.kakaocdn.net%2Fdn%2FkAv0g%2FbtsNzAmELUK%2FkOKb2ueSDtZTjzbgoDKXw0%2Fimg_xl.jpg"
                            }
                        },
                        "buttons": [
                            {
                                "label": "get analysis",
                                "action": "block",
                                "blockId": "680b22cabfa6987bff180209",
                                "extra": {
                                    "chat_id": chat_id,
                                }
                            }
                        ]
                    }
                ]
            }
        }

    except Exception as e:
        print(e)
        return e



@app.post("/analyze/result")
async def get_analysis_result(request: Request):
    try:
        request = await request.json()
        print(request)
        # chat_id = request["userRequest"]["block"]["extra"]["chat_id"]
        # chat_history = repository.get_chat_history(chat_id)

        # return {"ai_analysis": technical_analysis}

    except Exception as e:
        print(e)
        return e
