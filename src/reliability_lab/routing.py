from __future__ import annotations


ROUTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("incident_analysis", ("incident", "outage", "failure", "error", "postmortem")),
    ("technical_review", ("review", "audit", "evaluate", "assess", "quality", "rubric")),
)


def route_request(text: str) -> dict[str, object]:
    normalized = text.casefold()
    scores = {
        route: sum(1 for keyword in keywords if keyword in normalized)
        for route, keywords in ROUTES
    }
    selected = max(scores, key=scores.get)
    if scores[selected] == 0:
        selected = "technical_review"
    return {
        "route": selected,
        "confidence": 1.0 if scores[selected] >= 2 else 0.7 if scores[selected] == 1 else 0.4,
        "matched_signals": scores[selected],
    }

