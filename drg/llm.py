"""Tiny LLM client over plain HTTP (requests); no vendor SDKs.

Provider and model come from the environment (a .env file is loaded if present):
  LLM_PROVIDER = groq | ollama     LLM_MODEL = model name
  groq:   GROQ_API_KEY
  ollama: OLLAMA_HOST (default http://localhost:11434)
All errors surface as LLMError.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import find_dotenv, load_dotenv

from . import config

DEFAULT_MODELS = {"groq": "llama-3.3-70b-versatile", "ollama": "llama3.1:8b"}
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMError(Exception):
    def __init__(self, msg, status=None):
        super().__init__(msg)
        self.status = status  # HTTP status when the failure was an HTTP error


class LLMQuotaError(LLMError):
    """The provider's daily limit is reached (429 with a long retry-after): retrying within this process is pointless."""


QUOTA_WAIT_S = 60  # a 429 asking for a longer wait than this is a daily cap (TPD / RPD): fail fast, do not sleep
api_calls = 0  # real provider requests made by chat() in this process (cache hits excluded)
total_wait = 0.0  # seconds spent sleeping on 429 retry-after waits in this process (for eval latency)
RETRY_429 = 3  # retries after an HTTP 429
RETRY_WAIT_DEFAULT = 20  # seconds, when there is no usable retry-after header


def _retry_after(r):
    try:
        return max(0.0, float(r.headers.get("retry-after")))
    except (TypeError, ValueError):
        return float(RETRY_WAIT_DEFAULT)


def _post(url, **kw):
    """requests.post; on 429 wait for retry-after (else 20 s) and retry up to 3 times.
    A 413 raises LLMError(status=413) so the caller can shrink the request."""
    for attempt in range(RETRY_429 + 1):
        r = requests.post(url, **kw)
        if r.status_code == 429 and attempt < RETRY_429:
            wait = _retry_after(r)
            if wait > QUOTA_WAIT_S:
                raise LLMQuotaError(f"HTTP 429: provider limit reached, retry-after {wait:g}s "
                                    f"(> {QUOTA_WAIT_S}s: daily cap) - not waiting: {r.text[:240]!r}", status=429)
            print(f"LLM HTTP 429 (rate limited): waiting {wait:g}s, retry {attempt + 1}/{RETRY_429}",
                  file=sys.stderr, flush=True)
            time.sleep(wait)
            global total_wait
            total_wait += wait
            continue
        if r.status_code == 413:
            raise LLMError(f"HTTP 413 request too large: {r.text[:300]!r}", status=413)
        return r


def _env():
    load_dotenv(find_dotenv(usecwd=True))  # never overrides variables already set
    provider = os.environ.get("LLM_PROVIDER", "groq").strip().lower()
    model = os.environ.get("LLM_MODEL", "").strip() or DEFAULT_MODELS.get(provider, "")
    return provider, model


# ------------------------------------------------------------------ optional response cache (evaluation only)
# Keyed on (provider, model, system, user); a hit makes no API call. Off unless enable_cache() is called (run_eval
# does it for --answers); the ask / search CLIs never use it. Only successful responses are stored.
_cache = {"dir": None, "hits": 0, "misses": 0}


def enable_cache(path):
    _cache["dir"] = Path(path)
    _cache["dir"].mkdir(parents=True, exist_ok=True)


def cache_stats():
    return dict(hits=_cache["hits"], misses=_cache["misses"])


def cache_key(system, user):
    provider, model = _env()
    return hashlib.sha256("\x00".join([provider, model, system, user]).encode("utf-8")).hexdigest()


def _cache_file(system, user):
    return _cache["dir"] / (cache_key(system, user) + ".json")


def cache_put(system, user, text):
    if _cache["dir"] is not None:
        _cache_file(system, user).write_text(json.dumps({"text": text}), encoding="utf-8")


def chat(system, user, timeout=None):
    """One temperature-0 chat completion that asks for a JSON object. Returns the text."""
    if _cache["dir"] is not None:
        f = _cache_file(system, user)
        if f.exists():
            _cache["hits"] += 1
            print("LLM cache hit (no API call)", file=sys.stderr, flush=True)
            return json.loads(f.read_text(encoding="utf-8"))["text"]
        _cache["misses"] += 1
    text = _chat_uncached(system, user, timeout)
    cache_put(system, user, text)
    return text


def _chat_uncached(system, user, timeout=None):
    global api_calls
    api_calls += 1
    provider, model = _env()
    timeout = timeout or config.LLM_TIMEOUT
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        if provider == "groq":
            key = os.environ.get("GROQ_API_KEY", "").strip()
            if not key:
                raise LLMError("GROQ_API_KEY is not set")
            r = _post(
                GROQ_URL, timeout=timeout,
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "temperature": 0,
                      "response_format": {"type": "json_object"}})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        if provider == "ollama":
            host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
            r = _post(
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
        status = getattr(getattr(e, "response", None), "status_code", None)
        raise LLMError(f"{provider} request failed: {e}{detail}", status=status) from e
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise LLMError(f"{provider} returned an unexpected response: {e!r}") from e


if __name__ == "__main__":  # pragma: no cover
    print(_env(), file=sys.stderr)
