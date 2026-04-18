from langchain_groq import ChatGroq

from config.settings import get_settings


def get_llm(temperature: float = 0.1) -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
    )
