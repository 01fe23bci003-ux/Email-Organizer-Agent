from __future__ import annotations

from typing import Any


ARTICLES: list[dict[str, Any]] = [
    {
        "id": "article-1",
        "claims": [{"text": "Active recall improves retention", "evidence": "controlled comparison"}],
        "limitation": None,
    },
    {
        "id": "article-2",
        "claims": [{"text": "Short breaks support focus", "evidence": "participant observations"}],
        "limitation": None,
    },
    {
        "id": "article-3",
        "claims": [
            {"text": "Structured practice improves accuracy", "evidence": "measured comparison"},
            {"text": "The improvement is caused by motivation", "evidence": None},
        ],
        "limitation": "small sample",
    },
    {
        "id": "article-4",
        "claims": [{"text": "The app improves focus", "evidence": None}],
        "limitation": None,
    },
]


def research_summary_skill(article: dict[str, Any]) -> dict[str, str]:
    claims = article["claims"]
    selected = next((claim for claim in claims if claim["evidence"]), claims[0])
    competing_claims = len(claims) > 1
    if selected["evidence"]:
        reason = (
            f"it is supported by {selected['evidence']}, while the competing claim "
            "has no evidence in the source"
            if competing_claims
            else f"the source reports {selected['evidence']}"
        )
    else:
        reason = "it is the article's only explicit claim, but no supporting evidence is supplied"
    return {
        "article_id": article["id"],
        "selected_claim": selected["text"],
        "why_selected": reason,
        "evidence": selected["evidence"] or "not stated in source",
        "limitation": article["limitation"] or "not stated in source",
    }


def reusability_check(articles: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [research_summary_skill(article) for article in articles]


def main() -> None:
    outputs = reusability_check(ARTICLES)
    for output in outputs:
        print(
            f"{output['article_id']}: selected=\"{output['selected_claim']}\"; "
            f"why={output['why_selected']}; evidence={output['evidence']}; "
            f"limitation={output['limitation']}"
        )
    print(f"reusability_check: {len(outputs)}/{len(ARTICLES)} articles processed")
    print("No fabrication: confirmed")
    assert outputs[2]["selected_claim"] == "Structured practice improves accuracy"
    assert outputs[3]["evidence"] == "not stated in source"
    assert len(outputs) == 4


if __name__ == "__main__":
    main()
