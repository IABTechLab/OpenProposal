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
  - Option names are unique, and included[], selected[], and deltas name options.
  - selected[] or included[] fits max_select, and an empty set has a stated meaning
    (section 3.1).
  - A settable field holds its form, and each buyer value is within its bounds
    (section 3.2). A line item declares geo or markets, not both (section 5.5).
  - agreed_rate recomputes under section 5.6, on the committed entry only.
  - Each mechanism option fits its row in section 5.9. deal_origin is on a deal line
    item only, a deal reference names deal_origin (section 5.10), and availability is
    forecast under non_guaranteed (section 5.6).
  - The manifest is a strict path subset of the full objects (section 2.1), and lists
    each public, published line item (section 2.3).
  - seller and buyer on a proposal hold legal_name (section 4.1).
  - Each section 4.1.1 removal path resolves to a table row.
  - record_digest in examples/proposal-agreed.yaml and examples/proposal-issued.yaml
    recomputes under section 4.1.1, over the line items each entry names, and a
    buyer_supplied that holds no key after the removals moves no digest.
  - In those examples a withdrawal or decline matches a commitment entry before it,
    an acceptance matches a live commitment entry, and a line item is agreed only
    with a matching pair (section 4.1.2).
  - A change_requests[] baseline names an agreed line item at the version of its
    acceptance entry (section 4.4).

KNOWN holds findings that a later change removes. It only shrinks. Run with
--regen-manifest to rewrite examples/manifest.json from the full examples.

Run: python3 scripts/check_examples.py
"""
import argparse
import hashlib
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "openproposal-3.0.md"
EXAMPLES = ROOT / "examples"

# Object types whose extra keys are allowed.
OPEN_TYPES = {"DocumentRef", "ErrorObject"}
# A named type that holds the keys of another.
COMPOSES = {"Commitment": ["CommitmentAmount"], "ManifestEntry": ["ProposalSummary"]}

# (file, path, finding): removed by the change named in the comment.
KNOWN = {
    # Line items: proposal.yaml shows them in their own files (section 6.1), until the
    # change that lists the published line items inline in proposal.yaml.
    ("proposal.yaml", "(root)", "line_items"),
}


# Selectable fields whose row gives an empty set a meaning (section 3.1).
EMPTY_ALLOWED = set()
# The cost methods delta_cpm applies to (section 3.1).
IMPRESSION_METHODS = set()
# The mechanism table of section 5.9.
MECHANISMS = {}


def _options(item):
    options = (item.get("transaction_mechanism") or {}).get("available", [])
    return [o for o in options if isinstance(o, dict)]


def _mechanisms(item):
    return {o.get("id") for o in _options(item)}


def _is_deal(mechanisms):
    return any(MECHANISMS.get(m, {}).get("deal") for m in mechanisms)


def _committed_entry(item):
    """The pricing[] entry the line item's commitment is priced against, if any."""
    entries = item.get("pricing") or []
    if not item.get("commitment"):
        return None
    return entries[0] if len(entries) == 1 else None


def _has_order_reference(entry, proposal):
    """Whether the line item a change_requests[] entry names has an order id."""
    named = (entry.get("baseline") or {}).get("line_item_id")
    for item in (proposal or {}).get("line_items", []):
        if item.get("line_item_id") == named:
            refs = item.get("external_references", [])
            return any(r.get("reference_type") == "order" for r in refs)
    return False


