"""Tiny LLM client over plain HTTP (requests); no vendor SDKs.

Provider and model come from the environment (a .env file is loaded if present):
  LLM_PROVIDER = groq | ollama     LLM_MODEL = model name
  groq:   GROQ_API_KEY
  ollama: OLLAMA_HOST (default http://localhost:11434)
All errors surface as LLMError.
"""
import os
import sys

import requests
from dotenv import find_dotenv, load_dotenv

from . import config

DEFAULT_MODELS = {"groq": "llama-3.3-70b-versatile", "ollama": "llama3.1:8b"}
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMError(Exception):
    pass


def _env():
    load_dotenv(find_dotenv(usecwd=True))  # never overrides variables already set
    provider = os.environ.get("LLM_PROVIDER", "groq").strip().lower()
    model = os.environ.get("LLM_MODEL", "").strip() or DEFAULT_MODELS.get(provider, "")
    return provider, model


def chat(system, user, timeout=None):
    """One temperature-0 chat completion that asks for a JSON object. Returns the text."""
    provider, model = _env()
    timeout = timeout or config.LLM_TIMEOUT
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        if provider == "groq":
            key = os.environ.get("GROQ_API_KEY", "").strip()
            if not key:
                raise LLMError("GROQ_API_KEY is not set")
            r = requests.post(
                GROQ_URL, timeout=timeout,
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "temperature": 0,
                      "response_format": {"type": "json_object"}})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        if provider == "ollama":
            host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
            r = requests.post(
                f"{host}/api/chat", timeout=timeout,
                json={"model": model, "messages": messages, "stream": False,
                      "format": "json", "options": {"temperature": 0}})
            r.raise_for_status()
            return r.json()["message"]["content"]
        raise LLMError(f"unknown LLM_PROVIDER {provider!r}; expected groq or ollama")
    except LLMError:
        raise
    except requests.RequestException as e:
        detail = ""
        if getattr(e, "response", None) is not None:
            detail = f" body={e.response.text[:300]!r}"
        raise LLMError(f"{provider} request failed: {e}{detail}") from e
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise LLMError(f"{provider} returned an unexpected response: {e!r}") from e


if __name__ == "__main__":  # pragma: no cover
    print(_env(), file=sys.stderr)
