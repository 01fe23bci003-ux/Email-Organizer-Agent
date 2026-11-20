from __future__ import annotations

from collections.abc import Sequence


NODE_GRAPH = {
    "planner": {"output": "build specification", "owner": "planner_agent"},
    "builder": {"input": "build specification", "output": "application artifact", "owner": "builder_agent"},
    "security_scan": {
        "input": "application artifact",
        "output": "scan report",
        "owner": "security_agent",
        "success_criteria": "no high-severity findings",
        "failure_behavior": "stop and escalate to a human",
    },
    "tester": {"input": "scanned artifact", "output": "test report", "owner": "tester_agent"},
    "release": {"input": "passing test report", "output": "release candidate", "owner": "human"},
}
MAX_BUILDER_RETRIES = 1


def execute(builder_results: Sequence[bool], scan_passes: bool = True) -> list[str]:
    trace = ["planner: specification ready"]
    attempts = 0
    for succeeds in builder_results:
        attempts += 1
        trace.append(f"builder attempt {attempts}: {'success' if succeeds else 'failure'}")
        if succeeds:
            break
        if attempts > MAX_BUILDER_RETRIES:
            trace.append("human escalation: builder retry limit reached")
            return trace
    else:
        trace.append("human escalation: builder produced no result")
        return trace

    trace.append("security_scan: pass" if scan_passes else "security_scan: fail")
    if not scan_passes:
        trace.append("human escalation: security scan failed; tester not run")
        return trace
    trace.extend(["tester: pass", "release: ready for human approval"])
    return trace


def main() -> None:
    cases = [
        ("(a)", execute([False, True])),
        ("(b)", execute([False, False])),
        ("(c)", execute([True], scan_passes=False)),
    ]
    for label, trace in cases:
        print(f"CASE {label}")
        for step in trace:
            print(f"  {step}")
    assert "tester: pass" in cases[0][1]
    assert any("retry limit" in step for step in cases[1][1])
    assert not any(step.startswith("tester") for step in cases[2][1])


if __name__ == "__main__":
    main()
