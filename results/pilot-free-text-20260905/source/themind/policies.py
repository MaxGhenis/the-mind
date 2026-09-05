"""Stateless prompts, explicit baselines, and small auditable HTTP adapters.

No provider SDK, automatic retries, model substitution, tool execution, or fallback
actions are used. A failed call is an observed failure, never a fabricated move.
"""

from __future__ import annotations

import asyncio
import http.client
import ipaddress
import json
import math
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from typing import Any

from .engine import Decision, InvalidResponse, Observation, ProviderError

PROMPT_VERSION = "numerical-scheduling-v1"
MAX_RESPONSE_BYTES = 1_048_576
DEFAULT_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
}


class ProportionalPolicy:
    """An explicit shared convention that solves the idealized timing task."""

    def __init__(self, scale: float = 1.0):
        if isinstance(scale, bool) or not math.isfinite(scale) or scale <= 0:
            raise ValueError("scale must be finite and positive")
        self.scale = float(scale)

    @property
    def descriptor(self) -> dict:
        return {"policy": "proportional", "scale": self.scale}

    async def decide(self, obs: Observation) -> Decision:
        times = tuple(
            max(obs.now, obs.horizon * card / (obs.deck_size + 1) * self.scale) for card in obs.hand
        )
        return Decision(times, {"policy": self.descriptor})


class RandomPolicy:
    """Independent random times per card; deliberately does not sort them."""

    def __init__(self, seed: int):
        self.seed = seed
        self._rng = random.Random(seed)

    @property
    def descriptor(self) -> dict:
        return {"policy": "random", "seed": self.seed}

    async def decide(self, obs: Observation) -> Decision:
        times = tuple(self._rng.uniform(obs.now, obs.horizon) for _ in obs.hand)
        return Decision(times, {"policy": self.descriptor})


class OrdinalPolicy:
    """A hand-rank baseline that ignores card values and therefore induces ties."""

    @property
    def descriptor(self) -> dict:
        return {"policy": "ordinal"}

    async def decide(self, obs: Observation) -> Decision:
        times = tuple(
            obs.now + (obs.horizon - obs.now) * (index + 1) / (len(obs.hand) + 1)
            for index, _ in enumerate(obs.hand)
        )
        return Decision(times, {"policy": self.descriptor})


def build_prompts(obs: Observation, *, mode: str, convention: str) -> tuple[str, str]:
    """Serialize only a player's supplied observation, with no hidden state."""
    if mode not in {"precommit", "feedback"}:
        raise ValueError("mode must be precommit or feedback")
    if convention not in {"none", "proportional"}:
        raise ValueError("convention must be none or proportional")
    system = (
        "You are one player in a cooperative numerical scheduling task inspired "
        "by The Mind. This is a virtual-clock variant, not the commercial game's "
        "full rules. Unique integer cards were sampled without replacement from "
        "1 through deck_size and dealt privately. The team's objective is to play "
        "all dealt cards in strictly increasing numerical order by the round "
        "deadline horizon. You see only your remaining hand, public plays, and "
        "the current virtual time now. Other players' remaining cards and planned "
        "times are hidden. You cannot send messages to them. No tools are available. "
        "Times are absolute virtual round-clock values, never wall-clock times "
        "or delays. Model response latency does not advance this virtual clock. "
        "For each card in the supplied hand order, output its intended play time. "
        "Each time must be a finite number at least now; a time after horizon "
        "misses the deadline. Exact simultaneous plays are ordered by an "
        "independent randomized tie-break, so ties do not guarantee correct order. "
        'Return only a JSON object with exactly one key: {"times":[numbers]}. '
        "The array must have exactly as many entries as hand. No markdown fences, "
        "explanation, additional keys, or nonnumeric values. "
    )
    if mode == "precommit":
        system += (
            "All players commit their complete schedules once before any play. "
            "Every scheduled card is executed at its submitted time; there is "
            "no opportunity to revise this schedule. "
        )
    else:
        system += (
            "All active players submit a plan at each decision epoch. Only the "
            "first time, for your next lowest remaining card, is considered. "
            "After the next public play, all unexecuted plans are discarded and "
            "every active player replans from the new observation. "
        )
    if convention == "proportional":
        system += (
            "This condition supplies an explicit shared timing convention to "
            "every model player: play card c at max(now, horizon*c/(deck_size+1)). "
        )
    else:
        system += "No explicit timing convention is supplied in this condition. "
    system += (
        "A null time in a public play means that past play's timestamp was "
        "redacted; its card, seat, and chronological position remain visible. "
        "The current event time now remains visible even in that condition."
    )
    user = json.dumps(asdict(obs), separators=(",", ":"), allow_nan=False)
    return system, user


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _normalize_json_response(text: str) -> tuple[str, str]:
    """Remove one complete Markdown JSON fence, never prose or partial fences."""
    if isinstance(text, str):
        match = re.fullmatch(
            r"[ \t\r\n]*```(?:json)?[ \t]*\r?\n(.*?)\r?\n```[ \t\r\n]*",
            text,
            flags=re.DOTALL,
        )
        if match and "```" not in match.group(1):
            return match.group(1), "json_fence"
    return text, "none"


