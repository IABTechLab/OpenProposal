#!/usr/bin/env python3
"""Check every example against the tables of the specification.

Every rule here reads the spec, so a table change reaches the examples without a
change to this script. It checks:

  - Each file parses strictly: no duplicate keys, no implicit dates.
  - Each REQUIRED field and key is present. A `REQUIRED when <condition>` cell is
    tested by its entry in CONDITIONS, and a wording with no entry is an error.
  - Each key at a typed position is a key its table lists, and each value has its
    Type: Instant, Duration, Digest, Domain, VocabularyTerm, the other shared types,
    and the base types. An Enum value is on the list its row opens with.
  - An option name in included[] or deltas names an option in available[].
  - The manifest is a strict path subset of the full objects (section 2.1), and lists
    each public line item (section 2.3).

KNOWN holds findings that a later change removes. It only shrinks. Run with
--regen-manifest to rewrite examples/manifest.json from the full examples.

Run: python3 scripts/check_examples.py
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "openproposal-3.0.md"
EXAMPLES = ROOT / "examples"

# Object types whose extra keys are allowed.
OPEN_TYPES = {"DocumentRef"}
# A named type that holds the keys of another.
COMPOSES = {"Commitment": ["CommitmentAmount"], "ManifestEntry": ["ProposalSummary"]}

# (file, path, finding): removed by the change named in the comment.
KNOWN = {
    # Option ids: these options are named by a key value until option ids are defined.
    ("line-item-display.yaml", "measurement_source.included", "IAS"),
    ("line-item-display.yaml", "reporting.included", "aggregate"),
    ("line-item-display.yaml", "reporting.deltas", "log_level"),
    # Line items: proposal.yaml shows them in their own files (section 6.1), until the
    # change that lists the published line items inline in proposal.yaml.
    ("proposal.yaml", "(root)", "line_items"),
}


# Each `REQUIRED when <condition>` wording, as (object, line item, proposal) -> bool.
CONDITIONS = {
    "`type` is `custom`": lambda o, i, p: o.get("type") == "custom",
    "`basis` is `spend`": lambda o, i, p: o.get("basis") == "spend",
    "`at` is absent": lambda o, i, p: "at" not in o,
    "`before_start` is absent": lambda o, i, p: "before_start" not in o,
    "`url` is absent": lambda o, i, p: "url" not in o,
    "`markup` is absent": lambda o, i, p: "markup" not in o,
}

BASE = {"String", "Integer", "Number", "Boolean", "Enum", "Object"}
INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
# The RFC 3339 Appendix A grammar without its week form: section 2.2 writes P14D, never P2W.
_DUR_TIME = r"T(?:\d+H(?:\d+M(?:\d+S)?)?|\d+M(?:\d+S)?|\d+S)"
_DUR_DATE = r"(?:\d+Y(?:\d+M(?:\d+D)?)?|\d+M(?:\d+D)?|\d+D)"
DURATION = re.compile(rf"P(?:{_DUR_DATE}(?:{_DUR_TIME})?|{_DUR_TIME})\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
DOMAIN = re.compile(r"[a-z0-9-]+(\.[a-z0-9-]+)+\Z")
# The VocabularyTerm form of section 2.2: a bare term, or a domain and a term.
TERM_PART = r"[A-Za-z0-9_-]+"
TERM_DOMAIN = r"[a-z0-9-]+(?:\.[a-z0-9-]+)+:"
TERM = re.compile(rf"(?:{TERM_DOMAIN})?{TERM_PART}\Z")
SIDE = ("buyer", "seller")
CALENDAR_UNIT = ("hour", "day", "week", "month")
SCALARS = {
    "Instant": (lambda v: isinstance(v, str) and INSTANT.match(v)),
    "Duration": (lambda v: isinstance(v, str) and DURATION.match(v)),
    "Digest": (lambda v: isinstance(v, str) and DIGEST.match(v)),
    "Domain": (lambda v: isinstance(v, str) and DOMAIN.match(v)),
    "RegistrableDomain": (lambda v: isinstance(v, str) and DOMAIN.match(v)),
    "Measurer": (lambda v: v in SIDE or (isinstance(v, str) and DOMAIN.match(v))),
    "VocabularyTerm": (lambda v: isinstance(v, str) and TERM.match(v)),
    "MediaChannel": (lambda v: isinstance(v, str) and TERM.match(v)),
    "String": (lambda v: isinstance(v, str)),
    "Url": (lambda v: isinstance(v, str) and v.startswith(("http://", "https://"))),
    "Integer": (lambda v: (isinstance(v, int) and not isinstance(v, bool))
                or (isinstance(v, float) and v.is_integer())),  # JSON's integer: JCS writes 3.0 as 3
    "IntegerFlag": (lambda v: v in (0, 1) and not isinstance(v, bool)),
    "Number": (lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)),
    "Amount": (lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)),
    "Boolean": (lambda v: isinstance(v, bool)),
    "Fraction": (lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1),
    "FractionDelta": (lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and v > -1),
    "CalendarUnit": (lambda v: v in CALENDAR_UNIT),
    "TimeUnit": (lambda v: v in CALENDAR_UNIT + ("flight",)),
    "ZoneName": (lambda v: isinstance(v, str)),
    "IanaZone": (lambda v: isinstance(v, str)),
    "Side": (lambda v: v in SIDE),
    "EntryRef": (lambda v: isinstance(v, str) and re.fullmatch(r"[^/@]+/[^/@]+/[^/@]+@[^/@]+", v)),
    "FieldPointer": (lambda v: isinstance(v, str) and (v == "" or v.startswith("/"))),
}


class StrictLoader(yaml.SafeLoader):
    """Reject duplicate keys, and keep dates as strings to reject them by type."""


def _strict_map(loader, node):
    out = {}
    for k_node, v_node in node.value:
        key = loader.construct_object(k_node, deep=True)
        if key in out:
            raise yaml.YAMLError(f"duplicate key {key!r} at line {k_node.start_mark.line + 1}")
        out[key] = loader.construct_object(v_node, deep=True)
    return out


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _strict_map)
StrictLoader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(path):
    return yaml.load(path.read_text(), Loader=StrictLoader)


def load_json(path):
    def pairs(items):
        keys = [k for k, _ in items]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate key in {path.name}")
        return dict(items)

    return json.loads(path.read_text(), object_pairs_hook=pairs)


# Spec reading --------------------------------------------------------------


def cells(line):
    body = line.strip()
    if not (body.startswith("|") and body.endswith("|")):
        return None
    return [p.strip() for p in re.split(r"(?<!\\)\|", body[1:-1])]


def clean_key(cell):
    return cell.strip("`")


def enum_values(typ, meaning):
    """The closed list an Enum row opens its Meaning or Description with (section 2.6)."""
    if typ != "Enum":
        return None
    m = re.match(r"^((?:`[^`]+`(?: \([^)]*\))?(?: \\\| )?)+)", meaning)
    if not m:
        return None
    return re.findall(r"`([^`]+)`", m.group(1))


class Spec:
    def __init__(self):
        self.lines = SPEC.read_text().splitlines()
        self.proposal, self.line_item = {}, {}
        self.tables = {}
        self.manifest_keys = {}
        self.summary_paths, self.proposal_paths = [], []
        self._read_fields()
        self._read_key_tables()
        self._read_lists()

    def _read_fields(self):
        target, in_table = None, False
        for line in self.lines:
            if line.startswith("## Appendix"):
                break
            m = re.match(r"^#{2,4} (\d+)\.", line)
            if m:
                target = {"4": self.proposal, "5": self.line_item}.get(m.group(1))
                in_table = False
                continue
            c = cells(line)
            if not c:
                in_table = False
            elif c[0] == "Field":
                in_table = True
            elif in_table and target is not None and len(c) == 5 and c[0].startswith("`"):
                target[clean_key(c[0])] = {
                    "type": c[1], "required": c[2], "marker": c[3],
                    "values": enum_values(c[1], c[4]),
                }

    def _read_key_tables(self):
        current = None
        for i, line in enumerate(self.lines):
            if line.startswith("## Appendix"):
                break
            m = re.match(r"^\*\*`([A-Z][A-Za-z]+)`", line)
            if m:
                current = m.group(1)
                continue
            c = cells(line)
            if c and c[:2] == ["Key", "Type"]:
                if current:
                    self.tables.setdefault(current, {})
                    rows = self.tables[current]
                    j = i + 2
                    while j < len(self.lines) and self.lines[j].startswith("|"):
                        r = cells(self.lines[j])
                        rows[clean_key(r[0])] = {
                            "type": r[1], "required": r[2], "values": enum_values(r[1], r[3]),
                        }
                        j += 1
                current = None

    def _read_lists(self):
        text = "\n".join(self.lines)
        m = re.search(r"`LineItemSummary` lists these paths[^\n]*\n\n```text\n(.*?)```", text, re.S)
        self.summary_paths = m.group(1).split()
        m = re.search(r"`ProposalSummary` lists these paths[^\n]*\n\n```text\n(.*?)```", text, re.S)
        self.proposal_paths = m.group(1).split()


# Type walking --------------------------------------------------------------


def split_generic(typ):
    m = re.fullmatch(r"([A-Za-z]+)\[(.*)\]", typ)
    if not m:
        return typ, []
    args, depth, cur = [], 0, ""
    for ch in m.group(2):
        if ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
            continue
        depth += ch == "["
        depth -= ch == "]"
        cur += ch
    args.append(cur.strip())
    return m.group(1), args


def bare(key):
    return key[:-2] if key.endswith("[]") else key


class Checker:
    def __init__(self, spec):
        self.spec = spec
        self.errors = []
        self.used_known = set()
        self.item, self.proposal = {}, None

    def err(self, file, path, what, msg):
        if (file, path, what) in KNOWN:
            self.used_known.add((file, path, what))
            return
        self.errors.append(f"{file}: {path}: {msg}")

    def required(self, file, path, cell, obj):
        """Return whether a Required cell makes its key required on obj."""
        if cell == "REQUIRED":
            return True
        if not cell.startswith("REQUIRED when "):
            return False
        condition = cell[len("REQUIRED when "):]
        if condition not in CONDITIONS:
            self.errors.append(f"{file}: {path}: no CONDITIONS entry for: {condition}")
            return False
        return CONDITIONS[condition](obj, self.item, self.proposal)

    def check_value(self, file, path, value, row):
        values = row.get("values")
        if values is not None and value not in values:
            self.err(file, path, repr(value), f"{value!r} is not on the list {values}")
            return
        self.check_type(file, path, value, row["type"])

    def check_type(self, file, path, value, typ):
        base, args = split_generic(typ)
        if base == "Array":
            if not isinstance(value, list):
                self.err(file, path, "array", f"expected an array, found {type(value).__name__}")
                return
            for i, item in enumerate(value):
                self.check_type(file, f"{path}[{i}]", item, args[0])
            return
        if base == "Map":
            if not isinstance(value, dict):
                self.err(file, path, "map", f"expected a map, found {type(value).__name__}")
                return
            for k, item in value.items():
                self.check_type(file, f"{path}.{k}", item, args[1])
            return
        if base == "Selectable":
            self.check_selectable(file, path, value, args[0])
            return
        if base == "Settable":
            self.check_settable(file, path, value, args[0])
            return
        if base == "Range":
            if not isinstance(value, dict) or not value or not value.keys() <= {"min", "max"}:
                self.err(file, path, "range", "a Range holds min, max, or both")
                return
            for k, item in value.items():
                self.check_type(file, f"{path}.{k}", item, args[0])
            return
        if base == "Enum":
            if not isinstance(value, str):
                self.err(file, path, repr(value), f"{value!r} is not an Enum value")
            return
        if base == "Object":
            if not isinstance(value, dict):
                self.err(file, path, "object", f"expected an object, found {type(value).__name__}")
            return
        if base in SCALARS:
            if not SCALARS[base](value):
                self.err(file, path, repr(value), f"{value!r} is not a {base}")
            return
        if base in self.spec.tables:
            self.check_object(file, path, value, base)

    def rows_of(self, name):
        rows = dict(self.spec.tables.get(name, {}))
        # A path list (section 2.1) gives its type the first segment of each path. The
        # summary check below compares the values with the full objects.
        heads = {"LineItemSummary": self.spec.summary_paths,
                 "ProposalSummary": self.spec.proposal_paths}.get(name, [])
        for path in heads:
            rows.setdefault(path.split(".")[0], {"type": "", "required": "OPTIONAL"})
        for extra in COMPOSES.get(name, []):
            rows.update(self.rows_of(extra))
        return rows

    def check_object(self, file, path, value, name):
        if not isinstance(value, dict):
            self.err(file, path, "object", f"expected a {name}, found {type(value).__name__}")
            return
        known = {bare(k): r for k, r in self.rows_of(name).items()}
        if name not in OPEN_TYPES:
            for key in value:
                if key not in known:
                    self.err(file, path, key, f"key {key!r} is not in the {name} table")
        for key, row in known.items():
            if key not in value and self.required(file, path, row["required"], value):
                self.err(file, path, key, f"REQUIRED key {key!r} of {name} is missing")
            if key in value:
                self.check_value(file, f"{path}.{key}", value[key], row)

    def check_settable(self, file, path, value, entry_type):
        """Section 3.2: an enumerated set in allowed[], or a range in min and max."""
        if not isinstance(value, dict) or not value:
            self.err(file, path, "settable", "expected a Settable")
            return
        if "allowed" in value:
            if value.keys() != {"allowed"}:
                self.err(file, path, "settable", "a Settable declares allowed[] or min and max")
            self.check_type(file, f"{path}.allowed", value["allowed"], f"Array[{entry_type}]")
        elif not value.keys() <= {"min", "max"}:
            self.err(file, path, "settable", "a Settable declares allowed[] or min and max")

    def check_selectable(self, file, path, value, option_type):
        if not isinstance(value, dict):
            self.err(file, path, "selectable", "expected a Selectable")
            return
        if "available" not in value:
            self.err(file, path, "available", "a Selectable holds available[]")
            return
        known = {bare(k) for k in self.spec.tables["Selectable"]}
        for key in value:
            if key not in known:
                self.err(file, path, key, f"key {key!r} is not a Selectable key")
        names = []
        for i, option in enumerate(value["available"]):
            if isinstance(option, dict):
                names.append(option.get("id"))
                if option_type in self.spec.tables:
                    self.check_object(file, f"{path}.available[{i}]", option, option_type)
            else:
                names.append(str(option))
                self.check_type(file, f"{path}.available[{i}]", option, option_type)
        if "included" not in value:
            self.err(file, path, "included", "REQUIRED key 'included' is missing")
        for name in value.get("included", []):
            if name not in names:
                self.err(file, f"{path}.included", name, f"{name!r} names no option")
        for name in (value.get("deltas") or {}):
            if name not in names:
                self.err(file, f"{path}.deltas", name, f"{name!r} names no option")
        if "max_select" in value:
            self.check_type(file, f"{path}.max_select", value["max_select"], "Integer")

    def check_fields(self, file, path, doc, fields):
        known = {bare(k): r for k, r in fields.items() if "[]." not in k}
        if "line_item_id" in doc:
            self.item = doc
        else:
            self.proposal = doc
            self.item = {}
        for key in doc:
            if key not in known:
                self.err(file, path or "(root)", key, f"key {key!r} is not in a field table")
        for key, row in known.items():
            if key not in doc and self.required(file, path, row["required"], doc):
                self.err(file, path or "(root)", key, f"REQUIRED field {key!r} is missing")
            if key in doc:
                sub = f"{path}.{key}" if path else key
                if key == "pricing" and isinstance(doc[key], list):
                    self.check_pricing(file, sub, doc[key], fields)
                elif key == "line_items":
                    continue
                else:
                    self.check_value(file, sub, doc[key], row)

    def check_pricing(self, file, path, entries, fields):
        rows = {bare(k[len("pricing[]."):]): r for k, r in fields.items() if k.startswith("pricing[].")}
        for i, entry in enumerate(entries):
            sub = f"{path}[{i}]"
            for key in entry:
                if key not in rows:
                    self.err(file, sub, key, f"key {key!r} is not in the pricing[] rows")
            for key, row in rows.items():
                if key not in entry and self.required(file, sub, row["required"], entry):
                    self.err(file, sub, key, f"REQUIRED key {key!r} is missing")
                if key in entry:
                    self.check_value(file, f"{sub}.{key}", entry[key], row)


# Summary -------------------------------------------------------------------


def project(doc, paths):
    """Return the strict path subset of doc for the listed paths."""
    tree = {}
    for path in paths:
        node = tree
        for part in path.split("."):
            node = node.setdefault(part, {})

    def walk(value, spec):
        if not spec:
            return value
        if isinstance(value, list):
            return [walk(v, spec) for v in value]
        if not isinstance(value, dict):
            return value
        res = {}
        for key, sub in spec.items():
            if bare(key) in value:
                res[bare(key)] = walk(value[bare(key)], sub)
        return res

    return walk(doc, tree)


def full_examples():
    items = {}
    for path in sorted(EXAMPLES.glob("line-item-*.yaml")):
        doc = load_yaml(path)
        items[doc["line_item_id"]] = doc
    return items


def line_item_summary(item, spec):
    out = project(item, spec.summary_paths)
    out["has_requires"] = "requires" in item
    return out


def proposal_summary(proposal, spec):
    return project(proposal, spec.proposal_paths)


def build_manifest(spec):
    """Section 2.3: the proposal's public line items, as summaries."""
    proposal = load_yaml(EXAMPLES / "proposal.yaml")
    entry = proposal_summary(proposal, spec)
    entry["full_url"] = f"https://examplepub.example/openproposal/{proposal['proposal_id']}"
    entry["line_items"] = [
        line_item_summary(item, spec) for item in full_examples().values()
        if item.get("visibility") == "public"
    ]
    return {
        "seller_id": proposal["seller_id"],
        "generated_at": "2026-10-03T15:00:00Z",
        "spec_version": "3.0",
        "proposals": [entry],
    }


