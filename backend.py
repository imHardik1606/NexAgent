from dataclasses import dataclass, field
import json
import time
from typing import Any, Protocol
from uuid import uuid4

import config


@dataclass
class BackendResponse:
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    error: str = ""


class ProviderError(RuntimeError):
    """Raised when a provider or request payload prevents an evaluation step."""


class ModelBackend(Protocol):
    model_name: str

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> BackendResponse:
        ...


def _tool_call(call: Any) -> dict[str, Any]:
    if isinstance(call, dict):
        function = call.get("function", call)
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except (TypeError, ValueError):
                pass
        return {"id": call.get("id") or f"call_{uuid4().hex}", "type": "function",
                "function": {"name": function.get("name", ""), "arguments": arguments}}
    function = getattr(call, "function", None)
    arguments = getattr(function, "arguments", {})
    return {"id": getattr(call, "id", None) or f"call_{uuid4().hex}", "type": "function",
            "function": {"name": getattr(function, "name", ""), "arguments": arguments}}


def _value(response: Any, name: str, default: Any = None) -> Any:
    if isinstance(response, dict):
        return response.get(name, default)
    return getattr(response, name, default)


def _canonical_message(message: dict[str, Any], provider: str) -> dict[str, Any]:
    converted = {key: value for key, value in message.items() if key not in {"tool_calls", "tool_call_id", "tool_name"}}
    if message.get("role") == "assistant" and message.get("tool_calls"):
        calls = message["tool_calls"]
        if provider == "cloud":
            converted["tool_calls"] = [
                {"id": call["id"], "type": "function",
                 "function": {"name": call["function"]["name"],
                               "arguments": call["function"]["arguments"] if isinstance(call["function"]["arguments"], str)
                               else json.dumps(call["function"]["arguments"])} }
                for call in calls
            ]
        else:
            converted["tool_calls"] = [
                {"id": call["id"], "function": {"name": call["function"]["name"],
                                                   "arguments": call["function"]["arguments"]}}
                for call in calls
            ]
    elif message.get("role") == "tool" and provider == "local":
        converted["tool_name"] = message.get("tool_name", "")
    if message.get("role") == "tool":
        converted["content"] = message.get("content", "")
    return converted


def _provider_messages(messages: list[dict[str, Any]], provider: str) -> list[dict[str, Any]]:
    tool_names = {
        call["id"]: call["function"]["name"]
        for message in messages
        if message.get("role") == "assistant"
        for call in message.get("tool_calls", [])
    }
    converted = []
    for message in messages:
        item = _canonical_message(message, provider)
        if provider == "local" and message.get("role") == "tool":
            item["tool_name"] = message.get("tool_name") or tool_names.get(message.get("tool_call_id", ""), "")
        if provider == "cloud" and message.get("role") == "tool":
            item["tool_call_id"] = message.get("tool_call_id", "")
        converted.append(item)
    return converted


class CloudBackend:
    model_name = config.CLOUD_MODEL

    def __init__(self) -> None:
        if not config.GROQ_API_KEY or config.GROQ_API_KEY == "your_key_here":
            raise ValueError("GROQ_API_KEY is required for cloud mode")
        from groq import Groq
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def preflight(self) -> None:
        try:
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Reply with OK."}],
                max_tokens=1,
                temperature=0.0,
            )
        except Exception as exc:
            raise ProviderError(f"Cloud model {self.model_name} preflight failed: {exc}") from exc

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> BackendResponse:
        started = time.perf_counter()
        try:
            response = self.client.chat.completions.create(model=self.model_name,
                                                           messages=_provider_messages(messages, "cloud"), tools=tools,
                                                           tool_choice="auto", temperature=config.TEMPERATURE)
            message = response.choices[0].message
            usage = response.usage
            return BackendResponse(content=message.content or "", tool_calls=[_tool_call(call) for call in (message.tool_calls or [])],
                                   prompt_tokens=getattr(usage, "prompt_tokens", 0), completion_tokens=getattr(usage, "completion_tokens", 0),
                                   latency_s=time.perf_counter() - started)
        except Exception as exc:
            raise ProviderError(f"Cloud provider request failed for {self.model_name}: {exc}") from exc


class LocalBackend:
    model_name = config.LOCAL_MODEL

    def __init__(self) -> None:
        from ollama import Client
        self.client = Client(host="http://localhost:11434")

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> BackendResponse:
        started = time.perf_counter()
        try:
            response = self.client.chat(model=self.model_name, messages=_provider_messages(messages, "local"), tools=tools,
                                        options={"temperature": config.TEMPERATURE})
            message = _value(response, "message", {})
            message = message if isinstance(message, dict) else {
                "content": getattr(message, "content", ""),
                "tool_calls": getattr(message, "tool_calls", []) or [],
            }
            return BackendResponse(content=message.get("content", ""),
                                   tool_calls=[_tool_call(call) for call in message.get("tool_calls", [])],
                                   prompt_tokens=_value(response, "prompt_eval_count", 0) or 0,
                                   completion_tokens=_value(response, "eval_count", 0) or 0,
                                   latency_s=time.perf_counter() - started)
        except Exception as exc:
            raise ProviderError(f"Ollama provider request failed for {self.model_name}: {exc}") from exc