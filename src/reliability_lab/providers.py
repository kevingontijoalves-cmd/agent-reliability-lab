from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    input_tokens: int
    output_tokens: int


class Provider(Protocol):
    name: str
    input_price_per_million: float
    output_price_per_million: float

    def complete(self, system: str, user: str) -> ProviderResponse: ...


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        model: str,
        *,
        input_price_per_million: float = 0.0,
        output_price_per_million: float = 0.0,
    ) -> None:
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model
        self.input_price_per_million = input_price_per_million
        self.output_price_per_million = output_price_per_million

    def complete(self, system: str, user: str) -> ProviderResponse:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        usage = response.usage
        return ProviderResponse(
            text=response.output_text,
            input_tokens=int(usage.input_tokens if usage else 0),
            output_tokens=int(usage.output_tokens if usage else 0),
        )


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        model: str,
        *,
        input_price_per_million: float = 0.0,
        output_price_per_million: float = 0.0,
    ) -> None:
        from anthropic import Anthropic

        self.client = Anthropic()
        self.model = model
        self.input_price_per_million = input_price_per_million
        self.output_price_per_million = output_price_per_million

    def complete(self, system: str, user: str) -> ProviderResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        return ProviderResponse(
            text=text,
            input_tokens=int(response.usage.input_tokens),
            output_tokens=int(response.usage.output_tokens),
        )