def parse_times(text: str, obs: Observation) -> tuple[float, ...]:
    """Validate the exact times schema, optionally inside one complete JSON fence.

    Only an enclosing triple-backtick fence with an optional literal ``json``
    label and newline-delimited contents is removed. Prose, multiple fences,
    malformed JSON, extra fields, and invalid numbers are never repaired.
    """
    text, _ = _normalize_json_response(text)
    try:
        result = json.loads(text, object_pairs_hook=_unique_object)
    except (ValueError, TypeError, RecursionError) as exc:
        raise InvalidResponse("Response is not a single strict JSON object") from exc
    if not isinstance(result, dict) or set(result) != {"times"}:
        raise InvalidResponse("Response must contain exactly the key 'times'")
    times = result["times"]
    if not isinstance(times, list) or len(times) != len(obs.hand):
        raise InvalidResponse("Response must provide one time for every remaining card")
    parsed = []
    for value in times:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidResponse("Every time must be a finite JSON number")
        try:
            value = float(value)
        except (ValueError, OverflowError) as exc:
            raise InvalidResponse("Every time must be a finite JSON number") from exc
        if not math.isfinite(value) or value < obs.now:
            raise InvalidResponse("Every time must be finite and at least now")
        parsed.append(value)
    return tuple(parsed)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # urllib normally forwards authentication headers during redirects.
        raise urllib.error.HTTPError(req.full_url, code, "Redirect refused", headers, fp)


def _validate_endpoint(endpoint: str) -> None:
    try:
        parsed = urllib.parse.urlsplit(endpoint)
        hostname = parsed.hostname
        parsed.port  # Validate malformed port syntax before creating a request.
    except ValueError as exc:
        raise ValueError("Invalid provider endpoint") from exc
    if not hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Endpoint must have a host and no credentials, query, or fragment")
    local = hostname == "localhost"
    try:
        local = local or ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        pass
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise ValueError("Provider endpoint requires HTTPS except on loopback hosts")


def _redact(value: Any, key: str) -> Any:
    """Keep an accidental provider echo of its credential out of audit files."""
    if isinstance(value, str):
        return value.replace(key, "[REDACTED]") if key else value
    if isinstance(value, list):
        return [_redact(item, key) for item in value]
    if isinstance(value, dict):
        return {_redact(name, key): _redact(item, key) for name, item in value.items()}
    return value