# Each `REQUIRED when <condition>` wording, as (object, line item, proposal) -> bool.
CONDITIONS = {
    "`type` is `custom`": lambda o, i, p: o.get("type") == "custom",
    "`type` is `custom` or `assent[]` is present":
        lambda o, i, p: o.get("type") == "custom" or "assent" in o,
    "the current `version` is frozen (§ 4.1.3)": lambda o, i, p: o.get("status") != "draft",
    "`requested_value` is present": lambda o, i, p: "requested_value" in o,
    "the entry's `action` is `requested`":
        lambda o, i, p: any(e.get("action") == "requested" and any(x is o for x in e.get("paths", []))
                            for e in (p or {}).get("negotiation_history", [])),
    "`invoice_period` is `cycle`": lambda o, i, p: o.get("invoice_period") == "cycle",
    "`role` is `commitment`": lambda o, i, p: o.get("role") == "commitment",
    "the line item has an `order` reference (§ 5.10)":
        lambda o, i, p: _has_order_reference(o, p),
    # No example holds a CommitResult. A ground of availability is the one sign of it.
    "`entries[]` holds a `decline` for lack of availability":
        lambda o, i, p: any(e.get("role") == "decline" and e.get("ground") == "availability"
                            for e in o.get("entries", [])),
    "`basis` is `spend`": lambda o, i, p: o.get("basis") == "spend",
    "`at` is absent": lambda o, i, p: "at" not in o,
    "`before_start` is absent": lambda o, i, p: "before_start" not in o,
    "`url` is absent": lambda o, i, p: "url" not in o,
    "`markup` is absent": lambda o, i, p: "markup" not in o,
    "this is the committed entry": lambda o, i, p: _committed_entry(i) is o,
    "`daypart` or `frequency_cap` is present":
        lambda o, i, p: "daypart" in o or "frequency_cap" in o,
    "an option's `delivery_type` is `share_of_voice`":
        lambda o, i, p: any(x.get("delivery_type") == "share_of_voice" for x in _options(i)),
    "`sov_basis` is `impressions`": lambda o, i, p: i.get("sov_basis") == "impressions",
    "the line item offers a deal mechanism": lambda o, i, p: _is_deal(_mechanisms(i)),
    "the entry prices a deal mechanism": lambda o, i, p: _is_deal(_mechanisms(i)),
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
# A GeoCode (section 5.5): ISO 3166-1 alpha-2, ISO 3166-2, or an extension term.
GEO_CODE = re.compile(rf"(?:[A-Z]{{2}}(?:-[A-Z0-9]{{1,3}})?|{TERM_DOMAIN}{TERM_PART})\Z")
CLOCK_TIME = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z|24:00\Z")
SIDE = ("buyer", "seller")
PROPOSAL_STATUS = ("draft", "published", "under_review", "agreed", "withdrawn", "expired")
CALENDAR_UNIT = ("hour", "day", "week", "month")
SCALARS = {
    "Instant": (lambda v: isinstance(v, str) and INSTANT.match(v)),
    "Duration": (lambda v: isinstance(v, str) and DURATION.match(v)),
    "Digest": (lambda v: isinstance(v, str) and DIGEST.match(v)),
    "Domain": (lambda v: isinstance(v, str) and DOMAIN.match(v)),
    "RegistrableDomain": (lambda v: isinstance(v, str) and DOMAIN.match(v)),
    "Measurer": (lambda v: v in SIDE or (isinstance(v, str) and DOMAIN.match(v))),
    "VocabularyTerm": (lambda v: isinstance(v, str) and TERM.match(v)),
    "GeoCode": (lambda v: isinstance(v, str) and GEO_CODE.match(v)),
    "ClockTime": (lambda v: isinstance(v, str) and CLOCK_TIME.match(v)),
    "DayOfWeek": (lambda v: v in ("monday", "tuesday", "wednesday", "thursday", "friday",
                                  "saturday", "sunday")),
    "MediaChannel": (lambda v: isinstance(v, str) and TERM.match(v)),
    "String": (lambda v: isinstance(v, str)),
    "Url": (lambda v: isinstance(v, str) and v.startswith(("http://", "https://"))),
    "HttpsUrl": (lambda v: isinstance(v, str) and v.startswith("https://")),
    "Integer": (lambda v: isinstance(v, int) and not isinstance(v, bool)),
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
    "ProposalStatus": (lambda v: v in PROPOSAL_STATUS),
    "LineItemStatus": (lambda v: v in PROPOSAL_STATUS or v == "sold_out"),
    "ApprovalStatus": (lambda v: v in ("PENDING", "APPROVED", "REJECTED")),
    "TransactionMechanism": (lambda v: v in MECHANISMS),
    "DeliveryType": (lambda v: v in ("guaranteed", "share_of_voice", "non_guaranteed")),
    "EntryRef": (lambda v: isinstance(v, str) and re.fullmatch(r"[^/@]+/[^/@]+/[^/@]+@[^/@]+", v)),
    "FieldPointer": (lambda v: isinstance(v, str) and (v == "" or v.startswith("/"))),
    "Ext": (lambda v: isinstance(v, dict) and all(
        isinstance(k, str) and DOMAIN.match(k) and isinstance(item, dict)
        for k, item in v.items()
    )),
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
        self.removal = []
        self._read_fields()
        self._read_key_tables()
        self._read_lists()
        self._read_option_rules()
        self._read_mechanisms()

    def _read_mechanisms(self):
        """The section 5.9 table: deal or not, and the allowed delivery types."""
        start = self.lines.index(
            "| `transaction_mechanism` | Deal mechanism | `delivery_type` |")
        for line in self.lines[start + 2:]:
            c = cells(line)
            if not c:
                break
            MECHANISMS[clean_key(c[0])] = {
                "deal": c[1] == "Yes",
                "delivery": None if c[2] == "Any" else re.findall(r"`([^`]+)`", c[2]),
            }

    def _read_option_rules(self):
        """Sections 3.1 and 5.6: what a row says of its options and its deltas."""
        for key, row in self.line_item.items():
            if not row["type"].startswith("Selectable["):
                continue
            if re.search(r"[Nn]othing in effect", row["description"]):
                EMPTY_ALLOWED.add(key)
        IMPRESSION_METHODS.update(re.findall(r"`([A-Z]+)`", self.tables["Delta"]["delta_cpm"]["meaning"]))

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
                    "values": enum_values(c[1], c[4]), "description": c[4],
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
                            "meaning": r[3],
                        }
                        j += 1
                current = None

    def _read_lists(self):
        text = "\n".join(self.lines)
        m = re.search(r"`LineItemSummary` lists these paths[^\n]*\n\n```text\n(.*?)```", text, re.S)
        self.summary_paths = m.group(1).split()
        m = re.search(r"`ProposalSummary` lists these paths[^\n]*\n\n```text\n(.*?)```", text, re.S)
        self.proposal_paths = m.group(1).split()
        m = re.search(r"#### 4\.1\.1.*?```\n(.*?)```", text, re.S)
        self.removal = [l for l in m.group(1).splitlines() if l.startswith("$")]


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
        if base == "SettableRange":
            self.check_settable_range(file, path, value, args[0])
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
                if "id" not in option:
                    self.err(file, f"{path}.available[{i}]", "id", "an object option has an id")
                names.append(option.get("id"))
                if option_type in self.spec.tables:
                    self.check_object(file, f"{path}.available[{i}]", option, option_type)
            else:
                self.check_type(file, f"{path}.available[{i}]", option, option_type)
                names.append(str(option))
        if len(names) != len(set(names)):
            self.err(file, path, "names", "option names are not unique in the field")
        if "included" not in value:
            self.err(file, path, "included", "REQUIRED key 'included' is missing")
        for name in value.get("included", []):
            if name not in names:
                self.err(file, f"{path}.included", name, f"{name!r} names no option")
        for name in value.get("selected", []):
            if name not in names:
                self.err(file, f"{path}.selected", name, f"{name!r} names no option")
        for name, delta in (value.get("deltas") or {}).items():
            if name not in names:
                self.err(file, f"{path}.deltas", name, f"{name!r} names no option")
            self.check_object(file, f"{path}.deltas.{name}", delta, "Delta")
            if not delta:
                self.err(file, f"{path}.deltas.{name}", "delta", "a Delta holds at least one key")
        if "max_select" in value:
            self.check_type(file, f"{path}.max_select", value["max_select"], "Integer")
        field = path.rsplit(".", 1)[-1]
        in_effect = value.get("selected", value.get("included", []))
        if "max_select" in value and len(in_effect) > value["max_select"]:
            self.err(file, path, "max_select", "more options in effect than max_select")
        if not in_effect and field not in EMPTY_ALLOWED:
            self.err(file, path, "empty", f"{field} gives an empty set no meaning")

    def covers(self, field, outer, inner):
        """Whether an entry of a settable field covers another (sections 3.2, 5.5)."""
        if outer == inner:
            return True
        if field == "geo":
            return str(inner).startswith(f"{outer}-")
        if field == "device":
            return outer == 1 and inner in (4, 5)
        if field == "daypart":
            return (set(inner.get("days", [])) <= set(outer.get("days", []))
                    and outer.get("start", "") <= inner.get("start", "")
                    and inner.get("before", "") <= outer.get("before", ""))
        return False

    def check_narrowing(self, file, path, value, item_type, allowed):
        if not isinstance(value, dict) or not value.keys() <= {"include", "exclude"}:
            self.err(file, path, "narrowing", "a Narrowing holds include[] and exclude[]")
            return
        if "include" not in value:
            self.err(file, path, "include", "REQUIRED key 'include' is missing")
        field = path.split(".")[-2]
        include, exclude = value.get("include", []), value.get("exclude", [])
        for key, within, entries in (("allowed", allowed, include), ("include", include, exclude)):
            for entry in entries:
                self.check_type(file, path, entry, item_type)
                if not any(self.covers(field, outer, entry) for outer in within):
                    self.err(file, path, "covered", f"{entry!r} is not covered by {key}")

    def check_settable(self, file, path, value, item_type):
        """Section 3.2: the envelope form, allowed[] with a default and the buyer's value."""
        if not isinstance(value, dict) or not value.keys() <= {"allowed", "default", "value"}:
            self.err(file, path, "settable", "a Settable holds allowed[], default, and value")
            return
        for key in ("allowed", "default"):
            if key not in value:
                self.err(file, path, key, f"REQUIRED key {key!r} is missing")
        allowed = value.get("allowed", [])
        for i, entry in enumerate(allowed):
            self.check_type(file, f"{path}.allowed[{i}]", entry, item_type)
        for key in ("default", "value"):
            if key in value:
                self.check_narrowing(file, f"{path}.{key}", value[key], item_type, allowed)

    def check_settable_range(self, file, path, value, item_type):
        """Section 3.2: the range form, the keys of Range with a default and the buyer's value."""
        if not isinstance(value, dict) or not value.keys() <= {"min", "max", "default", "value"}:
            self.err(file, path, "settable", "a SettableRange holds min, max, default, and value")
            return
        if "min" not in value and "max" not in value:
            self.err(file, path, "bound", "a SettableRange holds at least one bound")
        if "default" not in value:
            self.err(file, path, "default", "REQUIRED key 'default' is missing")
        for key in ("min", "max", "default", "value"):
            if key in value:
                self.check_type(file, f"{path}.{key}", value[key], item_type)
        if "min" in value and "max" in value and value["min"] > value["max"]:
            self.err(file, path, "bound", "min is greater than max")
        for key in ("default", "value"):
            if key in value and ((("min" in value) and value[key] < value["min"])
                                 or (("max" in value) and value[key] > value["max"])):
                self.err(file, f"{path}.{key}", "bounds", f"{key} is outside the bounds")

    def check_agreed_rate(self, file, path, item):
        """Recompute agreed_rate on the committed entry (section 5.6)."""
        committed = _committed_entry(item)
        for entry in item.get("pricing") or []:
            if entry is not committed and "agreed_rate" in entry:
                self.err(file, path, "agreed_rate", "agreed_rate on an uncommitted entry")
        if committed is None or "agreed_rate" not in committed:
            return
        decimal = lambda n: Decimal(str(n))
        cpm, factor = Decimal(0), Decimal(1)
        for value in item.values():
            if not isinstance(value, dict) or "available" not in value:
                continue
            included = value.get("included", [])
            names = [n for n in value.get("selected", included) if n not in included]
            for name in names:
                delta = (value.get("deltas") or {}).get(name, {})
                if committed.get("cost_method") in IMPRESSION_METHODS:
                    cpm += decimal(delta.get("delta_cpm", 0))
                elif set(delta) == {"delta_cpm"}:
                    self.err(file, path, name, "an option priced only by delta_cpm on this entry")
                factor *= 1 + decimal(delta.get("delta_fraction", 0))
        rate = (decimal(committed["list_rate"]) + cpm) * factor
        rate = rate.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        if rate != decimal(committed["agreed_rate"]):
            self.err(file, path, "agreed_rate", f"agreed_rate recomputes to {rate}")

    def check_mechanisms(self, file, path, item):
        """Sections 5.6, 5.9, and 5.10: the mechanism options and what they require."""
        for option in _options(item):
            row = MECHANISMS.get(option.get("id"))
            if row and row["delivery"] is not None and option.get("delivery_type") not in row["delivery"]:
                self.err(file, path, option["id"],
                         f"{option['id']} does not allow delivery_type {option.get('delivery_type')!r}")
        if "deal_origin" in item and not _is_deal(_mechanisms(item)):
            self.err(file, path, "deal_origin", "deal_origin on a line item with no deal mechanism")
        for ref in item.get("external_references") or []:
            if ref.get("reference_type") == "deal" and ref.get("system") != item.get("deal_origin"):
                self.err(file, path, "deal", "a deal reference has system other than deal_origin")
        mechanism = item.get("transaction_mechanism") or {}
        in_effect = mechanism.get("selected", mechanism.get("included", []))
        delivery = {o.get("delivery_type") for o in _options(item) if o.get("id") in in_effect}
        figures = item.get("availability")
        if figures and delivery == {"non_guaranteed"} and figures.get("type") != "forecast":
            self.err(file, path, "availability", "availability.type is forecast when delivery_type is non_guaranteed")

    def check_fields(self, file, path, doc, fields):
        known = {bare(k): r for k, r in fields.items() if "[]." not in k}
        if "line_item_id" in doc:
            self.item = doc
        else:
            self.proposal = doc
            self.item = {}
            for key in ("seller", "buyer"):
                if key in doc and "legal_name" not in doc[key]:
                    self.err(file, key, "legal_name", "legal_name is REQUIRED here")
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
        if "line_item_id" in doc:
            self.check_agreed_rate(file, path or "(root)", doc)
            self.check_mechanisms(file, path or "(root)", doc)
            if "geo" in doc and "markets" in doc:
                self.err(file, path or "(root)", "markets", "a line item declares geo or markets")

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

    def check_removal_paths(self):
        for path in self.spec.removal:
            head_path = path.split(",")[0]
            parts = [p for p in head_path.lstrip("$.").split(".") if p != "*"]
            parts = [re.sub(r"\[\*\]$", "", p) for p in parts]
            fields = self.spec.proposal
            if parts[0] == "line_items":
                fields, parts = self.spec.line_item, parts[1:]
            ok = parts[0] in {bare(k) for k in fields}
            if ok and len(parts) > 1 and parts[0] == "pricing":
                ok = f"pricing[].{parts[1]}" in fields
            if not ok:
                self.err("spec", "removal path", path, f"{path} resolves to no row")


# Digest --------------------------------------------------------------------


def jcs_number(n):
    if isinstance(n, bool):
        return "true" if n else "false"
    if isinstance(n, int):
        return str(n)
    if n == int(n) and abs(n) < 1e21:
        return str(int(n))
    return repr(n)


def jcs(value):
    """RFC 8785 serialization, for the values examples use."""
    if value is None:
        return "null"
    if isinstance(value, (bool, int, float)):
        return jcs_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(jcs(v) for v in value) + "]"
    keys = sorted(value, key=lambda k: k.encode("utf-16-be"))
    return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + jcs(value[k]) for k in keys) + "}"


