# Changelog

Changes to the OpenProposal specification. Every normative entry references the
issue that caused it, so the comment record and the spec history line up.

## [Unreleased]

- § 2.1, § 2.6, § 2.7, § 5.2, § 5.2.4 to § 5.2.8, § 5.5, § 5.6, § 5.6.4, examples, checkers —
  seller relationship and the property option. `PropertyOption` has one key table in § 5.2.4,
  and a screen has its own in § 5.2.8, with `Loop` and `SyncGroup`. App identity, seller
  relationship, child-directed status, and DOOH screens each have a numbered section. Each
  property states the seller's relationship and the accounts a buyer checks against the
  governing ads.txt or app-ads.txt. An app's governing developer domain comes from the store
  listing. Properties declare `child_audience` and `child_treatment`, and § 5.2.7 states
  what follows. `AppId` is `{ store, bundle }` and `App` adds `store_url` and
  `developer_domain`. `platform` becomes `store`, a `VocabularyTerm` that names the store
  rather than the device, stated once. A block list's `app_bundle[]` becomes `apps[]` of
  `AppId`. A summary lists each property's apps, `child_audience`, and `seller_relationship`.
  Absent `properties` promises no property, and the audio example names one. A key table
  follows a lead-in that names its type, and an object option's type ends `Option`. A property
  MAY carry `tv_channel` and `tv_network`, AdCOM 1.0 `Channel` and `Network` objects matched by
  `domain`. Breaking
  ([#88](https://github.com/IABTechLab/OpenProposal/issues/88),
  [#8](https://github.com/IABTechLab/OpenProposal/issues/8),
  [#15](https://github.com/IABTechLab/OpenProposal/issues/15),
  [#96](https://github.com/IABTechLab/OpenProposal/issues/96),
  [#97](https://github.com/IABTechLab/OpenProposal/issues/97),
  [#71](https://github.com/IABTechLab/OpenProposal/pull/71)).

- § 1.1, § 2.1, § 2.2, § 2.6, § 3.3, § 5.2, § 5.5, § 5.6, § 5.6.4, § 5.7.1, § 5.9, § 6.9, appendices,
  examples, checker — DOOH properties, plays, and impressions. When `channel` is `dooh`, a
  property is a set of screens of one venue type. It carries `venue_type`, `allocation`,
  `min_screens`, `screens[]`, `slots_per_loop`, and `sync_groups[]`, and a summary lists
  `venue_type` and the multiplier's type, source, and accreditation. `viewer_local` is each screen's own zone. `frequency_cap.per` is a
  `VocabularyTerm` with the core term `screen`, and `availability.unit` gains
  `slots_per_loop`. § 5.6.4 defines a play and an impression. `delivery_counting`, REQUIRED
  on a `dooh` line item, holds `play_tolerance_ms`, `proof_of_performance`,
  `partial_play_credit`, and a nested `impression_multiplier`, which MAY state its source's
  `accreditation` (`industry_currency` or `publisher_reported`). A line item that counts only
  plays needs the outer object alone. `proof_of_performance` has a key table, and
  `evidence[]` is a `VocabularyTerm`. The committed quantity on a `dooh` line item has one
  rule, in § 5.6.4: it is in the committed entry's `unit`. The multiplier's source controls
  the count of impressions, and `metric` gains the count term `impressions`. A `loop_time`
  share derives from the loop, a domination is `guaranteed` with sole exclusivity, and a
  share's eligible screens are the line item's screen set. A domination can cover a location or
  its paid zone, with the matching `separation`. A play is inside a window when it starts inside
  it, and the multiplier MAY name the `demographic` whose value settles. A loop's `length_s`
  counts every item the loop plays, paid or not. Unless the committed entry is `CPP` or `CPA`, a
  line item that counts impressions has the multiplier's source as `counted_by`. § 1.1 maps a
  `dooh` line item's owners and screens to Deals API 1.0 `pubcount`, `dinventory`, and
  `inventory.inclinventory`. Breaking
  ([#92](https://github.com/IABTechLab/OpenProposal/issues/92),
  [#96](https://github.com/IABTechLab/OpenProposal/issues/96),
  [#79](https://github.com/IABTechLab/OpenProposal/issues/79),
  [#134](https://github.com/IABTechLab/OpenProposal/issues/134)).

- § 3.1, § 5.5, § 5.6.5, § 5.7, § 5.7.1, § 5.9, § 5.10, § 8, appendices, examples, docs,
  checkers — who measures, the metric terms, and the terms settlement reads. Settlement reads
  the terms in force: the agreed record plus any change the applying system has applied.
  § 5.7.1 says what OpenDirect 2.1 `Stats` reports. It also says that no standard in § 1.1
  states a final count, a delivered share of impressions, a reconciliation, or a remedy.
  `controlling_measurement` names whose count is invoiced and when it is final. It is
  REQUIRED with `committed_metrics[]`, `commitment_bounds.spend`, or a `pricing[].unit_bounds`,
  and `discrepancy_threshold` names the other measurement. `measurement_source` option
  `vendor` becomes `measured_by`, and `counted_by` names who counts. Both are a `Measurer`,
  compared byte for byte, and a `qualifier` beside either names a product or method.
  `verification[]` holds the domains of third parties that can attest enforcement.
  `CommittedMetric` has a key table: `value` becomes `level`, and `direction` is REQUIRED.
  `basis` and `seller_reported` are removed: the term names the standard, and
  `measurement_source` says who measures. `metric` has a core table of `viewable_rate`,
  `completion_rate`, and `ivt_rate`, each naming its standard, and `viewability_standard`
  gains the core term `mrc`. § 3.1 lets a named type hold the keys of a `Selectable[T]`, so
  `shortfall_remedy` is a `ShortfallRemedy`, and `RemedyTerms` has a key table. § 5.7.1
  states what a shortfall is and how `shortfall_remedy` settles it. `guaranteed` covers a
  `FLAT` entry, which has no units. `feed_type` becomes `report_type`, a `VocabularyTerm`,
  and `delivery_mechanism` becomes `delivery_method`. `provided_metrics[]` takes the § 5.6.5
  `unit` terms and the § 5.7.1 rate terms.
  `billing.invoice_period` points at § 5.7.1, and § 8 gains question 10, on a shortfall with
  no remedy left. When `preemption` states a `remedy`, the delivery a preemption takes, less any
  replacement within `commitment.flight`, is a shortfall on any `delivery_type` and settles under
  that `remedy`. Question 10 also asks how much delivery a preemption takes. On a `CPA` entry,
  `counted_by` MUST be `cost_parameters.action_source`. Breaking
  ([#93](https://github.com/IABTechLab/OpenProposal/issues/93),
  [#95](https://github.com/IABTechLab/OpenProposal/issues/95),
  [#134](https://github.com/IABTechLab/OpenProposal/issues/134),
  [#38](https://github.com/IABTechLab/OpenProposal/issues/38),
  [#80](https://github.com/IABTechLab/OpenProposal/issues/80)).

- § 1.1, § 2.1, § 2.2, § 2.4, § 2.5, § 3.1 to § 3.3, § 4.1, § 4.3.2, § 4.4, § 5.6, § 5.6.1, § 5.6.3,
  § 5.6.5 to § 5.6.7, § 6, § 8, appendices, examples, docs, checkers, pricing fixtures — pricing.
  `cost_method` is an open vocabulary, with core terms that have a `unit` and a rate per in
  § 5.6.5. An extension term is domain-prefixed and has `rate_per`, `unit_label`, and a
  `cost_definition` that is a `DocumentRef`. `pricing[]` entries are alternatives, each with a `pricing_id`, and a commitment
  names one. `Amount` is the one money type, read in the committed entry's `CurrencyCode`, so
  `commitment.currency` and the currency on `requires.min_commitments[]` are gone. Every `Amount` is
  on one basis, which § 8 asks about. `min_spend` and the budget keys become
  `commitment_bounds.spend`, and `commitment_bounds` gains the informative `earliest_start` and
  `latest_end`. `min_impressions` and `max_impressions` become `pricing[].unit_bounds`, which counts
  the entry's unit and which a `grant` MAY widen. `derived_units` rounds down, `FLAT` and `TIME` set
  the figures from the rate and the flight, and `FLAT` delivery is days of the flight.
  `Availability` has a key table: `type` becomes `certainty`, `as_of` becomes `computed_at`, `basis`
  goes, and `window` names the dates. A cancellation option has `notice_duration`, `fees[]`, and
  `dated_shares[]`, and a `change_requests[]` entry's `cancellation` is a `CancellationNotice`. An
  exclusivity option is an `ExclusivityOption`, with a `window`. The pricing vectors use these
  names and round as § 5.6 and § 5.6.5 state. A granted rate is the `list_rate` of the next
  `version`, so `accepted_counter` and `selection_key` are removed. `agreed_rate` is never negative, and is above 0 under `spend` on an entry other than `FLAT` or `TIME`. A `counter` of `list_rate` may also change `included[]`. `separation` adds `location` and `paid_zone`, and a `demographic` term states how it treats co-viewers and unknown age. A line item MAY state `preemption`: what can preempt its delivery, and with what notice. A line item whose `preemption` names `exclusivity` doesn't block a later exclusivity term once its notice has run, and preemption doesn't excuse a shortfall. A `remedy` on `preemption` states what the buyer gets for the delivery a preemption takes.
  A `TIME` entry's `derived_units` rounds to the nearest whole `rate_unit`, half up. On a `day`
  rate, `calendar_zone` makes it count the calendar days in that zone that the flight touches,
  and `calendar_zone` is absent on any other rate. `action_type` takes its core terms from
  ECAPI 1.0: the `event_type` values in its Standard Events and Additional Events tables, other
  than `custom`. Breaking
  ([#94](https://github.com/IABTechLab/OpenProposal/issues/94),
  [#98](https://github.com/IABTechLab/OpenProposal/issues/98),
  [#117](https://github.com/IABTechLab/OpenProposal/pull/117),
  [#127](https://github.com/IABTechLab/OpenProposal/issues/127),
  [#115](https://github.com/IABTechLab/OpenProposal/issues/115),
  [#70](https://github.com/IABTechLab/OpenProposal/pull/70),
  [#30](https://github.com/IABTechLab/OpenProposal/issues/30),
  [#125](https://github.com/IABTechLab/OpenProposal/issues/125),
  [#121](https://github.com/IABTechLab/OpenProposal/issues/121),
  [#80](https://github.com/IABTechLab/OpenProposal/issues/80)).

- § 2.4, § 3.4, § 4.1.1, § 4.1.3, § 4.3, § 4.3.1, § 4.3.2, § 4.3.4, § 5.6, § 5.6.1, § 5.6.2,
  appendices, examples, checkers — holds. `hold_status` splits in two: `hold_terms`,
  `{ available, duration }`, is `seller-set` and inside the record, and `hold` is `lifecycle`
  and outside it, so the removal path has no exception. An absent `hold_terms` means
  `available` is `false`, and asking for a hold it doesn't offer returns `not_offered`.
  `state` and `hold_expires_at` become `status` and `valid_until`, and `none` goes: `hold`
  is absent until the buyer first asks. `HoldStatus` adds `declined`, a lapsed hold can be
  asked again, and the transitions are exhaustive. The held terms are the offered terms of
  `hold.version`. `hold` gains `version`, `position`, the queue order of granted holds, and
  two optional keys: `requested_terms`, the `LineItemWrites` the buyer asks to hold, and
  `held_availability`, what the seller reserves. `held_availability` is typed
  `Availability`, whose keys the `availability` row lists until its key table lands.
  `hold_scope` is removed: under `linked_execution: all`, holds move as a unit. The re-offer
  is a listed transition, and `valid_until` states its cap. The CTV example no longer offers
  a hold on a `private_auction` line item. Breaking `held` means reserved inventory, and a hold stays `held` while a `commit` made during it is open. `hold.reference` holds the seller's id for the reservation, and `renewal_right` offers a right to the next cycle.
  ([#66](https://github.com/IABTechLab/OpenProposal/issues/66),
  [#134](https://github.com/IABTechLab/OpenProposal/issues/134)).
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
  and responses are both signed. § 2.8 defines the profile: an origin as identity, key directories
  signed by every key they list, the verification order, replay, and the failure statuses, with
  conformance vectors in a reference implementation. Which signing origins a party accepts is its own configuration,
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
  The manifest's `hold_limits` declares the most holds a seller grants at once, per buyer and
  per advertiser ([#156](https://github.com/IABTechLab/OpenProposal/issues/156)).
- § 1.1, § 2.1, § 2.2, § 2.6, § 2.7, § 3, § 3.1 to § 3.4, § 4.1, § 4.1.1, § 4.1.3, § 4.3.1,
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
  minute, and `supported_formats` is removed. A `min_rate` is as readable as its line item,
  so on a `public` line item it is public. Breaking
  ([#22](https://github.com/IABTechLab/OpenProposal/issues/22),
  [#30](https://github.com/IABTechLab/OpenProposal/issues/30),
  [#58](https://github.com/IABTechLab/OpenProposal/issues/58),
  [#14](https://github.com/IABTechLab/OpenProposal/issues/14),
  [#111](https://github.com/IABTechLab/OpenProposal/issues/111),
  [#47](https://github.com/IABTechLab/OpenProposal/issues/47)).
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
  tables. A preview served through server-side ad insertion uses a session in which the
  insertion service sends no production notifications. If the service can't provide one, the
  creative is inspected outside the stitched stream. Breaking
  ([#121](https://github.com/IABTechLab/OpenProposal/issues/121),
  [#31](https://github.com/IABTechLab/OpenProposal/issues/31),
  [#33](https://github.com/IABTechLab/OpenProposal/issues/33),
  [#2](https://github.com/IABTechLab/OpenProposal/issues/2),
  [#3](https://github.com/IABTechLab/OpenProposal/issues/3),
  [#42](https://github.com/IABTechLab/OpenProposal/issues/42)).
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
- § 5.2 — Properties can carry `apps[]` for app and CTV inventory, keyed as
  OpenRTB 2.6 `app`, and the Summary Representation lists the app identifier
  ([#15](https://github.com/IABTechLab/OpenProposal/issues/15)).

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
