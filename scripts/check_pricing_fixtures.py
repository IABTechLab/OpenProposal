#!/usr/bin/env python3
"""Pricing arithmetic vectors for #30, #94 and #115.

These test this adapter's arithmetic against fixed expected values. They read neither
the specification nor the examples; scripts/check_examples.py does that.
"""

import argparse
import json
import math
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


def check_range(bounds, actual, outside):
    """Apply a Range (section 2.2) of decimal strings to one value."""
    shape(bounds, (), ("min", "max"))
    require(bounds, "empty_bounds")
    values = {key: number(value) for key, value in bounds.items()}
    require(all(value >= 0 for value in values.values()), "negative_bound")
    require(len(values) < 2 or values["min"] <= values["max"], "inverted_bounds")
    require(actual >= values.get("min", actual) and actual <= values.get("max", actual), outside)


def resolve(case):
    """Resolve already selected adjustments using exact rational arithmetic.

    Keys take their names from sections 3.1, 5.6 and 5.6.1. basis, amount and
    pricing_id are the commitment's, and adjustments holds the deltas in effect.
    """
    shape(case, ("pricing", "basis", "amount", "adjustments"), ("pricing_id", "commitment_bounds"))
    rows = case["pricing"]
    require(isinstance(rows, list) and rows, "missing_pricing")
    for row in rows:
        shape(row, ("pricing_id", "cost_method", "list_rate", "currency"), ("min_rate", "unit_bounds"))
        require(isinstance(row["pricing_id"], str) and row["pricing_id"], "invalid_pricing_id")
    ids = [row["pricing_id"] for row in rows]
    require(len(ids) == len(set(ids)), "duplicate_pricing_id")
    require(len(rows) == 1 or "pricing_id" in case, "pricing_choice_required")
    chosen = case.get("pricing_id", ids[0])
    require(chosen in ids, "unknown_pricing_id")
    row = rows[ids.index(chosen)]
    method = row["cost_method"]
    require(isinstance(method, str), "invalid_shape")
    require(method in ("CPM", "CPMV", "CPC"), "unsupported_cost_method")
    require(isinstance(row["currency"], str) and re.fullmatch(r"[A-Z]{3}", row["currency"]),
            "invalid_currency")
    require(case["basis"] in ("spend", "units"), "unsupported_basis")
    amount = number(case["amount"])
    require(amount > 0, "nonpositive_amount")
    rate = number(row["list_rate"])
    require(rate >= 0, "nonpositive_rate")
    cpm_delta, flat, factors = Fraction(0), Fraction(0), []
    adjustments = case["adjustments"]
    require(isinstance(adjustments, list), "invalid_shape")
    adjustment_ids = set()
    for adjustment in adjustments:
        shape(adjustment, ("id",), ("delta_cpm", "delta_fraction", "delta_flat"))
        key = adjustment["id"]
        require(isinstance(key, str) and key, "invalid_adjustment_id")
        require(key not in adjustment_ids, "duplicate_adjustment")
        adjustment_ids.add(key)
        require(len(adjustment) > 1, "empty_adjustment")
        if "delta_cpm" in adjustment:
            # Section 3.1: it enters only a CPM or CPMV rate, and an option priced
            # only by it doesn't resolve against any other entry.
            delta = number(adjustment["delta_cpm"])
            if method in ("CPM", "CPMV"):
                cpm_delta += delta
            else:
                require(len(adjustment) > 2, "incompatible_delta_cpm")
        if "delta_flat" in adjustment:
            fee = number(adjustment["delta_flat"])
            require(fee >= 0, "unsupported_flat_credit")
            flat += fee
        if "delta_fraction" in adjustment:
            factor = 1 + number(adjustment["delta_fraction"])
            require(factor > 0, "invalid_delta_fraction")
            factors.append(factor)
    rate += cpm_delta
    for factor in factors:
        rate *= factor
    # Section 5.6: exact decimal, rounded once, half up, to 6 places.
    rate = Fraction(math.floor(rate * 10**6 + Fraction(1, 2)), 10**6)
    require(rate > 0 if case["basis"] == "spend" else rate >= 0, "nonpositive_rate")
    # min_rate is a hint (section 5.6), so it never changes the result.
    require(number(row.get("min_rate", "0")) >= 0, "negative_min_rate")
    rate_per = 1000 if method in ("CPM", "CPMV") else 1
    if case["basis"] == "spend":
        total = amount
        require(total >= flat, "fees_exceed_spend")
        media = total - flat
        # Section 5.6.5: rounded down to a whole unit.
        units = Fraction(math.floor(media / rate * rate_per))
    else:
        units = amount
        media = units / rate_per * rate
        total = media + flat
    commitment_bounds = case.get("commitment_bounds", {})
    shape(commitment_bounds, (), ("spend",))
    if "spend" in commitment_bounds:
        check_range(commitment_bounds["spend"], total, "outside_spend_bounds")
    if "unit_bounds" in row:
        check_range(row["unit_bounds"], units, "outside_unit_bounds")
    return {"pricing_id": chosen, "currency": row["currency"], "min_rate_check": "not_checked",
            **{key: str(value) for key, value in {
                "agreed_rate": rate, "flat_charges": flat, "media_spend": media,
                "seller_total": total, "derived_units": units}.items()}}


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
        print(f"{passed}/{len(results)} pricing arithmetic vectors pass; "
              "this reads neither the specification nor the examples")
    return int(passed != len(results))


if __name__ == "__main__":
    raise SystemExit(main())
