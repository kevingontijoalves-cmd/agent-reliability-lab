from __future__ import annotations

import os
from pathlib import Path

from mcp.server import MCPServer

from .evaluation import evaluate_output
from .prompts import PromptRegistry
from .routing import route_request
from .storage import RunStore

ROOT = Path(__file__).resolve().parents[2]
PROMPT_DIR = ROOT / "prompts"
DB_PATH = Path(os.getenv("RELIABILITY_DB_PATH", ROOT / "reliability_runs.db"))

registry = PromptRegistry(PROMPT_DIR)
store = RunStore(DB_PATH)
mcp = MCPServer(
    "Agent Reliability Lab",
    instructions=(
        "Route technical-review requests, evaluate structured AI outputs, "
        "inspect versioned prompts, and report reliability telemetry."
    ),
)


@mcp.tool()
def route_technical_request(text: str) -> dict[str, object]:
    """Route a request using deterministic, inspectable keyword signals."""
    return route_request(text)


@mcp.tool()
def inspect_prompt(prompt_id: str, version: str | None = None) -> dict[str, object]:
    """Return a versioned prompt contract without exposing credentials."""
    prompt = registry.get(prompt_id, version)
    return {
        "id": prompt.prompt_id,
        "version": prompt.version,
        "output_format": prompt.output_format,
        "required_keys": list(prompt.required_keys),
    }


@mcp.tool()
def score_ai_output(
    output: str,
    prompt_id: str = "technical_review",
    version: str | None = None,
    reference_facts: list[str] | None = None,
) -> dict[str, object]:
    """Evaluate format, completeness, instruction compliance, and traceability."""
    prompt = registry.get(prompt_id, version)
    return evaluate_output(
        output,
        output_format=prompt.output_format,
        required_keys=prompt.required_keys,
        reference_facts=tuple(reference_facts or []),
    ).as_dict()


@mcp.tool()
def reliability_metrics() -> dict[str, object]:
    """Return aggregate latency, cost, fallback, and quality metrics from SQL."""
    return store.metrics()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