def check_manifest(checker, spec):
    path = EXAMPLES / "manifest.json"
    manifest = load_json(path)
    checker.check_object("manifest.json", "(root)", manifest, "ProposalManifest")
    expected = build_manifest(spec)
    expected["generated_at"] = manifest.get("generated_at")
    if manifest != expected:
        checker.err("manifest.json", "(root)", "subset",
                    "the manifest is not the path subset of the full examples; "
                    "run --regen-manifest")


# Main ----------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--regen-manifest", action="store_true")
    args = ap.parse_args()
    spec = Spec()
    if args.regen_manifest:
        manifest = build_manifest(spec)
        (EXAMPLES / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        print("examples/manifest.json regenerated")
        return 0

    checker = Checker(spec)
    for path in sorted(EXAMPLES.glob("*.yaml")):
        try:
            doc = load_yaml(path)
        except yaml.YAMLError as e:
            checker.errors.append(f"{path.name}: does not parse strictly: {e}")
            continue
        checker.proposal = None
        if "line_item_id" in doc:
            checker.check_fields(path.name, "", doc, spec.line_item)
        else:
            checker.check_fields(path.name, "", doc, spec.proposal)
            for i, item in enumerate(doc.get("line_items", [])):
                checker.check_fields(path.name, f"line_items[{i}]", item, spec.line_item)
    try:
        check_manifest(checker, spec)
    except (ValueError, KeyError) as e:
        checker.errors.append(f"manifest.json: {e}")

    stale = KNOWN - checker.used_known
    for item in sorted(stale):
        checker.errors.append(f"KNOWN no longer needed, remove it: {item}")

    if checker.errors:
        print("Examples disagree with the specification:\n")
        for e in checker.errors:
            print(f"  - {e}")
        return 1
    print("Examples match the tables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
