from __future__ import annotations


def main() -> None:
    costs = {"design": 30, "engineering": 45, "marketing": 40}
    budget_cap = 100
    total = sum(costs.values())
    print(
        f"initial cost: design={costs['design']}, engineering={costs['engineering']}, "
        f"marketing={costs['marketing']}; total={total}; cap={budget_cap}"
    )
    if total > budget_cap:
        print(f"conflict: planned cost {total} exceeds shared cap {budget_cap}")

    critiques = [
        ("design_agent", "premium venue is not needed for the core experience"),
        ("engineering_agent", "contingency is too small for the integration risk"),
        ("marketing_agent", "paid campaign exceeds the remaining budget"),
    ]
    for role, objection in critiques:
        print(f"objection [{role}]: {objection}")

    # budget_over_preference keeps the cap fixed and reduces optional scope.
    costs["marketing"] -= total - budget_cap
    resolved_total = sum(costs.values())
    print(
        f"resolution [budget_over_preference]: reduce optional marketing spend "
        f"40 -> {costs['marketing']}; total={resolved_total}"
    )
    assert resolved_total == budget_cap
    assert len({role for role, _ in critiques}) >= 2


if __name__ == "__main__":
    main()
