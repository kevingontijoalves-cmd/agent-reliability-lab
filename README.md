# Agent Reliability Lab

A small, verifiable MCP server built with the official Python SDK. It exposes deterministic request routing, versioned prompt contracts, structured-output evaluation, and SQL-backed reliability metrics. A separate service layer demonstrates provider fallback and records latency, token usage, estimated cost, prompt version, and quality score.

## Why this project exists

LLM demos often hide three operational questions: which prompt ran, what happened when the primary provider failed, and how output quality was checked. This project makes those decisions explicit and testable.

## Implemented evidence

- A real MCP v2 server with four typed tools.
- Numeric prompt version selection and explicit version pinning.
- Rubric-based checks for schema, completeness, instruction compliance, and traceability.
- Primary/fallback provider orchestration.
- OpenAI Responses API and Anthropic Messages API adapters.
- SQLite persistence with aggregate SQL for latency, cost, fallback count, and evaluation score.
- Offline tests with fake providers; no paid API calls are required.

## Architecture

```text
MCP client
   |
   +--> route_technical_request ----> deterministic router
   +--> inspect_prompt -------------> JSON prompt registry
   +--> score_ai_output ------------> evaluation rubric
   +--> reliability_metrics --------> SQLite analytics

ReliabilityService
   primary provider --> fallback provider --> evaluate --> record telemetry
```

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\pytest -q
.\.venv\Scripts\python -m reliability_lab.server
```

The server uses stdio by default. It can be inspected with the MCP CLI:

```powershell
.\.venv\Scripts\mcp dev src/reliability_lab/server.py
```

## Optional real providers

Copy `.env.example` to `.env` and set provider keys in the environment. The tests never require or transmit credentials. Prices default to zero because model pricing changes; pass reviewed per-million-token prices when constructing the provider so cost estimates remain explicit.

## Verification boundaries

This repository proves local MCP tool registration, routing, evaluation, fallback behavior, telemetry, and SQL analytics. It does not claim enterprise traffic, paid clients, cloud data-warehouse deployment, or production uptime. Those claims should only be added after real evidence exists.

