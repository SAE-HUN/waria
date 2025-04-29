from langchain.chat_models import init_chat_model
from langchain.tools import Tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
from typing import List
from app.models import ChatHistory
import time
from datetime import datetime

from app.llm.templates import (
    examples,
    technical_analysis_template,
)


class LLM:
    def __init__(self) -> None:
        self.model = init_chat_model(
            "claude-3-7-sonnet-latest", model_provider="anthropic", temperature=0.7
        )

    def change_model(self, model_name: str) -> None:
        self.model = init_chat_model(model_name, model_provider="openai", temperature=0)

    def get_technical_analysis(
        self, utterance: str, stock_data_func, chat_history: List[ChatHistory]
    ):
        tools = [
            Tool(
                name="get_stock_data",
                description="Get stock data for a given ticker symbol (e.g. '011070.KS'). Returns OHLCV data for technical analysis.",
                func=stock_data_func,
            )
        ]

        system_message = SystemMessage(content=technical_analysis_template)
        example_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", "{input}"),
                ("ai", "{output}"),
            ]
        )
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=examples,
        )
        few_shot_messages = few_shot_prompt.format()
        messages = [system_message]
        messages.extend(few_shot_messages)

        for chat in chat_history:
            if not chat.utterance or not chat.response:
                continue
            messages.append(HumanMessage(content=chat.utterance))
            messages.append(AIMessage(content=chat.response))
        messages.append(HumanMessage(content=utterance))

        llm_with_tools = self.model.bind_tools(tools)

        start_time = time.time()
        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"\nllm_with_tools.invoke start: {current_time}")

        ai_message = llm_with_tools.invoke(messages)

        end_time = time.time()
        elapsed = end_time - start_time
        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"llm_with_tools.invoke end: {current_time} (took {elapsed:.3f}s)")
        print(ai_message)

        if not ai_message.tool_calls:
            return ai_message.content
        
        messages.append(ai_message)
        for tool_call in ai_message.tool_calls:
            selected_tool = {"get_stock_data": tools[0]}[tool_call["name"].lower()]

            start_time = time.time()
            current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"\nselected_tool.invoke start: {current_time}")
            tool_message = selected_tool.invoke(tool_call)
            end_time = time.time()
            elapsed = end_time - start_time
            current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"selected_tool.invoke end: {current_time} (took {elapsed:.3f}s)")
            messages.append(tool_message)

        start_time = time.time()
        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"\nllm_with_data.invoke start: {current_time}")

        result = llm_with_tools.invoke(messages)
        print(result)

        end_time = time.time()
        elapsed = end_time - start_time
        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"llm_with_data.invoke end: {current_time} (took {elapsed:.3f}s)")

        return result.content