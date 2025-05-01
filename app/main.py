import os
import time
from datetime import datetime, timezone, timedelta
import asyncio
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks

from app.util.log_formatter import JsonFormatter
from app.finance.fetcher import Fetcher
from app.llm.chat_bot import ChatBot
from app.repository.models import Chat, ChatAccess
from app.repository.chat_repository import ChatRepository
from app.repository.chat_access_repository import ChatAccessRepository

load_dotenv()

API_LIMIT = os.environ.get("API_LIMIT")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

OPEN_ROUTER_URL = os.environ.get("OPEN_ROUTER_URL")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL")

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")

app = FastAPI()
chat_repository = ChatRepository(SUPABASE_URL, SUPABASE_KEY, "chats")
chat_access_repository = ChatAccessRepository(
    SUPABASE_URL, SUPABASE_KEY, "chat_accesses"
)
chat_bot = ChatBot(OPEN_ROUTER_URL, OPENROUTER_API_KEY, LLM_MODEL)
fetcher = Fetcher(FINNHUB_API_KEY)

FAILURE_MESSAGE = "미안, 이번엔 분석이 실패했어. 다시 한 번 시도해줄래?"
WAITING_MESSAGE = "아직 분석이 완료되지 않았어. 잠시만 더 기다려줘!"
RATE_LIMIT_MESSAGE = "오늘 사용 횟수가 모두 소진되었어. 내일 다시 시도해줘!"


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)


async def analyze(chat_id: str, utterance: str, chat_history):
    try:
        result = await asyncio.wait_for(
            chat_bot.get_analysis(
                utterance,
                fetcher.get_technical_data,
                fetcher.get_fundamental_data,
                chat_history,
            ),
            timeout=30.0,
        )
        chat_repository.update_chat_response(chat_id, result)
    except Exception as e:
        chat_repository.update_chat_response(chat_id, FAILURE_MESSAGE)
        logger.error({
            "chat_id": chat_id,
            "utterance": utterance,
            "error": str(e),
        })


@app.post("/analyze/request")
async def request_analysis(request: Request, background_tasks: BackgroundTasks):
    user_id = None
    chat_id = None
    utterance = None
    try:
        request = await request.json()
        user_id = request["userRequest"]["user"]["id"]
        utterance = request["userRequest"]["utterance"]

        chat_history = chat_repository.get_chats(user_id)
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        today_start_kst = datetime(
            now_kst.year, now_kst.month, now_kst.day, 0, 0, 0, tzinfo=kst
        )
        today_chats = [
            chat for chat in chat_history
            if chat.created_at.replace(tzinfo=timezone.utc).astimezone(kst) >= today_start_kst
        ]
        
        if len(today_chats) >= int(API_LIMIT):
            return {
                "version": "2.0",
                "template": {"outputs": [{"simpleText": {"text": RATE_LIMIT_MESSAGE}}]},
            }

        new_chat = Chat(
            user_id=user_id,
            utterance=utterance,
        )
        result = chat_repository.save_chat(new_chat)
        chat_id = result.data[0]["id"]
        background_tasks.add_task(analyze, chat_id, utterance, chat_history)

        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "textCard": {
                            "title": "분석 중",
                            "description": "약 10초 뒤 결과를 받을 수 있어. 버튼을 눌러 확인해줘!",
                            "buttons": [
                                {
                                    "action": "block",
                                    "label": "결과 받기",
                                    "blockId": "680b22cabfa6987bff180209",
                                    "extra": {
                                        "chat_id": chat_id,
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        }
    except Exception as e:
        logger.error({
            "user_id": user_id,
            "chat_id": chat_id,
            "utterance": utterance,
            "error": str(e),
        })
        return {
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": FAILURE_MESSAGE}}]},
        }


@app.post("/analyze/result")
async def get_analysis_result(request: Request):
    user_id = None
    chat_id = None
    
    try:
        request = await request.json()
        chat_id = request["action"]["clientExtra"]["chat_id"]
        user_id = request["userRequest"]["user"]["id"]

        chat = chat_repository.get_chat(chat_id)
        result = ""
        chat_status = ""

        if chat.response:
            result = chat.response
            chat_status = "SUCCESS"
        elif chat.created_at and (time.time() - chat.created_at.timestamp()) < 60:
            result = WAITING_MESSAGE
            chat_status = "WAITING"
        else:
            result = FAILURE_MESSAGE
            chat_status = "FAILURE"

        chat_access = ChatAccess(
            user_id=user_id,
            chat_id=chat_id,
            chat_status=chat_status,
        )
        chat_access_repository.save_chat_access(chat_access)

        return {"result": result}
    except Exception as e:
        logger.error({
            "user_id": user_id,
            "chat_id": chat_id,
            "error": str(e),
        })
        return {"result": FAILURE_MESSAGE}
