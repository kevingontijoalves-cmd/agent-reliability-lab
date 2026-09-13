from __future__ import annotations

import json
from pathlib import Path

import pytest

from reliability_lab.evaluation import evaluate_output
from reliability_lab.prompts import PromptRegistry
from reliability_lab.providers import ProviderResponse
from reliability_lab.routing import route_request
from reliability_lab.service import AllProvidersFailed, ReliabilityService
from reliability_lab.storage import RunStore


PROMPTS = Path(__file__).resolve().parents[1] / "prompts"


class FakeProvider:
    input_price_per_million = 2.0
    output_price_per_million = 8.0

    def __init__(self, name: str, response: str = "", failure: Exception | None = None) -> None:
        self.name = name
        self.response = response
        self.failure = failure

    def complete(self, system: str, user: str) -> ProviderResponse:
        if self.failure:
            raise self.failure
        return ProviderResponse(self.response, input_tokens=100, output_tokens=50)


def test_registry_uses_latest_numeric_version() -> None:
    prompt = PromptRegistry(PROMPTS).get("technical_review")
    assert prompt.version == "1.1.0"
    assert "evidence" in prompt.required_keys


def test_registry_can_pin_version() -> None:
    prompt = PromptRegistry(PROMPTS).get("technical_review", "1.0.0")
    assert prompt.version == "1.0.0"
    assert "evidence" not in prompt.required_keys


def test_registry_rejects_unknown_prompt() -> None:
    with pytest.raises(KeyError):
        PromptRegistry(PROMPTS).get("missing")


def test_router_detects_incident() -> None:
    result = route_request("Investigate the outage and produce a postmortem")
    assert result["route"] == "incident_analysis"
    assert result["confidence"] == 1.0


def test_router_has_safe_default() -> None:
    assert route_request("Explain this system")["route"] == "technical_review"


def test_evaluator_reports_missing_contract_fields() -> None:
    result = evaluate_output(
        '{"verdict": "pass"}',
        required_keys=("verdict", "findings", "recommendation"),
    )
    assert result.schema_valid
    assert result.missing_keys == ("findings", "recommendation")
    assert result.overall < 1


def test_evaluator_rejects_invalid_json() -> None:
    result = evaluate_output("not-json", required_keys=("verdict",))
    assert not result.schema_valid
    assert result.instruction_compliance == 0


def test_evaluator_checks_reference_facts() -> None:
    result = evaluate_output(
        '{"verdict":"pass","findings":[],"recommendation":"keep API v2"}',
        required_keys=("verdict", "findings", "recommendation"),
        reference_facts=("API v2", "latency 80ms"),
    )
    assert result.missing_facts == ("latency 80ms",)
    assert result.traceability == 0.5


def test_service_falls_back_and_records_metrics(tmp_path: Path) -> None:
    response = json.dumps(
        {"verdict": "pass", "findings": [], "recommendation": "ship", "evidence": []}
    )
    store = RunStore(tmp_path / "runs.db")
    service = ReliabilityService(
        PromptRegistry(PROMPTS),
        store,
        [
            FakeProvider("primary", failure=TimeoutError()),
            FakeProvider("fallback", response=response),
        ],
    )

    result = service.run("technical_review", "Review this")

    assert result["provider"] == "fallback"
    assert result["used_fallback"] is True
    assert result["prior_failures"] == ["primary: TimeoutError"]
    assert result["estimated_cost_usd"] == 0.0006
    metrics = store.metrics()
    assert metrics["run_count"] == 1
    assert metrics["fallback_count"] == 1


def test_service_fails_after_all_providers(tmp_path: Path) -> None:
    service = ReliabilityService(
        PromptRegistry(PROMPTS),
        RunStore(tmp_path / "runs.db"),
        [FakeProvider("one", failure=RuntimeError()), FakeProvider("two", failure=TimeoutError())],
    )
    with pytest.raises(AllProvidersFailed, match="one: RuntimeError; two: TimeoutError"):
        service.run("technical_review", "Review")

