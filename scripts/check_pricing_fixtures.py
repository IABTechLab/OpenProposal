#!/usr/bin/env python3
"""Executable discussion profile for #30, #94 and #115, not a wire validator."""

import argparse
import json
import re
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECIMAL = re.compile(r"-?\d{1,18}(?:\.\d{1,9})?\Z")


class ProfileError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ProfileError(code)


def number(value):
    # Decimal strings make these test vectors independent of binary floats.
    require(isinstance(value, str) and DECIMAL.fullmatch(value), "invalid_number")
    return Fraction(value)


def shape(obj, required, optional=()):
    require(isinstance(obj, dict), "invalid_shape")
    require(set(required) <= obj.keys(), "missing_field")
    require(obj.keys() <= set(required) | set(optional), "unsupported_field")


def resolve(case):
    """Resolve already selected adjustments using exact rational arithmetic.

    Input names are fixture adapter keys, not proposed OpenProposal fields.
    Only a caller that has established acceptance may supply accepted_counter.
    """
    shape(case, ("pricing", "basis", "amount", "currency", "adjustments"),
          ("pricing_id", "accepted_counter", "selection_key", "bounds"))
    rows = case["pricing"]
    require(isinstance(rows, list) and rows, "missing_pricing")
    for row in rows:
        shape(row, ("pricing_id", "cost_method", "gross_rate", "currency"), ("floor",))
        require(isinstance(row["pricing_id"], str) and row["pricing_id"], "invalid_pricing_id")
    ids = [row["pricing_id"] for row in rows]
    require(len(ids) == len(set(ids)), "duplicate_pricing_id")
    require(len(rows) == 1 or "pricing_id" in case, "pricing_choice_required")
    chosen = case.get("pricing_id", ids[0])
    require(chosen in ids, "unknown_pricing_id")
    row = rows[ids.index(chosen)]
    method = row["cost_method"]
    require(isinstance(method, str), "invalid_shape")
    method = method.upper()
    require(method in ("CPM", "CPMV", "CPC"), "unsupported_cost_method")
    require(isinstance(row["currency"], str) and re.fullmatch(r"[A-Z]{3}", row["currency"]),
            "invalid_currency")
    require(case["currency"] == row["currency"], "currency_mismatch")
    require(case["basis"] in ("spend", "units"), "unsupported_basis")
    amount = number(case["amount"])
    require(amount > 0, "nonpositive_amount")
    rate = number(row["gross_rate"])
    require(rate > 0, "nonpositive_rate")
    cpm_delta, flat, factors = Fraction(0), Fraction(0), []
    adjustments = case["adjustments"]
    require(isinstance(adjustments, list), "invalid_shape")
    adjustment_ids = set()
    for adjustment in adjustments:
        shape(adjustment, ("id",), ("delta_cpm", "delta_pct", "delta_flat"))
        key = adjustment["id"]
        require(isinstance(key, str) and key, "invalid_adjustment_id")
        require(key not in adjustment_ids, "duplicate_adjustment")
        adjustment_ids.add(key)
        require(len(adjustment) > 1, "empty_adjustment")
        if "delta_cpm" in adjustment:
            require(method in ("CPM", "CPMV"), "incompatible_delta_cpm")
            cpm_delta += number(adjustment["delta_cpm"])
        if "delta_flat" in adjustment:
            fee = number(adjustment["delta_flat"])
            require(fee >= 0, "unsupported_flat_credit")
            flat += fee
        if "delta_pct" in adjustment:
            factor = 1 + number(adjustment["delta_pct"])
            require(factor > 0, "nonpositive_percentage_factor")
            factors.append(factor)
    rate += cpm_delta
    for factor in factors:
        rate *= factor
    if "accepted_counter" in case:
        counter = case["accepted_counter"]
        shape(counter, ("rate", "selection_key"))
        require(isinstance(case.get("selection_key"), str) and case["selection_key"],
                "counter_binding_required")
        require(counter["selection_key"] == case["selection_key"], "stale_counter")
        # The accepted counter is the final composed rate, not a new base rate.
        rate = number(counter["rate"])
    require(rate > 0, "nonpositive_rate")
    floor = number(row.get("floor", "0"))
    require(floor >= 0, "negative_floor")
    require(rate >= floor, "below_floor")
    rate_per = 1000 if method in ("CPM", "CPMV") else 1
    if case["basis"] == "spend":
        total = amount
        require(total >= flat, "fees_exceed_spend")
        media = total - flat
        units = media / rate * rate_per
    else:
        units = amount
        media = units / rate_per * rate
        total = media + flat
    bounds = case.get("bounds", {})
    shape(bounds, (), ("min_budget", "max_budget", "min_spend", "min_impressions", "max_impressions"))
    values = {key: number(value) for key, value in bounds.items()}
    require(all(value >= 0 for value in values.values()), "negative_bound")
    for low, high in (("min_budget", "max_budget"), ("min_impressions", "max_impressions")):
        require(low not in values or high not in values or values[low] <= values[high],
                "inverted_bounds")
    require("min_spend" not in values or "max_budget" not in values or
            values["min_spend"] <= values["max_budget"], "inverted_bounds")
    for name, value in values.items():
        actual = total
        if name.endswith("impressions"):
            require(method == "CPM", "unsupported_impression_bound")
            actual = units
        require(actual >= value if name.startswith("min_") else actual <= value,
                "outside_" + name)
    return {"pricing_id": chosen, "currency": row["currency"],
            **{key: str(value) for key, value in {
                "agreed_rate": rate, "flat_charges": flat, "media_spend": media,
                "seller_total": total, "units": units}.items()}}


def evaluate(case):
    try:
        return {"result": resolve(case)}
    except ProfileError as error:
        return {"error": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit per-vector evidence")
    args = parser.parse_args()
    corpus = json.loads((ROOT / "fixtures/pricing/cases.json").read_text())
    results = []
    for vector in corpus["cases"]:
        actual = evaluate(vector["input"])
        results.append({"id": vector["id"], "passed": actual == vector["expected"],
                        "actual": actual, "expected": vector["expected"]})
    passed = sum(result["passed"] for result in results)
    if args.json:
        print(json.dumps({"profile": corpus["profile"], "passed": passed,
                          "total": len(results), "cases": results}, indent=2))
    else:
        for result in results:
            print(("PASS " if result["passed"] else "FAIL ") + result["id"])
            if not result["passed"]:
                print(json.dumps(result, indent=2))
        print(f"{passed}/{len(results)} pricing discussion vectors pass")
    return int(passed != len(results))


if __name__ == "__main__":
    raise SystemExit(main())
