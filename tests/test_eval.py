import io
import os
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from backend import CloudBackend, LocalBackend
from eval import run
from eval.tasks import checker_self_test


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        import json
        return json.dumps(self.payload).encode("utf-8")


class FakeCloudCompletions:
    def __init__(self):
        self.messages = None

    def create(self, **kwargs):
        self.messages = kwargs["messages"]
        return type("Response", (), {
            "choices": [type("Choice", (), {"message": type("Message", (), {"content": "done", "tool_calls": []})()})()],
            "usage": type("Usage", (), {"prompt_tokens": 1, "completion_tokens": 1})(),
        })()


class FakeLocalClient:
    def __init__(self):
        self.messages = None

    def chat(self, **kwargs):
        self.messages = kwargs["messages"]
        return {"message": {"content": "done", "tool_calls": []}, "prompt_eval_count": 1, "eval_count": 1}


class EvalTests(unittest.TestCase):
    def test_checker_self_test(self):
        self.assertEqual(checker_self_test()["smoke_simple"], False)

    def test_all_local_preflight_does_not_require_cloud_key(self):
        payload = {"models": [{"name": "llama3.2:3b"}]}
        with patch.dict(os.environ, {}, clear=True), patch.object(run.urllib.request, "urlopen", return_value=FakeResponse(payload)):
            self.assertTrue(run.preflight_check("all_local"))

    def test_cloud_preflight_failure_writes_nothing(self):
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), redirect_stderr(output):
            with self.assertRaises(SystemExit):
                run.preflight_check("all_cloud")
        self.assertIn("GROQ_API_KEY is not set", output.getvalue())

    def test_backend_tool_message_payloads(self):
        history = [
            {"role": "user", "content": "start"},
            {"role": "assistant", "content": "", "tool_calls": [{
                "id": "call_one", "type": "function",
                "function": {"name": "read_file", "arguments": {"path": "one.txt"}},
            }]},
            {"role": "tool", "tool_call_id": "call_one", "tool_name": "read_file", "content": "one"},
            {"role": "assistant", "content": "", "tool_calls": [{
                "id": "call_two", "type": "function",
                "function": {"name": "read_file", "arguments": {"path": "two.txt"}},
            }]},
            {"role": "tool", "tool_call_id": "call_two", "tool_name": "read_file", "content": "two"},
        ]

        cloud_client = FakeCloudCompletions()
        cloud = CloudBackend.__new__(CloudBackend)
        cloud.client = type("Client", (), {"chat": type("Chat", (), {"completions": cloud_client})()})()
        cloud.chat(history, [])
        cloud_calls = [message["tool_calls"][0] for message in cloud_client.messages if message.get("tool_calls")]
        self.assertTrue(all(call["id"] for call in cloud_calls))
        self.assertTrue(all(call["type"] == "function" and "function" in call for call in cloud_calls))
        self.assertIsInstance(cloud_calls[0]["function"]["arguments"], str)

        local_client = FakeLocalClient()
        local = LocalBackend.__new__(LocalBackend)
        local.client = local_client
        local.chat(history, [])
        local_calls = [message["tool_calls"][0] for message in local_client.messages if message.get("tool_calls")]
        self.assertTrue(all(call["id"] for call in local_calls))
        self.assertTrue(all("function" in call for call in local_calls))
        self.assertIsInstance(local_calls[0]["function"]["arguments"], dict)


if __name__ == "__main__":
    unittest.main()