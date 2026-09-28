import json
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from backend import CloudBackend, LocalBackend, ModelBackend
from config import BASE_PATH, ESCALATE_TOOLS, MAX_STEPS, TEMPERATURE
from logger import logger
from tools import AVAILABLE_FUNCTIONS, TOOL_DEFINITIONS, configure_run, get_tool_audit, load_memory
from traceroot import observe, update_current_span


@dataclass
class ModelCall:
    step_index: int
    backend: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    latency_s: float
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_call_valid: bool = True
    escalated: bool = False
    error: str = ""
    blocked_command_attempted: bool = False


@dataclass
class RunResult:
    final_answer: str = ""
    steps: int = 0
    calls: list[ModelCall] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    passed: bool = False
    failure_reason: str = ""
    hit_step_limit: bool = False


SYSTEM_PROMPT = (
    "You are NexAgent, a professional and high-end AI assistant. "
    "You have access to tools for filesystem operations and web searching. "
    "GUIDELINES:\n"
    "1. Always identify yourself clearly as NexAgent.\n"
    "2. Use tools whenever needed to provide accurate info.\n"
    "3. If a tool result is technical, summarize it in clean English.\n"
    "4. If 'wttr.in' is down, try searching the web for current weather.\n"
    "5. Avoid technical shorthand when it looks messy.\n"
    "6. DO NOT hallucinate tool calls or use XML-like tags. Output ONLY valid JSON tool calls when using a tool.\n"
    "7. Do not provide explanations or thoughts before making a tool call.\n"
    "8. Be concise and confirm your actions professionally."
)


def _parse_arguments(raw: Any) -> tuple[dict[str, Any] | None, str]:
    if isinstance(raw, dict):
        return raw, ""
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError) as exc:
        return None, f"malformed tool arguments: {exc}"
    if not isinstance(parsed, dict):
        return None, "tool arguments must be a JSON object"
    return parsed, ""


def _canonical_call(call: dict[str, Any]) -> dict[str, Any]:
    function = call.get("function", call)
    arguments = function.get("arguments", {})
    return {
        "id": call.get("id") or f"call_{uuid4().hex}",
        "type": "function",
        "function": {"name": function.get("name", ""), "arguments": arguments},
    }


def _tool_schemas(eval_mode: bool) -> list[dict[str, Any]]:
    if not eval_mode:
        return TOOL_DEFINITIONS
    return [schema for schema in TOOL_DEFINITIONS
            if schema["function"]["name"] not in {"search_web", "get_weather", "update_memory"}]


def _backend_pair(mode: str, backends: dict[str, ModelBackend] | None) -> dict[str, ModelBackend]:
    if backends is not None:
        return backends
    if mode == "all_local":
        return {"local": LocalBackend()}
    if mode == "all_cloud":
        return {"cloud": CloudBackend()}
    return {"local": LocalBackend(), "cloud": CloudBackend()}


