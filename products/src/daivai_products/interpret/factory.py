"""LLM abstraction factory — Ollama/Groq/Claude/OpenAI backends."""

from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable


logger = logging.getLogger(__name__)

# Default max tokens for LLM responses — used across all backends
LLM_MAX_TOKENS = 4096

# Default config values (replaces jyotish.config dependency)
_DEFAULTS: dict[str, str] = {
    "llm.default_backend": "ollama",
    "llm.ollama.model": "qwen3:8b",
    "llm.ollama.base_url": "http://localhost:11434",
    "llm.groq.model": "llama-3.1-8b-instant",
    "llm.claude.model": "claude-sonnet-4-20250514",
    "llm.openai.model": "gpt-4o",
}


@runtime_checkable
class LLMBackend(Protocol):
    """Protocol defining the interface for all LLM backends."""

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate a response from the LLM."""
        ...

    def name(self) -> str:
        """Return the backend name (e.g. 'groq/llama-3.1-8b-instant')."""
        ...

    def is_available(self) -> bool:
        """Check if this backend is configured and reachable."""
        ...


class OllamaBackend:
    """Ollama local LLM backend."""

    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        """Initialize with model name and Ollama server URL."""
        self._model = model or _DEFAULTS["llm.ollama.model"]
        self._base_url = base_url or _DEFAULTS["llm.ollama.base_url"]

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate response via local Ollama server."""
        try:
            import ollama
        except ImportError:
            raise RuntimeError("Ollama package not installed. Run: pip install ollama") from None
        try:
            client = ollama.Client(host=self._base_url)
            response = client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                options={"temperature": temperature},
            )
            return str(response["message"]["content"])
        except Exception as e:
            raise RuntimeError(
                f"Ollama error: {e}\n"
                f"Make sure Ollama is running: ollama serve\n"
                f"And model is pulled: ollama pull {self._model}"
            ) from e

    def name(self) -> str:
        """Return backend identifier."""
        return f"ollama/{self._model}"

    def is_available(self) -> bool:
        """Check if Ollama server is running and model exists."""
        try:
            import ollama

            client = ollama.Client(host=self._base_url)
            client.list()
            return True
        except Exception:
            return False


class GroqBackend:
    """Groq cloud LLM backend (free tier)."""

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        """Initialize with model name and API key."""
        self._model = model or _DEFAULTS["llm.groq.model"]
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate response via Groq cloud API."""
        try:
            from groq import Groq
        except ImportError:
            raise RuntimeError("Groq package not installed. Run: pip install groq") from None
        if not self._api_key:
            raise RuntimeError("GROQ_API_KEY not set. Get one at https://console.groq.com")
        client = Groq(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content or ""

    def name(self) -> str:
        """Return backend identifier."""
        return f"groq/{self._model}"

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self._api_key)


class ClaudeBackend:
    """Anthropic Claude API backend."""

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        """Initialize with model name and API key."""
        self._model = model or _DEFAULTS["llm.claude.model"]
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate response via Anthropic Claude API."""
        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "Anthropic package not installed. Run: pip install anthropic"
            ) from None
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set.")
        client = anthropic.Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model=self._model,
            max_tokens=LLM_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
        )
        block = response.content[0]
        return block.text if hasattr(block, "text") else str(block)

    def name(self) -> str:
        """Return backend identifier."""
        return f"claude/{self._model}"

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self._api_key)


class OpenAIBackend:
    """OpenAI API backend."""

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        """Initialize with model name and API key."""
        self._model = model or _DEFAULTS["llm.openai.model"]
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate response via OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("OpenAI package not installed. Run: pip install openai") from None
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY not set.")
        client = OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content or ""

    def name(self) -> str:
        """Return backend identifier."""
        return f"openai/{self._model}"

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self._api_key)


class NoLLMBackend:
    """Dummy backend — returns raw prompt data without LLM interpretation."""

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Return the user prompt as-is (no LLM processing)."""
        return user_prompt

    def name(self) -> str:
        """Return backend identifier."""
        return "none"

    def is_available(self) -> bool:
        """Always available — no external dependency."""
        return True


_BACKENDS: dict[str, type] = {
    "ollama": OllamaBackend,
    "groq": GroqBackend,
    "claude": ClaudeBackend,
    "openai": OpenAIBackend,
    "none": NoLLMBackend,
}


def get_backend(
    name: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> LLMBackend:
    """Factory function to get an LLM backend.

    Args:
        name: Backend name (ollama/groq/claude/openai/none). Default: ollama.
        model: Override model name.
        api_key: Override API key.

    Returns:
        An LLMBackend instance.
    """
    if name is None:
        name = _DEFAULTS["llm.default_backend"]

    backend_class = _BACKENDS.get(name)
    if backend_class is None:
        raise ValueError(f"Unknown backend: {name}. Options: {', '.join(_BACKENDS.keys())}")

    if name == "none":
        return NoLLMBackend()

    kwargs: dict = {}
    if model:
        kwargs["model"] = model
    if api_key:
        kwargs["api_key"] = api_key

    return backend_class(**kwargs)  # type: ignore[call-arg, no-any-return]


def list_backends() -> list[str]:
    """List all available backend names."""
    return list(_BACKENDS.keys())
