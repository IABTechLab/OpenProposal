# OpenProposal — Object Model Specification

**AAMP 3.0 · Draft for public comment**

**Version 3.0 draft 1** · *Published for comment 2026-09-22*

> **Status:** Draft. This document is open for public comment. It is not a
> ratified IAB Tech Lab standard and MUST NOT be treated as one. See
> [CONTRIBUTING.md](../CONTRIBUTING.md) for how to comment and
> [docs/comment-process.md](../docs/comment-process.md) for what happens to
> your comment.

**License.** OpenProposal Specification by IAB Tech Lab is licensed under a
Creative Commons Attribution 3.0 License. To view a copy of this license, visit
[creativecommons.org/licenses/by/3.0/](https://creativecommons.org/licenses/by/3.0/).
See [LICENSE](../LICENSE).

OpenProposal is the core AAMP 3.0 object: the descriptive specification for
what is being bought and sold, engineered so a buying agent can parse and
evaluate it at machine speed. It pulls through from initial brief to binding
commercial terms, and is the canonical object a seller manages alongside its
OMS and ad server.

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, MAY and OPTIONAL in this document are to be interpreted as
described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

---

## 1. Preamble and scope

OpenProposal defines commercial and operational offers across their lifecycle,
from proposal creation to binding agreement. It carries both the shape of an
offer and the states and interactions that act on it.

Two shapes of the object exist:

- **Standard proposal** — published unilaterally by the seller's agent. No brief required.
- **Custom proposal** — built in response to a buyer's agent brief, referenced via `brief_id`.

### 1.1 Downstream standards

OpenProposal does not replace IAB Tech Lab execution standards. Each line item
lands in the one its `transaction_mechanism` maps to:

| OpenProposal concept | Downstream standard |
| :--- | :--- |
| Direct buy | OpenDirect 2.1 · Order + Line |
| Programmatic guaranteed | OpenDirect 2.1 + Deals API · `deal_id` |
| PMP deal | Deals API + OpenRTB 2.6 · Deal |
| Open market | OpenRTB 2.6 · open auction, no deal |

### 1.2 Relationship to other AAMP artifacts

**Identity.** Three questions about a party stay separate, for the buyer and the
seller alike. An answer to one is not an answer to another.

| Layer | Question | Answered by | Owner | In the proposal object |
| :--- | :--- | :--- | :--- | :--- |
| Request authentication | Which origin sent this request? | An [HTTP Message Signature](https://www.rfc-editor.org/rfc/rfc9421), with the key in that origin's [Web Bot Auth](https://datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/) directory | The AAMP agent identity and signing profile (provisional name) | Nothing. The object never carries or re-proves it |
| Authorization | What may this party, or its agent, do? | The seller's eligibility rules; a mandate the principal publishes or signs | This specification for the rules (§ 5.8); the AAMP authority document (provisional name) for mandates | The rules only, never the proof |
| Legal assent | Which legal entity agreed to which terms? | The `assent[]` entries for the binding version, with both parties named in the proposal | This specification for the parties and the record (§ 4.1); the profile for any signature over it | Parties, `assent[]` |

A request signature proves an `https` origin. It does not prove which party that
origin speaks for: a hosted agent's origin is the host's, and a mandate the party
publishes or signs connects them. What authenticates a seller's response is the
profile's to state. Reading a public file (§ 2.3) needs none of this.

---

## 2. Object shape

```
Proposal          → the merchandising pitch, identity, lifecycle state and assent
line_items[]      → buyable units, each in exactly one channel
```

**No-inheritance rule.** A field on a line item MUST NOT inherit its value from
the proposal or from a sibling line item. There is no "overridable unless
restated" semantics anywhere in this specification. Every term of a line item is
on the line item. The proposal supplies only identity, `spec_version`, the offer
window, `version`, and linked execution.

**Subsettable proposals.** A buyer MAY select and commit a subset of a
proposal's line items, unless the proposal sets `linked_execution` to `all`
(§ 4.1). A line item that declares `requires` (§ 5.6.3) may be committed only
when its conditions are met.

### 2.1 Summary and full representations

Every proposal and every line item has two representations.

**Full Representation:** every field the object holds, with a proposal's line items
in their Full Representation. A full fetch MUST return it, except for line items the
requester may not read (§ 5.8).

**Summary Representation:** what a buying agent reads when screening many
sellers' shelves. A manifest entry holds it (§ 2.3), and a response MAY
carry it. A summary is a strict path subset of the full object: a listed path has
the type and value it has in the Full Representation, it appears when the full form
has it, and no other path appears. A summary's own table adds keys beside these
paths: `has_requires`, which the full object doesn't hold, and the `line_items[]` of
`ProposalSummary`, whose entries are line item summaries.

`LineItemSummary` lists these paths of a line item (§ 5):

```text
line_item_id
channel
environments.available[]
content_detail
properties.available[].id
properties.available[].name
properties.available[].domains[]
audiences.available[].id
audiences.available[].name
formats.included[]
geo
pricing[].cost_method
pricing[].gross_rate
pricing[].currency
min_spend
commitment_bounds
addressable_scale
committed_metrics[]
required_credentials[]
buyer_requirements.allowed_dsps[]
transaction_mechanism.available[]
```

**`LineItemSummary`** adds this key:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `has_requires` | Boolean | REQUIRED | Derived: `true` when the line item declares `requires` (§ 5.6.3), so a screening agent does not recommend a line item that cannot be bought on its own |

`ProposalSummary` lists these paths of a proposal (§ 4):

```text
proposal_id
version
seller.domain
seller.legal_name
description
offer_window
linked_execution
```

**`ProposalSummary`** adds this key:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `line_items[]` | Array[LineItemSummary] | REQUIRED | The full form's line items, each as a summary. In a manifest entry, only those § 2.3 lists |

### 2.2 Shared types

One concept has one type, and every field that holds the concept uses it. A field
that holds a shared type states what the value means there, not its form. Its row
MAY narrow the type for that field, by requiring a key the type leaves OPTIONAL or by
limiting the values or count the type allows, and says so. A row never loosens a
shared type or changes its form.

| Type | Form | Rules |
| :--- | :--- | :--- |
| `Digest` | String of 71 characters: `sha256:` followed by the 64 lowercase hexadecimal characters of the SHA-256 of its input | The value carries the algorithm, and a field name never names it. `sha256` is the only algorithm in this version. Each field that holds a `Digest` states its input |
| `Domain` | String: lowercase ASCII, internationalized labels in A-label form ([RFC 5890](https://www.rfc-editor.org/rfc/rfc5890)), with no scheme, port, path, or trailing dot | Producers MUST write this form. Consumers MUST compare byte for byte and MUST NOT normalize a value before comparing it. A value read from ads.txt or sellers.json is converted to this form before comparison |
| `RegistrableDomain` | A `Domain` that is the [Public Suffix List](https://publicsuffix.org/) registrable domain, taken over the whole list, PRIVATE section included | It names a business |
| `Side` | `buyer` \| `seller` | It says which side, never who that side is. `Party` says who |
| `ProposalStatus` | `draft` \| `published` \| `under_review` \| `agreed` \| `withdrawn` \| `expired` | A proposal's `status`, computed by § 4.3.3 |
| `LineItemStatus` | A `ProposalStatus`, or `sold_out` | A line item's `status`, moved as § 4.3.2 states |
| `ApprovalStatus` | `PENDING` \| `APPROVED` \| `REJECTED` | An approval outcome, in the spelling of OpenDirect 2.1's ChangeRequest `status` |
| `Measurer` | A `Side`, or a `RegistrableDomain` | Who counts or measures. A seller writes `seller`, never its own domain. Two values name one party only when they are equal byte for byte. A `qualifier` beside a value names a product or method of that party and is not compared |
| `EntryRef` | String: `<domain>/<collection>/<entry_id>@<version>`, with no `/` or `@` inside a part | A named entry at one exact version, whose content does not change. `<domain>` is a `Domain`. It carries no digest |
| `VocabularyTerm` | String: a bare core term, or `<domain>:<term>` with `<domain>` a `Domain` the definer controls. A term is ASCII letters, digits, `_`, and `-` | See below |
| `CalendarUnit` | `hour` \| `day` \| `week` \| `month` | A calendar bucket |
| `TimeUnit` | A `CalendarUnit`, or `flight` | `flight` is the whole of `commitment.flight` |
| `IntegerFlag` | Integer: `0` (no) \| `1` (yes) | A yes or no that another standard writes as an integer. Each field says what `1` affirms |
| `Amount` | Number | Money. It carries no currency: the field that holds it states which one it reads in |
| `Fraction` | Number from 0 to 1 | A proportion |
| `FractionDelta` | Number greater than -1 | Used only by a price delta expressed as a proportion |
| `Instant` | String: an RFC 3339 `date-time` in whole seconds, ending in `Z` | A point in time. One written form, so one instant has one digest input |
| `Duration` | String: the ISO 8601 grammar of RFC 3339 Appendix A without its week form (`P14D`, not `P2W`) | A length of time. A comparison names its anchor. A length within the playback of an ad or a placement, such as a play, view, read, loop, slot, or refresh, is instead an Integer whose key ends `_s` or `_ms`, except a key imported from another standard, which keeps its spelling (§ 2.6) |
| `IanaZone` | String: a name in the [IANA time zone database](https://www.iana.org/time-zones), such as `America/New_York` or `UTC` | A time zone |
| `ZoneName` | An `IanaZone`, or `viewer_local` | `viewer_local` is where the ad renders |
| `Url` | String: an absolute `http` or `https` URL ([RFC 3986](https://www.rfc-editor.org/rfc/rfc3986)) | A location a client can fetch |
| `FieldPointer` | String: a JSON Pointer ([RFC 6901](https://www.rfc-editor.org/rfc/rfc6901)) | A location in the object this specification defines |
| `Ext` | `Map[Domain, Object]` | The extension container. § 2.5 states its rules |

**`VocabularyTerm` rules.** A field that takes a `VocabularyTerm` lists its core
terms. Anyone MAY define an extension term. Terms compare byte for byte. A
published meaning never changes; a changed meaning takes a new term. IAB Tech Lab
keeps core lists apart from the schema, so a new core term needs no schema change.
A receiver that doesn't know a term treats the option or entry that holds it as
unavailable. A term in an `Array[VocabularyTerm]` is not an entry of its own: it
belongs to the option or entry that holds the array. Where the term binds outside
any option or entry, the receiver skips the line item and doesn't reject the
proposal because of it. For a `channel` (§ 5.1.1) or `cost_method` (§ 5.6) term,
these effects are a MUST. A receiver never assents to what it can't read. A field MAY
state another effect.

**`DocumentRef`** pins a binding document. The object is open, so its publisher can
add a version or a date. It is never inlined. The publisher keeps every version
retrievable, and the counterparty stores a copy.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `url` | Url | REQUIRED | The document. It MAY need authentication |
| `digest` | Digest | REQUIRED | Over the exact bytes served, with no content coding |

**`VersionRef`** locates an offer at a version. It carries no digest. A `proposal_id`
is unique only within a `seller.domain` (§ 4.1): a `VersionRef` inside a proposal
resolves against that proposal's `seller`, and a system that holds one outside a
proposal keeps the `seller.domain` beside it.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `proposal_id` | String | REQUIRED | The proposal |
| `version` | Integer | REQUIRED | The proposal's `version` |
| `line_item_id` | String | OPTIONAL | A line item in that version |

**`Party`** names a legal party. `domain` is the identifier, and `registry_id` is
an attestation. An absent or unresolvable `registry_id` MUST NOT make a document
malformed, and a consumer MUST ignore a resolved entry whose verified domain is
not `domain`. The Agent Registry defines its reference format and how it exposes the
verified domain.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `domain` | RegistrableDomain | REQUIRED | The party's domain |
| `legal_name` | String | OPTIONAL | The party's legal name. A `registry_id` entry that applies can attest it; the value alone attests nothing |
| `registry_id` | String | OPTIONAL | An IAB Tech Lab Agent Registry reference for the entity controlling `domain` |

**`SeatRef`** names a buyer's seats. A seat always travels with its DSP.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `dsp` | RegistrableDomain | REQUIRED | The DSP's primary domain |
| `ids[]` | Array[String] | OPTIONAL | The ids the DSP issues, the same values OpenRTB 2.6 carries in `Deal.wseat` |

**`TaxonomyCodes`** holds codes in one taxonomy. Each field that holds it names the
list `taxonomy` comes from and whether an id covers its descendants.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `taxonomy` | Integer | REQUIRED | A value from the list the field names |
| `ids[]` | Array[String] | REQUIRED | Ids in that taxonomy |

**`Interval`** is an absolute window, with `end` later than `start`.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `start` | Instant | REQUIRED | The first second |
| `end` | Instant | REQUIRED | The last second, inclusive |

**`Range`** bounds a value of type `T`, written `Range[T]`. At least one bound is
present, and `min` is no greater than `max`.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `min` | T | OPTIONAL | The lower bound |
| `max` | T | OPTIONAL | The upper bound |

### 2.3 Publication

A seller MAY publish `https://<seller.domain>/.well-known/openproposal.json`, a
`ProposalManifest`.

**`ProposalManifest`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `generated_at` | Instant | REQUIRED | When the seller generated the file |
| `spec_version` | String | REQUIRED | The version of this specification the file follows |
| `proposals[]` | Array[ManifestEntry] | REQUIRED | One per listed proposal |

**`ManifestEntry`** holds the keys of `ProposalSummary` (§ 2.1) and this one:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `full_url` | Url | REQUIRED | Where the second phase fetches the Full Representation |

- At least one of `ETag` and `Last-Modified` is REQUIRED, so buyers can poll cheaply.
  § 8 asks whether both are.
- Only shared proposals (§ 4.3) appear, and within them only line items whose
  `visibility` (§ 5.8) is `public` and whose `status` is `published`.
  `registry_gated` and `named` line items do not.
- A buyer discards an entry whose `seller.domain` differs from the domain in the
  URL it requested, before any redirect.
- `full_url` returns only what the requester may read (§ 5.8), so a request with
  no authenticated identity gets only `public` line items.
- Manifest entries MUST match the current version of each proposal. A stale
  entry is a seller error.

Two-phase flow:

1. **Discover:** fetch the manifest and screen the summaries. No language model
   is required.
2. **Propose:** fetch the Full Representation of shortlisted line items from
   `full_url`. Asks, holds, and commits run on a proposal issued to the buyer
   (§ 4.3).

### 2.4 Errors

A party that rejects a request MUST return `errors[]`, one or more
`ErrorObject`s. This specification defines the object. The binding that carries
the request carries the errors.

A seller's decline of a resolved `commitment`, or of a hold, answers a valid
request and is not an error. What a party answers when request authentication
fails is the AAMP agent identity and signing profile's to state.

**`ErrorObject`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `code` | VocabularyTerm | REQUIRED | A core code (below) or an extension code |
| `detail` | String | REQUIRED | Human-readable. A receiver SHOULD NOT parse it |
| `pointer` | FieldPointer | OPTIONAL | Into the object this specification defines that the request carries, to the value that caused the error |
| `version` | Integer | REQUIRED when the request names a proposal the requester may read | The proposal's `version` when the error was decided |
| `retry` | Enum | REQUIRED | `same` \| `refetch` \| `none`. `same`: the same request can succeed later. `refetch`: a new attempt, composed on the current `version`, can succeed. `none`: only a changed request can succeed. On a commitment attempt, `same` keeps the `idempotency_key` and such an error is not a stored result (§ 5.6.1), and `refetch` and `none` take a new `idempotency_key` |

Core codes: `validation` \| `not_found` \| `not_offered` \| `unresolved_reference` \|
`not_committable` \| `stale_version` \| `expired` \| `idempotency_conflict` \|
`not_eligible` \| `record_mismatch`.

| `code` | Returned when |
| :--- | :--- |
| `validation` | A value breaks a rule of this specification and no other code applies |
| `not_found` | A named proposal or line item does not exist, or the requester may not read it (§ 5.8) |
| `not_offered` | A buyer value is outside what the seller declared (§ 3.1, § 3.2, § 4.3.2, § 5.5) |
| `unresolved_reference` | A `DocumentRef` (§ 2.2) does not resolve, or its content does not match its `digest` |
| `not_committable` | A line item's `status` rules out an ask (§ 4.3.2), a `requires` that is unmet rules out a `commit` (§ 5.6.3), or a seller rejects a `commit` before `offer_window.start` (§ 5.6.1) |
| `stale_version` | An ask is stale (§ 4.1.3) |
| `expired` | `offer_window.end` or `price_valid_until` has passed |
| `idempotency_conflict` | An `idempotency_key` is reused with a different body |
| `not_eligible` | The buyer or the sender fails an eligibility or authority check the seller applies (§ 5.8) |
| `record_mismatch` | A `record_digest` in the request does not equal the one the receiver recomputes (§ 4.1.1) |

An `ErrorObject` is open. A receiver that does not recognize a code, or a key of
the object, acts on `retry`.

Informative: over HTTP, `validation`, `not_offered`, and
`unresolved_reference` fit 400 Bad Request; `not_eligible` 403 Forbidden;
`not_found` 404 Not Found; `not_committable`, `stale_version`, and
`record_mismatch` 409 Conflict; `expired` 410 Gone; `idempotency_conflict` 422
Unprocessable Content. An error with `retry: same` fits 503 Service Unavailable.

### 2.5 Extensions

The proposal and each line item MAY carry
`ext`, an `Ext`. Each key MUST be a `Domain` that its owner controls, and each value
is an object that the owner defines. A seller's own entries MUST use its
`seller.domain` as the key.

```yaml
ext:
  examplepub.example: { placement_code: "BD-ROS-300x250-Q4" }
```

- An `ext` entry MUST NOT change the meaning of a field this specification
  defines. A term the counterparty must understand to transact MUST NOT be an
  `ext` entry; it is a field or a vocabulary term.
- A receiver MUST ignore an `ext` entry it does not understand, and MUST NOT
  reject a document because of it. It MUST keep `ext` unchanged when it
  stores or forwards the document.
- In an object whose keys this specification lists, a key outside `ext` that
  it does not list is invalid. The open objects `DocumentRef` (§ 2.2) and
  `ErrorObject` (§ 2.4) are unaffected.
- On the proposal and a line item, `ext` is part of the Full Representation and
  of the record frozen at `agreed` (§ 4.1.1), and a seller change to it is a
  revision.
- Apart from an unknown term (§ 2.2), a receiver MAY skip a whole line item it
  cannot read, without assenting to it. It MUST NOT keep a line item after removing
  fields from it.

### 2.6 Table and naming conventions

**Tables.** A field table has the columns Field, Type, Required, Mutability, and
Description. A key table has the columns Key, Type, Required, and Meaning, and MAY
add a last column that names a source standard. The key table of a `mixed` field adds
Mutability as its last column. A row names one key, and a key that holds an array ends
`[]`.

A value table has one row per value of a list. Its first header cell is the code name
of the key that holds the list. Its first column equals the list, so it defines no
second one, unless the text names the table as the list. The § 2.2 table has one row
per shared type. A Form that adds a value to a type reads ``A `T`, or `b` ``, and one
that adds a second type reads ``A `T`, or a `U` ``. The § 3 table
has one row per marker. Any other table states rules as prose does, and defines no
key, type, or list.

**Presence.** A Required cell is `REQUIRED`, `OPTIONAL`, `RECOMMENDED`, or `REQUIRED
when <condition>`. Presence is relative to the object that holds the key, and a row
that narrows a shared type (§ 2.2) may require a key of it. A key that must be absent
under a condition says so in its Meaning or Description. A lead-in may limit its
table's keys instead, with `holds exactly one key` or `At least one <noun> is present`.

**Types.** A Type cell holds `String`, `Integer`, `Number`, `Boolean`, `Enum`,
`Object`, a shared type (§ 2.2), a type its section names, or a named key table.
`Array[T]`, `Map[K, V]`, `Range[T]`, `Selectable[T]` (§ 3.1), and `Settable[T]`
(§ 3.2) take other types. `T`, `K`, and `V` stand for a type's arguments, and a Type
cell inside that type's table may name them. `Enum` is a closed list of strings,
written in the row that uses it, and a generic never takes it: a list a generic takes
has a name. A closed list of integers written in a row has Type `Integer`. `Object`
holds keys that another definition sets. A lead-in that reads "`X` holds the keys of
`Y`" gives `X` every key of `Y`, with the rules `Y` states on them, and the rows of its
own table. The keys sit flat in `X`, and `X` doesn't repeat them. `Y` may take a type,
such as `Range[T]`. A lead-in that adds "each `<marker>`" gives the composed keys that
marker. A lead-in that reads "`X` lists these paths" is followed by a `text` block with
one path per line. The first segment of a path is a key of `X`, and later segments nest
as they do in the object `X` is a subset of. A segment written `<name>` stands for what
the lead-in says. A key table led in by "`X` adds this key" or "`X` adds these keys"
follows that block and gives `X` those keys beside the listed paths.

**Value lists.** A list is written once, as `` `a` \| `b` ``, or `` `a` `` alone when it
has one value, or as the first column of a value table the text names as the list.
Other mentions point to it. A `VocabularyTerm` field says so and lists its core terms,
or points to other lists, whole or in part, and adds any others;
every other list is closed, and in a row it opens the Meaning cell.

**Keys.** Every key is snake_case, except in an object that a section copies from
another standard and says so; that object keeps the standard's spelling and cites
it. A key name repeats only where it means the same thing, and each row's Type cell
states its form there. An array named by a noun is plural, except the mass nouns
`pricing[]` and `negotiation_history[]`, and a name another standard spells. A name
that isn't a noun keeps its form, such as `available[]`, `best_for[]`, and `all_of[]`.
The suffix `_ref` is reserved for `DocumentRef` and `EntryRef`. A Boolean flag may end
`_allowed` or `_required`, and a list never does.

**Values.** Every term compares byte for byte. A list this specification owns is
lower snake case. A list taken from another standard keeps that standard's spelling
and names it. A list built on another standard's list follows its case and names it:
`cost_method` is upper case, like OpenDirect 2.1 `Line.ratetype`.

**Yes or no.** A key from another standard keeps that standard's values, as
`IntegerFlag` does. Every other flag is a Boolean.

**Nothing.** `none` is a value only where it has its own meaning or the key is
required. Otherwise, absence means none.

**Paths.** Prose names a field by its full table path, such as
`properties.available[].domains[]`. The key alone is enough in the section that
holds its table, beside the object it belongs to, or beside a reference to that
section. A value that points into a document is a `FieldPointer`.

### 2.7 Security considerations

This section is informative. It sets no requirement on a party to a transaction.

**Text is data.** Agents that can spend read this object, and much of it is text
the counterparty wrote: `description`, `specifications`, `best_for[]`,
`not_suitable_for[]`, `seasonality_notes`, `approval`, `creative_policy`, `ext` values,
an error's `detail`, and the document behind a
`DocumentRef`. That text is data, and it can hold instructions aimed at a language
model. An agent keeps it apart from its own instructions, and rests a decision to
assent or spend on the structured fields, not on prose alone.

**URLs.** A document names URLs its author chose: `proposals[].full_url`,
a `DocumentRef`'s `url`, an `Asset`'s `url`, and a `CreativeDelivery`'s `endpoint`. Fetching one lets the
author choose where a client connects. A client uses `https`, bounds the size of a
response and the number of redirects, and refuses an address inside its own
network, on every redirect as well. § 5.4.1 covers what inspecting a creative may
request.

**Digests.** A `digest` shows that the bytes are the ones a `DocumentRef` names. It
does not show who wrote them, or that they are safe to act on. A client compares
it before reading the bytes, and `unresolved_reference` (§ 2.4) reports a mismatch.

**Buyer lists.** `exclusions`, `buyer_supplied.segments[]`, and
`buyer_supplied.suppression_list` show a buyer's strategy and can hold data about
people. A party that holds them limits who can read them, in stored records and
logs as well as in responses. § 5.8 states the disclosure rule for `exclusions`.

---

## 3. Field mutability

Every field carries exactly one marker.

| Marker | Meaning |
| :--- | :--- |
| `immutable` | Set once at creation. Neither party may change it. |
| `seller-set` | The seller sets it and MAY revise it while the `status` of the object that carries it is `draft`, `published` or `under_review`. § 4.3.2 states what a revision does to a line item `under_review`. The buyer cannot change it directly. |
| `selectable` | The buyer chooses from a seller-declared set. Each option MAY carry a price delta. Resolves without a round trip. |
| `settable` | The buyer supplies a value within seller-declared bounds. Resolves without a round trip. |
| `supplied` | The buyer provides data or an artifact. The seller does not pre-populate it. |
| `requestable` | The buyer MAY ask for a value outside the declared space. Requires explicit seller assent. |
| `derived` | Computed by a rule this specification states. Neither party sets it directly. |
| `lifecycle` | Live state of the object. The party its section names moves it between the stated values. Not a term. |
| `recorded` | Written by the party that acted. Append-only: an entry is never edited or removed. Not a term. |
| `asserted` | The seller states it from data the buyer can't recompute. Not a term, and it changes without a new version. |
| `mixed` | The keys of the object carry different markers: in the Mutability column of its key table, in its lead-in for composed keys, or on its rows for `pricing[]`. |

**Whose `status`.** The proposal's (§ 4.1) for a field defined in § 4; the line
item's (§ 5.1) for a field defined in § 5, including `seller-set` sub-fields of
a `mixed` field (`pricing[]`, `buyer_requirements`) and a field treated as
`seller-set` under § 3.1 or § 3.2.

§ 4.3, not the `seller-set` revision rule, governs the seller's answer to a `requestable` ask.

**Resolution without a round trip.** `selectable`, `settable` and `supplied`
fields MUST resolve without a round trip — everything needed to validate and
price them is declared in the proposal. Only `requestable` fields require the
counterparty to respond.

Resolution is validation and pricing, not acceptance. A resolved `commitment` is
an offer to buy (§ 5.6.1).

A field is never silently reverted. An unset `selectable` or `settable` field
takes its declared `included[]` or default, and that default MUST be explicit in
the proposal.

### 3.1 Selectable structure

Every field marked `selectable` is a `Selectable[T]`, where `T` is the option type.

**`Selectable`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `available[]` | Array[T] | REQUIRED | The options the seller offers |
| `included[]` | Array[String] | REQUIRED | Which options are in the base rate. MAY be empty |
| `deltas` | Map[String, Delta] | OPTIONAL | Delta per option beyond those included, keyed by option: one of `delta_cpm`, `delta_flat`, or `delta_pct` |
| `max_select` | Integer | OPTIONAL | Cap on how many options the buyer may choose |

A field marked `selectable` that carries a bare value and no `available[]` MUST
be treated as `seller-set`.

### 3.2 Settable bounds

Every field marked `settable` is a `Settable[T]` and MUST declare its bounds:
either `allowed[]` (an enumerated set) or `min` / `max` (a numeric or date range).
`frequency_cap` declares its bounds in `count`, and `commitment` within
`commitment_bounds` (§ 5.6).

A field marked `settable` that carries a bare value and no bounds MUST be
treated as `seller-set`.

### 3.3 Re-computation

Because audiences, properties, formats and, where it is selectable, `geo` are
`selectable`, and buyer `exclusions` (§ 5.5) narrow delivery, `addressable_scale` and `availability`
MUST be recomputed against the buyer's actual selection and exclusions. A
single declared figure is correct only for the default composition.

---

## 4. Proposal

The proposal establishes identity, lifespan, negotiation state and the
merchandising case for the line items beneath it. Nothing here is a commercial
commitment, and nothing here is channel-specific — that all lives on the line
items.

### 4.1 Identity and lifecycle

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `proposal_id` | String | REQUIRED | immutable | Identifies the proposal. Unique within `seller.domain` |
| `version` | Integer | REQUIRED | derived | Monotonically increasing revision number, starting at 1, held by the seller. Each version is a snapshot of the proposal's offered terms (§ 4.1.3). A version is frozen at the earliest of: the proposal's `status` leaving `draft`; a `negotiation_history[]` entry or a `commitment` naming it; a counterparty receiving it in any representation (§ 2.1). The offered terms of a frozen version MUST NOT change; a change to them creates version `n+1`. The values § 4.1.3 lists as not offered terms change without a new version |
| `spec_version` | String | REQUIRED | seller-set | The version of this specification the document follows, such as `3.0` |
| `seller` | Party | REQUIRED | immutable | The selling entity. `seller.domain` is the seller's identifier for all purposes, including `assent[]`. `legal_name` is REQUIRED here |
| `buyer` | Party | REQUIRED when `type` is `custom` or `assent[]` is present | immutable | The entity that assents, usually the agency. Its presence makes the proposal issued to that buyer (§ 4.3). Whom the spend is for is `commitment.advertisers[]` (§ 5.6.1), and whether the buyer may bind that advertiser is authorization (§ 1.2). `legal_name` is REQUIRED here |
| `type` | Enum | REQUIRED | immutable | `standard` \| `custom` |
| `proposal_template_id` | String | OPTIONAL | immutable | Links a proposal to the seller's template. Opaque to buyers; used for the seller's reporting |
| `issued_from` | VersionRef | OPTIONAL | immutable | The shared proposal and version an issued proposal was made from (§ 4.3). A pointer: nothing is inherited through it |
| `status` | ProposalStatus | REQUIRED | derived | Computed from the line items (§ 4.3.3) |
| `record_digest` | Digest | OPTIONAL | derived | Of the binding record of this document over every line item it contains (§ 4.1.1). Either party MUST be able to recompute it from the document alone. Verifiable only against the Full Representation; a Summary Representation or manifest entry MAY carry it as a pointer |
| `assent[]` | Array[AssentEntry] | OPTIONAL | recorded | Assent entries. Each entry is written whole by the party its `role` implies, is immutable once written, and MUST NOT be altered or removed by the other party. Entry: `{ role: commitment \| acceptance, version, record_digest, line_item_ids[], signed_at, signer, signature }`. See § 4.1.2. The form of `signer`, the signature container, key discovery and agent authentication are defined by the AAMP agent identity and signing profile, not by this specification |
| `offer_window` | Interval | OPTIONAL | seller-set | The window the offer holds: it does not hold before `start` or after `end`. **This is the offer window, not the campaign flight** |
| `brief_id` | String | REQUIRED when `type` is `custom` | immutable | The buyer's brief this proposal answers |
| `negotiation_history[]` | Array[HistoryEntry] | REQUIRED when the current `version` is frozen (§ 4.1.3) | recorded | Ordered, append-only. Entries MUST NOT be edited or removed. A commit and its acceptance are in `assent[]`, not here |
| `line_items[]` | Array[LineItem] | REQUIRED | seller-set | The line items (§ 5), in the order the seller wrote them |
| `linked_execution` | Enum | OPTIONAL | seller-set | `all`. Every `line_item_id` the version carries is committed together, as though each line item's `requires.all_of[]` named the others (§ 5.6.3). Absent, the proposal is subsettable (§ 2) |
| `ext` | Ext | OPTIONAL | seller-set | See Extensions (§ 2.5) |

**`HistoryEntry`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `version` | Integer | REQUIRED | The version the act created or refers to (§ 4.1.3) |
| `actor` | Side | REQUIRED | The side that acted |
| `action` | Enum | REQUIRED | `published` \| `requested` \| `granted` \| `countered` \| `declined` \| `withdrawn`. § 4.3.1 says which interaction writes each |
| `paths[]` | Array[HistoryPath] | REQUIRED | The fields the act changed or asked about. MAY be empty |
| `at` | Instant | REQUIRED | When the side acted |

**`HistoryPath`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `line_item_id` | String | REQUIRED when `requested_value` is present | The line item. When absent, `pointer` is into the proposal |
| `pointer` | FieldPointer | REQUIRED | Into that line item or the proposal |
| `requested_value` | RequestedValue | REQUIRED when the entry's `action` is `requested` | On a `requested` entry, the value the buyer asked for. On a `declined` entry, or a buyer's `withdrawn` entry, the value of the `request` it ended. Absent on every other entry |

**`RequestedValue`** holds exactly one key: the `requestable` field `pointer` names, in the
form its row states.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `materials_due` | MaterialsDue | OPTIONAL | The line item's `materials_due` |
| `committed_metrics[]` | Array[CommittedMetric] | OPTIONAL | The line item's `committed_metrics[]` |

`proposal_template_id` MUST NOT be required for a buyer to transact. Buyers never
resolve it.

**Seller identity.** A proposal names exactly one `seller.domain`. A seller MUST
NOT name a domain it does not control. For this specification one `seller.domain`
is one seller: entities that transact under one domain are one seller here, and
`seller.legal_name` carries the legal name. A selling entity that controls several
registrable domains SHOULD use the same `seller.domain` for every proposal it
publishes as one seller; a seller that publishes proposals under several domains
holds an Agent Registry entry for each, or the entry does not apply. The field is immutable,
so a seller that moves to another domain publishes new proposals. Where a third party
hosts a seller's agent or published files, `seller.domain` is the selling
entity's own registrable domain, never the host's. Continuity of a legal entity
across domains, rebrands, or acquisitions is a fact the Agent Registry attests; this
object does not encode it. Whether to deal with a seller that has no Agent
Registry entry is buyer policy.

#### 4.1.1 Binding record and record_digest

The binding record of a document for a set of line items S is the JSON form of
that document in its Full Representation (§ 2.1), restricted to the line items in
S, with the following paths removed and no others. The paths are RFC 9535 JSONPath.
Arrays hash in document order, and no party reorders an array it did not write. The
hold's status is every `hold_status` key except `hold_available`, `hold_duration`
and `hold_scope`.

```
$.version
$.status
$.assent
$.record_digest
$.negotiation_history
$.line_items[*].status
$.line_items[*].availability
$.line_items[*].addressable_scale
$.line_items[*].assets
$.line_items[*].buyer_supplied.match_rate_expected
$.line_items[*].pricing[*].seller_rate
$.line_items[*].pricing[*].floor
$.line_items[*].hold_status.*, except hold_available, hold_duration and hold_scope
$.line_items[*].commitment.version
$.line_items[*].commitment.idempotency_key
$.line_items[*].commitment.derived_units
$.line_items[*].deal_id_issuance
$.line_items[*].external_references
$.line_items[*].correlation_id
```

Each removed path is one of three things: lifecycle state or sequence position
(`version`, `status`, `assent[]`, `record_digest`, `negotiation_history[]`, the
hold's status, `commitment.version`, `idempotency_key`); a seller assertion, an
informative figure, or an identifier minted downstream of agreement
(`availability`, `addressable_scale`, `match_rate_expected`, `derived_units`,
`deal_id_issuance`, `external_references[]`, `correlation_id`); or a value that
is not a term of the agreement: the seller's own figures (`seller_rate`,
`floor`; the transacted rate is `agreed_rate`) and buyer artifacts delivered
after agreement (`assets[]`). The requirement on creative (`formats`, `specs`,
`creative_policy`, `materials_due`) is a term.

Every other value is inside the record: `seller`, `buyer`, and `issued_from`; every
`seller-set` field, including prose (`description`, `specifications`, `content_detail`,
`creative_policy`, `specs`); every option space (`available[]`, `included[]`, `deltas`,
`max_select`, `allowed[]`, `min` / `max`); every value the buyer writes under
§ 3 (selections, `settable` values, `commitment`, data under `supplied` fields
other than `assets[]`, any resolved `requestable` ask); `pricing[].agreed_rate`;
and `hold_available`, `hold_duration`, `hold_scope`.

**Digest input.** The record is computed over the composed record as the parties
exchange it: the Full Representation of `version` as the seller published it to
this buyer, with the buyer's § 3 writes applied. Each party computes it over the
document it transmits or receives, never over its internal store; a value
present in a store but absent from the exchanged document is, by construction,
not a term. A `derived` value inside the record is computed by the rule this
specification states for it; where no rule exists, the two parties' digests
differ and the line item is not agreed.

**Canonical form.** The digest input is the RFC 8785 (JSON Canonicalization
Scheme) serialization of the binding record, encoded as UTF-8. This
specification names no wire format; for this section JSON is the data model, and
a document carried as YAML is converted to JSON under the YAML 1.2 core schema
before canonicalization. A document whose JSON form contains duplicate object
keys is invalid. Strings, timestamps included, are hashed as written; a party
MUST NOT reformat a value it did not write. Numbers serialize as RFC 8785
§ 3.2.2.3 prescribes (IEEE-754 double precision, shortest round-trip form). A
producer MUST NOT write a Number that this serialization does not reproduce as
the decimal value written; a Number with at most 15 significant digits inside
the range of a double always does, and a document containing one that does not
is invalid for this section. `24.00` and `24` are the same value.

`record_digest` is the `Digest` (§ 2.2) of the digest input.

**Two values.** On a shared proposal no buyer-written value is present, and
the digest identifies the offered terms of that version: what a cache or a
manifest entry compares. On a composed record the
buyer's writes are present, and the digest identifies what this buyer and the
seller agree to. An `assent[]` entry always carries the second. A shared proposal
carries no `assent[]`.

A receiving party MUST recompute `record_digest` and compare it byte-for-byte
before relying on any `assent[]` entry. A `record_digest` asserted in a document
is a convenience, not evidence.

#### 4.1.2 Assent

- `assent[]` is carried on the composed record exchanged between one buyer and
  the seller. A proposal MAY carry any number of entries. A line item MUST NOT
  be named by more than one live buyer `commitment` entry, nor by more than one
  live seller `acceptance` entry. An entry is live until it is void or replaced
  under the following rules.
- The parties are the record's `seller` and `buyer` (§ 4.1). `role` names what
  the entry does, and it implies the party. `role: commitment` is written by the
  buyer. Its `line_item_ids[]` MUST be non-empty, MUST name line items whose
  `commitment` object (§ 5.6.1) is populated in the record, and on their own MUST
  meet linked execution and each named line item's `requires` (§ 5.6.3).
  `role: acceptance` is written by the seller and names the `version`,
  `record_digest` and `line_item_ids[]` the seller accepts. Neither entry refers
  to the other, and the order in which they are written is not constrained.
- `record_digest` in an entry is the digest of the binding record for the line
  items in that entry's `line_item_ids[]` (§ 4.1.1). It equals the
  document-level `record_digest` when the document contains exactly those line
  items. `version` in an entry is the `version` of the record the digest was
  computed over; because `version` is outside the binding record, the entry
  binds it explicitly.
- The line items of a buyer `commitment` entry are `agreed` when, and only when,
  `assent[]` contains a live seller `acceptance` entry with equal `version`,
  equal `record_digest` and equal `line_item_ids[]`, and both signatures verify
  under the AAMP agent identity and signing profile. `line_item_ids[]` compare as
  sets. Equal digests already imply
  equal line item sets; the explicit condition rules out partial acceptance. A
  line item for which no such pair exists is not agreed, whatever its `status`
  says.
- A seller MUST NOT write an `acceptance` entry after the proposal's
  `offer_window.end`, nor for a `commitment` entry it receives after the
  `price_valid_until` of the committed `pricing[]` entry of any line item the
  `commitment` entry names.
  Such a `commitment` entry is void, and so is one unmatched when `offer_window.end`
  passes. A `negotiation_history[]` entry at the same `version` with
  `actor: buyer, action: withdrawn` or `actor: seller, action: declined`,
  written after the `commitment` entry, also voids it. A void entry stays in
  `assent[]`, does not count toward `agreed`, and the line items it names MAY
  appear in a new `commitment` entry.
- A later entry from the same party whose `version`, `record_digest` and
  `line_item_ids[]` equal those of one of its live entries replaces that entry
  (a retry after a lost response). A later entry from the same party that names
  a line item already in one of its live entries but differs in any of the three
  is invalid, and the earlier entry stands.
- The signing input of an entry is the RFC 8785 serialization of the entry with
  `signature` removed. `signature` is a detached signature over that input in
  the container the AAMP agent identity and signing profile defines, carrying
  the key identifier and algorithm. `signer` identifies the agent that signed;
  if the container also names the signer, that name MUST equal `signer`. The
  form of `signer`, the container and algorithms, key resolution, and how
  `signer` is bound to the party `role` implies are defined by the profile.
  This specification requires of the profile only that (a) verification needs
  only the stored record and key material the signer has published, or a
  retained copy of it, and MUST NOT require an interactive request to the
  counterparty or a registry lookup; (b) the signature is bound to this artifact
  type, so an assent signature cannot be presented as a signature over any other
  AAMP artifact; and (c) a signature remains verifiable for the life of the
  agreement, including after the signing key is rotated.
- Transitional rule. Until the profile is published, `signer` and `signature`
  MAY be absent. An entry without them is an unsigned assent record whose
  authenticity rests on the authenticated channel it arrived over, and the
  `agreed` rule applies without the signature condition.
- Adding an `assent[]` entry does not change `version`.
- `agreed` is terminal for a line item. Every `seller-set`, `selectable`,
  `settable`, and `requestable` value of it and its `pricing[].agreed_rate` MUST
  remain as in the version `assent[]` names. A later version of the proposal does
  not touch the agreed record: a party verifies an entry over the version it
  names (§ 4.1.3), not the current one. A change to a value inside the record is
  applied outside it, in the downstream standard the line item lands in (§ 1.1),
  against the agreed record as its baseline.

#### 4.1.3 Offered terms and versions

**Offered terms.** The offered terms of a version are every value the seller
writes: `immutable` and `seller-set` fields; the seller-declared structure of
`selectable`, `settable` and `requestable` fields (`available[]`, `included[]`,
`deltas`, `max_select`, `allowed[]`, `min`, `max`, declared defaults and
ceilings); and the set of `line_item_id`s the version carries. The following
are not offered terms and MAY change without a new version: `status` (proposal
and line item), `assent[]`, `negotiation_history[]`, `availability`,
`addressable_scale`, the hold's status (every `hold_status` key except
`hold_available`, `hold_duration` and `hold_scope`, which offer the hold),
`deal_id_issuance`, `external_references[]`, `correlation_id`,
`assets[].approval_status`; `pricing[].seller_rate`, which is what the publisher
receives and not a term offered to the buyer; every value the buyer writes
(`supplied` fields, `commitment`, selections and values on `selectable` and
`settable` fields, and a `requestable` ask); and every `derived` value computed
from a buyer's writes (`pricing[].agreed_rate`, `commitment.derived_units`). A
buyer composes against a named `version` and never increments it.

**Freezing.** A seller MAY edit a proposal in place only while its current
version is not yet frozen (§ 4.1). Two representations of the same
`(proposal_id, version)` whose offered terms differ, compared on the fields and line
items both carry, are non-conformant. A line item that
appears in a frozen version MUST NOT be removed from the proposal; it leaves the
shelf by its `status` (§ 5.1), which is a lifecycle change. Adding a line item
changes the offered terms.

**Versions.** Each change to the offered terms of a frozen version MUST create
version `n+1` and MUST append exactly one `negotiation_history[]` entry carrying
that `version`, with `actor: seller` and `paths[]` naming every offered-terms
field whose value differs from version `n`. Its `action` is one of
the following:

- `published` for version 1, appended no later than the moment version 1 is
  frozen, and for a change the seller makes on its own initiative, including a
  change to `seller-set` prose.
- `granted` or `countered` for a change that answers a buyer's `requestable`
  ask: `granted` puts the requested value into force, `countered` puts a different
  value into force in its place.

Only the seller changes offered terms, so only these entries create versions.
Every other entry (`requested`, `declined`, `withdrawn`) carries the version it
refers to.

**Staleness.** An ask or a hold is on a `version`. It is *stale* when the binding
record (§ 4.1.1) for the line items it names, with any buyer writes applied,
differs between that `version` and the current one. `version` is outside the
record, so a revision that touches only another line item does not make it stale,
and a change to a proposal-level term does. Under `linked_execution: all`, a change
to the set of `line_item_id`s also makes it stale. The seller computes the test
from the versions it retains, and no digest is published for it. For a `commit`,
the seller recomputes `record_digest` over the line items as they stand plus the
buyer's writes. A value equal to the one in the buyer's `assent[]` entry means the
seller MAY accept, at the `version` that entry names.

**Retention.** A seller MUST keep every version that a `negotiation_history[]`
entry, a `commitment` or an `assent[]` entry names retrievable by
`(proposal_id, version)` for as long as the proposal is retrievable. This
specification does not define how a party fetches a version.

### 4.2 Agent comprehension

The case a buying agent reads to decide whether to look further.

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `description` | String | REQUIRED | seller-set | Prose, not a name. Where the "why buy" case is made, including which channels a multi-channel proposal spans |
| `specifications` | String | OPTIONAL | seller-set | Detail at media-kit depth |
| `best_for[]` | Array[String] | OPTIONAL | seller-set | Advisory planning hints. Non-normative, and never the basis for a match |
| `not_suitable_for[]` | Array[String] | OPTIONAL | seller-set | Advisory exclusion guidance. Non-normative |
| `seasonality_notes` | String | OPTIONAL | seller-set | When the proposal performs differently |

### 4.3 Lifecycle

**Shared and issued.** A proposal with no `buyer` is *shared*. A proposal with a
`buyer` is *issued* to that buyer. The seller creates one with `publish`: a new
`proposal_id`, version 1, `buyer`, and, when it is made from a shared proposal,
`issued_from`. A `custom` proposal is issued from the start. `buyer` is immutable,
so every later version stays with that buyer. Each issued proposal has an
independent `status`, `version` and `negotiation_history[]`.

A buyer that wants an issued proposal sends, over the binding, the ask, hold, or commit
it would make, naming the shared proposal and `version` it read, or a brief. A seller
that issues one answers with `publish`, and the buyer sends its ask, hold, or commit
against the new `proposal_id`.

Asks, `under_review`, holds, and assent live on a proposal issued to one buyer; a
shared proposal, or any other record more than one buyer can read (§ 5.8), carries
none of them.

**Asks.** A buyer `request` (`requestable`, not `hold_status`) or `commit`
(§ 5.6.1) is an *ask*: it names a `version` and stays *open* until answered or
withdrawn, or until it goes stale (§ 4.1.3) or void (§ 4.3.2, § 4.3.4). A `commit` is one
act: the buyer's `assent[]` entry and the `commitment` of each line item that entry
names. A `request` is identified by its `line_item_id`, `pointer`, and `requested_value`
(§ 4.1). Two equal ones are one ask while that ask is open, and an equal `request` after
it ends is a new ask. Holds change neither `status` nor `negotiation_history[]`.

#### 4.3.1 Interactions

| Interaction | Actor | Effect; history `action` |
| :--- | :--- | :--- |
| `publish` | seller | version 1 of a new or `draft` proposal, or the next `version` for a change to offered terms (§ 4.1.3); `published`. Moving a `draft` line item in a frozen version: neither (§ 4.3.2) |
| `request` | buyer | asks a `requestable` value on one line item against a named `version`, stated as a `HistoryPath` (§ 4.1) with `requested_value`; `requested` |
| `grant` | seller | of a `request`: new `version` with the requested value in force as an offered term; `granted` |
| `counter` | seller | of a `request`: new `version` with another value; `countered` |
| `decline` | seller | no new `version`; `declined` |
| `commit` | buyer | `commitment` (§ 5.6.1) pinned to `version`, with the buyer's `assent[]` entry; no entry |
| `accept` | seller | of a `commit`: the seller's `assent[]` entry, no new `version`; no entry |
| `withdraw` | seller: line item or proposal; buyer: its own ask | `withdrawn`. A seller's is one entry. For each line item it moved to `withdrawn`, its `paths[]` holds a `HistoryPath` with that `line_item_id` and the `pointer` `/status` |
| hold request, grant, decline, release | buyer; seller; seller; buyer, or seller on a revision (rule 2) | `hold_status` only; no entry |

A buyer that turns down an offer, including a counter, takes no action and leaves no entry.

#### 4.3.2 Line-item status transitions

A line item moves between `status` values as follows. These transitions are
exhaustive, so a status with none leading out of it is terminal.

- `draft` → `draft` at a new `version`: seller `publish`.
- `draft` → `published`: seller `publish`. In a frozen version this changes only `status`,
  so it makes no new `version` and no entry (§ 4.1.3).
- `draft` → `withdrawn`: seller.
- `published` → `published` at a new `version`: seller `publish`.
- `published` → `under_review`: buyer ask.
- `under_review` → `under_review`: another buyer ask, a seller or buyer act that
  ends one ask while another stays open, or a seller `publish` that makes no open
  ask stale.
- `under_review` → `published`: the last open ask ends by seller `grant`,
  `counter`, or `decline`, by buyer `withdraw`, or by going stale on a new
  `version` (rule 2).
- `under_review` → `agreed`: seller `accept` of a `commit` (§ 4.1.2); open asks are void.
- `published` | `under_review` → `sold_out`: seller, never while `held`; open
  asks are void.
- `published` | `under_review` | `sold_out` → `withdrawn`: seller, never while
  `held`, nor until the latest `price_valid_until` of its `pricing[]` entries; open
  asks are void.
- `sold_out` → `published`: seller, when quantity returns, with no new `version`,
  because `availability` is not an offered term.
- `published` | `under_review` | `sold_out` → `expired`: `offer_window.end` passes
  (§ 4.3.4).

A *firm entry* is a `pricing[]` entry with a `price_valid_until`. It holds until
that date or `offer_window.end`, whichever comes first. While it holds, a seller
revision MUST NOT change that entry, and MUST NOT end it sooner by moving
`offer_window.end`. A revision that narrows who may commit (§ 5.8) does not apply,
while the entry holds, to a buyer that was eligible when the entry was first offered.
The seller of an issued proposal MUST answer a resolved `commit` under it that arrives
while the entry holds, on or after `offer_window.start`, and passes the checks of
§ 5.6.1 and any authority check the seller applies (§ 5.8): accept it, or decline it
on an allowed ground. The allowed grounds are lack of availability, an exclusivity
conflict (§ 5.6), and a ground stated in the `terms_ref` in force when the entry was
first offered. `sold_out` is lack of availability: a `commit` that arrives while the
line item is `sold_out` returns `not_committable` (§ 2.4).

Two rules apply:

1. A stale ask (§ 4.1.3) is not open and not evaluated. The seller rejects it with
   `stale_version` (§ 2.4).
2. A seller MAY revise a line item while an ask is open or a hold runs. The
   revision is a new `version` (§ 4.1.3). An ask it makes stale ends (rule 1), and
   the seller MUST release a `held` hold it makes stale or re-offer it at the new
   `version`, where `state` stays `held`. A `commit` MUST NOT carry a `requestable`
   ask: `accept` makes no new `version`, so another value takes a separate `request`.

#### 4.3.3 Proposal status

A proposal's `status` is the first of the following that applies:

1. `draft` when every line item is `draft`.
2. `under_review` when any line item is.
3. `published` when any line item is `draft`, `published` or `sold_out`.
4. `agreed` when any line item is `agreed`.
5. Otherwise `expired` when any line item is `expired`, else `withdrawn`.

A seller `withdraw` of the proposal moves to `withdrawn` every line item that
§ 4.3.2 lets the seller withdraw.

#### 4.3.4 Expiry

| Instant | Ends | Effect when passed |
| :--- | :--- | :--- |
| `offer_window.end` | the offer window | every `published`, `under_review`, or `sold_out` line item is `expired`; open asks are void |
| `pricing[].price_valid_until` | the firm entry | `status` unchanged; the seller MUST NOT accept a later `commit` under that entry, and SHOULD `publish` or `withdraw` |
| `hold_status.hold_expires_at` | the hold | `hold_status.state` becomes `expired`; `status` unchanged |

`hold_expires_at` MUST NOT exceed `offer_window.end` or the earliest
`pricing[].price_valid_until`.

---

## 5. Line items

Everything a buying agent needs to transact, per buyable unit, in exactly one
channel.

### 5.1 Identity

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `line_item_id` | String | REQUIRED | immutable | Identity within the proposal |
| `status` | LineItemStatus | REQUIRED | lifecycle | Independent of the proposal's status, so one line item may sell out while the rest of the shelf stays live |
| `channel` | MediaChannel | REQUIRED | immutable | Core terms in § 5.1.1. The discriminator for how the rest of the line item is read |
| `ext` | Ext | OPTIONAL | seller-set | See Extensions (§ 2.5) |

#### 5.1.1 channel

An impression's channel is the first row of this table that the impression
matches. Conditions are stated in
[AdCOM 1.0](https://github.com/InteractiveAdvertisingBureau/AdCOM/blob/26c59ba1b235cd8d938c9877409e506f1b8d3f0c/AdCOM%20v1.0%20FINAL.md)
terms: the
[distribution channel](https://github.com/InteractiveAdvertisingBureau/AdCOM/blob/26c59ba1b235cd8d938c9877409e506f1b8d3f0c/AdCOM%20v1.0%20FINAL.md#abstract_distributionchannel),
the ad's media
([`Placement`](https://github.com/InteractiveAdvertisingBureau/AdCOM/blob/26c59ba1b235cd8d938c9877409e506f1b8d3f0c/AdCOM%20v1.0%20FINAL.md#object_placement)
subtypes) and the
[device type](https://github.com/InteractiveAdvertisingBureau/AdCOM/blob/26c59ba1b235cd8d938c9877409e506f1b8d3f0c/AdCOM%20v1.0%20FINAL.md#list_devicetypes).
Where an impression accepts more than one medium, its media is that of the ad
served.

| `channel` | Condition |
| :--- | :--- |
| `dooh` | Distribution channel `Dooh` |
| `audio` | Audio ad (`AudioPlacement`) |
| `ctv` | Device type Connected TV (3), Connected Device (6) or Set Top Box (7) |
| `native` | Native ad (`DisplayPlacement.nativefmt`), including native ads with video assets |
| `video` | Video ad (`VideoPlacement`) |
| `display` | Any other display ad (`DisplayPlacement`) |

**`MediaChannel`** is a `VocabularyTerm` (§ 2.2) whose core terms are the rows of this
table. An impression a row matches has that row's channel, so an extension term
covers only impressions no row matches.

Device types are values of AdCOM 1.0 List: Device Types, each written as its
name followed by its code.

- The seller MUST serve a line item only on impressions of its `channel`.
  Placement type, such as interstitial or rewarded
  ([OpenRTB 2.6](https://github.com/InteractiveAdvertisingBureau/openrtb2.x/blob/1debba8001f40eb14597102dec3205afddf811d4/2.6.md#objectimp)
  `video.plcmt`, `imp.instl` and `imp.rwdd`), does not change the channel.
- Impressions in linear TV, including addressable linear, are outside this
  table: they have no core `channel` term in 3.0.

### 5.2 Inventory composition

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `properties` | Selectable[PropertyOption] | OPTIONAL | selectable | Options of `{ id, name, domains[], supported_formats[] }` |
| `content_detail` | Object | OPTIONAL | seller-set | Shows, series, sections, network verticals |
| `environments` | Selectable[Environment] | OPTIONAL | selectable | The distribution channels and device types the line item runs on. See 5.2.1. Absent: the seller promises no environment |

#### 5.2.1 environments

**`Environment`** is a value of this table. Each value is the set of (distribution
channel, device type) pairs formed from its row, in AdCOM 1.0 terms. An impression
matches the value when both its distribution channel and its device type are in the
row. Device types are as in 5.1.1.

| `environments` | Distribution channel | Device types |
| :--- | :--- | :--- |
| `web_desktop` | `Site` | Personal Computer (2) |
| `web_mobile` | `Site` | Mobile/Tablet - General (1), Phone (4), Tablet (5) |
| `app_mobile` | `App` | Mobile/Tablet - General (1), Phone (4), Tablet (5) |
| `ctv` | `Site` or `App` | Connected TV (3), Connected Device (6), Set Top Box (7) |
| `dooh` | `Dooh` | Any |

Each `environments.available[]` value MUST match at least one impression to
which 5.1.1 gives the line item's `channel`.

### 5.3 Audience reach

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `audiences` | Selectable[AudienceOption] | OPTIONAL | selectable | Options of `{ id, name, taxonomy_ref, provenance, addressable_scale }`. Their `deltas` are `delta_cpm` |
| `addressable_scale` | Integer | OPTIONAL | asserted | Reachable units in the flight, recomputed against the buyer's selection. Not segment size |
| `activation_route` | Selectable[VocabularyTerm] | OPTIONAL | selectable | Core terms: `publisher_side` \| `clean_room` \| `id_partner` |
| `buyer_supplied` | BuyerSupplied | OPTIONAL | mixed | `{ segments_allowed, suppression_allowed, match_rate_expected, segments[], suppression_list }`. `segments_allowed`, `suppression_allowed` and `match_rate_expected` are `seller-set`; `match_rate_expected` is the seller's stated expectation. `segments[]` and `suppression_list` are `supplied` |

### 5.4 Creative requirements

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `formats` | Selectable[String] | OPTIONAL | selectable | Registry format ids namespaced by channel, such as `display/300x250` and `audio/host-read-30s` |
| `specs` | Object | OPTIONAL | seller-set | As defined by the referenced format registry entry. OpenProposal does not hardcode a shape per channel |
| `third_party_tags` | Object | OPTIONAL | seller-set | Accepted wrapper types and VAST versions |
| `creative_delivery` | CreativeDelivery | OPTIONAL | seller-set | How creative reaches the seller |
| `assets[]` | Array[Asset] | OPTIONAL | mixed | Buyer-delivered |
| `materials_due` | MaterialsDue | OPTIONAL | requestable | Deadline for creative to land. A buyer MAY request a later date |
| `approval` | Object | OPTIONAL | seller-set | Review SLA and revision policy |
| `production` | Selectable[ProductionOption] | OPTIONAL | selectable | Custom units. See `ProductionOption` below |

**`MaterialsDue`** holds exactly one key:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `at` | Instant | REQUIRED when `before_start` is absent | The deadline |
| `before_start` | Duration | REQUIRED when `at` is absent | The deadline, as a length of time before `commitment.flight.start` |

**`Asset`** keys:

| Key | Type | Required | Meaning | Mutability |
| :--- | :--- | :--- | :--- | :--- |
| `asset_id` | String | REQUIRED | Identity of the asset within the line item | supplied |
| `format_id` | String | REQUIRED | The `formats.available[]` id the asset is for | supplied |
| `url` | String | REQUIRED when `markup` is absent | Where the asset is, such as a tag URL with its macros unexpanded | supplied |
| `markup` | String | REQUIRED when `url` is absent | The tag or creative markup | supplied |
| `submitted_at` | Instant | OPTIONAL | When the buyer delivered it | supplied |
| `approval_status` | ApprovalStatus | OPTIONAL | The seller's review outcome. The seller moves it | lifecycle |

**`CreativeDelivery`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `method` | VocabularyTerm | REQUIRED | Core terms: `buyer_hosted` \| `seller_hosted` \| `api` \| `platform_managed` |
| `protocol` | String | OPTIONAL | How the creative is delivered, such as a VAST version or a JavaScript tag |
| `secure_required` | Boolean | OPTIONAL | Whether the creative must load over a secure connection |
| `endpoint` | Url | OPTIONAL | Where the buyer sends creative |

**`ProductionOption`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `id` | String | REQUIRED | Option id |
| `custom_unit` | String | OPTIONAL | The custom unit built |
| `build_owner` | Side | OPTIONAL | Which side builds it |
| `lead_time` | Duration | OPTIONAL | Time the build needs |
| `cost` | Number | OPTIONAL | Cost of the build |

#### 5.4.1 Creative inspection and previews

For this section, inspection means evaluating a creative outside live campaign
delivery, including discovery, composition, submission checks and previews. A
production notification is an event report intended for a campaign's live
measurement or delivery diagnostics.

An implementation performing inspection MUST NOT send any production
notification. This includes requesting an event URL solely to check its
availability, regardless of the HTTP method used.

An implementation MAY retrieve creative documents, follow VAST wrappers and
inspect referenced media as needed for its checks. Permission to retrieve these
resources does not extend to firing their event URLs. Retrieval can itself be
logged by the resource owner; this requirement does not imply that inspection
produces no server activity.

A landing-page inspection remains subject to the same notification prohibition,
including any redirect requests. The presence of a URL in VAST `<ClickThrough>`
does not establish that requesting it is safe for inspection. The inspector
MUST NOT request a destination or redirect that sends a production notification;
it MAY use a separate inspection URL or the receiving service's documented test
mode under the conditions below.

A preview that executes creative or verification code MUST prevent that code
from sending production notifications. Synthetic events MAY be sent to test
endpoints, or through a test mode that the receiving service documents as
excluding those events from production measurement and delivery diagnostics. An
inspector's own test flag is insufficient unless the receiving service supports
it.

Inspection failures MUST be reported through diagnostics, without firing a
production VAST `<Error>` or `verificationNotExecuted` URL. An implementation
MUST NOT report a check that was skipped or could not finish as passed.

These requirements apply to inspection only. During live delivery,
implementations remain subject to the tracking and error-reporting requirements
of the applicable execution standard.

### 5.5 Targeting envelope

Each field except `time_zone`, `exclusions_accepted` and `exclusions` declares
bounds, not a value (§ 3.2). A bare value means the field is `seller-set`. For
`exclusions_accepted` and `exclusions`, the seller declares what it can
enforce, and the buyer supplies its lists. `geo` MAY instead declare the
selectable structure of § 3.1, so a line item can be priced by market.

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `geo` | Settable[String] | OPTIONAL | settable | `allowed[]` of geo codes the buyer may select within. A `geo` MAY instead declare `available[]` with `included[]`, `deltas` and `max_select` (§ 3.1), for a line item priced by market. See below |
| `device` | Settable[String] | OPTIONAL | settable | `allowed[]` of device categories |
| `daypart` | Settable[Object] | OPTIONAL | settable | `allowed[]` of `{ days[], start, end }`: `days[]` from `monday` \| `tuesday` \| `wednesday` \| `thursday` \| `friday` \| `saturday` \| `sunday`, HH:MM civil time, `end` exclusive, up to `24:00` |
| `time_zone` | String | REQUIRED when `daypart` or `frequency_cap` is present | seller-set | IANA time zone name, or `viewer_local` (where the ad renders). The clock for `daypart` and `frequency_cap.period` |
| `frequency_cap` | FrequencyCap | OPTIONAL | settable | See below |
| `exclusions_accepted` | Object | OPTIONAL | seller-set | What the seller can enforce: `{ types[], max_entries, enforcement, verification[] }`. See below |
| `exclusions` | Object | OPTIONAL | supplied | The buyer's block lists: `{ domain[], app_bundle[], iab_content_category[], keyword[], list_ref }`. See below |

**Block lists.** The seller declares which exclusion types it accepts and how it
enforces each; the buyer supplies its lists within that declaration.

```yaml
exclusions_accepted:
  types:        [domain, app_bundle, iab_content_category, keyword]
  max_entries:  { domain: 5000, keyword: 500 }
  enforcement:  { domain: pre_serve, app_bundle: pre_serve,
                  iab_content_category: pre_serve, keyword: best_effort }
  verification: ["IAS", "DoubleVerify"]

exclusions:
  domain:           ["example-gambling.example"]
  app_bundle:       [{ platform: roku, bundle: "123456" }]
  iab_content_category: ["IAB-CT3.0:<id>"]   # IAB Content Taxonomy ids
  keyword:          ["crypto"]
  list_ref:         { url: "<url>", sha256: "<hash>" }
```

- Each `app_bundle[]` entry is `{ platform, bundle }`. `bundle` is the OpenRTB
  2.6 `app.bundle` value; `platform` names the store (`ios` \| `android` \|
  `roku` \| `fire_tv` \| `samsung_tv` and other store platforms). A seller MUST
  reject an entry whose platform it cannot determine, rather than apply it
  across stores, with `validation`.
- `iab_content_category[]` entries are IAB Content Taxonomy ids.
- `enforcement` is `pre_serve` or `best_effort` per type.
- A buyer MUST NOT supply an exclusion type absent from
  `exclusions_accepted.types`. A seller MUST reject it deterministically
  rather than ignore it, with `not_offered`.
- A seller MUST NOT present `best_effort` enforcement as a guarantee.
- `list_ref` MUST be hash-pinned, and resolved into the stored record at
  `agreed`.

**`FrequencyCap`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `count` | Range[Integer] | REQUIRED | The bounds on the cap |
| `period` | TimeUnit | REQUIRED | The bucket the count runs over |
| `per` | Enum | REQUIRED | `device` \| `household` \| `listener`. Who is capped. It matters: CTV typically caps at household, audio at listener |

**Market-priced lines.** A seller whose rate differs by market MAY declare `geo`
with the selectable structure of § 3.1:

```yaml
geo:
  available:  ["SGP", "THA", "IDN", "MYS"]
  included:   ["SGP", "THA"]
  deltas:     { "IDN": { delta_cpm: 18.00 }, "MYS": { delta_cpm: 21.00 } }
  max_select: 4
```

- A `geo` that declares `allowed[]` and no `available[]` MUST be treated as
  `settable` (§ 3.2). A `geo` MUST NOT declare both.
- `deltas` add to `agreed_rate` as for any selectable field (§ 3.1).

**Window shape.** A `daypart` window is `{ days[], start, end }`, with `days[]`
from Monday to Sunday, `start` and `end` as HH:MM, and `end` exclusive,
later than `start`, and allowed to be `24:00`. A window that crosses midnight
is two windows:

```yaml
# Late fringe, 23:00 to 01:00, Monday night into Tuesday
daypart:
  allowed:
    - { days: [monday],  start: "23:00", end: "24:00" }
    - { days: [tuesday], start: "00:00", end: "01:00" }
time_zone: "America/New_York"
```

**Clock.** `time_zone` names a zone in the
[IANA time zone database](https://www.iana.org/time-zones), such as
America/New_York or UTC. Windows follow daylight-saving rules: a skipped
hour matches no instant; a repeated hour matches both. Like the calendar Day of
[OpenDirect 2.1 `Line.frequencyinterval`](https://github.com/InteractiveAdvertisingBureau/OpenDirect/blob/82bc294314aba017fc639ba634aecc53adfd675f/OpenDirect.v2.1.final.md#object_line),
`frequency_cap.period` is a calendar period in `time_zone`; weeks start on
Monday.

### 5.6 Commercial terms

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `pricing[]` | Array[PricingEntry] | REQUIRED | mixed | See below |
| `pricing[].cost_method` | VocabularyTerm | REQUIRED | seller-set | The billable unit. Core terms: `CPM` \| `CPC` \| `FLAT` |
| `pricing[].gross_rate` | Number | REQUIRED | seller-set | The list rate the buyer pays |
| `pricing[].agreed_rate` | Number | OPTIONAL | derived | The transacted rate after selections and any agreed request |
| `pricing[].seller_rate` | Number | OPTIONAL | seller-set | What the publisher receives |
| `pricing[].price_valid_until` | Instant | OPTIONAL | seller-set | How long the entry holds (§ 4.3.2). Distinct from the proposal's `offer_window.end` |
| `pricing[].currency` | String | REQUIRED | seller-set | ISO-4217 |
| `pricing[].floor` | Number | OPTIONAL | seller-set | The lowest rate the seller will consider. Enables a `requestable` counter to be evaluated without a round trip |
| `availability` | Object | OPTIONAL | asserted | `{ unit, basis, as_of, granularity, type: forecast \| reservable, quantity }`, with `as_of` an `Instant` and `granularity` a `CalendarUnit`. Recomputed against the buyer's selection |
| `commitment_bounds` | Object | OPTIONAL | seller-set | The envelope inside which a buyer may commit: `{ min_impressions, max_impressions, min_budget, max_budget }` |
| `commitment` | Commitment | OPTIONAL | settable | **The buyer's actual commitment.** See 5.6.1 |
| `hold_status` | HoldStatus | OPTIONAL | mixed | See 5.6.2 |
| `min_spend` | Number | OPTIONAL | seller-set | Minimum spend for this line item |
| `cancellation_policy` | Selectable[CancellationOption] | OPTIONAL | selectable | The cancellation rights the seller offers |
| `exclusivity` | Selectable[ExclusivityTerm] | OPTIONAL | selectable | The exclusivity terms the seller offers |
| `creative_policy` | Object | OPTIONAL | seller-set | Content and category restrictions on creative |
| `requires` | Requires | OPTIONAL | seller-set | Conditions that must hold in the same `commit` for this line item to be committable. See 5.6.3 |

#### 5.6.1 commitment

Absent on a shared proposal (§ 4.3). Populated during composition. A
`commitment` resolves under § 3 when the buyer is eligible (§ 5.8), and the
commitment fits `commitment_bounds` and `min_spend`, is not stale (§ 4.1.3),
and meets `requires` (§ 5.6.3). A resolved `commitment` is an offer to buy. It
binds only when the seller accepts it;
`assent[]` (§ 4.1) records that acceptance for the binding `version`. A seller
MAY decline a resolved `commitment`; the buyer MAY recompose. A decline for lack
of availability MUST return `availability` recomputed against the buyer's
composition; the seller's determination is authoritative. While a buyer's hold
(§ 5.6.2) runs, the seller MUST NOT decline that buyer's `commitment` for lack of
availability. This does not cover inventory that a hold granted ahead of it
(§ 5.6.2) reserves or took on converting. A firm entry limits a
decline to the grounds in § 4.3.2. Acceptance ends the availability check; booking
is downstream (§ 1.1). Frozen when the line item's `status` becomes `agreed`.

**`CommitmentAmount`** is the committed figure. `basis` means only this.

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `basis` | Enum | REQUIRED | `spend` \| `units` |
| `amount` | Number | REQUIRED | The figure committed |

**`Commitment`** holds the keys of `CommitmentAmount` and these:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `proposal_id` | String | REQUIRED | The proposal the commitment is made against |
| `version` | Integer | REQUIRED | The proposal `version` the commitment was priced against |
| `currency` | String | REQUIRED when `basis` is `spend` | ISO-4217 |
| `flight` | Interval | REQUIRED | The buyer's campaign. **Distinct from `offer_window`** |
| `advertisers[]` | Array[Party] | OPTIONAL | Whom the spend is for |
| `derived_units` | Integer | OPTIONAL | Computed from `amount`, `agreed_rate` and `cost_method`. Informative, not binding |
| `idempotency_key` | String | REQUIRED | Buyer-generated, unique per commitment attempt |

An `idempotency_key` is opaque and scoped to one buyer and seller pair. The
seller MUST NOT interpret it.

The seller MUST reject a new commitment attempt that is stale (§ 4.1.3), whose
proposal is past `offer_window.end`, or where the `pricing[]` entry the commitment is priced against
is past its `price_valid_until`. The rejection MUST carry `stale_version`, or
`expired` when `offer_window.end` or `price_valid_until` has passed, so the buyer can
fetch it again. These checks MUST be deterministic: they depend only on the
stored proposal and the time the seller receives the attempt. A seller that
rejects an attempt before `offer_window.start` returns `not_committable` with
`retry: same`.

For a replay from the same buyer of a commitment attempt the seller has
already processed, with the same `idempotency_key` and the same body (every
value the buyer sent with the attempt except `idempotency_key`), the seller
MUST return the original result, whether an acceptance or a rejection, and
MUST NOT create a second commitment. The staleness and expiry checks apply to a
new attempt, not to returning a stored result. An error whose `retry` is `same`
is not a stored result, so the retry runs the checks again. Reusing an
`idempotency_key` with a different body MUST return `idempotency_conflict` and
MUST NOT create or modify a commitment. A retry against a new `version` is a
new attempt, with a new `idempotency_key`.

#### 5.6.2 hold_status

**`HoldStatus`** keys:

| Key | Type | Required | Meaning | Mutability |
| :--- | :--- | :--- | :--- | :--- |
| `hold_available` | Boolean | OPTIONAL | Whether this line item may be held | seller-set |
| `hold_duration` | Duration | OPTIONAL | How long the hold runs | seller-set |
| `hold_scope` | Enum | OPTIONAL | `line_item` \| `proposal` | seller-set |
| `state` | Enum | OPTIONAL | `none` \| `requested` \| `held` \| `expired` \| `released` \| `converted`, moved as below | lifecycle |
| `hold_expires_at` | Instant | OPTIONAL | Set when the hold is granted | lifecycle |

Transitions: `none` → `requested` → `held` → (`expired` | `released` |
`converted`). `converted` is terminal and occurs when the line item reaches
`agreed`.

#### 5.6.3 requires

**`Requires`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `all_of[]` | Array[String] | OPTIONAL | Line items that MUST all be in the same `commit` |
| `any_of[]` | Array[String] | OPTIONAL | Line items of which at least one MUST be in the same `commit` |
| `min_commitments[]` | Array[MinCommitment] | OPTIONAL | Purchase-level thresholds: `{ line_item_id, basis, amount, currency }` |

```yaml
requires:
  all_of:  ["business-daily-display", "weather-app-ctv"]
  min_commitments:
    - { line_item_id: "business-daily-display", basis: spend, amount: 50000.00, currency: USD }
```

A bonus line item is a line item with `requires` and its own pricing, such as
a discounted `gross_rate` or `cost_method: FLAT` at 0. A conditional discount
is modelled as a separate line item that `requires` unlocks, not as a price
that changes according to the other line items selected. Every price remains
self-contained.

- References in `requires` MUST point to line items in the same proposal and
  version.
- A seller MUST reject a `commit` that includes a line item whose `requires`
  is unmet. An unmet `requires` returns `not_committable`. This check MUST be
  deterministic.
- If a line item referenced in `requires` becomes `sold_out` or `withdrawn`
  before a `commit`, and the line items left can't meet `requires`, the dependent
  line item becomes non-committable. After `agreed`, cancellation of a referenced
  line item is governed by the dependent line item's `cancellation_policy`.

### 5.7 Guarantees

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `committed_metrics[]` | Array[CommittedMetric] | OPTIONAL | requestable | `{ metric, value, basis }` tuples — `viewable_rate` for display, `completion_rate` for video/audio/CTV, an audience-modelled metric for DOOH. Seller declares a ceiling; a buyer MAY request above it |
| `measurement_source` | Selectable[MeasurementOption] | OPTIONAL | selectable | See `MeasurementOption` below. Lets a buyer transact in its own currency |
| `shortfall_remedy` | Selectable[VocabularyTerm] | OPTIONAL | selectable | Core terms: `makegood` \| `credit` \| `none`, plus `remedy_terms` |
| `reporting` | Selectable[ReportingOption] | OPTIONAL | selectable | See `ReportingOption` below |

**`MeasurementOption`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `vendor` | String | REQUIRED | The measurement provider |
| `attribution_window` | Duration | OPTIONAL | How long after exposure the provider attributes an event |
| `qualifier` | String | OPTIONAL | A product or method of the provider |

**`ReportingOption`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `feed_type` | Enum | REQUIRED | `log_level` \| `aggregate` |
| `cadence` | TimeUnit | OPTIONAL | How often a report arrives |
| `delivery_mechanism` | VocabularyTerm | OPTIONAL | How a report arrives. Core terms: `api` \| `s3` |
| `provided_metrics[]` | Array[String] | OPTIONAL | The metrics a report holds |
| `latency` | Duration | OPTIONAL | How long after the period a report arrives |

### 5.8 Transaction eligibility

`visibility` says who may read a line item. `required_credentials[]`,
`eligible_buyers[]`, `eligible_seats[]`, and `buyer_requirements` (§ 5.9) say who
may commit to it.

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `visibility` | Enum | REQUIRED | seller-set | `public` \| `registry_gated` \| `named`. See below |
| `required_credentials[]` | Array[RequiredCredential] | OPTIONAL | seller-set | What a buyer holds to be eligible |
| `eligible_buyers[]` | Array[RegistrableDomain] | OPTIONAL | seller-set | The buyers that may commit, by `buyer.domain` |
| `eligible_seats[]` | Array[SeatRef] | OPTIONAL | seller-set | The seats that may commit. An entry with an absent or empty `ids[]` names no seat and admits no one, unlike an absent OpenRTB 2.6 `Deal.wseat`, which sets no restriction |
| `terms_acceptance_required` | Boolean | OPTIONAL | seller-set | Whether legal terms must be accepted before assent |
| `terms_ref` | Object | REQUIRED when `terms_acceptance_required` is `true` | seller-set | `{ url, sha256, version }`: the legal terms or IO template the buyer accepts at assent. Hash-pinned, so assent (§ 4.1) binds to an exact document |

`terms_ref` MUST be hash-pinned and frozen at `agreed`.

`exclusions` (§ 5.5) reveal the buyer's strategy. A seller MUST NOT disclose a
buyer's `exclusions` to any party other than that buyer.

**Who may read.** Each `visibility` value names who may read the line item:

- `public`: any requester, with no authentication.
- `registry_gated`: an authenticated requester (§ 1.2) acting for a party the
  IAB Tech Lab Agent Registry attests.
- `named`: an authenticated requester acting for a party that `eligible_buyers[]`
  names, or that holds a seat `eligible_seats[]` names.

How a seller learns which party a requester acts for, or that it holds a seat, is
authorization (§ 1.2), and the object doesn't carry it.

An authenticated requester acting for the party a proposal's `buyer` names may read all
of it, whatever `visibility` says. Any other requester may read a proposal's own fields
only when it may read one of its line items. A response carries only the line items the
requester may read, and a request for any other line item, or for a proposal the
requester may not read, returns `not_found` (§ 2.4). A full fetch leaves out only line
items (§ 2.1), so a value it returns can name a line item the requester may not read,
such as a line item's `requires` (§ 5.6.3) or a `negotiation_history[]` path.

**Who may commit.** A buyer is eligible when each of these that is present holds:

- `eligible_buyers[]`, `eligible_seats[]`: `buyer.domain` MUST be in
  `eligible_buyers[]`, or `buyer_requirements.seats` MUST name at least one seat, each
  in an `eligible_seats[]` entry for its `dsp`.
- `buyer_requirements.allowed_dsps[]` (§ 5.9): when `buyer_requirements.seats` is
  present, its `dsp` MUST be in the list.
- `required_credentials[]`: the buyer meets it.

A buyer that fails these rules, or an authority check the seller applies (whether the
sender may make this request for `buyer`, or `buyer` for an advertiser it names, § 1.2),
gets `not_eligible` (§ 2.4), or `not_found` when the requester may not read what the request
names. That is a rejection, not a decline, so the limits on a decline (§ 4.3.2,
§ 5.6.1) do not apply. A mandate is not a field of this object.

**`RequiredCredential`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `credential_type` | VocabularyTerm | REQUIRED | What the buyer holds. Core term: `iab_registry`, an entry in the IAB Tech Lab Agent Registry |
| `issuer` | Domain | REQUIRED | Who issues it |

A consumer that does not know a `credential_type` MUST NOT treat the proposal or
line item as invalid for that reason. It MUST treat that entry as unsatisfiable.

Agent identity and request authentication are defined by the AAMP agent identity
and signing profile (provisional name). They are not expressed through
`required_credentials[]`.

### 5.9 Execution

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `buying_route` | Enum | OPTIONAL | seller-set | `DIRECT_PUBLISHER` \| `PUBLISHER_AD_SERVER` \| `SSP_PLATFORM` \| `DSP` \| `SEARCH_SOCIAL` |
| `transaction_mechanism` | Selectable[TransactionMechanism] | REQUIRED | selectable | See `TransactionMechanism` below. A seller MAY offer the same inventory through more than one |
| `serving_mode` | VocabularyTerm | OPTIONAL | seller-set | Core terms: `client_side` \| `ssai` \| `dai` |
| `deal_id_issuance` | String | OPTIONAL | derived | When and how the deal id is minted. Issued on acceptance of the commitment (§ 5.6.1) |
| `buyer_requirements` | BuyerRequirements | OPTIONAL | mixed | See below |
| `serving_platform` | String | OPTIONAL | seller-set | Where the line item serves |

**`TransactionMechanism`** is `direct_io` \| `programmatic_guaranteed` \|
`preferred_deal` \| `private_auction` \| `open_auction`.

**`BuyerRequirements`** keys:

| Key | Type | Required | Meaning | Mutability |
| :--- | :--- | :--- | :--- | :--- |
| `seats_expected` | Boolean | OPTIONAL | The seller asks the buyer to supply `seats` | seller-set |
| `allowed_dsps[]` | Array[RegistrableDomain] | OPTIONAL | The DSPs that may receive the deal (§ 5.8), each by its primary domain, as `SeatRef.dsp` (§ 2.2) | seller-set |
| `seats` | SeatRef | OPTIONAL | The buyer's seats on the deal, as the Deals API 1.0 `wseat` | supplied |
| `seat_owner` | Party | OPTIONAL | The legal entity that owns the seats. Absent: the `buyer` | supplied |

### 5.10 External references and settlement

| Field | Type | Required | Mutability | Description |
| :--- | :--- | :--- | :--- | :--- |
| `external_references[]` | Array[ExternalReference] | OPTIONAL | recorded | `{ system, namespace, id, role }`. Replaces platform-specific key names. The party that learns an id writes the entry. `role` is a `VocabularyTerm`. Core terms: `io`, an IO id generated by an order management system and carried back on the line item; `agreement`, a buyer-held agreement id |
| `agreement` | Agreement | OPTIONAL | seller-set | The master or annual agreement the line item is priced under. An informative pointer; the agreement itself is outside this specification. A buyer-held agreement id travels as an `external_references[]` entry with `role: agreement` |
| `correlation_id` | String | OPTIONAL | derived | One identity for this line item's commitment, carried across every system it touches |
| `billing` | Billing | OPTIONAL | seller-set | Who delivers is not always who invoices |
| `supported_order_systems[]` | Array[String] | OPTIONAL | seller-set | Declared up front so the agent knows it will reconcile |

**`Agreement`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `agreement_id` | String | REQUIRED | The agreement's id |
| `parties[]` | Array[Party] | OPTIONAL | The agreement's parties |
| `agreement_type` | VocabularyTerm | OPTIONAL | Core terms: `upfront` \| `annual` \| `master_services`. A receiver that doesn't know the term still reads the `agreement` |
| `term` | Interval | OPTIONAL | When the agreement runs |
| `document` | DocumentRef | OPTIONAL | The agreement, where the parties pin it |

**`Billing`** keys:

| Key | Type | Required | Meaning |
| :--- | :--- | :--- | :--- |
| `delivering_party` | Party | OPTIONAL | Who delivers. Absent: the `seller` |
| `invoicing_party` | Party | OPTIONAL | Who invoices. Absent: the `seller` |
| `payment_terms` | String | OPTIONAL | The payment terms, such as `net 30` |
| `invoice_period` | VocabularyTerm | OPTIONAL | The invoice period. Core terms: `month` (default) \| `cycle` |
| `cycle_length` | Duration | REQUIRED when `invoice_period` is `cycle` | How long each `cycle` period runs, such as `P28D` (4 weeks) |
| `time_zone` | IanaZone | OPTIONAL | The clock for a `month` invoice period. Absent: `UTC` |

A buyer's own code for a supplier goes in `external_references[]`.

This specification does not define IO generation. IO creation is a connector
concern. OpenProposal supplies the agreed record, `terms_ref` and
`correlation_id` a connector needs.

---

## 6. Examples

Runnable copies of every example below live in [`examples/`](../examples/).

### 6.1 Proposal

Shows version 2 after one seller revision (§ 4.1.3). See
[`examples/proposal.yaml`](../examples/proposal.yaml). Its line items are
shown in their own files, §§ 6.2 to 6.5.

### 6.2 Display line item — fully worked

Shows `selectable` audiences with per-option pricing and `settable` bounds. See
[`examples/line-item-display.yaml`](../examples/line-item-display.yaml).

### 6.3 CTV line item

See [`examples/line-item-ctv.yaml`](../examples/line-item-ctv.yaml).

Inspecting this line item's VAST creative is subject to § 5.4.1.

### 6.4 Audio line item

See [`examples/line-item-audio.yaml`](../examples/line-item-audio.yaml).

### 6.5 Bonus line item

A CTV line item unlocked by buying the display and CTV line items together,
priced on its own. See
[`examples/line-item-ctv-bonus.yaml`](../examples/line-item-ctv-bonus.yaml).

### 6.6 Publication manifest

A manifest (§ 2.3) listing the public line items of the example proposal. The
display line item is `registry_gated`, so it is not listed. See
[`examples/manifest.json`](../examples/manifest.json).

### 6.12 Issued proposal, partly agreed

A proposal issued to one buyer from the shared proposal of § 6.1 (§ 4.3). One line
item is agreed at version 1, with a commitment. The other stays `published` at
version 2, with a hold, so the proposal stays `published` (§ 4.3.3). The `assent[]`
entries name version 1, and the digest is over that line item alone (§ 4.1.2). See
[`examples/proposal-issued.yaml`](../examples/proposal-issued.yaml).

---

## 7. Why this split

- **No inheritance mechanism to specify or debug.** Fields live at exactly one
  level, so there is no "overridable unless restated" rule to maintain.
- **The proposal reads as a pitch, not a schema dump.** `description`,
  `specifications`, `best_for[]` and `seasonality_notes` are what a model needs to
  decide whether to look further.
- **Every line item states its own terms, in exactly one channel.** A
  buying agent can hand a line item, with the proposal's identity, to a downstream
  system, with no proposal-level defaults or cross-channel ambiguity to resolve.
- **Channels share one object, not a schema fork per channel.** `channel` is the
  discriminator, and `committed_metrics[]` names the metric in each tuple. The
  format registry, through `specs`, carries what is channel-specific about creative
  shape.
- **Composition resolves without a round trip.** Because the seller declares the
  option set and its pricing up front, a buyer agent performs constraint
  satisfaction rather than negotiation. Only genuinely out-of-envelope asks
  require the counterparty to respond.

**Templates and issued proposals (non-normative).**

- **Template:** seller-side only. It lives in the seller's own systems (its
  proposal store), is not part of the public object, and is never transacted
  directly.
- **Issued proposal:** what a buyer commits against (§ 4.3). Each has its own
  `proposal_id` per counterparty or destination, and may carry
  `proposal_template_id` (§ 4.1) to trace it back to its template and `issued_from`
  to trace it back to a shared proposal.
- Buyer-specific terms, such as annual rates and named visibility, live on the
  issued proposal's line items: `visibility: named`, `eligible_buyers[]` and
  their own `pricing[]`.

**Relationships, agreements and IOs (non-normative).** Buyer–seller
relationships are expressed as issued proposals (`visibility: named`,
`eligible_buyers[]` set to that buyer, with the negotiated `pricing[]`) plus
the buyer agent's business rules. "Preferred partner" weighting is a buyer-side
ranking rule, not part of this specification. `agreement` and `terms_ref`
(§ 5.10, § 5.8) point at the agreement and terms a line item is executed under;
IO generation happens through connectors.

---

## 8. Open questions

Comment is specifically invited on the following. Each has a tracking issue —
see [docs/open-questions.md](../docs/open-questions.md).

1. **Does per-field mutability belong in 3.0?** Sections 3 and 5 make
   composition part of the object. The alternative is a catalog format where a
   buyer selects whole line items and everything else is a round trip.
2. **Is a fetchable reference to a seller catalog needed?** The object is fully
   inline: a seller reuses catalog entries in its own systems, and a summary lists
   what § 2.1 names.
3. **Cross-channel guarantee comparability is unsolved.** Once one line item
   guarantees `viewable_rate` and another `completion_rate`, there is no
   normalised way for a buying agent to compare or optimise across them. Likely
   WS4, but worth stating rather than pretending 3.0 covers it.
4. **The format registry has no entries for `audio/*`, `ctv/*` or `dooh/*`.**
   `specs` delegates to a registry that cannot currently answer for half the
   declared channels.
5. **Do `linked_execution` and `requires` cover bundle purchases**, or does the
   proposal also need a `min_line_items` field?
6. **Should `billing.payment_terms` and `billing.invoicing_party` be repeated on
   every line item,** given they are usually identical across a seller's shelf?
7. **`environments.available[]` needs validation against real inventory.** The
   list is proposed, not derived from implementation experience.
8. **How does a receiver read a document from a later release?** `spec_version`
   names the release a document follows, and § 2.5 makes a key the receiver's
   release does not list invalid. Nothing says whether a receiver rejects a release
   it does not know, or keeps and ignores keys it does not list.
11. **Must a manifest response carry both `ETag` and `Last-Modified`, or is either
    enough?** § 2.3 requires at least one, so a buyer's client handles whichever the
    seller sends.

---

## Appendix A — Field index

Every field in the specification, in document order, with its type, presence,
and mutability marker. Generated from the body of this document; **if the two disagree, the
body is normative.**

| Field | Section | Type | Required | Marker |
| :--- | :--- | :--- | :--- | :--- |
| `proposal_id` | 4.1 Identity and lifecycle | String | REQUIRED | immutable |
| `version` | 4.1 Identity and lifecycle | Integer | REQUIRED | derived |
| `spec_version` | 4.1 Identity and lifecycle | String | REQUIRED | seller-set |
| `seller` | 4.1 Identity and lifecycle | Party | REQUIRED | immutable |
| `buyer` | 4.1 Identity and lifecycle | Party | REQUIRED when `type` is `custom` or `assent[]` is present | immutable |
| `type` | 4.1 Identity and lifecycle | Enum | REQUIRED | immutable |
| `proposal_template_id` | 4.1 Identity and lifecycle | String | OPTIONAL | immutable |
| `issued_from` | 4.1 Identity and lifecycle | VersionRef | OPTIONAL | immutable |
| `status` | 4.1 Identity and lifecycle | ProposalStatus | REQUIRED | derived |
| `record_digest` | 4.1 Identity and lifecycle | Digest | OPTIONAL | derived |
| `assent[]` | 4.1 Identity and lifecycle | Array[AssentEntry] | OPTIONAL | recorded |
| `offer_window` | 4.1 Identity and lifecycle | Interval | OPTIONAL | seller-set |
| `brief_id` | 4.1 Identity and lifecycle | String | REQUIRED when `type` is `custom` | immutable |
| `negotiation_history[]` | 4.1 Identity and lifecycle | Array[HistoryEntry] | REQUIRED when the current `version` is frozen (§ 4.1.3) | recorded |
| `line_items[]` | 4.1 Identity and lifecycle | Array[LineItem] | REQUIRED | seller-set |
| `linked_execution` | 4.1 Identity and lifecycle | Enum | OPTIONAL | seller-set |
| `ext` | 4.1 Identity and lifecycle | Ext | OPTIONAL | seller-set |
| `description` | 4.2 Agent comprehension | String | REQUIRED | seller-set |
| `specifications` | 4.2 Agent comprehension | String | OPTIONAL | seller-set |
| `best_for[]` | 4.2 Agent comprehension | Array[String] | OPTIONAL | seller-set |
| `not_suitable_for[]` | 4.2 Agent comprehension | Array[String] | OPTIONAL | seller-set |
| `seasonality_notes` | 4.2 Agent comprehension | String | OPTIONAL | seller-set |
| `line_item_id` | 5.1 Identity | String | REQUIRED | immutable |
| `status` | 5.1 Identity | LineItemStatus | REQUIRED | lifecycle |
| `channel` | 5.1 Identity | MediaChannel | REQUIRED | immutable |
| `ext` | 5.1 Identity | Ext | OPTIONAL | seller-set |
| `properties` | 5.2 Inventory composition | Selectable[PropertyOption] | OPTIONAL | selectable |
| `content_detail` | 5.2 Inventory composition | Object | OPTIONAL | seller-set |
| `environments` | 5.2 Inventory composition | Selectable[Environment] | OPTIONAL | selectable |
| `audiences` | 5.3 Audience reach | Selectable[AudienceOption] | OPTIONAL | selectable |
| `addressable_scale` | 5.3 Audience reach | Integer | OPTIONAL | asserted |
| `activation_route` | 5.3 Audience reach | Selectable[VocabularyTerm] | OPTIONAL | selectable |
| `buyer_supplied` | 5.3 Audience reach | BuyerSupplied | OPTIONAL | mixed |
| `formats` | 5.4 Creative requirements | Selectable[String] | OPTIONAL | selectable |
| `specs` | 5.4 Creative requirements | Object | OPTIONAL | seller-set |
| `third_party_tags` | 5.4 Creative requirements | Object | OPTIONAL | seller-set |
| `creative_delivery` | 5.4 Creative requirements | CreativeDelivery | OPTIONAL | seller-set |
| `assets[]` | 5.4 Creative requirements | Array[Asset] | OPTIONAL | mixed |
| `materials_due` | 5.4 Creative requirements | MaterialsDue | OPTIONAL | requestable |
| `approval` | 5.4 Creative requirements | Object | OPTIONAL | seller-set |
| `production` | 5.4 Creative requirements | Selectable[ProductionOption] | OPTIONAL | selectable |
| `geo` | 5.5 Targeting envelope | Settable[String] | OPTIONAL | settable |
| `device` | 5.5 Targeting envelope | Settable[String] | OPTIONAL | settable |
| `daypart` | 5.5 Targeting envelope | Settable[Object] | OPTIONAL | settable |
| `frequency_cap` | 5.5 Targeting envelope | FrequencyCap | OPTIONAL | settable |
| `exclusions_accepted` | 5.5 Targeting envelope | Object | OPTIONAL | seller-set |
| `exclusions` | 5.5 Targeting envelope | Object | OPTIONAL | supplied |
| `pricing[]` | 5.6 Commercial terms | Array[PricingEntry] | REQUIRED | mixed |
| `pricing[].cost_method` | 5.6 Commercial terms | VocabularyTerm | REQUIRED | seller-set |
| `pricing[].gross_rate` | 5.6 Commercial terms | Number | REQUIRED | seller-set |
| `pricing[].agreed_rate` | 5.6 Commercial terms | Number | OPTIONAL | derived |
| `pricing[].seller_rate` | 5.6 Commercial terms | Number | OPTIONAL | seller-set |
| `pricing[].price_valid_until` | 5.6 Commercial terms | Instant | OPTIONAL | seller-set |
| `pricing[].currency` | 5.6 Commercial terms | String | REQUIRED | seller-set |
| `pricing[].floor` | 5.6 Commercial terms | Number | OPTIONAL | seller-set |
| `availability` | 5.6 Commercial terms | Object | OPTIONAL | asserted |
| `commitment_bounds` | 5.6 Commercial terms | Object | OPTIONAL | seller-set |
| `commitment` | 5.6 Commercial terms | Commitment | OPTIONAL | settable |
| `hold_status` | 5.6 Commercial terms | HoldStatus | OPTIONAL | mixed |
| `min_spend` | 5.6 Commercial terms | Number | OPTIONAL | seller-set |
| `cancellation_policy` | 5.6 Commercial terms | Selectable[CancellationOption] | OPTIONAL | selectable |
| `exclusivity` | 5.6 Commercial terms | Selectable[ExclusivityTerm] | OPTIONAL | selectable |
| `creative_policy` | 5.6 Commercial terms | Object | OPTIONAL | seller-set |
| `requires` | 5.6 Commercial terms | Requires | OPTIONAL | seller-set |
| `committed_metrics[]` | 5.7 Guarantees | Array[CommittedMetric] | OPTIONAL | requestable |
| `measurement_source` | 5.7 Guarantees | Selectable[MeasurementOption] | OPTIONAL | selectable |
| `shortfall_remedy` | 5.7 Guarantees | Selectable[VocabularyTerm] | OPTIONAL | selectable |
| `reporting` | 5.7 Guarantees | Selectable[ReportingOption] | OPTIONAL | selectable |
| `visibility` | 5.8 Transaction eligibility | Enum | REQUIRED | seller-set |
| `required_credentials[]` | 5.8 Transaction eligibility | Array[RequiredCredential] | OPTIONAL | seller-set |
| `eligible_buyers[]` | 5.8 Transaction eligibility | Array[RegistrableDomain] | OPTIONAL | seller-set |
| `eligible_seats[]` | 5.8 Transaction eligibility | Array[SeatRef] | OPTIONAL | seller-set |
| `terms_acceptance_required` | 5.8 Transaction eligibility | Boolean | OPTIONAL | seller-set |
| `terms_ref` | 5.8 Transaction eligibility | Object | REQUIRED when `terms_acceptance_required` is `true` | seller-set |
| `buying_route` | 5.9 Execution | Enum | OPTIONAL | seller-set |
| `transaction_mechanism` | 5.9 Execution | Selectable[TransactionMechanism] | REQUIRED | selectable |
| `serving_mode` | 5.9 Execution | VocabularyTerm | OPTIONAL | seller-set |
| `deal_id_issuance` | 5.9 Execution | String | OPTIONAL | derived |
| `buyer_requirements` | 5.9 Execution | BuyerRequirements | OPTIONAL | mixed |
| `serving_platform` | 5.9 Execution | String | OPTIONAL | seller-set |
| `external_references[]` | 5.10 External references and settlement | Array[ExternalReference] | OPTIONAL | recorded |
| `agreement` | 5.10 External references and settlement | Agreement | OPTIONAL | seller-set |
| `correlation_id` | 5.10 External references and settlement | String | OPTIONAL | derived |
| `billing` | 5.10 External references and settlement | Billing | OPTIONAL | seller-set |
| `supported_order_systems[]` | 5.10 External references and settlement | Array[String] | OPTIONAL | seller-set |

---

## Appendix B — Fields by marker

| Marker | Count | Meaning | Fields |
| :--- | :--- | :--- | :--- |
| immutable | 9 | Set once at creation. Neither party may change it. | `proposal_id`, `seller`, `buyer`, `type`, `proposal_template_id`, `issued_from`, `brief_id`, `line_item_id`, `channel` |
| seller-set | 39 | The seller sets it and MAY revise it while the `status` of the object that carries it is `draft`, `published` or `under_review`. § 4.3.2 states what a revision does to a line item `under_review`. The buyer cannot change it directly. | `spec_version`, `offer_window`, `line_items[]`, `linked_execution`, `ext` (proposal), `description`, `specifications`, `best_for[]`, `not_suitable_for[]`, `seasonality_notes`, `ext` (line item), `content_detail`, `specs`, `third_party_tags`, `creative_delivery`, `approval`, `exclusions_accepted`, `pricing[].cost_method`, `pricing[].gross_rate`, `pricing[].seller_rate`, `pricing[].price_valid_until`, `pricing[].currency`, `pricing[].floor`, `commitment_bounds`, `min_spend`, `creative_policy`, `requires`, `visibility`, `required_credentials[]`, `eligible_buyers[]`, `eligible_seats[]`, `terms_acceptance_required`, `terms_ref`, `buying_route`, `serving_mode`, `serving_platform`, `agreement`, `billing`, `supported_order_systems[]` |
| selectable | 12 | The buyer chooses from a seller-declared set. Each option MAY carry a price delta. Resolves without a round trip. | `properties`, `environments`, `audiences`, `activation_route`, `formats`, `production`, `cancellation_policy`, `exclusivity`, `measurement_source`, `shortfall_remedy`, `reporting`, `transaction_mechanism` |
| settable | 5 | The buyer supplies a value within seller-declared bounds. Resolves without a round trip. | `geo`, `device`, `daypart`, `frequency_cap`, `commitment` |
| supplied | 1 | The buyer provides data or an artifact. The seller does not pre-populate it. | `exclusions` |
| requestable | 2 | The buyer MAY ask for a value outside the declared space. Requires explicit seller assent. | `materials_due`, `committed_metrics[]` |
| derived | 6 | Computed by a rule this specification states. Neither party sets it directly. | `version`, `status` (proposal), `record_digest`, `pricing[].agreed_rate`, `deal_id_issuance`, `correlation_id` |
| lifecycle | 1 | Live state of the object. The party its section names moves it between the stated values. Not a term. | `status` (line item) |
| recorded | 3 | Written by the party that acted. Append-only: an entry is never edited or removed. Not a term. | `assent[]`, `negotiation_history[]`, `external_references[]` |
| asserted | 2 | The seller states it from data the buyer can't recompute. Not a term, and it changes without a new version. | `addressable_scale`, `availability` |
| mixed | 5 | The keys of the object carry different markers: in the Mutability column of its key table, in its lead-in for composed keys, or on its rows for `pricing[]`. | `buyer_supplied`, `assets[]`, `pricing[]`, `hold_status`, `buyer_requirements` |

### What the distribution says

Of 85 fields, **20 are touched by the buyer** — 12 `selectable`, 5 `settable`, 1
`supplied` and 2 `requestable`. The remaining 65 are `seller-set`, `immutable`,
`derived`, `lifecycle`, `recorded`, `asserted` or `mixed`.

Only the 2 `requestable` fields require a round trip to resolve (§ 5.6.1).
Everything else the buyer touches — 18 fields — resolves against bounds the seller
declared up front. That ratio is the design claim: composition is constraint
satisfaction, and negotiation is the exception.
