from typing import List
from app.repository.models import Chat
import json
import requests

from app.llm.templates import (
    examples,
    system_message,
)


class LLM:
    def __init__(
        self,
        OPEN_ROUTER_URL: str,
        OPENROUTER_API_KEY: str,
        model: str,
        temperature: float = 0.7,
    ) -> None:
        self.open_router_headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
        }
        self.open_router_url = OPEN_ROUTER_URL
        self.model = model
        self.temperature = temperature

    def get_analysis(
        self,
        utterance: str,
        technical_data_func,
        fundamental_data_func,
        chat_history: List[Chat],
    ):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_technical_data",
                    "description": "Get technical data for a given symbol (e.g. '011070.KS'). Returns OHLCV data and indicators for technical analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The symbol to get data for",
                            }
                        },
                        "required": ["symbol"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_fundamental_data",
                    "description": "Get fundamental data for a given symbol (e.g. '011070.KS'). Returns fundamental metrics for fundamental analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The symbol to get data for",
                            },
                        },
                        "required": ["symbol"],
                    },
                },
            },
        ]
        tool_functions = {
            "get_technical_data": technical_data_func,
            "get_fundamental_data": fundamental_data_func,
        }

        messages = [{"role": "system", "content": system_message}]

        # Add few-shot examples
        for example in examples:
            messages.append({"role": "user", "content": example["input"]})
            messages.append({"role": "assistant", "content": example["output"]})

        # Add chat history
        for chat in chat_history:
            if not chat.utterance or not chat.response:
                continue
            messages.append({"role": "user", "content": chat.utterance})
            messages.append({"role": "assistant", "content": chat.response})

        # Add current user message
        messages.append({"role": "user", "content": utterance})

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": self.temperature,
        }

        # First API call to get tool calls
        response = requests.post(
            self.open_router_url, headers=self.open_router_headers, json=payload
        )

        response_data = response.json()
        assistant_message = response_data["choices"][0]["message"]
        print(response_data)

        # If no tool calls, return the content directly
        if "tool_calls" not in assistant_message or not assistant_message["tool_calls"]:
            return assistant_message["content"]

        # Add assistant message with tool calls to messages
        messages.append(assistant_message)

        # Process tool calls
        for tool_call in assistant_message["tool_calls"]:
            print(tool_call)
            function_name = tool_call["function"]["name"].lower()

            if not function_name in tool_functions:
                continue

            args = json.loads(tool_call["function"]["arguments"])
            tool_result = tool_functions[function_name](**args)
            if hasattr(tool_result, "__dataclass_fields__"):
                tool_result = {
                    field: getattr(tool_result, field)
                    for field in tool_result.__dataclass_fields__
                }

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": tool_call["function"]["name"],
                    "content": json.dumps(tool_result),
                }
            )

        # Second API call with tool results
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        response = requests.post(
            self.open_router_url, headers=self.open_router_headers, json=payload
        )

        response_data = response.json()
        final_result = response_data["choices"][0]["message"]["content"]
        print(response_data)

        return final_result
