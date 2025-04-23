import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI

from app.finance.analyzer import Analyzer
from app.llm.chat_bot import LLM
from app.models import ChatHistory, KakaoRequest
from app.repository import Repository

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_LIMIT = os.environ.get("API_LIMIT")

app = FastAPI()
repository = Repository(SUPABASE_URL, SUPABASE_KEY)
llm = LLM()
analyzer = Analyzer()


@app.post("/")
async def root(request: KakaoRequest):
    try:
        user_id = request.userRequest.user.id
        utterance = request.userRequest.utterance

        chat_history = repository.get_chat_history(user_id)
        today_logs = [
            log
            for log in chat_history
            if (time.time() - log.created_at.timestamp()) < 24 * 60 * 60
        ]
        if len(today_logs) >= int(API_LIMIT):
            return {
                "message": "Daily usage limit (3) exceeded. Please try again tomorrow.",
                "status": 429,
            }

        technical_analysis = llm.get_technical_analysis(utterance, analyzer.get_data)
        new_chat = ChatHistory(
            user_id=user_id,
            utterance=utterance,
            response=technical_analysis,
            is_user_friend=request.userRequest.user.properties.isFriend,
        )
        repository.save_chat_log(new_chat)

        return {"ai_analysis": technical_analysis}

    except Exception as e:
        print(e)
        return e
