from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.chat_models import init_chat_model
from langchain.tools import Tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)

from app.llm.templates import (
    examples,
    human_template,
    technical_analysis_template,
)


class LLM:
    def __init__(self) -> None:
        self.model = init_chat_model(
            "gpt-4o",
            model_provider="openai",
            temperature=0.7,
        )

    def change_model(self, model_name: str) -> None:
        self.model = init_chat_model(
            model_name, model_provider="openai", temperature=0.7
        )

    def get_technical_analysis(
        self, utterance: str, stock_data_func, chat_history=None
    ):
        tools = [
            Tool(
                name="get_stock_data",
                description="Get stock data for a given ticker symbol (e.g. '011070.KS'). Returns OHLCV data for technical analysis.",
                func=stock_data_func,
            )
        ]

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            technical_analysis_template
        )
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

        history_messages = []
        if chat_history:
            for chat in chat_history:
                history_messages.extend(
                    [
                        HumanMessage(content=chat.utterance),
                        AIMessage(content=chat.response),
                    ]
                )
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt_template = ChatPromptTemplate.from_messages(
            [
                system_message_prompt,
                few_shot_prompt,
                MessagesPlaceholder(variable_name="chat_history"),
                human_message_prompt,
                ("assistant", "{agent_scratchpad}"),
            ]
        )
        agent = create_openai_functions_agent(self.model, tools, chat_prompt_template)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
        )

        result = agent_executor.invoke(
            {"user_query": utterance, "chat_history": history_messages}
        )

        return result["output"]
