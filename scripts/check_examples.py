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
  - excluded[] names excludable options outside the set in effect, and combine holds
    the operators section 5.3 lists, with one in effect and no deltas.
  - An exclusions entry is an array of its type's entries or a DocumentRef, and its
    type is one accepted_exclusions accepts. A Map key has the Map's key type.
  - selected[] or included[] fits max_select, and an empty set has a stated meaning
    (section 3.1).
  - A settable field holds its form, and each buyer value is within its bounds
    (section 3.2). A line item declares geo or markets, not both (section 5.5).
  - agreed_rate recomputes under section 5.6, on the committed entry only.
  - A commitment's arithmetic holds under section 5.6.5, on FLAT and TIME as well,
    and it fits commitment_bounds.spend and the committed entry's unit_bounds.
  - pricing_id is unique, two entries don't share a cost method, cost parameters, a
    currency, and a mechanism, and the committed entry covers the mechanism in effect
    (section 5.6).
  - A Range's min is not greater than its max, and an Interval's end is later than its
    start (section 2.2).
  - Each mechanism option fits its row in section 5.9. deal_origin is on a deal line
    item only, a deal reference names deal_origin (section 5.10), and availability is
    forecast under non_guaranteed (section 5.6).
  - A tentative event is outside included[] and priced only by delta_flat (section
    5.2.9), and an embedded line item follows section 5.9.
  - The manifest is a strict path subset of the full objects (section 2.1), and lists
    each public, published line item (section 2.3).
  - seller and buyer on a proposal hold legal_name (section 4.1).
  - Each section 4.1.1 removal path resolves to a table row, below a typed field too.
  - An array whose row says MUST be non-empty holds an entry.
  - record_digest in examples/proposal-agreed.yaml and examples/proposal-issued.yaml
    recomputes under section 4.1.1, over the line items each entry names, and a
    buyer_supplied that holds no key after the removals moves no digest.
  - In those examples a withdrawal or decline matches a commitment entry before it,
    an acceptance matches a live commitment entry, and a line item is agreed only
    with a matching pair (section 4.1.2).
  - A change_requests[] baseline names an agreed line item at the version of its
    acceptance entry (section 4.4). A cancellation names an option in effect, and its
    cancelled_share is within the max_share of the range holding its effective date, or
    the top-level one, and an option's dated_shares[] windows don't overlap (section 5.6.6).
  - A core metric's level has the kind its row states, and counted_by equals the
    party sections 5.6.4 and 5.7.1 name, under the Measurer comparison (section 2.2).

KNOWN holds findings that a later change removes. It only shrinks. Run with
--regen-manifest to rewrite examples/manifest.json from the full examples.

Run: python3 scripts/check_examples.py
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "openproposal-3.0.md"
EXAMPLES = ROOT / "examples"

# Object types whose extra keys are allowed.
OPEN_TYPES = {"DocumentRef", "ErrorObject", "CostParameters"}
# A named type that holds the keys of another.
COMPOSES = {"App": ["AppId"], "Commitment": ["CommitmentAmount"],
            "MinCommitment": ["CommitmentAmount"], "ManifestEntry": ["ProposalSummary"]}
# Named types that hold the keys of BuyerWrites (section 3.4), a path list.
WRITES_TYPES = {"LineItemWrites"}
# Named types that hold the keys of a Selectable[T], with their T, and add their own rows.
SELECTABLE_HOLDERS = {"ShortfallRemedy": "VocabularyTerm", "AudienceSelectable": "AudienceOption"}

# (file, path, finding): removed by the change named in the comment.
KNOWN = {
    # Line items: proposal.yaml shows them in their own files (section 6.1), until the
    # change that lists the published line items inline in proposal.yaml.
    ("proposal.yaml", "(root)", "line_items"),
}


