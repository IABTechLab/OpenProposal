# Open questions

The draft asks seven questions it does not answer. These are the highest-value
places to comment, because the working group is genuinely undecided.

Each gets its own tracking issue when the comment period opens. **Maintainers:
file these seven issues with the `open-question` label and fill the links
below.**

---

### OQ-1 — Does per-field mutability belong in 3.0?

**Issue:** `TBD`  ·  **Spec:** § 3, § 5

Sections 3 and 5 make composition part of the object: the seller declares an
option space, and the buyer resolves inside it without a round trip. The
alternative is a catalog format where a buyer selects whole line items and
everything else is a round trip.

**What would settle it:** evidence from a seller about whether their inventory
can actually be expressed as a declared option space, and from a buyer about
whether resolving inside one is worth the modelling cost.

---

### OQ-2 — Do seller catalogs (`catalog_ref`) belong in 3.0?

**Issue:** `TBD`  ·  **Spec:** § 2.2

Or should the object stay fully inline until a later version? `catalog_ref`
buys compactness across a large shelf at the cost of a resolution step during
discovery and a versioning regime sellers must operate.

**What would settle it:** how large a real shelf gets, and whether sellers
already maintain versioned, immutable catalog entries or would have to build
that.

---

### OQ-3 — Cross-channel guarantee comparability is unsolved

**Issue:** `TBD`  ·  **Spec:** § 5.7

Once one line item guarantees `viewable_rate` and another `completion_rate`,
there is no normalised way for a buying agent to compare or optimise across
them. Likely WS4, but the draft states it rather than pretending 3.0 covers it.

**What would settle it:** whether anyone has a normalisation that survives
contact with a real cross-channel plan — or confirmation that this is correctly
deferred.

---

### OQ-4 — The format registry has no entries for `audio/*`, `ctv/*` or `dooh/*`

**Issue:** `TBD`  ·  **Spec:** § 5.4

`specs` delegates to a registry that cannot currently answer for half the
declared channels. Either the registry is extended before 3.0 ratifies, or the
spec has to say what an agent does when a format id has no registry entry.

**What would settle it:** a commitment and timeline on registry coverage, or a
proposed fallback behaviour.

---

### OQ-5 — Is a `min_line_items` field needed?

**Issue:** `TBD`  ·  **Spec:** § 2, § 4

The draft makes proposals subsettable unless binding terms mandate linked
execution. Does the proposal need an explicit `min_line_items` to require a
bundle purchase, or is that left to buyer discretion and the binding terms?

**What would settle it:** whether sellers actually merchandise bundles that must
be bought whole, and whether "binding terms" is a precise enough hook.

---

### OQ-6 — Should `payment_terms` and `invoicing_party` be catalog references?

**Issue:** `TBD`  ·  **Spec:** § 5.10

Rather than repeated on every line item, given they are usually identical across
a seller's shelf. Note this is in tension with the no-inheritance rule (§ 2) —
a `catalog_ref` is explicitly not inheritance, but the ergonomics are similar.

**What would settle it:** whether `billing` genuinely varies per line item in
practice (different supplier of record, different invoicing entity per
property).

---

### OQ-7 — `environments[]` needs validation against real inventory

**Issue:** `TBD`  ·  **Spec:** § 5.2

The enum — `web_desktop`, `web_mobile`, `app_mobile`, `ctv`, `dooh`,
`audio_streaming` — is proposed, not derived from implementation experience.

**What would settle it:** sellers mapping their real inventory onto the enum and
reporting what does not fit.

---

## Not on this list but worth saying

If you think the draft has a problem it has not asked about, file it as a
[Comment](https://github.com/IABTechLab/OpenProposal/issues/new?template=comment.yml) or a
[Change request](https://github.com/IABTechLab/OpenProposal/issues/new?template=change-request.yml). The seven
above are where we know we are undecided, not the limit of what we will consider.