def remove_path(node, parts, keep=()):
    if not parts:
        return
    head, rest = parts[0], parts[1:]
    if head.endswith("[*]"):
        for item in (node.get(head[:-3]) or []):
            remove_path(item, rest, keep)
        return
    if head == "*":
        if isinstance(node, dict):
            for key in list(node):
                if key not in keep:
                    del node[key]
        return
    if not rest:
        node.pop(head, None)
    elif isinstance(node.get(head), dict):
        remove_path(node[head], rest, keep)


def record_digest(doc, removal, line_item_ids):
    """Section 4.1.1: the digest of the binding record for the named line items."""
    copy = json.loads(json.dumps(doc))
    copy["line_items"] = [i for i in copy.get("line_items", []) if i["line_item_id"] in line_item_ids]
    for path in removal:
        head, _, tail = path.partition(", except ")
        keep = re.split(r",\s*|\s+and\s+", tail) if tail else ()
        remove_path(copy, head[2:].split("."), keep)
    # Section 4.1.1: the one object the removals don't leave in place when it is empty.
    for item in copy.get("line_items", []):
        if item.get("buyer_supplied") == {}:
            del item["buyer_supplied"]
    return "sha256:" + hashlib.sha256(jcs(copy).encode("utf-8")).hexdigest()


def check_digest_ignores_empty_buyer_supplied(checker, doc, removal):
    """Section 4.1.1: a removed buyer_supplied value moves no digest, and a kept one does."""
    item = doc["line_items"][0]
    forms = [
        None,
        {},
        {"match_rate_expected": 0.65},
        {"segments": [], "suppression_list": {}, "match_rate_expected": 0.65},
    ]
    digests = set()
    for form in forms:
        copy = json.loads(json.dumps(doc))
        copy["line_items"][0].pop("buyer_supplied", None)
        if form is not None:
            copy["line_items"][0]["buyer_supplied"] = form
        digests.add(record_digest(copy, removal, [item["line_item_id"]]))
    if len(digests) != 1:
        checker.errors.append("record_digest: an absent and an empty buyer_supplied give different digests")
    copy = json.loads(json.dumps(doc))
    copy["line_items"][0]["buyer_supplied"] = {"suppression_allowed": True}
    if record_digest(copy, removal, [item["line_item_id"]]) in digests:
        checker.errors.append("record_digest: a buyer_supplied that keeps a term moved no digest")