# Selectable fields whose row gives an empty set a meaning (section 3.1).
EMPTY_ALLOWED = set()
# The cost methods delta_cpm applies to (section 3.1), and the units they count.
IMPRESSION_METHODS = set()
IMPRESSION_UNITS = set()
# The mechanism table of section 5.9.
MECHANISMS = {}
# The cost table of section 5.6.5, as cost_method -> rate per, and -> unit terms.
RATE_PER = {}
COST_UNIT = {}
# The core metric table of section 5.7.1, as term -> Rate or Count.
METRIC_KIND = {}
# Fields absent when embedded (section 5.9).
EMBEDDED_ABSENT = []
# The exclusion type table of section 5.5, as term -> entry type.
EXCLUSION_ENTRY = {}
RATE_UNIT_SECONDS = {"hour": 3600, "day": 86400, "week": 604800}


def _options(item):
    options = (item.get("transaction_mechanism") or {}).get("available", [])
    return [o for o in options if isinstance(o, dict)]


def _mechanisms(item):
    return {o.get("id") for o in _options(item)}


def _is_deal(mechanisms):
    return any(MECHANISMS.get(m, {}).get("deal") for m in mechanisms)


def _counts_impressions(item):
    # Section 5.6.4: any count on the line item is in impressions.
    if any(p.get("cost_method") in IMPRESSION_METHODS for p in item.get("pricing", [])):
        return True
    if any(m.get("metric") == "impressions" for m in item.get("committed_metrics", [])):
        return True
    if (item.get("availability") or {}).get("unit") in IMPRESSION_UNITS:
        return True
    return False


def _audiences_can_combine(audiences):
    """Whether more than one seller audience can be in effect (section 5.3)."""
    options = audiences.get("available", [])
    return len(options) > 1 and audiences.get("max_select", len(options)) > 1


def _has_sync_groups(item):
    options = (item.get("properties") or {}).get("available", [])
    return any("sync_groups" in o for o in options)


def _committed_entry(item):
    """The pricing[] entry the line item's commitment is under, if any."""
    commitment, entries = item.get("commitment"), item.get("pricing") or []
    if not commitment:
        return None
    named = commitment.get("pricing_id")
    if named is None:
        return entries[0] if len(entries) == 1 else None
    return next((e for e in entries if e.get("pricing_id") == named), None)


def _cost_method(parameters, item):
    """The cost_method of the pricing[] entry that holds these cost_parameters."""
    for entry in item.get("pricing", []):
        if entry.get("cost_parameters") is parameters:
            return entry.get("cost_method")
    return None


