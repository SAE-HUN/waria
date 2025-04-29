import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
import asyncio
from concurrent.futures import TimeoutError

from app.finance.fetcher import Fetcher
from app.llm.chat_bot import LLM
from app.repository.models import Chat
from app.repository.chat_repository import ChatRepository

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
llm = LLM(OPEN_ROUTER_URL, OPENROUTER_API_KEY, LLM_MODEL)
fetcher = Fetcher(FINNHUB_API_KEY)


FAILURE_MESSAGE = "미안, 이번엔 분석이 실패했어. 다시 한 번 시도해줄래?"
WAITING_MESSAGE = "아직 분석이 완료되지 않았어. 잠시만 더 기다려줘!"


async def analyze_stock(chat_id: str, utterance: str, chat_history):
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                llm.get_analysis,
                utterance,
                fetcher.get_technical_data,
                fetcher.get_fundamental_data,
                chat_history,
            ),
            timeout=30.0,  # 30초 타임아웃
        )
        chat_repository.update_chat_response(chat_id, result)
    except TimeoutError:
        print(f"TimeoutError: {chat_id}: {utterance}")
        chat_repository.update_chat_response(chat_id, FAILURE_MESSAGE)
    except Exception as e:
        print(f"Analysis error: {e}")
        chat_repository.update_chat_response(chat_id, FAILURE_MESSAGE)


@app.post("/analyze/request")
async def request_analysis(request: Request, background_tasks: BackgroundTasks):
    try:
        request = await request.json()
        user_id = request["userRequest"]["user"]["id"]
        utterance = request["userRequest"]["utterance"]

        chat_history = chat_repository.get_chats(user_id)
        today_chats = [
            chat
            for chat in chat_history
            if (time.time() - chat.created_at.timestamp())
            < 24 * 60 * 60  # TODO 한국 시간으로 하루 맞추기
        ]
        if len(today_chats) >= int(API_LIMIT):
            return {
                "message": f"Daily usage limit ({API_LIMIT}) exceeded. Please try again tomorrow.",
                "status": 429,
            }

        new_chat = Chat(
            user_id=user_id,
            utterance=utterance,
        )
        result = chat_repository.save_chat(new_chat)
        chat_id = result.data[0]["id"]
        background_tasks.add_task(analyze_stock, chat_id, utterance, chat_history)

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
        print(e)
        return e


@app.post("/analyze/result")
async def get_analysis_result(request: Request):
    try:
        # TODO DB 기록 남기기
        request = await request.json()
        chat_id = request["action"]["clientExtra"]["chat_id"]
        chat = chat_repository.get_chat(chat_id)

        if chat.response:
            return {"result": chat.response}
        elif chat.created_at and (time.time() - chat.created_at.timestamp()) < 60:
            return {"result": WAITING_MESSAGE}
        else:
            return {"result": FAILURE_MESSAGE}
    except Exception as e:
        print(e)
        return e
