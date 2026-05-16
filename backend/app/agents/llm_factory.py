"""LLM provider factory — creates appropriate LLM instance based on config."""

import logging
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class LLMUsage:
    """Track token usage across LLM calls."""
    def __init__(self):
        self.input_tokens: int = 0
        self.output_tokens: int = 0

    def record(self, result: Any):
        metadata = getattr(result, "usage_metadata", None) or {}
        self.input_tokens = metadata.get("input_tokens", 0)
        self.output_tokens = metadata.get("output_tokens", 0)

    def to_dict(self) -> Dict[str, int]:
        return {"input_tokens": self.input_tokens, "output_tokens": self.output_tokens}


class LLMWrapper:
    """Wrapper that provides a unified ainvoke interface for all providers."""

    def __init__(self, llm: Any, usage: Optional[LLMUsage] = None):
        self._llm = llm
        self._usage = usage or LLMUsage()

    @property
    def last_token_usage(self) -> Dict[str, int]:
        return self._usage.to_dict()

    async def ainvoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        result = await self._llm.ainvoke(messages)
        self._usage.record(result)
        return result.content


def _try_import(module: str, package: str = None) -> Any:
    """Try to import a module, return None if unavailable."""
    try:
        return __import__(module) if package is None else __import__(module, fromlist=[package])
    except ImportError:
        return None


def create_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
) -> "LLMWrapper":
    """Create an LLM instance based on provider configuration.

    Args:
        model: Model name (defaults to settings.LLM_MODEL)
        temperature: Temperature (defaults to settings.LLM_TEMPERATURE)
        api_key: API key (defaults to settings.LLM_API_KEY)
        provider: Provider name (defaults to settings.LLM_PROVIDER)
        base_url: Base URL for custom endpoints (defaults to settings.LLM_BASE_URL)

    Returns:
        LLMWrapper instance with unified ainvoke interface

    Raises:
        LLMError: If the provider is unsupported or dependencies are missing
    """
    model = model or settings.LLM_MODEL or settings.OPENAI_MODEL or "gpt-4-turbo"
    temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE or 0.7
    api_key = api_key or settings.LLM_API_KEY or settings.OPENAI_API_KEY or ""
    provider = (provider or settings.LLM_PROVIDER or "openai").lower()
    base_url = base_url or settings.LLM_BASE_URL or ""

    api_key = api_key.strip() if api_key else ""
    if not api_key and provider not in ("ollama",):
        raise LLMError(
            f"API key required for provider '{provider}'. "
            f"Set LLM_API_KEY in .env or switch to LLM_PROVIDER=ollama"
        )

    logger.info(f"Creating LLM: provider={provider}, model={model}")

    if provider == "openai":
        return _create_openai(model, temperature, api_key)
    elif provider == "gemini":
        return _create_gemini(model, temperature, api_key)
    elif provider == "ollama":
        return _create_ollama(model, temperature, base_url)
    elif provider == "custom":
        return _create_custom_openai_compatible(model, temperature, api_key, base_url)
    else:
        raise LLMError(f"Unsupported LLM provider: {provider}")


def _create_openai(model: str, temperature: float, api_key: str) -> LLMWrapper:
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key or None,
        )
        logger.info("Using OpenAI provider")
        return LLMWrapper(llm)
    except ImportError:
        raise LLMError("OpenAI provider requires: pip install langchain-openai")


def _create_anthropic(model: str, temperature: float, api_key: str) -> LLMWrapper:
    try:
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(
            model=model,
            temperature=temperature,
            anthropic_api_key=api_key or None,
        )
        logger.info("Using Anthropic provider")
        return LLMWrapper(llm)
    except ImportError:
        raise LLMError("Anthropic provider requires: pip install langchain-anthropic")


def _create_gemini(model: str, temperature: float, api_key: str) -> LLMWrapper:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key or None,
        )
        logger.info("Using Google Gemini provider")
        return LLMWrapper(llm)
    except ImportError:
        raise LLMError("Gemini provider requires: pip install langchain-google-genai")


def _create_ollama(model: str, temperature: float, base_url: str) -> LLMWrapper:
    try:
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url or settings.OLLAMA_BASE_URL or "http://localhost:11434",
        )
        logger.info("Using Ollama provider")
        return LLMWrapper(llm)
    except ImportError:
        raise LLMError("Ollama provider requires: pip install langchain-ollama")


def _create_custom_openai_compatible(
    model: str, temperature: float, api_key: str, base_url: str
) -> LLMWrapper:
    if not base_url:
        raise LLMError("Custom OpenAI-compatible provider requires LLM_BASE_URL to be set")
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key or None,
            base_url=base_url,
        )
        logger.info(f"Using custom OpenAI-compatible provider: {base_url}")
        return LLMWrapper(llm)
    except ImportError:
        raise LLMError("Custom provider requires: pip install langchain-openai")


def create_embeddings(
    text: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> list:
    """Generate embeddings for text using the configured provider.

    Args:
        text: Input text to embed
        provider: Embedding provider (openai | ollama | custom)
        api_key: API key
        model: Embedding model name
        base_url: Base URL for custom endpoints

    Returns:
        List of floats (embedding vector)
    """
    provider = (provider or settings.EMBEDDING_PROVIDER or "openai").lower()
    api_key = api_key or settings.EMBEDDING_API_KEY or settings.LLM_API_KEY or settings.OPENAI_API_KEY or ""
    model = model or settings.EMBEDDING_MODEL or "text-embedding-3-small"
    base_url = base_url or settings.EMBEDDING_BASE_URL or ""

    logger.info(f"Generating embedding: provider={provider}, model={model}")

    if provider == "ollama":
        return _ollama_embed(text, model, base_url)
    elif provider == "custom":
        return _custom_openai_embed(text, model, api_key, base_url)
    else:
        return _openai_embed(text, model, api_key)


def _openai_embed(text: str, model: str, api_key: str) -> list:
    try:
        import openai
        client = openai.OpenAI(api_key=api_key or None)
        resp = client.embeddings.create(model=model, input=text)
        return resp.data[0].embedding
    except ImportError:
        raise LLMError("OpenAI embedding requires: pip install openai")


def _ollama_embed(text: str, model: str, base_url: str) -> list:
    try:
        import httpx
        url = (base_url or settings.OLLAMA_BASE_URL or "http://localhost:11434") + "/api/embed"
        resp = httpx.post(url, json={"model": model, "input": text}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings", [])
        if not embeddings:
            raise LLMError(f"Ollama embedding returned empty result for model '{model}'")
        return embeddings[0]
    except ImportError:
        raise LLMError("Ollama embedding requires: pip install httpx")
    except Exception as e:
        raise LLMError(f"Ollama embedding failed: {e}")


def _custom_openai_embed(text: str, model: str, api_key: str, base_url: str) -> list:
    if not base_url:
        raise LLMError("Custom embedding requires EMBEDDING_BASE_URL to be set")
    try:
        import openai
        client = openai.OpenAI(api_key=api_key or None, base_url=base_url)
        resp = client.embeddings.create(model=model, input=text)
        return resp.data[0].embedding
    except ImportError:
        raise LLMError("Custom embedding requires: pip install openai")
