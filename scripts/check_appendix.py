#!/usr/bin/env python3
"""Guard the field tables and Appendix A against drift.

The spec says the body is normative and Appendix A is generated from it. This
checks that the two agree on which fields exist and on each field's type,
presence, and marker. It also enforces the table grammar of section 2.6:

  - Every table uses a layout in LAYOUTS. A new layout is an error until it is
    added there on purpose.
  - A field or key row names one key, in one code span, and a key ends [] exactly
    when its Type is an Array.
  - A Required cell is REQUIRED, OPTIONAL, RECOMMENDED, or REQUIRED when <...>.
  - A marker is one that section 3 defines.
  - A Type cell parses, a generic in it takes no bare Enum, and each name in it is a
    base type, a shared type, or a named key table. Names and Object rows waiting on another change are in
    PENDING_TYPES and PENDING_OBJECTS. Both lists only shrink.
  - A key table follows a bold lead-in that names its type.
  - The key table of a mixed field, and only that table, has a Mutability column of
    markers. pricing[] has no key table: its rows carry the markers.
    A lead-in's "each `<marker>`" names a marker of section 3 too.
  - Every heading above the appendices is numbered.
  - Normative text cites no issue number.

Body tables are  | `field` | Type | Required | Marker | Description |
Appendix A is    | `field` | Section | Type | Required | Marker |

Run: python3 scripts/check_appendix.py
"""
import re
import sys
from pathlib import Path

SPEC = Path(__file__).resolve().parent.parent / "spec" / "openproposal-3.0.md"

FIELD_LAYOUT = ("Field", "Type", "Required", "Mutability", "Description")
KEY_LAYOUT = ("Key", "Type", "Required", "Meaning")
KEY_MUTABILITY_LAYOUT = ("Key", "Type", "Required", "Meaning", "Mutability")

LAYOUTS = {
    FIELD_LAYOUT,
    KEY_LAYOUT,
    KEY_MUTABILITY_LAYOUT,
    ("Type", "Form", "Rules"),
    ("Marker", "Meaning"),
    # Value tables (section 2.6): the first header cell names the key that holds the list.
    ("`channel`", "Condition"),
    ("`environments`", "Distribution channel", "Device types"),
    # Other tables state rules as prose does (section 2.6).
    ("OpenProposal concept", "Downstream standard"),
    # Generated.
    ("Field", "Section", "Type", "Required", "Marker"),
    ("Marker", "Count", "Meaning", "Fields"),
}

BASE_TYPES = {
    "String", "Integer", "Number", "Boolean", "Enum", "Object",
    "Array", "Map", "Range", "Selectable", "Settable", "T",
}

# Named in a Type cell before the change that gives them a key table. Remove a
# name when its table lands. This list only shrinks.
PENDING_TYPES = {
    "HistoryEntry": "the negotiation history entry",
    "PropertyOption": "the property option",
    "AudienceOption": "the audience option",
    "BuyerSupplied": "the buyer-supplied audience data",
    "Delta": "the price delta of an option",
    "CancellationOption": "the cancellation option",
    "ExclusivityTerm": "the exclusivity term",
    "MinCommitment": "the purchase-level threshold",
    "CommittedMetric": "the committed metric tuple",
    "BuyerRequirements": "the buyer's seat and DSP requirements",
    "ExternalReference": "the external reference entry",
}

# Objects typed Object: open by definition, small and inline, or waiting on the
# change that names them. Remove an entry when its table lands. Only shrinks.
PENDING_OBJECTS = {
    "`assent`": "waiting: the assent entry",
    "`content_detail`": "waiting: the content the line item serves within",
    "`specs`": "waiting: the format spec",
    "`third_party_tags`": "waiting: the accepted tag protocols",
    "`approval`": "waiting: the review policy",
    "`daypart`": "waiting: the clock window",
    "`availability`": "waiting: the availability figure",
    "`commitment_bounds`": "waiting: the commitment bounds",
    "`creative_policy`": "waiting: the creative policy",
    "`required_credentials[]`": "waiting: the required credential",
    "`billing`": "waiting: the billing terms",
}