def check_assent(checker, file, doc):
    """Section 4.1.2: only a matching pair makes agreed, and an acceptance matches a live entry."""
    def key(entry):
        return entry["version"], entry["record_digest"], frozenset(entry["line_item_ids"])

    items = {i["line_item_id"]: i for i in doc.get("line_items", [])}
    commitments, live, matched, agreed = [], set(), set(), set()
    for entry in doc.get("assent", []):
        role = entry["role"]
        if "ground" in entry and role != "decline":
            checker.errors.append(f"{file}: {role} entry carries ground")
        for named in entry["line_item_ids"]:
            if named not in items:
                checker.errors.append(f"{file}: {role} entry names {named}, which is not a line item")
            elif role == "commitment" and "commitment" not in items[named]:
                checker.errors.append(f"{file}: commitment entry names {named}, which has no commitment")
        if role == "commitment":
            commitments.append(key(entry))
            live.add(key(entry))
        elif role == "acceptance":
            # Section 4.1.2: an acceptance matches only a live commitment entry.
            if key(entry) not in live:
                checker.errors.append(f"{file}: acceptance entry matches no live commitment entry")
            else:
                matched.add(key(entry))
                agreed.update(entry["line_item_ids"])
        elif key(entry) not in commitments:
            checker.errors.append(f"{file}: {role} entry matches no commitment entry before it")
        elif key(entry) not in matched:
            live.discard(key(entry))
    for name, item in items.items():
        if (item.get("status") == "agreed") != (name in agreed):
            checker.errors.append(f"{file}: {name} has status {item.get('status')!r}, "
                                  f"and assent[] {'has' if name in agreed else 'has no'} matching pair")


