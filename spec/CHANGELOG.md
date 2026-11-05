# Changelog

Changes to the OpenProposal specification. Every normative entry references the
issue that caused it, so the comment record and the spec history line up.

## [Unreleased]

- § 2, § 3, § 4, § 5, § 7, § 8, appendices, examples, docs, checker — shared types and
  authoring rules. § 2.2 gives each repeated concept one type, with one rule for an
  unknown vocabulary term. § 2.6 states the table, presence, type, key, and value
  rules. Every field and key row has a Type and a Required column. § 3 adds the
  `lifecycle`, `recorded`, `asserted`, and `mixed` markers, and the proposal lists its
  `line_items[]`. The Summary Representation is a strict path subset, and the manifest
  has a key table. `catalog_ref` is removed. These names change: `valid_from` and
  `valid_until` become `offer_window`, and `flight_start` and `flight_end` become
  `commitment.flight`. `brief_ref` and `format_ref` become `brief_id` and `format_id`,
  and `url_or_tag` becomes `url` or `markup`. `fields_changed[]`, `min_commitment[]`,
  and `metrics_provided[]` become `paths[]`, `min_commitments[]`, and
  `provided_metrics[]`. `frequency_cap.max` and `frequency_cap.basis` become `count`
  and `per`, and the selectable `pricing` map becomes `deltas`. `materials_due` holds
  `at` or `before_start`. Owned value lists are lower snake case, every term compares
  byte for byte, and `cost_method` writes `FLAT`. Headings are numbered, and normative
  text cites no issue. `scripts/check_examples.py` checks the examples against the
  tables. Breaking
  ([#121](https://github.com/IABTechLab/OpenProposal/issues/121),
  [#31](https://github.com/IABTechLab/OpenProposal/issues/31),
  [#33](https://github.com/IABTechLab/OpenProposal/issues/33),
  [#2](https://github.com/IABTechLab/OpenProposal/issues/2),
  [#3](https://github.com/IABTechLab/OpenProposal/issues/3)).
- § 2.1, § 5.1, § 5.2 — `channel` and `environments` defined in AdCOM 1.0
  terms, with a first-match channel table, a skip rule for unknown channels
  and a channel and environment consistency rule. `audio_streaming` removed;
  the summary carries `environments.available[]`
  ([#90](https://github.com/IABTechLab/OpenProposal/issues/90)).
- Define the boundary between creative inspection and production notifications
  in section 5.4.1, with an informative CTV example note
  ([#42](https://github.com/IABTechLab/OpenProposal/issues/42)).
- § 2, § 4.1, § 5.6 — `linked_execution` on the proposal and `requires` on
  line items, for linked execution and bonus line items
  ([#23](https://github.com/IABTechLab/OpenProposal/issues/23)).
- § 2.3 — a seller MAY publish its public standard line items as a static
  manifest at `/.well-known/openproposal.json`, for a two-phase
  discover-then-propose flow
  ([#29](https://github.com/IABTechLab/OpenProposal/issues/29)).

## [3.0-draft-1] — 2026-09-22

Initial draft published for public comment. Ported from the working-group
document with no normative changes.

Notable from earlier working drafts:

- `audience_pricing` is **removed**, generalised into the `pricing` key on any
  `selectable` field (§ 3.1).
- Per-field mutability markers introduced (§ 3). See open question OQ-1.
- Explicit no-inheritance rule (§ 2): line items are fully self-contained.
- `channel` added as the line item discriminator; `committed_metrics[]`
  generalised to `{ metric, value, basis }` tuples, rather than a schema fork
  per channel.