BODY_SECTION = re.compile(r"^#{3,4} ((?:4|5)\.\d+(?:\.\d+)?)\s")
SECTION_3 = re.compile(r"^## 3\.")
APPENDIX_A = re.compile(r"^## Appendix A")
APPENDIX_B = re.compile(r"^## Appendix B")
NUMBERED = re.compile(r"^#{2,4} (\d+\.(\d+(\.\d+)?)? )")
PRESENCE = re.compile(r"^(REQUIRED|OPTIONAL|RECOMMENDED|REQUIRED when .+)$")
ONE_KEY = re.compile(r"^`[^`]+`$")
LEAD_IN = re.compile(r"^\*\*`([A-Z][A-Za-z]+)`")
SHARED_TYPE = re.compile(r"`([A-Z][A-Za-z]+)`")
ISSUE_CITE = re.compile(r"(?<![\w/&])#\d+\b|/issues/\d+")


def cells(line):
    body = line.strip()
    if not (body.startswith("|") and body.endswith("|")):
        return None
    return [p.strip() for p in re.split(r"(?<!\\)\|", body[1:-1])]


def type_names(cell):
    """Return the names in a Type cell, or None if it does not parse."""
    text = cell.strip("`")
    if not re.fullmatch(r"[A-Za-z]+(\[[A-Za-z\[\], ]+\])?", text):
        return None
    if text.count("[") != text.count("]"):
        return None
    return re.findall(r"[A-Za-z]+", text)


def declared_types(lines):
    """Names a bold lead-in declares, plus each row of a Type/Form/Rules table."""
    names, in_types = {"LineItem", "PricingEntry"}, False
    for line in lines:
        m = LEAD_IN.match(line)
        if m:
            names.add(m.group(1))
        c = cells(line)
        if c and c[0] == "Type":
            in_types = True
            continue
        if not c:
            in_types = False
        elif in_types and not c[0].startswith(":"):
            names.update(SHARED_TYPE.findall(c[0]))
    return names


def lead_in(lines, header):
    """The bold type name that opens the paragraph just above a table, or None."""
    i = header - 1
    while i >= 0 and not lines[i].strip():
        i -= 1
    while i >= 0 and lines[i].strip() and not lines[i].startswith("|"):
        m = LEAD_IN.match(lines[i])
        if m:
            return m.group(1)
        i -= 1
    return None


def lint_tables(lines, markers, errors):
    declared = declared_types(lines)
    objects_seen = set()
    mixed_types, key_tables = set(), {}
    for n, line in enumerate(lines):
        for marker in re.findall(r"^\*\*`[A-Za-z]+`\*\* holds the keys of `[^`]+`, each `([^`]+)`", line):
            if marker not in markers:
                errors.append(f"line {n + 1}: marker not defined in section 3: {marker}")
    i = 0
    while i < len(lines):
        line = lines[i]
        c = cells(line)
        is_header = (
            c and i + 1 < len(lines)
            and re.match(r"^\|\s*:?-{3}", lines[i + 1])
        )
        if not is_header:
            i += 1
            continue
        header = tuple(c)
        if header not in LAYOUTS:
            errors.append(f"line {i + 1}: table layout not in LAYOUTS: {line}")
        if header in (KEY_LAYOUT, KEY_MUTABILITY_LAYOUT):
            name = lead_in(lines, i)
            if not name:
                errors.append(f"line {i + 1}: a key table follows a lead-in that names its type")
            key_tables[name] = (i + 1, header)
        i += 2
        while i < len(lines) and lines[i].startswith("|"):
            row = cells(lines[i])
            where = f"line {i + 1}"
            if len(row) != len(header):
                errors.append(f"{where}: {len(row)} cells under a {len(header)}-cell header")
            elif header in (FIELD_LAYOUT, KEY_LAYOUT, KEY_MUTABILITY_LAYOUT):
                key, typ, required = row[0], row[1], row[2]
                if not ONE_KEY.match(key):
                    errors.append(f"{where}: a row names one key: {key}")
                if key.endswith("[]`") != typ.startswith("Array["):
                    errors.append(f"{where}: a key ends [] exactly when it holds an Array: {key} {typ}")
                if not PRESENCE.match(required):
                    errors.append(f"{where}: Required cell is not in the grammar: {required}")
                names = type_names(typ)
                if names is None:
                    errors.append(f"{where}: Type cell does not parse: {typ}")
                else:
                    for name in names:
                        if name not in BASE_TYPES | declared | set(PENDING_TYPES):
                            errors.append(f"{where}: Type names an undefined type: {name}")
                    if "Enum" in names and names != ["Enum"]:
                        errors.append(f"{where}: a generic never takes Enum: {typ}")
                    if "Object" in names:
                        objects_seen.add(key)
                        if key not in PENDING_OBJECTS:
                            errors.append(f"{where}: {key} is an Object with no key table")
                if header == FIELD_LAYOUT and row[3] not in markers:
                    errors.append(f"{where}: marker not defined in section 3: {row[3]}")
                if header == FIELD_LAYOUT and row[3] == "mixed":
                    mixed_types.update(n for n in re.findall(r"[A-Za-z]+", typ) if n != "Array")
                if header == KEY_MUTABILITY_LAYOUT and row[4] not in markers:
                    errors.append(f"{where}: marker not defined in section 3: {row[4]}")
            i += 1
    for name, (line, header) in key_tables.items():
        if (name in mixed_types) != (header == KEY_MUTABILITY_LAYOUT):
            errors.append(f"line {line}: {name}: the key table of a mixed field, and only it, has a Mutability column")
    for name, owner in PENDING_TYPES.items():
        if name in declared:
            errors.append(f"{name} has a key table now: remove it from PENDING_TYPES ({owner})")
    for key, owner in PENDING_OBJECTS.items():
        if key not in objects_seen:
            errors.append(f"{key} is no longer an Object row: remove it from PENDING_OBJECTS ({owner})")


