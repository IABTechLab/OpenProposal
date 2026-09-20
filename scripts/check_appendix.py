#!/usr/bin/env python3
"""Guard against Appendix A drifting from the normative body.

The spec says the body is normative and Appendix A is generated from it. This
checks the two agree on which fields exist and what marker each carries, so a
change request that updates one and forgets the other fails CI rather than
shipping.

Body tables are  | `field` | Type | Marker | Description |
Appendix A is    | `field` | Section | Type | Marker |

Run: python3 scripts/check_appendix.py
"""
import re
import sys
from pathlib import Path

SPEC = Path(__file__).resolve().parent.parent / "spec" / "openproposal-3.0.md"
MARKERS = {
    "immutable", "seller-set", "selectable", "settable",
    "supplied", "requestable", "derived", "mixed",
}
# Sections 4.x and 5.x carry the normative field tables.
BODY_SECTION = re.compile(r"^#{3,4} (4\.\d|5\.\d+(?:\.\d+)?)\s")
APPENDIX_A = re.compile(r"^## Appendix A")
APPENDIX_B = re.compile(r"^## Appendix B")
BODY_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([a-z-]+)\s*\|")
APPENDIX_ROW = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([a-z-]+)\s*\|"
)


def collect(rows):
    """Keep the first marker seen per field, and note fields declared twice.

    `status` legitimately appears twice — once on the proposal (4.1) and once on
    the line item (5.1) — so a repeat is not an error, but the markers must agree.
    """
    seen = {}
    for field, marker in rows:
        if field in seen and seen[field] != marker:
            seen[field] = f"CONFLICT({seen[field]}/{marker})"
        else:
            seen.setdefault(field, marker)
    return seen


def main():
    lines = SPEC.read_text().splitlines()
    try:
        a_start = next(i for i, l in enumerate(lines) if APPENDIX_A.match(l))
    except StopIteration:
        print("Could not find '## Appendix A' in the spec.")
        return 1

    body_rows, active = [], False
    for line in lines[:a_start]:
        if line.startswith("#"):
            active = bool(BODY_SECTION.match(line))
        if not active:
            continue
        m = BODY_ROW.match(line)
        if m and m.group(3) in MARKERS:
            body_rows.append((m.group(1), m.group(3)))

    appendix_rows = []
    for line in lines[a_start:]:
        if APPENDIX_B.match(line):
            break
        m = APPENDIX_ROW.match(line)
        if m and m.group(4) in MARKERS:
            appendix_rows.append((m.group(1), m.group(4)))

    body = collect(body_rows)
    appendix = collect(appendix_rows)

    errors = []
    if not body:
        errors.append("parsed no fields from the body — the table format changed")
    if not appendix:
        errors.append("parsed no fields from Appendix A — the table format changed")

    for field, marker in sorted(body.items()):
        if field not in appendix:
            errors.append(f"in the body but missing from Appendix A: `{field}`")
        elif appendix[field] != marker:
            errors.append(
                f"marker disagrees for `{field}`: "
                f"body says {marker}, Appendix A says {appendix[field]}"
            )
    for field in sorted(appendix):
        if field not in body:
            errors.append(f"in Appendix A but not in a body field table: `{field}`")

    if errors:
        print("Appendix A has drifted from the normative body:\n")
        for e in errors:
            print(f"  - {e}")
        print(
            "\nThe body is normative. Update Appendix A (and the counts in "
            "Appendix B) to match it."
        )
        return 1

    # Fewer unique keys than Appendix A rows is expected: the combined
    # `valid_from` · `valid_until` row is skipped, and `status` appears on both
    # the proposal and the line item, collapsing to one key.
    print(f"Appendix A matches the body: {len(body)} fields, markers agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
