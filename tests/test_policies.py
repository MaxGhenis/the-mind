import http.client
import io
import json
import random
import unittest
import urllib.error
import urllib.request
from unittest.mock import Mock, patch

from themind.engine import InvalidResponse, Observation, Play, ProviderError
from themind.policies import (
    MAX_RESPONSE_BYTES,
    JSONPolicy,
    OrdinalPolicy,
    ProportionalPolicy,
    RandomPolicy,
    _NoRedirect,
    build_prompts,
    parse_times,
)


def observation(**overrides):
    fields = dict(
        seat=0,
        hand=(10, 60),
        now=0.0,
        history=(),
        num_players=2,
        deck_size=100,
        horizon=101.0,
    )
    return Observation(**(fields | overrides))


def openai_response(text='{"times":[10,60]}', **overrides):
    return (
        dict(
            model="resolved-test-model-2026-01-01",
            id="test-request-1",
            usage={"prompt_tokens": 70, "completion_tokens": 8},
            choices=[{"message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        )
        | overrides
    )


def fake_opener(response):
    raw = response if isinstance(response, bytes) else json.dumps(response).encode()
    stream = io.BytesIO(raw)
    opener = Mock()
    opener.open.return_value = stream
    return opener


class BaselineTests(unittest.IsolatedAsyncioTestCase):
    async def test_proportional_is_absolute_and_clamps_only_to_now(self):
        result = await ProportionalPolicy().decide(observation(now=20))
        self.assertEqual(result.times, (20, 60))
        late = await ProportionalPolicy(scale=2).decide(observation())
        self.assertEqual(late.times, (20, 120))

    async def test_random_has_isolated_seeded_rng_and_does_not_sort(self):
        random.seed(999)
        state = random.getstate()
        left, right = RandomPolicy(0), RandomPolicy(0)
        first = await left.decide(observation(now=20))
        self.assertEqual(first, await right.decide(observation(now=20)))
        self.assertGreater(first.times[0], first.times[1])
        self.assertTrue(all(20 <= t <= 101 for t in first.times))
        self.assertNotEqual(first.times, (await left.decide(observation(now=20))).times)
        self.assertEqual(state, random.getstate())

    async def test_ordinal_ignores_values(self):
        policy = OrdinalPolicy()
        first = await policy.decide(observation(now=11))
        second = await policy.decide(observation(now=11, hand=(20, 80)))
        self.assertEqual(first.times, (41, 71))
        self.assertEqual(first.times, second.times)


class ParserTests(unittest.TestCase):
    def test_accepts_numbers_nonmonotone_times_and_deadline_misses(self):
        self.assertEqual(parse_times('{"times":[1e3,12.5]}', observation(now=10)), (1000, 12.5))

    def test_accepts_only_one_complete_optional_json_fence(self):
        for text in (
            '```json\n{"times":[10,60]}\n```',
            '```\n{"times":[10,60]}\n```',
            ' \n```json \r\n{"times":[10,60]}\r\n``` \n',
        ):
            with self.subTest(text=text):
                self.assertEqual(parse_times(text, observation()), (10, 60))

    def test_rejects_invalid_outputs_without_repair(self):
        bad = [
            "I would wait 10 seconds",
            'Here is my plan:\n```json\n{"times":[10,60]}\n```',
            '```json\n{"times":[10,60]}\n```\nThat is my plan.',
            '```json\n{"times":[10,60]}\n```\n```json\n{"times":[20,70]}\n```',
            '```JSON\n{"times":[10,60]}\n```',
            '```python\n{"times":[10,60]}\n```',
            '```json\n{"times":[10,60]}',
            '```json {"times":[10,60]}```',
            '```json\n{"times":[10,60],"explanation":"plan"}\n```',
            '```json\n{"times":[true,60]}\n```',
            '{"times":[10,60]} trailing',
            "[10,60]",
            '{"times":[10,60],"reason":"plan"}',
            '{"times":[10,60],"times":[20,70]}',
            '{"times":[10]}',
            '{"times":[10,60,90]}',
            '{"times":"10,60"}',
            '{"times":[true,60]}',
            '{"times":["10",60]}',
            '{"times":[null,60]}',
            '{"times":[NaN,60]}',
            '{"times":[Infinity,60]}',
            '{"times":[1e999,60]}',
            '{"times":[9,60]}',
            '{"times":[{},60]}',
            '{"times":[' + "9" * 400 + ",60]}",
        ]
        for text in bad:
            with self.subTest(text=text[:60]), self.assertRaises(InvalidResponse):
                parse_times(text, observation(now=10))

    def test_prompt_serializes_only_observation(self):
        obs = observation(now=17, history=(Play(seat=1, card=12, time=None),))
        system, user = build_prompts(obs, mode="feedback", convention="none")
        data = json.loads(user)
        self.assertEqual(
            set(data), {"seat", "hand", "now", "history", "num_players", "deck_size", "horizon"}
        )
        self.assertEqual(data["hand"], [10, 60])
        self.assertEqual(data["history"], [{"seat": 1, "card": 12, "time": None}])
        self.assertEqual(data["now"], 17)
        self.assertIn("current event time now remains visible", system)
        self.assertIn("Only the first time", system)
        self.assertNotIn("horizon*c", system)
        explicit, _ = build_prompts(obs, mode="precommit", convention="proportional")
        self.assertIn("horizon*c/(deck_size+1)", explicit)
        self.assertIn("commit their complete schedules once", explicit)


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    def policy(self, provider="openai", **kwargs):
        return JSONPolicy(provider, "requested-model-exact", "THE_MIND_TEST_KEY", **kwargs)

    async def test_openai_request_and_audit_metadata(self):
        opener = fake_opener(openai_response())
        with (
            patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
            patch("urllib.request.build_opener", return_value=opener),
        ):
            result = await self.policy(max_tokens=123, timeout=7).decide(observation())
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-test-key")
        self.assertEqual(opener.open.call_args.kwargs, {"timeout": 7.0})
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "requested-model-exact")
        self.assertEqual(payload["max_completion_tokens"], 123)
        self.assertNotIn("temperature", payload)
        self.assertNotIn("tools", payload)
        self.assertNotIn("response_format", payload)
        self.assertNotIn("output_config", payload)
        self.assertFalse(result.metadata["policy"]["structured_output"])
        self.assertEqual([m["role"] for m in payload["messages"]], ["system", "user"])
        self.assertEqual(result.times, (10, 60))
        audit = result.metadata
        self.assertEqual(audit["requested_model"], "requested-model-exact")
        self.assertEqual(audit["resolved_model"], "resolved-test-model-2026-01-01")
        self.assertEqual(audit["usage"]["completion_tokens"], 8)
        self.assertEqual(audit["response_text"], '{"times":[10,60]}')
        self.assertEqual(audit["response_body"], openai_response())
        self.assertEqual(audit["normalization"], "none")
        self.assertEqual(audit["request_body"], payload)
        self.assertGreaterEqual(audit["request_latency_seconds"], 0)
        self.assertNotIn("secret-test-key", json.dumps(audit))

    async def test_anthropic_request_and_response(self):
        response = {
            "model": "claude-exact-resolution",
            "id": "msg_test",
            "content": [{"type": "text", "text": '{"times":[10,60]}'}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 50, "output_tokens": 9},
        }
        opener = fake_opener(response)
        with (
            patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
            patch("urllib.request.build_opener", return_value=opener),
        ):
            result = await self.policy("anthropic", temperature=0, max_tokens=100).decide(
                observation()
            )
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(request.get_header("X-api-key"), "secret-test-key")
        self.assertEqual(request.get_header("Anthropic-version"), "2023-06-01")
        self.assertIsNone(request.get_header("Authorization"))
        payload = json.loads(request.data)
        self.assertEqual(payload["max_tokens"], 100)
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertIn("system", payload)
        self.assertNotIn("response_format", payload)
        self.assertNotIn("output_config", payload)
        self.assertEqual(result.times, (10, 60))
        self.assertEqual(result.metadata["resolved_model"], "claude-exact-resolution")
        self.assertEqual(result.metadata["response_body"], response)

    async def test_structured_output_uses_uniform_schema_and_native_provider_parameters(self):
        expected_schema = {
            "type": "object",
            "properties": {"times": {"type": "array", "items": {"type": "number"}}},
            "required": ["times"],
            "additionalProperties": False,
        }
        for provider in ("openai", "anthropic"):
            response = (
                openai_response()
                if provider == "openai"
                else {
                    "content": [{"type": "text", "text": '{"times":[10,60]}'}],
                    "stop_reason": "end_turn",
                }
            )
            opener = fake_opener(response)
            with (
                self.subTest(provider=provider),
                patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
                patch("urllib.request.build_opener", return_value=opener),
            ):
                result = await self.policy(provider, structured_output=True).decide(observation())
            request = opener.open.call_args.args[0]
            payload = json.loads(request.data)
            if provider == "openai":
                self.assertEqual(
                    payload["response_format"],
                    {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "mind_times",
                            "strict": True,
                            "schema": expected_schema,
                        },
                    },
                )
                self.assertNotIn("output_config", payload)
            else:
                self.assertEqual(
                    payload["output_config"],
                    {"format": {"type": "json_schema", "schema": expected_schema}},
                )
                self.assertNotIn("response_format", payload)
                self.assertIsNone(request.get_header("Anthropic-beta"))
            self.assertNotIn("tools", payload)
            self.assertEqual(result.times, (10, 60))
            self.assertEqual(result.metadata["response_body"], response)
            self.assertEqual(result.metadata["request_body"], payload)
            self.assertTrue(result.metadata["policy"]["structured_output"])
            self.assertEqual(result.metadata["policy"]["response_schema"], expected_schema)
            self.assertEqual(opener.open.call_count, 1)

    async def test_structured_output_does_not_skip_local_validation_or_retry(self):
        outputs = (
            ('{"times":[10]}', "stop", "end_turn"),
            ('{"times":[true,60]}', "stop", "end_turn"),
            ('{"times":[NaN,60]}', "stop", "end_turn"),
            ('{"times":[-1,60]}', "stop", "end_turn"),
            ('Here is my plan: {"times":[10,60]}', "stop", "end_turn"),
            ('{"times":[10,60]}', "length", "max_tokens"),
            ("Refused", "content_filter", "refusal"),
        )
        for provider in ("openai", "anthropic"):
            for text, openai_finish, anthropic_stop in outputs:
                response = (
                    openai_response(
                        choices=[{"message": {"content": text}, "finish_reason": openai_finish}]
                    )
                    if provider == "openai"
                    else {
                        "content": [{"type": "text", "text": text}],
                        "stop_reason": anthropic_stop,
                    }
                )
                opener = fake_opener(response)
                with (
                    self.subTest(provider=provider, text=text),
                    patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
                    patch("urllib.request.build_opener", return_value=opener),
                ):
                    with self.assertRaises(InvalidResponse) as caught:
                        await self.policy(provider, structured_output=True).decide(observation())
                self.assertTrue(caught.exception.metadata["policy"]["structured_output"])
                self.assertEqual(caught.exception.metadata["response_body"], response)
                self.assertEqual(opener.open.call_count, 1)

    async def test_unsupported_structured_output_has_no_text_fallback(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            "https://host", 400, "unsupported", {}, io.BytesIO()
        )
        with (
            patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
            patch("urllib.request.build_opener", return_value=opener),
        ):
            with self.assertRaisesRegex(ProviderError, "400"):
                await self.policy(structured_output=True).decide(observation())
        self.assertEqual(opener.open.call_count, 1)

    async def test_json_fence_normalization_preserves_raw_response_without_retry(self):
        raw_text = '```json\n{"times":[10,60]}\n```'
        for provider in ("openai", "anthropic"):
            response = (
                openai_response(raw_text)
                if provider == "openai"
                else {
                    "content": [{"type": "text", "text": raw_text}],
                    "stop_reason": "end_turn",
                }
            )
            opener = fake_opener(response)
            with (
                self.subTest(provider=provider),
                patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
                patch("urllib.request.build_opener", return_value=opener),
            ):
                result = await self.policy(provider).decide(observation())
            self.assertEqual(result.times, (10, 60))
            self.assertEqual(result.metadata["normalization"], "json_fence")
            self.assertEqual(result.metadata["response_text"], raw_text)
            self.assertEqual(result.metadata["response_body"], response)
            self.assertEqual(opener.open.call_count, 1)

    async def test_missing_key_fails_without_network(self):
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("urllib.request.build_opener") as builder,
        ):
            with self.assertRaises(ProviderError) as caught:
                await self.policy().decide(observation())
        builder.assert_not_called()
        self.assertIn("Missing API key", str(caught.exception))
        self.assertIn("prompts", caught.exception.metadata)

    async def test_http_errors_and_transport_failures_never_echo_body_or_key(self):
        failures = [
            urllib.error.HTTPError(
                "https://host", 401, "secret-test-key", {}, io.BytesIO(b"secret-test-key")
            ),
            urllib.error.URLError("secret-test-key"),
            TimeoutError("secret-test-key"),
            http.client.IncompleteRead(b"secret-test-key"),
        ]
        for failure in failures:
            opener = Mock()
            opener.open.side_effect = failure
            with (
                self.subTest(failure=type(failure).__name__),
                patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
                patch("urllib.request.build_opener", return_value=opener),
            ):
                with self.assertRaises(ProviderError) as caught:
                    await self.policy().decide(observation())
            self.assertEqual(opener.open.call_count, 1)
            self.assertNotIn("secret-test-key", str(caught.exception))
            self.assertNotIn("secret-test-key", json.dumps(caught.exception.metadata))

    async def test_model_invalid_json_is_not_a_provider_outage_or_fallback_move(self):
        opener = fake_opener(openai_response("secret-test-key " + "x" * 400))
        with (
            patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
            patch("urllib.request.build_opener", return_value=opener),
        ):
            with self.assertRaises(InvalidResponse) as caught:
                await self.policy().decide(observation())
        self.assertIn("response excerpt", str(caught.exception))
        self.assertLess(len(str(caught.exception)), 300)
        self.assertNotIn("secret-test-key", json.dumps(caught.exception.metadata))
        self.assertIn("[REDACTED]", caught.exception.metadata["response_text"])
        self.assertEqual(opener.open.call_count, 1)

    async def test_malformed_provider_envelope_is_explicit(self):
        for response in (b"not JSON", b"[]", b'{"choices":[],"choices":[]}', {"choices": []}):
            with (
                self.subTest(response=response),
                patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
                patch("urllib.request.build_opener", return_value=fake_opener(response)),
            ):
                with self.assertRaises(ProviderError):
                    await self.policy().decide(observation())

    async def test_truncation_and_tool_requests_are_invalid_even_with_valid_json(self):
        for message, finish in (
            ({"content": '{"times":[10,60]}'}, "length"),
            ({"content": '{"times":[10,60]}', "tool_calls": [{"id": "test"}]}, "stop"),
            ({"content": '{"times":[10,60]}', "refusal": "Refused"}, "stop"),
        ):
            response = openai_response(choices=[{"message": message, "finish_reason": finish}])
            with (
                self.subTest(message=message, finish=finish),
                patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
                patch("urllib.request.build_opener", return_value=fake_opener(response)),
            ):
                with self.assertRaises(InvalidResponse):
                    await self.policy().decide(observation())

    async def test_anthropic_nontext_content_cannot_execute_tools(self):
        response = {
            "content": [
                {"type": "tool_use", "name": "shell", "input": {"token": "secret-test-key"}}
            ],
            "usage": {"input_tokens": 11, "output_tokens": 5},
            "stop_reason": "tool_use",
        }
        with (
            patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
            patch("urllib.request.build_opener", return_value=fake_opener(response)),
        ):
            with self.assertRaises(InvalidResponse) as caught:
                await self.policy("anthropic").decide(observation())
        body = caught.exception.metadata["response_body"]
        self.assertEqual(body["content"][0]["input"]["token"], "[REDACTED]")
        self.assertEqual(body["usage"], response["usage"])
        self.assertEqual(body["stop_reason"], "tool_use")
        self.assertNotIn("secret-test-key", json.dumps(caught.exception.metadata))

    async def test_openai_refusal_body_preserved_with_credentials_redacted(self):
        response = openai_response(
            choices=[
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "refusal": "Refused secret-test-key",
                    },
                    "finish_reason": "stop",
                }
            ]
        )
        with (
            patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
            patch("urllib.request.build_opener", return_value=fake_opener(response)),
        ):
            with self.assertRaises(InvalidResponse) as caught:
                await self.policy().decide(observation())
        body = caught.exception.metadata["response_body"]
        self.assertEqual(body["choices"][0]["message"]["refusal"], "Refused [REDACTED]")
        self.assertEqual(body["usage"], response["usage"])
        self.assertNotIn("secret-test-key", json.dumps(caught.exception.metadata))

    async def test_response_size_is_bounded(self):
        opener = fake_opener(b"x" * (MAX_RESPONSE_BYTES + 1))
        with (
            patch.dict("os.environ", {"THE_MIND_TEST_KEY": "secret-test-key"}),
            patch("urllib.request.build_opener", return_value=opener),
        ):
            with self.assertRaisesRegex(ProviderError, "byte limit"):
                await self.policy().decide(observation())