def check_change_requests(checker, file, doc):
    """Section 4.4: each entry names an agreed line item at its agreed version."""
    items = {i["line_item_id"]: i for i in doc.get("line_items", [])}
    for n, entry in enumerate(doc.get("change_requests", [])):
        where = f"{file}: change_requests[{n}].baseline"
        baseline = entry.get("baseline", {})
        named = baseline.get("line_item_id")
        if baseline.get("proposal_id") != doc.get("proposal_id"):
            checker.errors.append(f"{where}: names another proposal")
        if named is None:
            checker.errors.append(f"{where}: line_item_id is REQUIRED here")
        elif items.get(named, {}).get("status") != "agreed":
            checker.errors.append(f"{where}: {named} is not an agreed line item")
        versions = {e["version"] for e in doc.get("assent", [])
                    if e["role"] == "acceptance" and named in e["line_item_ids"]}
        if baseline.get("version") not in versions:
            checker.errors.append(f"{where}: no acceptance entry names {named} at that version")


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
    """Section 2.3: the proposal's public, published line items, as summaries."""
    proposal = load_yaml(EXAMPLES / "proposal.yaml")
    entry = proposal_summary(proposal, spec)
    entry["full_url"] = f"https://{proposal['seller']['domain']}/openproposal/{proposal['proposal_id']}"
    entry["line_items"] = [
        line_item_summary(item, spec) for item in full_examples().values()
        if item.get("visibility") == "public" and item.get("status") == "published"
    ]
    return {
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
    checker.check_removal_paths()

    check_digest_ignores_empty_buyer_supplied(checker, load_yaml(EXAMPLES / "proposal-agreed.yaml"), spec.removal)

    digests = {}
    for name in ("proposal-agreed.yaml", "proposal-issued.yaml"):
        doc = load_yaml(EXAMPLES / name)
        check_assent(checker, name, doc)
        check_change_requests(checker, name, doc)
        for entry in doc.get("assent", []):
            digest = record_digest(doc, spec.removal, entry["line_item_ids"])
            digests[name] = digest
            if entry["record_digest"] != digest:
                checker.errors.append(f"{name}: record_digest recomputes to {digest}")

    stale = KNOWN - checker.used_known
    for item in sorted(stale):
        checker.errors.append(f"KNOWN no longer needed, remove it: {item}")

    if checker.errors:
        print("Examples disagree with the specification:\n")
        for e in checker.errors:
            print(f"  - {e}")
        return 1
    print("Examples match the tables.")
    for name, digest in digests.items():
        print(f"  record_digest of {name}: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
