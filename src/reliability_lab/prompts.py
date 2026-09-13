from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptSpec:
    prompt_id: str
    version: str
    system: str
    output_format: str
    required_keys: tuple[str, ...]

    def render(self, user_input: str) -> tuple[str, str]:
        return self.system, user_input.strip()


class PromptRegistry:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def get(self, prompt_id: str, version: str | None = None) -> PromptSpec:
        candidates: list[PromptSpec] = []
        for path in sorted(self.directory.glob(f"{prompt_id}--*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            contract = raw["output_contract"]
            candidates.append(
                PromptSpec(
                    prompt_id=raw["id"],
                    version=raw["version"],
                    system=raw["system"],
                    output_format=contract["format"],
                    required_keys=tuple(contract.get("required_keys", [])),
                )
            )
        if version is not None:
            candidates = [item for item in candidates if item.version == version]
        if not candidates:
            suffix = f" version {version}" if version else ""
            raise KeyError(f"Prompt {prompt_id!r}{suffix} was not found")
        return max(candidates, key=lambda item: self._version_tuple(item.version))

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, ...]:
        try:
            return tuple(int(part) for part in value.split("."))
        except ValueError as exc:
            raise ValueError(f"Invalid numeric prompt version: {value}") from exc

