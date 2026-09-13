from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from statistics import mean


@dataclass(frozen=True)
class EvaluationResult:
    schema_valid: bool
    missing_keys: tuple[str, ...]
    missing_facts: tuple[str, ...]
    completeness: float
    instruction_compliance: float
    traceability: float
    overall: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_output(
    output: str,
    *,
    output_format: str = "json",
    required_keys: tuple[str, ...] = (),
    reference_facts: tuple[str, ...] = (),
) -> EvaluationResult:
    parsed: object = output
    schema_valid = True
    if output_format == "json":
        try:
            parsed = json.loads(output)
            schema_valid = isinstance(parsed, dict)
        except json.JSONDecodeError:
            schema_valid = False
            parsed = {}

    mapping = parsed if isinstance(parsed, dict) else {}
    missing_keys = tuple(key for key in required_keys if key not in mapping)
    normalized = output.casefold()
    missing_facts = tuple(fact for fact in reference_facts if fact.casefold() not in normalized)

    completeness = 1.0 if not required_keys else (len(required_keys) - len(missing_keys)) / len(required_keys)
    instruction_compliance = 1.0 if schema_valid and not missing_keys else completeness * 0.75
    traceability = 1.0 if not reference_facts else (len(reference_facts) - len(missing_facts)) / len(reference_facts)
    overall = round(mean((completeness, instruction_compliance, traceability)), 3)
    return EvaluationResult(
        schema_valid=schema_valid,
        missing_keys=missing_keys,
        missing_facts=missing_facts,
        completeness=round(completeness, 3),
        instruction_compliance=round(instruction_compliance, 3),
        traceability=round(traceability, 3),
        overall=overall,
    )