def applicable_max_share(terms, notice):
    """Section 5.6.6: the range holding the effective date, or the top-level max_share."""
    parse = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    effective = parse(notice["requested_effective_at"])
    length = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", terms.get("notice_duration", "P0D"))
    if length:  # a length in months or years has no fixed span; the requested date stands
        days, hours, minutes, seconds = (int(part or 0) for part in length.groups())
        earliest = parse(notice["notice_received_at"]) + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        effective = max(effective, earliest)
    for span in terms.get("dated_shares", []):
        if parse(span["window"]["start"]) <= effective <= parse(span["window"]["end"]):
            return span["max_share"]
    return terms.get("max_share", 1)


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
    "`cost_method` is an extension term": lambda o, i, p: ":" in str(o.get("cost_method")),
    "the term requires keys":
        lambda o, i, p: o.get("cost_method") in ("CPMV", "CPV", "CPP", "CPA", "TIME"),
    "`pricing[]` has more than one entry": lambda o, i, p: len(i.get("pricing", [])) > 1,
    "`cost_method` is `CPMV`": lambda o, i, p: _cost_method(o, i) == "CPMV",
    "`cost_method` is `CPV` and `view_fraction` is absent":
        lambda o, i, p: _cost_method(o, i) == "CPV" and "view_fraction" not in o,
    "`cost_method` is `CPV` and `view_s` is absent":
        lambda o, i, p: _cost_method(o, i) == "CPV" and "view_s" not in o,
    "`cost_method` is `CPP`": lambda o, i, p: _cost_method(o, i) == "CPP",
    "`cost_method` is `CPA`": lambda o, i, p: _cost_method(o, i) == "CPA",
    "`cost_method` is `TIME`": lambda o, i, p: _cost_method(o, i) == "TIME",
    "`calculation` is `cancelled` or `commitment`":
        lambda o, i, p: o.get("calculation") in ("cancelled", "commitment"),
    "`calculation` is `fixed`": lambda o, i, p: o.get("calculation") == "fixed",
    "`scope` is `category`": lambda o, i, p: o.get("scope") == "category",
    "`at` is absent": lambda o, i, p: "at" not in o,
    "`before_start` is absent": lambda o, i, p: "before_start" not in o,
    "`url` is absent": lambda o, i, p: "url" not in o,
    "`markup` is absent": lambda o, i, p: "markup" not in o,
    "this is the committed entry": lambda o, i, p: _committed_entry(i) is o,
    "`daypart` or `frequency_cap` is present":
        lambda o, i, p: "daypart" in o or "frequency_cap" in o,
    "`status` is `held`": lambda o, i, p: o.get("status") == "held",
    "an option's `delivery_type` is `share_of_voice`":
        lambda o, i, p: any(x.get("delivery_type") == "share_of_voice" for x in _options(i)),
    "`sov_basis` is `impressions`": lambda o, i, p: i.get("sov_basis") == "impressions",
    "`channel` is `dooh`": lambda o, i, p: i.get("channel") == "dooh",
    "`channel` is `audio`": lambda o, i, p: i.get("channel") == "audio",
    "`channel` is `video`": lambda o, i, p: i.get("channel") == "video",
    "`channel` is `video` or `audio`": lambda o, i, p: i.get("channel") in ("video", "audio"),
    "`placement.feed` is Podcast (3) or Catch-up radio (4)":
        lambda o, i, p: (i.get("placement") or {}).get("feed") in (3, 4),
    "`serving_mode` is `embedded`": lambda o, i, p: i.get("serving_mode") == "embedded",
    "the line item counts impressions": lambda o, i, p: _counts_impressions(i),
    "`source_type` is not Publisher Provided (`2`)": lambda o, i, p: o.get("source_type") != 2,
    "a property has `sync_groups[]`": lambda o, i, p: _has_sync_groups(i),
    "`apps[]` is absent": lambda o, i, p: "apps" not in o,
    "`domains[]` is absent": lambda o, i, p: "domains" not in o,
    "`seller_relationship` is `reseller`, or the line item offers a deal mechanism (§ 5.9)":
        lambda o, i, p: o.get("seller_relationship") == "reseller" or _is_deal(_mechanisms(i)),
    "`child_audience` is `mixed`": lambda o, i, p: o.get("child_audience") == "mixed",
    "more than one seller audience can be in effect": lambda o, i, p: _audiences_can_combine(o),
    "`channel` is `dooh` and `allocation` is `all`":
        lambda o, i, p: i.get("channel") == "dooh" and o.get("allocation", "all") == "all",
    "`serving_mode` is `embedded` or the line item has `committed_metrics[]`, `commitment_bounds.spend`, or a `pricing[].unit_bounds`":
        lambda o, i, p: i.get("serving_mode") == "embedded"
        or "committed_metrics" in i or "spend" in (i.get("commitment_bounds") or {})
        or any("unit_bounds" in e for e in i.get("pricing", [])),
    "the line item offers a deal mechanism": lambda o, i, p: _is_deal(_mechanisms(i)),
    "the entry prices a deal mechanism":
        lambda o, i, p: _is_deal(o.get("transaction_mechanisms") or _mechanisms(i)),
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
    "ExclusionType": (lambda v: isinstance(v, str) and TERM.match(v)),
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
    "HoldStatus": (lambda v: v in ("requested", "held", "declined", "expired", "released",
                                   "converted")),
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
        self.write_paths = []
        self.removal = []
        self._read_fields()
        self._read_key_tables()
        self._read_lists()
        self._read_option_rules()
        self._read_embedded()
        self._read_mechanisms()
        self._read_cost_methods()
        self._read_metrics()
        self._read_exclusion_types()
        self._read_closed_types()

    def _read_exclusion_types(self):
        """The section 5.5 table: the entry type of each core exclusion type."""
        start = self.lines.index("| `exclusions` | Entry | Meaning |")
        for line in self.lines[start + 2:]:
            c = cells(line)
            if not c:
                break
            EXCLUSION_ENTRY[clean_key(c[0])] = clean_key(c[1])

    def _read_closed_types(self):
        """Closed lists the body names as a type, such as section 5.3's CombineOperator."""
        for line in self.lines:
            m = re.match(r"^\*\*`(\w+)`\*\* is ((?:`[^`]+`(?: \\\| )?)+)\.$", line)
            if m:
                values = re.findall(r"`([^`]+)`", m.group(2))
                SCALARS.setdefault(m.group(1), lambda v, values=values: v in values)

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

    def _read_cost_methods(self):
        """The section 5.6.5 table: the rate per of each core cost_method."""
        start = self.lines.index("| `cost_method` | `unit` | One unit | Rate per | `cost_parameters` |")
        for line in self.lines[start + 2:]:
            c = cells(line)
            if not c:
                break
            RATE_PER[clean_key(c[0])] = int(c[3].replace(",", "")) if c[3] else None
            COST_UNIT[clean_key(c[0])] = re.findall(r"`([^`]+)`", c[1].split(", by")[0])
        IMPRESSION_UNITS.update(t for method in IMPRESSION_METHODS for t in COST_UNIT.get(method, []))

    def _read_metrics(self):
        """The section 5.7.1 table: whether each core metric is a rate or a count."""
        start = self.lines.index("| `metric` | Kind | Usual `direction` | Definition |")
        for line in self.lines[start + 2:]:
            c = cells(line)
            if not c:
                break
            METRIC_KIND[clean_key(c[0])] = c[1]

    def _read_embedded(self):
        """Section 5.9: the fields an embedded line item leaves out."""
        m = re.search(r"^- ((?:`\w+`,? (?:and )?)+)MUST be absent", "\n".join(self.lines), re.M)
        EMBEDDED_ABSENT.extend(re.findall(r"`(\w+)`", m.group(1)))

    def _read_option_rules(self):
        """Sections 3.1 and 5.6: what a row says of its options and its deltas."""
        for key, row in self.line_item.items():
            if not row["type"].startswith("Selectable[") and row["type"] not in SELECTABLE_HOLDERS:
                continue
            if re.search(r"[Nn]othing in effect", row["description"]):
                EMPTY_ALLOWED.add(key)
        # Section 5.3 states this one in its numbered conditions, not in the row.
        EMPTY_ALLOWED.add("audiences")
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
        m = re.search(r"`BuyerWrites` lists these paths.*?```text\n(.*?)```", text, re.S)
        self.write_paths = m.group(1).split()
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
        if "MUST be non-empty" in row.get("meaning", row.get("description", "")) and value == []:
            self.err(file, path, "empty", "an array this row says MUST be non-empty is empty")
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
                if args[0] in SCALARS and not SCALARS[args[0]](k):
                    self.err(file, f"{path}.{k}", "key", f"key {k!r} is not a {args[0]}")
                self.check_type(file, f"{path}.{k}", item, args[1])
            return
        if base == "ExclusionList":
            self.check_exclusion_list(file, path, value)
            return
        if base == "Selectable":
            self.check_selectable(file, path, value, args[0])
            return
        if base in SELECTABLE_HOLDERS:
            self.check_selectable(file, path, value, SELECTABLE_HOLDERS[base], self.spec.tables.get(base, {}))
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
            low, high = value.get("min"), value.get("max")
            if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low > high:
                self.err(file, path, "range", "min is greater than max")
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
        if base == "Interval" and isinstance(value, dict):
            starts, ends = value.get("start"), value.get("end")
            if isinstance(starts, str) and isinstance(ends, str) and ends <= starts:
                self.err(file, path, "interval", "an Interval's end is not later than its start")
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
                if key in known:
                    continue
                if name in WRITES_TYPES:
                    if not self.is_write(key):
                        self.err(file, path, key, f"key {key!r} is not a BuyerWrites path")
                    continue
                self.err(file, path, key, f"key {key!r} is not in the {name} table")
        for key, row in known.items():
            if key not in value and self.required(file, path, row["required"], value):
                self.err(file, path, key, f"REQUIRED key {key!r} of {name} is missing")
            if key in value:
                self.check_value(file, f"{path}.{key}", value[key], row)

    def is_write(self, key):
        """Section 3.4: whether a key heads a BuyerWrites path."""
        marker = self.spec.line_item.get(key, {}).get("marker")
        if marker == "selectable" or (marker == "settable" and key != "frequency_cap"):
            return True
        return any(p.split(".")[0].removesuffix("[]") == key for p in self.spec.write_paths
                   if not p.startswith("<"))

    def check_selectable(self, file, path, value, option_type, extra=None):
        if not isinstance(value, dict):
            self.err(file, path, "selectable", "expected a Selectable")
            return
        if "available" not in value:
            self.err(file, path, "available", "a Selectable holds available[]")
            return
        extra = {bare(k): r for k, r in (extra or {}).items()}
        known = {bare(k) for k in self.spec.tables["Selectable"]} | set(extra)
        for key in value:
            if key not in known:
                self.err(file, path, key, f"key {key!r} is not a Selectable key")
        for key, row in extra.items():
            if key not in value and self.required(file, path, row["required"], value):
                self.err(file, path, key, f"REQUIRED key {key!r} is missing")
            if key in value:
                self.check_value(file, f"{path}.{key}", value[key], row)
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
            names += value.get("excluded", [])
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
        programs = item.get("programs") or {}
        for option in programs.get("available", []):
            if (option.get("schedule") or {}).get("eventstatus") == 2:
                name = option.get("id")
                if name in programs.get("included", []):
                    self.err(file, path, name, f"tentative {name} is in included[]")
                if set((programs.get("deltas") or {}).get(name, {})) - {"delta_flat"}:
                    self.err(file, path, name, f"tentative {name} has a delta other than delta_flat")
        if item.get("serving_mode") == "embedded":
            if item.get("episodes", "new") != "new":
                self.err(file, path, "episodes", "episodes on an embedded line item is new")
            for key in EMBEDDED_ABSENT:
                if key in item:
                    self.err(file, path, key, f"{key} on an embedded line item")
            if item.get("time_zone") == "viewer_local":
                self.err(file, path, "time_zone", "time_zone on an embedded line item is viewer_local")
            if _mechanisms(item) != {"direct_io"}:
                self.err(file, path, "transaction_mechanism", "an embedded line item offers only direct_io")
        mechanism = item.get("transaction_mechanism") or {}
        in_effect = mechanism.get("selected", mechanism.get("included", []))
        delivery = {o.get("delivery_type") for o in _options(item) if o.get("id") in in_effect}
        hold = item.get("hold") or {}
        for key, figures in (("availability", item.get("availability")),
                             ("hold.held_availability", hold.get("held_availability"))):
            if figures and delivery == {"non_guaranteed"} and figures.get("certainty") != "forecast":
                self.err(file, path, key, f"{key}.certainty is forecast when delivery_type is non_guaranteed")
        committed = _committed_entry(item)
        if committed and committed.get("transaction_mechanisms"):
            for name in in_effect:
                if name not in committed["transaction_mechanisms"]:
                    self.err(file, path, name, f"the committed entry does not price {name}")

    def check_commitment(self, file, path, item):
        """A commitment's arithmetic and its bounds (sections 5.6.1 and 5.6.5)."""
        for entry in item.get("pricing") or []:
            if entry.get("cost_method") == "FLAT" and "unit_bounds" in entry:
                self.err(file, path, "unit_bounds", "unit_bounds on a FLAT entry")
        commitment, committed = item.get("commitment"), _committed_entry(item)
        if not commitment or not committed or "agreed_rate" not in committed:
            return
        decimal = lambda n: Decimal(str(n))
        method, rate = committed.get("cost_method"), decimal(committed["agreed_rate"])
        basis, amount = commitment.get("basis"), decimal(commitment.get("amount", 0))
        charges = Decimal(0)
        for value in item.values():
            if isinstance(value, dict) and "available" in value:
                included = value.get("included", [])
                names = [n for n in value.get("selected", included) if n not in included]
                for name in names + value.get("excluded", []):
                    charges += decimal((value.get("deltas") or {}).get(name, {}).get("delta_flat", 0))
        flight = commitment.get("flight") or {}
        starts, ends = flight.get("start"), flight.get("end")
        total, units, elapsed = amount, None, None
        rate_per = decimal(committed.get("rate_per", RATE_PER.get(method) or 1))
        size = RATE_UNIT_SECONDS.get((committed.get("cost_parameters") or {}).get("rate_unit"))
        if method == "TIME" and starts and ends and size:
            parse = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
            elapsed = int(((parse(ends) - parse(starts)).total_seconds() + 1) // size)
        if method == "FLAT":
            if basis != "spend":
                self.err(file, path, "basis", "a FLAT commitment has basis spend")
            if amount != rate + charges:
                self.err(file, path, "amount", f"a FLAT amount is {rate + charges}")
            if "derived_units" in commitment:
                self.err(file, path, "derived_units", "derived_units on a FLAT commitment")
        elif elapsed is not None:
            units, total = elapsed, elapsed * rate + charges
            if amount != (elapsed if basis == "units" else total):
                self.err(file, path, "amount", f"a TIME commitment is for {elapsed} units, {total} in all")
        elif basis == "spend":
            if charges > amount:
                self.err(file, path, "amount", "delta_flat charges exceed the amount")
            if rate > 0:
                units = int((amount - charges) / rate * rate_per)
        else:
            total, units = amount / rate_per * rate + charges, amount
        if units is not None and "derived_units" in commitment and commitment["derived_units"] != units:
            self.err(file, path, "derived_units", f"derived_units recomputes to {units}")
        spend = (item.get("commitment_bounds") or {}).get("spend") or {}
        if ("min" in spend and total < decimal(spend["min"])) or ("max" in spend and total > decimal(spend["max"])):
            self.err(file, path, "commitment_bounds", f"seller total {total} is outside spend")
        unit_limits = committed.get("unit_bounds") or {}
        if units is not None and (units < unit_limits.get("min", units) or units > unit_limits.get("max", units)):
            self.err(file, path, "unit_bounds", f"{units} units are outside unit_bounds")

    def check_exclusion_list(self, file, path, value):
        """An array of the type's entries, or a DocumentRef (section 5.5)."""
        if isinstance(value, dict):
            self.check_object(file, path, value, "DocumentRef")
        elif not isinstance(value, list):
            self.err(file, path, "list", "an ExclusionList is an array or a DocumentRef")
        else:
            entry = EXCLUSION_ENTRY.get(path.rsplit(".", 1)[-1])
            for i, item in enumerate(value):
                if entry:
                    self.check_type(file, f"{path}[{i}]", item, entry)

    def check_exclusions(self, file, path, item):
        """A buyer supplies only the types the seller accepts (section 5.5)."""
        accepted = (item.get("accepted_exclusions") or {}).get("types", {})
        for term in accepted:
            if ":" not in term and term not in EXCLUSION_ENTRY:
                self.err(file, f"{path}.accepted_exclusions", term, f"{term!r} is not a core exclusion type")
        for term, entries in (item.get("exclusions") or {}).items():
            if term not in accepted:
                self.err(file, f"{path}.exclusions", term, f"{term!r} is not an accepted exclusion type")
            elif isinstance(entries, list) and len(entries) > accepted[term].get("max_entries", len(entries)):
                self.err(file, f"{path}.exclusions", term, f"{term!r} holds more than max_entries")

    def check_audiences(self, file, path, value):
        """The keys AudienceSelectable adds to its Selectable (section 5.3)."""
        combine = value.get("combine") or {}
        if combine.get("deltas"):
            self.err(file, f"{path}.combine", "deltas", "combine carries no deltas")
        if combine and (combine.get("max_select") != 1 or len(combine.get("included", [])) != 1):
            self.err(file, f"{path}.combine", "one", "combine needs max_select 1 and one included option")
        options = {o.get("id"): o for o in value.get("available", []) if isinstance(o, dict)}
        in_effect = value.get("selected", value.get("included", []))
        meaning = self.spec.tables["AudienceOption"]["taxonomy"]["meaning"]
        codes = {int(n) for n in re.findall(r"`(\d+)`", meaning)}
        vendor_from = int(re.search(r"\((\d+) and up\)", meaning).group(1))
        for name, option in options.items():
            taxonomy = option.get("taxonomy")
            if isinstance(taxonomy, int) and taxonomy not in codes and taxonomy < vendor_from:
                self.err(file, f"{path}.available", name,
                         f"{name!r} has taxonomy {taxonomy}, which section 5.3 does not allow")
        for name in value.get("excluded", []):
            if not options.get(name, {}).get("excludable"):
                self.err(file, f"{path}.excluded", name, f"{name!r} is not an excludable option")
            if name in in_effect:
                self.err(file, f"{path}.excluded", name, f"{name!r} is also in effect")

    def check_measurement(self, file, path, item):
        """Metric kinds, and the counted_by values sections 5.6.4 and 5.7.1 fix (section 2.2)."""
        for i, tuple_ in enumerate(item.get("committed_metrics") or []):
            kind, value = METRIC_KIND.get(tuple_.get("metric")), tuple_.get("level")
            if kind == "Rate" and not SCALARS["Fraction"](value):
                self.err(file, f"{path}.committed_metrics[{i}]", "kind", f"{value!r} is not a rate")
            if kind == "Count" and not SCALARS["Integer"](value):
                self.err(file, f"{path}.committed_metrics[{i}]", "kind", f"{value!r} is not a count")
        selection = item.get("controlling_measurement") or {}
        counters = selection.get("available", [])
        expected = {}
        if item.get("channel") == "dooh" and _counts_impressions(item):
            multiplier = (item.get("delivery_counting") or {}).get("impression_multiplier") or {}
            seller_domain = ((self.proposal or {}).get("seller") or {}).get("domain")
            vendor = multiplier.get("vendor")
            own = multiplier.get("source_type") == 2 or (seller_domain is not None and vendor == seller_domain)
            source = "seller" if own else vendor
            expected = {c.get("id"): source for c in counters}
        committed = _committed_entry(item)
        if committed and committed.get("cost_method") == "CPP":
            source = (committed.get("cost_parameters") or {}).get("rating_source")
            for name in selection.get("selected", selection.get("included", [])):
                expected[name] = source
        for counter in counters:
            name = counter.get("id")
            if name in expected and counter.get("counted_by") != expected[name]:
                self.err(file, path, name, f"counted_by of {name} is not {expected[name]!r}")

    def check_pricing_entries(self, file, path, item):
        """Section 5.6: entry ids are unique, and two entries differ on a key or mechanism."""
        entries = item.get("pricing") or []
        ids = [e.get("pricing_id") for e in entries]
        if len(ids) != len(set(ids)):
            self.err(file, path, "pricing_id", "two pricing[] entries share a pricing_id")
        seen = set()
        for entry in entries:
            for name in entry.get("transaction_mechanisms") or _mechanisms(item):
                key = (entry.get("cost_method"), json.dumps(entry.get("cost_parameters"), sort_keys=True),
                       entry.get("currency"), name)
                if key in seen:
                    self.err(file, path, "pricing", f"two pricing[] entries are the same on {name}")
                seen.add(key)

    def check_dated_shares(self, file, path, item):
        """Section 5.6.6: an option's dated_shares[] windows don't overlap."""
        for option in (item.get("cancellation_policy") or {}).get("available", []):
            windows = sorted((r["window"]["start"], r["window"]["end"]) for r in option.get("dated_shares", []))
            for earlier, later in zip(windows, windows[1:]):
                if later[0] <= earlier[1]:
                    self.err(file, path, "dated_shares", f"{option.get('id')}: dated_shares[] windows overlap")

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
            self.check_commitment(file, path or "(root)", doc)
            self.check_mechanisms(file, path or "(root)", doc)
            self.check_measurement(file, path or "(root)", doc)
            self.check_pricing_entries(file, path or "(root)", doc)
            self.check_dated_shares(file, path or "(root)", doc)
            self.check_exclusions(file, path or "(root)", doc)
            if "audiences" in doc:
                self.check_audiences(file, f"{path}.audiences" if path else "audiences", doc["audiences"])
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
            parts = [re.sub(r"\[\*\]$", "", p) for p in path.lstrip("$.").split(".")]
            fields = self.spec.proposal
            if parts[0] == "line_items":
                fields, parts = self.spec.line_item, parts[1:]
            ok = parts[0] in {bare(k) for k in fields}
            if ok and len(parts) > 1:
                if parts[0] == "pricing":
                    ok = f"pricing[].{parts[1]}" in fields
                else:
                    # Below a typed field, a path names a key of that type's table.
                    row = fields.get(parts[0]) or fields.get(f"{parts[0]}[]")
                    rows = self.rows_of(row["type"])
                    ok = not rows or parts[1] in {bare(k) for k in rows}
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


def remove_path(node, parts):
    if not parts:
        return
    head, rest = parts[0], parts[1:]
    if head.endswith("[*]"):
        for item in (node.get(head[:-3]) or []):
            remove_path(item, rest)
        return
    if not rest:
        node.pop(head, None)
    elif isinstance(node.get(head), dict):
        remove_path(node[head], rest)


def record_digest(doc, removal, line_item_ids):
    """Section 4.1.1: the digest of the binding record for the named line items."""
    copy = json.loads(json.dumps(doc))
    copy["line_items"] = [i for i in copy.get("line_items", []) if i["line_item_id"] in line_item_ids]
    for path in removal:
        remove_path(copy, path[2:].split("."))
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
        {"expected_match_rate": 0.65},
        {"segments": [], "suppression_list": {}, "expected_match_rate": 0.65},
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
        notice = entry.get("cancellation") or {}
        option = notice.get("option_id")
        if option is not None:
            policy = items.get(named, {}).get("cancellation_policy") or {}
            if option not in policy.get("selected", policy.get("included", [])):
                checker.errors.append(f"{file}: change_requests[{n}].cancellation: "
                                      f"{option} is not an option in effect")
            terms = next((o for o in policy.get("available", []) if o.get("id") == option), {})
            if notice.get("cancelled_share", 0) > applicable_max_share(terms, notice):
                checker.errors.append(f"{file}: change_requests[{n}].cancellation: "
                                      f"cancelled_share is above the max_share that applies")


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
