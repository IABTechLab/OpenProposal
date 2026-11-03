# Changelog

Changes to the OpenProposal specification. Every normative entry references the
issue that caused it, so the comment record and the spec history line up.

## [Unreleased]

- § 1.2, § 2.2, § 2.3, § 2.4, § 3, § 4.1, § 4.1.1, § 4.1.2, § 4.1.3, § 4.3, § 5.1, § 5.4,
  § 5.6, § 5.6.1, § 5.6.3, § 5.8, § 5.9, § 6, § 7, appendices, examples, checkers — who
  moves each status, and when an offer goes stale. The `seller-set` gate reads the `status`
  of the object that carries the field. § 4.1.1 and § 4.1.2 define the binding record,
  `record_digest`, and `assent[]` entries, which replace the `assent` object. § 4.1.3 freezes
  a version's offered terms, and § 4.3 states who moves each status. A resolved `commitment`
  is an offer until the seller accepts it. A proposal with no `buyer` is shared, and one with
  a `buyer` is issued; `issued_from`, a `VersionRef`, is added, and a `custom` proposal is
  issued from the start. An ask is stale only when the binding record of the line items it
  names differs between its `version` and the current one. History actions become
  `published`, `requested`, `granted`, `countered`, `declined`, and `withdrawn`, and a
  `commit` and its acceptance are in `assent[]` only. `accept` answers only a `commit`; a
  `request` is answered by `grant`, `counter`, or `decline`, and is identified by the value
  it asks. `HistoryEntry`, `HistoryPath`, `RequestedValue`, `ProposalStatus`,
  `LineItemStatus`, and `ApprovalStatus` are named types. The status table is exhaustive, a
  firm entry is defined per `pricing[]` entry, and the allowed grounds for declining one are
  listed once. A `draft` line item leaves the proposal `published`. `linked_execution` takes
  only `all`, which covers every `line_item_id` the version carries, and `offer_window` does
  not hold before `start`. `agreed` is stated once. Breaking
  ([#60](https://github.com/IABTechLab/OpenProposal/issues/60),
  [#64](https://github.com/IABTechLab/OpenProposal/issues/64),
  [#65](https://github.com/IABTechLab/OpenProposal/issues/65),
  [#67](https://github.com/IABTechLab/OpenProposal/issues/67),
  [#63](https://github.com/IABTechLab/OpenProposal/issues/63),
  [#68](https://github.com/IABTechLab/OpenProposal/issues/68),
  [#70](https://github.com/IABTechLab/OpenProposal/issues/70),
  [#26](https://github.com/IABTechLab/OpenProposal/issues/26),
  [#24](https://github.com/IABTechLab/OpenProposal/issues/24)).
- § 1.2, § 2.1 to § 2.5, § 4.1, § 5.6.1, § 5.8, § 5.9, § 5.10, § 7, § 8, appendices,
  examples, docs, checker — who the parties are, and what each identity layer proves.
  `seller_id` and `seller_name` become `seller`, a `Party` whose `legal_name` is
  REQUIRED, and the registry reference becomes `seller.registry_id`. `buyer` and
  `commitment.advertisers[]` are added. § 1.2 states who owns request authentication,
  authorization, and legal assent. § 5.8 defines each `visibility` value, which is
  REQUIRED, and separates who may read from who may commit. Eligibility is part of
  resolving a `commitment`; a failure returns `not_eligible`, and an unreadable line
  item returns `not_found`. `required_credentials[]` entries become
  `{ credential_type, issuer }`: `scheme`, its token list, and `id_required` are
  removed, and so are the `dsp_seat` and `custom` types. `eligible_bidders[]` splits
  into `eligible_buyers[]` and `eligible_seats[]`. `dsp_id` and `dsp_seat_id` become
  `buyer_requirements.seats`, a `SeatRef`; `seat_required` becomes `seats_expected`,
  `dsp_allowed[]` becomes `allowed_dsps[]`, and `seat_owner_entity` becomes
  `seat_owner`. `billing.supplier_id` and `billing.billing_supplier_id` become
  `billing.delivering_party`, and `billing` adds `invoice_period`, `cycle_length`, and
  `time_zone`. `agreement_ref` becomes `agreement`, with `agreement_type` and `term`,
  and its `parties[]` holds `Party` values. The manifest drops `seller_id`, filters on
  `status` as well as `visibility`, and needs at least one of `ETag` and
  `Last-Modified`; § 8 asks whether it needs both. A buyer discards a manifest entry
  whose `seller.domain` differs from the requested domain, and `full_url` returns only
  what the requester may read. A full fetch leaves out line items the requester may
  not read, and `ErrorObject.version` applies to a proposal the requester may read.
  `proposal_id` is unique within `seller.domain`, and a seller's own `ext` key is its
  `seller.domain`. `agreement_ref.valid_from` and `valid_until` become
  `agreement.term`, `agreement` adds `document`, and `external_references[].role` is a
  `VocabularyTerm`. Breaking
  ([#61](https://github.com/IABTechLab/OpenProposal/issues/61),
  [#62](https://github.com/IABTechLab/OpenProposal/issues/62),
  [#132](https://github.com/IABTechLab/OpenProposal/issues/132),
  [#126](https://github.com/IABTechLab/OpenProposal/issues/126),
  [#57](https://github.com/IABTechLab/OpenProposal/issues/57),
  [#29](https://github.com/IABTechLab/OpenProposal/issues/29),
  [#27](https://github.com/IABTechLab/OpenProposal/issues/27)).
- § 2, § 2.2, § 2.4, § 2.5, § 2.7, § 4.1, § 5.1, § 5.5, § 5.6.1, § 5.6.3, § 8,
  appendices, examples, docs, checker — errors, extensions, and forward
  compatibility. A rejection returns `errors[]`, one or more `ErrorObject`s with
  `code`, `detail`, `pointer`, `version`, and `retry`. The core codes include
  `not_eligible` and `record_mismatch`, and anyone can add a code under a domain
  they control. An `ErrorObject` is open, and `validation` applies when no other code
  does. `idempotency_conflict` tests the body, and an error with `retry: same` is not
  a stored result. § 5.5, § 5.6.1, and § 5.6.3 name the code each rejection returns.
  The proposal and each line item MAY carry `ext`, an `Ext` keyed by owner domain. A
  receiver ignores an entry it doesn't understand and keeps it unchanged, and `ext`
  is frozen at `agreed`. A key outside `ext` that a key table doesn't list is invalid.
  `spec_version` is a REQUIRED proposal field, and § 8 asks how a receiver reads a
  later release. § 2.7 adds informative security considerations. The `requires`
  cycle ban is removed. Breaking
  ([#130](https://github.com/IABTechLab/OpenProposal/issues/130),
  [#131](https://github.com/IABTechLab/OpenProposal/issues/131),
  [#33](https://github.com/IABTechLab/OpenProposal/issues/33)).
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
  in section 5.4, with an informative CTV example note
  ([#42](https://github.com/IABTechLab/OpenProposal/issues/42)).
- § 2, § 4.1, § 5.6 — `linked_execution` on the proposal and `requires` on
  line items, for linked execution and bonus line items
  ([#23](https://github.com/IABTechLab/OpenProposal/issues/23)).
- § 2.3 — a seller MAY publish its public standard line items as a static
  manifest at `/.well-known/openproposal.json`, for a two-phase
  discover-then-propose flow
  ([#29](https://github.com/IABTechLab/OpenProposal/issues/29)).
- § 5.5 — Buyer-supplied block lists: `exclusions_accepted` (what the seller
  can enforce) and `exclusions` (the buyer's lists)
  ([#25](https://github.com/IABTechLab/OpenProposal/issues/25)).
- § 4.1, § 5.6.1 — commitments carry `proposal_id` and `version`; a new
  attempt on a stale version, or past `valid_until` or `price_valid_until`, is
  rejected, and a replay returns the stored result. Breaking
  ([#24](https://github.com/IABTechLab/OpenProposal/issues/24)).
- § 5.8, § 5.10, § 7 — `terms_ref` for the exact terms accepted at assent,
  `agreement_ref` for the agreement a line item is priced under, and `io` and
  `agreement` roles on `external_references[]`. Breaking
  ([#27](https://github.com/IABTechLab/OpenProposal/issues/27)).
- § 4.1, § 7 — `proposal_template_id` links an issued proposal to the
  seller's template; each issued proposal has its own `status`, `version` and
  `negotiation_history[]`
  ([#26](https://github.com/IABTechLab/OpenProposal/issues/26)).
- § 5.5 — `geo` may be `selectable`, with per-market price deltas
  ([#14](https://github.com/IABTechLab/OpenProposal/issues/14)).
- § 5.5 — `time_zone` on the line item is the clock for `daypart` and
  `frequency_cap.period`: an IANA time zone name or `viewer_local`, REQUIRED
  with either. A `daypart` window is `{ days[], start, end }` in civil time,
  with `end` exclusive and later than `start`; a window that crosses midnight
  is two windows. `frequency_cap.period` is a calendar period in `time_zone`.
  Breaking ([#111](https://github.com/IABTechLab/OpenProposal/issues/111)).
- § 5.6 — `pricing[].floor` is the offer floor, not the downstream auction
  floor. Editorial clarification ([#16](https://github.com/IABTechLab/OpenProposal/issues/16)).

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
