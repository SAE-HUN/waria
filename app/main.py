import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks

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


def analyze_stock(chat_id: str, utterance: str, chat_history):
    analysis = llm.get_technical_analysis(utterance, analyzer.get_data, chat_history)
    repository.update_chat_response(chat_id, analysis)


@app.post("/analyze/request")
async def request_analysis(request: Request, background_tasks: BackgroundTasks):
    try:
        request = await request.json()
        user_id = request["userRequest"]["user"]["id"]
        utterance = request["userRequest"]["utterance"]

        chat_history = repository.get_chat_history(user_id)
        today_chats = [
            chat
            for chat in chat_history
            if (time.time() - chat.created_at.timestamp())
            < 24 * 60 * 60  # TODO 한국 시간으로 하루 맞추기
        ]
        if len(today_chats) >= int(API_LIMIT):
            return {
                "message": "Daily usage limit (3) exceeded. Please try again tomorrow.",
                "status": 429,
            }

        new_chat = ChatHistory(
            user_id=user_id,
            utterance=utterance,
        )
        result = repository.save_chat_history(new_chat)
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
        request = await request.json()
        chat_id = request["action"]["clientExtra"]["chat_id"]
        chat = repository.get_chat(chat_id)

        if chat.response:
            return {"analysis": chat.response}
        elif chat.created_at and (time.time() - chat.created_at.timestamp()) < 60:
            return {"analysis": "아직 분석이 완료되지 않았어. 잠시만 더 기다려줘!"}
        else:
            return {"analysis": "미안, 이번엔 분석이 실패했어. 다시 한 번 시도해줄래?"}
    except Exception as e:
        print(e)
        return e
