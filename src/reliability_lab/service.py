from __future__ import annotations

from time import perf_counter

from .evaluation import evaluate_output
from .prompts import PromptRegistry
from .providers import Provider, ProviderResponse
from .storage import RunStore


class AllProvidersFailed(RuntimeError):
    pass


class ReliabilityService:
    def __init__(
        self,
        registry: PromptRegistry,
        store: RunStore,
        providers: list[Provider],
    ) -> None:
        if not providers:
            raise ValueError("At least one provider is required")
        self.registry = registry
        self.store = store
        self.providers = providers

    def run(
        self,
        prompt_id: str,
        user_input: str,
        *,
        version: str | None = None,
        reference_facts: tuple[str, ...] = (),
    ) -> dict[str, object]:
        prompt = self.registry.get(prompt_id, version)
        system, user = prompt.render(user_input)
        failures: list[str] = []

        for index, provider in enumerate(self.providers):
            started = perf_counter()
            try:
                response: ProviderResponse = provider.complete(system, user)
            except Exception as exc:
                failures.append(f"{provider.name}: {type(exc).__name__}")
                continue

            latency_ms = round((perf_counter() - started) * 1000, 2)
            estimated_cost = round(
                response.input_tokens * provider.input_price_per_million / 1_000_000
                + response.output_tokens * provider.output_price_per_million / 1_000_000,
                8,
            )
            evaluation = evaluate_output(
                response.text,
                output_format=prompt.output_format,
                required_keys=prompt.required_keys,
                reference_facts=reference_facts,
            )
            run_id = self.store.record(
                prompt_id=prompt.prompt_id,
                prompt_version=prompt.version,
                provider=provider.name,
                used_fallback=int(index > 0),
                latency_ms=latency_ms,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                estimated_cost_usd=estimated_cost,
                evaluation_score=evaluation.overall,
            )
            return {
                "run_id": run_id,
                "prompt": {"id": prompt.prompt_id, "version": prompt.version},
                "provider": provider.name,
                "used_fallback": index > 0,
                "prior_failures": failures,
                "latency_ms": latency_ms,
                "estimated_cost_usd": estimated_cost,
                "evaluation": evaluation.as_dict(),
                "output": response.text,
            }

        raise AllProvidersFailed("; ".join(failures))

