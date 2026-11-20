from __future__ import annotations


QUALITY_RANK = {
    "peer-reviewed": 3,
    "independent benchmark": 2,
    "vendor blog": 1,
}
SOURCES = [
    ("S1", "peer-reviewed", "AI tutoring improved benchmark scores by 12%."),
    ("S2", "independent benchmark", "AI tutoring improved benchmark scores by 8%."),
    ("S3", "vendor blog", "AI tutoring improved benchmark scores by 20%."),
    ("S4", "independent benchmark", "AI tutoring showed no improvement in a long-form cohort."),
]


def main() -> None:
    for source_id, tier, claim in SOURCES:
        print(f"{source_id:<3} {tier:<24} {claim}")
    s1 = next(source for source in SOURCES if source[0] == "S1")
    s4 = next(source for source in SOURCES if source[0] == "S4")
    assert "improved" in s1[2] and "no improvement" in s4[2]
    print(
        "Conflict: S4 directly contradicts S1; plausible reason: S1 tests short "
        "benchmark tasks, while S4 measures long-form transfer in a different cohort."
    )
    best_quality = max(SOURCES, key=lambda source: QUALITY_RANK[source[1]])
    assert best_quality[0] == "S1"
    print(
        "Executive summary: The synthesis leans toward S1's 12% benchmark result "
        "because it is peer-reviewed. S3's 20% vendor claim is down-weighted, "
        "not discarded, because it is lower-tier and lacks independent replication."
    )


if __name__ == "__main__":
    main()
