import time
from datetime import datetime, timezone, timedelta
import asyncio

from fastapi import FastAPI, Request, BackgroundTasks

from app.util.logger import setup_logging, get_logger
from app.repository.models import Chat, ChatAccess
from app.config import API_LIMIT
from app.container import chat_repository, chat_access_repository, chat_bot, fetcher
from app.util.response_util import kakao_response, kakao_textcard_response

FAILURE_MESSAGE = "미안, 이번엔 분석이 실패했어. 다시 한 번 시도해줄래?"
WAITING_MESSAGE = "아직 분석이 완료되지 않았어. 잠시만 더 기다려줘!"
RATE_LIMIT_MESSAGE = "오늘 사용 횟수가 모두 소진되었어. 내일 다시 시도해줘!"

app = FastAPI()
setup_logging()
logger = get_logger(__name__)


async def analyze(chat_id: str, utterance: str, chat_history):
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                chat_bot.get_analysis,
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
            return kakao_response(RATE_LIMIT_MESSAGE)

        new_chat = Chat(
            user_id=user_id,
            utterance=utterance,
        )
        result = chat_repository.save_chat(new_chat)
        chat_id = result.data[0]["id"]
        background_tasks.add_task(analyze, chat_id, utterance, chat_history)

        return kakao_textcard_response(
            title="분석 중",
            description="약 10초 뒤 결과를 받을 수 있어. 버튼을 눌러 확인해줘!",
            chat_id=chat_id,
        )
    except Exception as e:
        logger.error({
            "user_id": user_id,
            "chat_id": chat_id,
            "utterance": utterance,
            "error": str(e),
        })
        return kakao_response(FAILURE_MESSAGE)


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


@app.get("/")
async def root():
    return {"message": "Hello World"}
