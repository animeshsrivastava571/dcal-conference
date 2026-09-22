"""Minimal LangChain + Claude example."""

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()  # reads ANTHROPIC_API_KEY from .env

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    max_tokens=16000,
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a concise assistant. Answer in at most 3 sentences."),
        ("human", "{question}"),
    ]
)

chain = prompt | llm | StrOutputParser()


def ask(question: str) -> str:
    return chain.invoke({"question": question})


if __name__ == "__main__":
    print(ask("Tell me capital of Iceland"))