class EndpointTests(unittest.TestCase):
    def test_structured_output_requires_boolean_and_returns_independent_audit_schema(self):
        for value in (None, 0, 1, "true", [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "boolean"):
                JSONPolicy("openai", "test", "TEST_KEY", structured_output=value)
        policy = JSONPolicy("openai", "test", "TEST_KEY", structured_output=True)
        descriptor = policy.descriptor
        descriptor["response_schema"]["properties"]["times"]["items"]["type"] = "string"
        self.assertEqual(
            policy.descriptor["response_schema"]["properties"]["times"]["items"]["type"], "number"
        )

    def test_remote_endpoints_require_https_and_no_inline_credentials(self):
        for endpoint in (
            "http://api.example.test/v1/chat/completions",
            "ftp://localhost/completions",
            "https://key@api.example.test/completions",
            "https://api.example.test/completions?key=credential",
            "https://api.example.test/completions#credential",
            "https:///completions",
            "https://api.example.test:invalid/completions",
        ):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                JSONPolicy("openai", "test", "TEST_KEY", endpoint=endpoint)

    def test_loopback_endpoints_supported(self):
        for host in ("localhost", "127.0.0.1", "[::1]"):
            policy = JSONPolicy(
                "openai",
                "local-model",
                "LOCAL_KEY",
                endpoint=f"http://{host}:8080/v1/chat/completions",
            )
            self.assertEqual(policy.descriptor["requested_model"], "local-model")

    def test_redirects_refused_before_authentication_headers_can_be_forwarded(self):
        request = urllib.request.Request(
            "https://provider.test", headers={"Authorization": "Bearer test"}
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            _NoRedirect().redirect_request(
                request, io.BytesIO(), 302, "Found", {}, "https://other.test"
            )
        caught.exception.close()

    def test_invalid_settings_rejected_before_requests(self):
        for settings in (
            {"timeout": 0},
            {"timeout": float("nan")},
            {"max_tokens": True},
            {"max_tokens": 1.5},
            {"temperature": -1},
            {"mode": "unknown"},
            {"convention": "unknown"},
        ):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                JSONPolicy("openai", "test", "TEST_KEY", **settings)


if __name__ == "__main__":
    unittest.main()
