from fastapi.responses import JSONResponse
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def success_response(data: Any = None, message: str = None) -> JSONResponse:
    resp = {"result": data}
    if message:
        resp["message"] = message
    return JSONResponse(content=resp)


def error_response(message: str, status_code: int = 500, extra: Dict = None) -> JSONResponse:
    resp = {"error": message}
    if extra:
        resp.update(extra)
    return JSONResponse(content=resp, status_code=status_code)


def kakao_response(text: str) -> Dict:
    return {
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": text}}]},
    }


def kakao_textcard_response(title: str, description: str, chat_id: str) -> Dict:
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": title,
                        "description": description,
                        "buttons": [
                            {
                                "action": "block",
                                "label": "결과 받기",
                                "blockId": "680b22cabfa6987bff180209",
                                "extra": {"chat_id": chat_id},
                            }
                        ],
                    }
                }
            ]
        },
    } 