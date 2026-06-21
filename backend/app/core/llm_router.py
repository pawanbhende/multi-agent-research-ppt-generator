"""
LLM Router
----------
Single place that turns (provider, model_name) into a ready-to-use LangChain
chat model instance. Agents never import langchain_openai/anthropic/groq
directly — they call `get_chat_model(role="researcher")` and the router
decides which provider/model to hand back based on Settings.

This indirection is what lets us swap GPT-4o <-> Claude <-> Llama-3.3-on-Groq
per agent via env vars alone, with zero code changes in the agents.
"""

from functools import lru_cache
from typing import Literal

from app.core.config import get_settings
from app.core.logging_config import logger

AgentRole = Literal["researcher", "analyst", "designer"]
Provider = Literal["openai", "anthropic", "groq"]


def _build_model(provider: Provider, model_name: str, temperature: float):
    settings = get_settings()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model_name,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=4096,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        # Fallback check for decommissioned Llama 3.1 legacy models
        if "llama-3.1-70b-versatile" in model_name:
            logger.warning(
                f"[LLM Router] intercepting decommissioned model '{model_name}'. Re-routing automatically to 'llama-3.3-70b-versatile'."
            )
            model_name = "llama-3.3-70b-versatile"

        return ChatGroq(
            model=model_name,
            api_key=settings.groq_api_key,
            temperature=temperature,
        )

    raise ValueError(f"Unknown LLM provider: {provider}")


@lru_cache(maxsize=8)
def get_chat_model(role: AgentRole, temperature: float = 0.3):
    """
    Returns a cached LangChain chat model instance configured for the given
    agent role, based on Settings (which is populated from .env).
    """
    settings = get_settings()

    role_config = {
        "researcher": (settings.researcher_model_provider, settings.researcher_model_name),
        "analyst": (settings.analyst_model_provider, settings.analyst_model_name),
        "designer": (settings.designer_model_provider, settings.designer_model_name),
    }

    if role not in role_config:
        raise ValueError(f"Unknown agent role: {role}")

    provider, model_name = role_config[role]
    logger.info(f"[LLM Router] role={role} -> provider={provider} model={model_name}")

    return _build_model(provider, model_name, temperature)