class JSONPolicy:
    """Text-only OpenAI-compatible chat completions or Anthropic messages.

    ``model`` and ``api_key_env`` are required and never inferred. ``max_tokens``
    is sent as ``max_completion_tokens`` to OpenAI-compatible providers and as
    ``max_tokens`` to Anthropic. Sampling temperature is omitted unless supplied,
    because not every model supports a configurable temperature.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        api_key_env: str,
        *,
        endpoint: str | None = None,
        mode: str = "precommit",
        convention: str = "none",
        timeout: float = 60.0,
        max_tokens: int = 512,
        temperature: float | None = None,
    ):
        if provider not in DEFAULT_ENDPOINTS:
            raise ValueError("provider must be openai or anthropic")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("An explicit model ID is required")
        if not isinstance(api_key_env, str) or not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*", api_key_env
        ):
            raise ValueError("api_key_env must name an environment variable")
        if mode not in {"precommit", "feedback"}:
            raise ValueError("mode must be precommit or feedback")
        if convention not in {"none", "proportional"}:
            raise ValueError("convention must be none or proportional")
        if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")
        if temperature is not None and (
            isinstance(temperature, bool)
            or not math.isfinite(temperature)
            or not 0 <= temperature <= (1 if provider == "anthropic" else 2)
        ):
            raise ValueError("temperature is outside the provider's supported range")
        self.provider = provider
        self.model = model
        self.api_key_env = api_key_env
        self.endpoint = endpoint or DEFAULT_ENDPOINTS[provider]
        _validate_endpoint(self.endpoint)
        self.mode = mode
        self.convention = convention
        self.timeout = float(timeout)
        self.max_tokens = max_tokens
        self.temperature = temperature

    @property
    def descriptor(self) -> dict:
        return {
            "policy": "json_http",
            "provider": self.provider,
            "requested_model": self.model,
            "endpoint": self.endpoint,
            "api_key_env": self.api_key_env,
            "mode": self.mode,
            "convention": self.convention,
            "timeout_seconds": self.timeout,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "prompt_version": PROMPT_VERSION,
            "retries": 0,
        }

    def _payload(self, system: str, user: str) -> dict:
        payload = {"model": self.model, "stream": False}
        if self.provider == "anthropic":
            payload.update(
                system=system,
                messages=[{"role": "user", "content": user}],
                max_tokens=self.max_tokens,
            )
        else:
            payload.update(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_completion_tokens=self.max_tokens,
            )
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        return payload

    def _post(self, payload: dict, key: str) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.provider == "anthropic":
            headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
        else:
            headers["Authorization"] = "Bearer " + key
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, allow_nan=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.build_opener(_NoRedirect()).open(
                request, timeout=self.timeout
            ) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            # Never read/log HTTP error bodies, which can reflect credentials.
            code = exc.code
            exc.close()
            raise ProviderError(f"Provider HTTP error {code}") from None
        except (OSError, urllib.error.URLError, http.client.HTTPException, ValueError) as exc:
            raise ProviderError(f"Provider transport failed ({type(exc).__name__})") from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderError("Provider response exceeded the byte limit")
        try:
            response = json.loads(raw, object_pairs_hook=_unique_object)
        except (ValueError, UnicodeError, RecursionError):
            raise ProviderError("Provider returned malformed response JSON") from None
        if not isinstance(response, dict):
            raise ProviderError("Provider response must be a JSON object")
        return response

    def _extract_text(self, response: dict, metadata: dict) -> str:
        metadata.update(
            resolved_model=response.get("model"),
            response_id=response.get("id"),
            usage=response.get("usage"),
            system_fingerprint=response.get("system_fingerprint"),
        )
        if self.provider == "anthropic":
            blocks = response.get("content")
            if not isinstance(blocks, list) or not blocks:
                raise ProviderError("Provider response has no content blocks")
            if any(not isinstance(block, dict) or block.get("type") != "text" for block in blocks):
                raise InvalidResponse("Provider returned non-text content; no tools are executed")
            texts = [block.get("text") for block in blocks]
            if any(not isinstance(text, str) for text in texts):
                raise ProviderError("Provider response has an invalid text block")
            text = "".join(texts)
            stop_reason = response.get("stop_reason")
            metadata.update(response_text=text, finish_reason=stop_reason)
            if stop_reason != "end_turn":
                raise InvalidResponse("Provider response did not complete normally")
        else:
            choices = response.get("choices")
            if (
                not isinstance(choices, list)
                or len(choices) != 1
                or not isinstance(choices[0], dict)
            ):
                raise ProviderError("Provider response must contain exactly one choice")
            choice = choices[0]
            message = choice.get("message")
            if not isinstance(message, dict):
                raise ProviderError("Provider choice has no message")
            text = message.get("content")
            metadata.update(response_text=text, finish_reason=choice.get("finish_reason"))
            if message.get("tool_calls") or message.get("function_call"):
                raise InvalidResponse("Provider returned a tool call; no tools are executed")
            if message.get("refusal"):
                raise InvalidResponse("Provider refused the requested response")
            if choice.get("finish_reason") != "stop":
                raise InvalidResponse("Provider response did not complete normally")
            if not isinstance(text, str):
                raise InvalidResponse("Provider response has no text")
        return text

    async def decide(self, obs: Observation) -> Decision:
        system, user = build_prompts(obs, mode=self.mode, convention=self.convention)
        payload = self._payload(system, user)
        metadata = {
            "policy": self.descriptor,
            "requested_model": self.model,
            "resolved_model": None,
            "prompts": {"system": system, "user": user},
            "request_body": payload,
            "request_latency_seconds": 0.0,
            "normalization": "none",
        }
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise ProviderError(
                f"Missing API key environment variable {self.api_key_env}", metadata
            )
        started = time.perf_counter()
        try:
            response = await asyncio.to_thread(self._post, payload, key)
            metadata["request_latency_seconds"] = time.perf_counter() - started
            # Redact before extracting text so neither exception nor audit can echo the key.
            response = _redact(response, key)
            metadata["response_body"] = response
            text = self._extract_text(response, metadata)
            _, metadata["normalization"] = _normalize_json_response(text)
            times = parse_times(text, obs)
        except (ProviderError, InvalidResponse) as exc:
            metadata["request_latency_seconds"] = time.perf_counter() - started
            metadata = _redact(metadata, key)
            message = str(exc)
            if isinstance(exc, InvalidResponse) and isinstance(metadata.get("response_text"), str):
                excerpt = metadata["response_text"][:200]
                message += f"; response excerpt: {excerpt!r}"
            raise type(exc)(_redact(message, key), metadata) from None
        return Decision(times, _redact(metadata, key))
