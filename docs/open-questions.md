# Open questions

These are the questions the draft asks and does not answer. They are the
highest-value places to comment, because the working group is genuinely undecided.

Each has its own tracking issue, labelled
[`open-question`](https://github.com/IABTechLab/OpenProposal/issues?q=label%3Aopen-question).
Answer on the issue.

---

### OQ-1 — Does per-field mutability belong in 3.0?

**Issue:** [#2](https://github.com/IABTechLab/OpenProposal/issues/2)  ·  **Spec:** § 3, § 5

Sections 3 and 5 make composition part of the object: the seller declares an
option space, and the buyer resolves inside it without a round trip. The
alternative is a catalog format where a buyer selects whole line items and
everything else is a round trip.

**What would settle it:** evidence from a seller about whether their inventory
can actually be expressed as a declared option space, and from a buyer about
whether resolving inside one is worth the modelling cost.

---

### OQ-2 — Is a fetchable reference to a seller catalog needed?

**Issue:** [#3](https://github.com/IABTechLab/OpenProposal/issues/3)  ·  **Spec:** § 2.1

The object is fully inline. A seller reuses catalog entries in its own systems, and
a summary lists what § 2.1 names. A reference a buyer could fetch would buy
compactness across a large shelf at the cost of a fetch rule, a resolution step
during discovery, and a versioning regime sellers must operate.

**What would settle it:** how large a real shelf gets, and whether sellers
already maintain versioned, immutable catalog entries or would have to build
that.

---

### OQ-3 — Cross-channel guarantee comparability is unsolved

**Issue:** [#4](https://github.com/IABTechLab/OpenProposal/issues/4)  ·  **Spec:** § 5.7

Once one line item guarantees `viewable_rate` and another `completion_rate`,
there is no normalised way for a buying agent to compare or optimise across
them. Likely WS4, but the draft states it rather than pretending 3.0 covers it.

**What would settle it:** whether anyone has a normalisation that survives
contact with a real cross-channel plan — or confirmation that this is correctly
deferred.

---

### OQ-4 — The format registry has no entries for `audio/*`, `ctv/*` or `dooh/*`

**Issue:** [#5](https://github.com/IABTechLab/OpenProposal/issues/5)  ·  **Spec:** § 5.4

`specs` delegates to a registry that cannot currently answer for half the
declared channels. Either the registry is extended before 3.0 ratifies, or the
spec has to say what an agent does when a format id has no registry entry.

**What would settle it:** a commitment and timeline on registry coverage, or a
proposed fallback behaviour.

---

### OQ-5 — Do `linked_execution` and `requires` cover bundle purchases?

**Issue:** [#6](https://github.com/IABTechLab/OpenProposal/issues/6)  ·  **Spec:** § 2, § 4

The draft makes proposals subsettable unless `linked_execution` is `all`, and a line
item can state `requires`. Does the proposal also need a `min_line_items` field?

**What would settle it:** whether sellers merchandise a bundle these two fields
can't express.

---

### OQ-6 — Should `payment_terms` and `invoicing_party` repeat on every line item?

**Issue:** [#7](https://github.com/IABTechLab/OpenProposal/issues/7)  ·  **Spec:** § 5.10

They are usually identical across a seller's shelf. Note this is in tension with the
no-inheritance rule (§ 2): sharing them would need another mechanism.

**What would settle it:** whether `billing` genuinely varies per line item in
practice (different supplier of record, different invoicing entity per
property).

---

### OQ-7 — `environments.available[]` needs validation against real inventory

**Issue:** [#8](https://github.com/IABTechLab/OpenProposal/issues/8)  ·  **Spec:** § 5.2

The enum — `web_desktop`, `web_mobile`, `app_mobile`, `ctv`, `dooh`, each
defined in § 5.2.1 — is proposed, not derived from implementation experience.

**What would settle it:** sellers mapping their real inventory onto the enum and
reporting what does not fit.

---

### OQ-8 — How does a receiver read a document from a later release?

**Issue:** [#131](https://github.com/IABTechLab/OpenProposal/issues/131)  ·  **Spec:** § 2.5, § 4.1

`spec_version` names the release a document follows, and § 2.5 makes a key the
receiver's release does not list invalid. Nothing says whether a receiver rejects a
release it does not know, or keeps and ignores keys it does not list.

**What would settle it:** how an implementer upgrades a seller and its buyers when
they don't move at the same time, and whether unread keys can reach an assent.

---

### OQ-11 — Must a manifest response carry both `ETag` and `Last-Modified`?

**Issue:** [#29](https://github.com/IABTechLab/OpenProposal/issues/29)  ·  **Spec:** § 2.3

The draft requires at least one, so a buyer's client handles whichever the seller
sends.

**What would settle it:** which validator polling clients use, and what the hosts
that serve the manifest send by default.

---

## Not on this list but worth saying

If you think the draft has a problem it has not asked about, file it as a
[Comment](https://github.com/IABTechLab/OpenProposal/issues/new?template=comment.yml) or a
[Change request](https://github.com/IABTechLab/OpenProposal/issues/new?template=change-request.yml). The questions
above are where we know we are undecided, not the limit of what we will consider.
