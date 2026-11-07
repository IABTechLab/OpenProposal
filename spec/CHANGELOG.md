# Changelog

Changes to the OpenProposal specification. Every normative entry references the
issue that caused it, so the comment record and the spec history line up.

## [Unreleased]

- § 1.1, § 2.1, § 2.6, § 5.4, § 5.5, § 5.6, § 5.9, § 5.10, § 6.2, § 8, appendices, examples,
  docs, checkers — downstream handoff. § 5.9 has one table of `transaction_mechanism` values.
  It states which are deal mechanisms and which `delivery_type` each allows. § 1.1 keys on
  those values, with each one's `reference_type` and change path. An option is
  `{ id, delivery_type }`. `delivery_type` says what the seller promises: `guaranteed`,
  `share_of_voice`, or `non_guaranteed`. A share of voice carries `sov_basis` and `sov_share`,
  and `availability` is a forecast under `non_guaranteed`. `open_auction` is removed: with no
  deal ID, no bid request can name a line item. A line item agreed under a deal mechanism maps
  to a Deals API 1.0 `Deal`, which the system named by `deal_origin` pushes. The seller records
  the deal ID as an `external_references[]` entry with `reference_type: deal`. The Deals API
  table maps a `CPM` entry and says other cost methods have no mapping yet. `agreed_rate` is the
  deal's price, and `pricing[].price_type` says how it clears. § 1.1 gains an OpenDirect 2.1
  mapping for a `direct_io` line item and a `programmatic_guaranteed` reservation. It covers who
  acts, which `cost_method` values have a `ratetype`, and what the record doesn't hold. Each
  `creative_delivery.method` is defined, and it routes the creative under any mechanism:
  `assets[]` and `materials_due` read only where creative reaches the seller. `buying_route`
  and `supported_order_systems[]` are removed, and `serving_platform` is a `Domain`. The bonus
  example sells as `direct_io`. Breaking A `VersionRef` outside its proposal carries `seller_domain`, and a Deals API push may carry the agreed baseline in `ext.baseline`.
  ([#132](https://github.com/IABTechLab/OpenProposal/issues/132),
  [#133](https://github.com/IABTechLab/OpenProposal/issues/133),
  [#93](https://github.com/IABTechLab/OpenProposal/issues/93),
  [#109](https://github.com/IABTechLab/OpenProposal/issues/109)).

- § 1.2, § 2.1, § 2.4, § 2.5, § 2.7, § 4.1.1, § 4.1.2, § 4.1.3, § 4.3, § 4.4, § 5.6.1, § 5.10,
  § 6.8, § 8, appendices, examples, docs, issue templates, checkers — after `agreed`. § 1.2 separates what a
  request or response carries, which this document states, from the envelope and binding of the
  message. "Message binding" names that layer. The contract has a provisional name, `iab-agentic-primitives` is named as its
  nearest artifact, the hub is named, and the contract governs only once it is published on a standards track. The baseline
  is the `VersionRef` that names the agreed line item, at the `version` of its agreed record.
  § 4.4 adds `change_requests[]`, outside the record, with the OpenDirect 2.1 ChangeRequest
  fields except `webhook`, plus `baseline`, `actor`, `at`, and `cancellation`. `cancellation` is typed `CancellationNotice`, whose key table lands with the pricing change. `orderid` is
  REQUIRED only when the line item has an `order` reference. `accountid` and `requesterid` are
  OPTIONAL, because only an OpenDirect 2.1 ChangeRequest requires them. `status` is an
  `ApprovalStatus`, a change of `status` is a new entry, and an entry MAY carry `ext`. § 8 asks
  how an entry states a change other than a cancellation. `correlation_id` is removed: the
  baseline and `external_references[]` do the job. `ExternalReference` has a key table, `role`
  becomes `reference_type`, and `io` gives way to `order` and `line`. A receiver that doesn't know
  a `reference_type` ignores the entry. § 5.10 and § 6.8 take new titles. Breaking
  ([#59](https://github.com/IABTechLab/OpenProposal/issues/59),
  [#68](https://github.com/IABTechLab/OpenProposal/issues/68)).

- § 1.2, § 2.2, § 2.4, § 2.8, § 3.4, § 4, § 4.1, § 4.1.1, § 4.1.2, § 4.1.3, § 4.2, § 4.3,
  § 4.3.1, § 4.3.2, § 4.3.4, § 5.5, § 5.6, § 5.6.1, § 5.8, § 5.9, § 5.10, § 6, § 7, appendices,
  examples, checkers — what is signed, and how a seller checks it. `record_digest` sits only on
  `assent[]` entries, and the document-level field and its "two values" are gone. § 4.1.1 states
  the exact bytes of the digest input. A removal leaves an empty object in place, except
  `buyer_supplied`, and nothing fills in a default. `agreed_rate` takes the § 5.6 result, a
  `DocumentRef` enters whole, and the YAML conversion and validity tests are stated. The removal
  list drops `seller_rate`, `deal_id_issuance`, `commitment.version`, and
  `commitment.idempotency_key`. It adds `min_rate`, `best_for[]`, `not_suitable_for[]`,
  `seasonality_notes`, `segments[]`, and `suppression_list`. `AssentEntry` has a key table: `role`
  is `commitment`, `acceptance`, `withdrawal`, or `decline`, and `signed_at` becomes `at`.
  `signer` is removed, and `idempotency_key` moves here from `commitment`. Only `assent[]` decides
  whether a line item is agreed, and a history entry voids nothing. A `commitment` entry stops
  being live when its `commit` goes stale or void, and an `acceptance` matches only a live entry.
  A `Commit` holds the buyer's entry and its `writes`. A `CommitResult` holds the entries and any
  `availability` figures a `decline` states. The seller's check on `version` becomes a recomputed
  digest. Its rejections come in order: `expired`, `stale_version`, `not_committable`, then
  `record_mismatch`. A `commit` writes an entry only on an issued proposal, and a replay returns
  the result as it stands. A seller MUST keep a rejection whose `retry` is not `same` until
  `offer_window.end`, or, with no end, as long as it keeps the proposal. An entry travels in the body of an HTTP message signed under the
  OpenProposal profile of Web Bot Auth (§ 2.8). `Content-Digest` covers the body, and requests
  and responses are both signed. Which signing origins a party accepts is its own configuration,
  and any signed copy of an entry is evidence of it. The evidence is OPTIONAL, and `agreed`
  doesn't depend on it. Each party keeps the agreed record. `terms_ref` and
  `terms_acceptance_required` become `terms_refs[]` of `DocumentRef`, and a `commitment` entry
  accepts them all. An absent list accepts no document. A `DocumentRef`'s `url` is an `HttpsUrl`,
  a new type, and `list_ref` is a `DocumentRef`. `commitment.proposal_id` and
  `commitment.version` go, because the entry pins the version. `seller_rate` is removed. Breaking A `commitment` names at least one advertiser, a `decline` states its `ground`, and a seller answers a `commit` under a firm entry while the entry holds.
  ([#63](https://github.com/IABTechLab/OpenProposal/issues/63),
  [#27](https://github.com/IABTechLab/OpenProposal/issues/27),
  [#24](https://github.com/IABTechLab/OpenProposal/issues/24),
  [#34](https://github.com/IABTechLab/OpenProposal/issues/34),
  [#45](https://github.com/IABTechLab/OpenProposal/issues/45),
  [#73](https://github.com/IABTechLab/OpenProposal/issues/73),
  [#75](https://github.com/IABTechLab/OpenProposal/issues/75)).
  Where a `String` value in the binding record conflicts with a typed field of the same
  `version`, the typed field governs ([#155](https://github.com/IABTechLab/OpenProposal/issues/155)).
- § 1.1, § 2.1, § 2.2, § 2.6, § 3, § 3.1 to § 3.4, § 4.1, § 4.1.1, § 4.1.3, § 4.3.1,
  § 4.3.2, § 5.1.1, § 5.2, § 5.2.1, § 5.4, § 5.5, § 5.6, § 5.6.1, § 5.6.3, § 5.7, § 5.9,
  § 6, appendices, examples, checker — what the buyer writes, and how the rate is computed.
  `selected[]` is the complete set of options in effect and replaces `included[]`; `value`
  is the buyer's key on a `settable` field, beside a required `default`. An envelope's
  `value` is `{ include[], exclude[] }` and only narrows `allowed[]`. `frequency_cap.count`
  is the range form. The bare-value fallbacks are gone. An object option has a required
  `id`, unique in the field. Options combine freely, and `measurement_source` and
  `reporting` say what nothing in effect means. `agreed_rate` has one formula, sits only on
  the committed entry, and rounds once. `gross_rate` becomes `list_rate`, and `floor`
  becomes `min_rate`, a hint that grants nothing
  ([#133](https://github.com/IABTechLab/OpenProposal/issues/133)). `delta_pct` becomes
  `delta_fraction`, a fraction, so 2 percent is `0.02`. `list_rate` and `commitment_bounds`
  are `requestable`, and a granted rate is the `list_rate` of the next version. `commitment`
  is `mixed`. `transaction_mechanism` declares `max_select: 1`. § 3.3 states the
  availability read, and § 3.4 names `BuyerWrites` and `LineItemWrites`. `geo` holds
  `GeoCode` entries as a `settable` field, and the selectable form becomes `markets`.
  `device` holds AdCOM codes, a `daypart` window is a `ClockWindow` that ends `before` a
  minute, and `supported_formats` is removed. Breaking
  ([#22](https://github.com/IABTechLab/OpenProposal/issues/22),
  [#30](https://github.com/IABTechLab/OpenProposal/issues/30),
  [#58](https://github.com/IABTechLab/OpenProposal/issues/58),
  [#14](https://github.com/IABTechLab/OpenProposal/issues/14),
  [#111](https://github.com/IABTechLab/OpenProposal/issues/111)).
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
