"""LLM abstraction factory — Ollama/Groq/Claude/OpenAI backends."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

from jyotish.config import get as cfg_get

# Default max tokens for LLM responses — used across all backends
LLM_MAX_TOKENS = 4096


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
        self._model = model or cfg_get("llm.ollama.model", "qwen3:8b")
        self._base_url = base_url or cfg_get("llm.ollama.base_url", "http://localhost:11434")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate response via local Ollama server."""
        try:
            import ollama
        except ImportError:
            raise RuntimeError("Ollama package not installed. Run: pip install ollama")
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
            return response["message"]["content"]
        except Exception as e:
            raise RuntimeError(
                f"Ollama error: {e}\n"
                f"Make sure Ollama is running: ollama serve\n"
                f"And model is pulled: ollama pull {self._model}"
            )

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
        self._model = model or cfg_get("llm.groq.model", "llama-3.1-8b-instant")
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate response via Groq cloud API."""
        try:
            from groq import Groq
        except ImportError:
            raise RuntimeError("Groq package not installed. Run: pip install groq")
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
        self._model = model or cfg_get("llm.claude.model", "claude-sonnet-4-20250514")
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate response via Anthropic Claude API."""
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("Anthropic package not installed. Run: pip install anthropic")
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
        return response.content[0].text

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
        self._model = model or cfg_get("llm.openai.model", "gpt-4o")
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Generate response via OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("OpenAI package not installed. Run: pip install openai")
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
        name: Backend name (ollama/groq/claude/openai/none). Default from config.
        model: Override model name.
        api_key: Override API key.

    Returns:
        An LLMBackend instance.
    """
    if name is None:
        name = cfg_get("llm.default_backend", "ollama")

    backend_class = _BACKENDS.get(name)
    if backend_class is None:
        raise ValueError(
            f"Unknown backend: {name}. Options: {', '.join(_BACKENDS.keys())}"
        )

    if name == "none":
        return NoLLMBackend()

    kwargs: dict = {}
    if model:
        kwargs["model"] = model
    if api_key:
        kwargs["api_key"] = api_key

    return backend_class(**kwargs)  # type: ignore[call-arg]


def list_backends() -> list[str]:
    """List all available backend names."""
    return list(_BACKENDS.keys())