def run_task(prompt: str, mode: str, sandbox: str | None = None, memory_path: str | None = None,
             backends: dict[str, ModelBackend] | None = None,
             history: list[dict[str, Any]] | None = None) -> RunResult:
    eval_mode = sandbox is not None
    configure_run(sandbox, memory_path)
    memory = load_memory()
    system = SYSTEM_PROMPT + (f"\nLONG-TERM MEMORY: {json.dumps(memory)}" if memory else "")
    messages = history if history is not None else [{"role": "system", "content": system}]
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    result = RunResult()
    pair = _backend_pair(mode, backends)
    tools = _tool_schemas(eval_mode)

    for step_index in range(MAX_STEPS):
        result.steps = step_index + 1
        backend_name, backend = ("local", pair["local"]) if mode in {"all_local", "routed"} else ("cloud", pair["cloud"])
        response = backend.chat(messages, tools)
        parsed_calls: list[dict[str, Any]] = []
        valid = not response.error
        parse_error = response.error
        for call in response.tool_calls:
            normalized = _canonical_call(call)
            arguments, error = _parse_arguments(normalized["function"]["arguments"])
            normalized["function"]["arguments"] = arguments if arguments is not None else normalized["function"]["arguments"]
            name = normalized["function"]["name"]
            normalized["valid"] = not error and name in AVAILABLE_FUNCTIONS
            if error:
                valid, parse_error = False, error
            elif name not in AVAILABLE_FUNCTIONS:
                valid, parse_error = False, f"unknown tool: {name}"
            parsed_calls.append(normalized)

        should_escalate = mode == "routed" and backend_name == "local" and (
            not valid or any(call["function"]["name"] in ESCALATE_TOOLS for call in parsed_calls)
        )
        if should_escalate:
            result.calls.append(ModelCall(step_index=step_index, backend="local", model_name=backend.model_name,
                                          prompt_tokens=response.prompt_tokens, completion_tokens=response.completion_tokens,
                                          latency_s=response.latency_s, content=response.content, tool_calls=parsed_calls,
                                          tool_call_valid=valid, error=parse_error))
            backend_name, backend = "cloud", pair["cloud"]
            response = backend.chat(messages, tools)
            parsed_calls, valid, parse_error = [], not response.error, response.error
            for call in response.tool_calls:
                normalized = _canonical_call(call)
                arguments, error = _parse_arguments(normalized["function"]["arguments"])
                normalized["function"]["arguments"] = arguments if arguments is not None else normalized["function"]["arguments"]
                name = normalized["function"]["name"]
                normalized["valid"] = not error and name in AVAILABLE_FUNCTIONS
                if error:
                    valid, parse_error = False, error
                elif name not in AVAILABLE_FUNCTIONS:
                    valid, parse_error = False, f"unknown tool: {name}"
                parsed_calls.append(normalized)
            escalated = True
        else:
            escalated = False

        call_record = ModelCall(step_index=step_index, backend=backend_name, model_name=backend.model_name,
                                prompt_tokens=response.prompt_tokens, completion_tokens=response.completion_tokens,
                                latency_s=response.latency_s, content=response.content, tool_calls=parsed_calls,
                                tool_call_valid=valid, escalated=escalated, error=parse_error)
        result.calls.append(call_record)
        if response.error or not valid:
            result.failure_reason = parse_error or "invalid model response"
            return result
        try:
            update_current_span(model=backend.model_name, model_parameters={"temperature": TEMPERATURE},
                                usage={"input_tokens": response.prompt_tokens, "output_tokens": response.completion_tokens},
                                prompt=messages)
        except Exception:
            pass

        if not parsed_calls:
            result.final_answer = response.content
            messages.append({"role": "assistant", "content": response.content})
            result.passed = True
            return result

        messages.append({"role": "assistant", "content": response.content, "tool_calls": parsed_calls})
        for call in parsed_calls:
            name = call["function"]["name"]
            function = AVAILABLE_FUNCTIONS.get(name)
            if not function:
                result.failure_reason = f"unknown tool: {name}"
                return result
            audit_start = len(get_tool_audit())
            try:
                tool_result = function(**call["function"]["arguments"])
            except Exception as exc:
                tool_result = f"Error executing tool: {exc}"
            blocked = any(event.get("blocked") for event in get_tool_audit()[audit_start:])
            call["blocked_command_attempted"] = blocked
            result.tool_calls.append(call)
            call_record.blocked_command_attempted = call_record.blocked_command_attempted or blocked
            messages.append({"role": "tool", "tool_call_id": call["id"], "tool_name": name,
                             "content": str(tool_result)})

    result.hit_step_limit = True
    result.failure_reason = "maximum step limit exceeded"
    return result


class Agent:
    def __init__(self) -> None:
        self.memory = load_memory()
        self.history = [{"role": "system", "content": SYSTEM_PROMPT + f"\nBase user directory: {BASE_PATH}"}]
        self.interaction_count = 0
        self.backends: dict[str, ModelBackend] = {}
        logger.debug("Agent initialized")

    @observe(name="NexAgent Interaction", type="agent")
    def run(self, user_input: str) -> str:
        try:
            result = run_task(user_input, "all_cloud", backends=self.backends or None, history=self.history)
            if result.passed:
                self.interaction_count += 1
                return result.final_answer
            return f"Error: {result.failure_reason}"
        except Exception as exc:
            logger.error(f"Error in Agent.run: {exc}")
            return "Sorry, I encountered an error. Please try again."

    def get_interaction_count(self) -> int:
        return self.interaction_count

    def clear_history(self) -> None:
        self.history = self.history[:1]
        logger.info("History cleared")
