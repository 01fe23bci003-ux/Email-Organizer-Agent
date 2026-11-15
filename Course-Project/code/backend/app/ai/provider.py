import os
from pathlib import Path
from typing import Any, Protocol

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class AIProvider(Protocol):
    name: str

    def complete(self, task: str, context: dict[str, Any]) -> str: ...


class MockAIProvider:
    name = "mock"

    def complete(self, task: str, context: dict[str, Any]) -> str:
        if task != "draft_reply":
            raise ValueError(f"Mock provider does not implement task: {task}")
        return str(context["fallback_draft"])


PROVIDER_FACTORIES: dict[str, type[AIProvider]] = {"mock": MockAIProvider}


def register_provider(name: str, provider_factory: type[AIProvider]) -> None:
    PROVIDER_FACTORIES[name.casefold()] = provider_factory


def get_provider() -> AIProvider:
    provider_name = os.getenv("AI_PROVIDER", "mock").casefold()
    factory = PROVIDER_FACTORIES.get(provider_name)
    if factory is None:
        raise RuntimeError(
            f"AI_PROVIDER={provider_name!r} is not registered. Register an AIProvider adapter or use 'mock'."
        )
    return factory()