def lint_headings(lines, errors):
    for i, line in enumerate(lines):
        if APPENDIX_A.match(line):
            break
        if line.startswith("##") and not NUMBERED.match(line):
            errors.append(f"line {i + 1}: heading has no number: {line}")


def lint_citations(lines, errors):
    active = True
    for i, line in enumerate(lines):
        if line.startswith("## 8."):
            active = False  # Section 8 tracks open questions, which are issues.
        if APPENDIX_A.match(line):
            active = True
        if active and ISSUE_CITE.search(line):
            errors.append(f"line {i + 1}: normative text cites an issue: {line.strip()[:80]}")


def marker_table(lines):
    start = next(i for i, l in enumerate(lines) if SECTION_3.match(l))
    markers = []
    for line in lines[start:]:
        if line.startswith("## ") and not SECTION_3.match(line):
            break
        c = cells(line)
        if c and len(c) == 2 and c[0].startswith("`"):
            markers.append(c[0].strip("`"))
    return markers


def collect(rows):
    """Keep the first row seen per field, and flag a repeat that differs.

    `status` legitimately appears on the proposal (4.1) and on the line item
    (5.1), so a repeat is not an error, but the type and marker must agree
    between the body and the appendix for each pair.
    """
    seen = {}
    for field, *rest in rows:
        seen.setdefault(field, []).append(tuple(rest))
    return seen


def main():
    lines = SPEC.read_text().splitlines()
    try:
        a_start = next(i for i, l in enumerate(lines) if APPENDIX_A.match(l))
    except StopIteration:
        print("Could not find '## Appendix A' in the spec.")
        return 1

    markers = marker_table(lines)
    body_rows, active, in_field = [], False, False
    for line in lines[:a_start]:
        if line.startswith("#"):
            active = bool(BODY_SECTION.match(line))
            in_field = False
            continue
        if not active:
            continue
        c = cells(line)
        if not c:
            in_field = False
        elif tuple(c) == FIELD_LAYOUT:
            in_field = True
        elif in_field and not c[0].startswith(":") and len(c) == 5:
            body_rows.append((c[0], c[1], c[2], c[3]))

    appendix_rows = []
    for line in lines[a_start:]:
        if APPENDIX_B.match(line):
            break
        c = cells(line)
        if c and len(c) == 5 and c[0].startswith("`"):
            appendix_rows.append((c[0], c[2], c[3], c[4]))

    body = collect(body_rows)
    appendix = collect(appendix_rows)

    errors = []
    if not body:
        errors.append("parsed no fields from the body: the table format changed")
    if not appendix:
        errors.append("parsed no fields from Appendix A: the table format changed")

    for field, values in sorted(body.items()):
        if field not in appendix:
            errors.append(f"in the body but missing from Appendix A: {field}")
        elif appendix[field] != values:
            errors.append(
                f"type, presence, or marker disagrees for {field}: "
                f"body says {values}, Appendix A says {appendix[field]}"
            )
    for field in sorted(appendix):
        if field not in body:
            errors.append(f"in Appendix A but not in a body field table: {field}")

    lint_tables(lines, markers, errors)
    lint_headings(lines, errors)
    lint_citations(lines, errors)

    if errors:
        print("The tables have drifted from the grammar or from Appendix A:\n")
        for e in errors:
            print(f"  - {e}")
        print(
            "\nThe body is normative. Run regen_appendices.py after a body change, "
            "and fix what the lint names."
        )
        return 1

    print(
        f"Appendix A matches the body: {len(body)} field names, "
        f"{len(body_rows)} rows. Table grammar holds."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
