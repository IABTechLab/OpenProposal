# OpenProposal

**AAMP 3.0 · Object Model Specification — open for public comment**

OpenProposal is the core AAMP 3.0 object: the descriptive specification for what
is being bought and sold, engineered so a buying agent can parse and evaluate it
at machine speed. It pulls through from initial brief to binding commercial
terms, and is the canonical object a seller manages alongside its OMS and ad
server.

> **This is a draft.** Nothing here is a ratified IAB Tech Lab standard. Do not
> build production systems against it expecting stability.

| | |
| :--- | :--- |
| **Current draft** | [`spec/openproposal-3.0.md`](spec/openproposal-3.0.md) |
| **Comment period opens** | 2026-09-22 |
| **Comment period closes** | 2026-10-22 |
| **Announcement** | [IAB Tech Lab introduces AAMP 3.0 with OpenProposal](https://iabtechlab.com/press-releases/iab-tech-lab-introduces-aamp-3-0-with-openproposal/) |
| **How to comment** | [CONTRIBUTING.md](CONTRIBUTING.md) |
| **Open questions we especially want answered** | [docs/open-questions.md](docs/open-questions.md) |

---

## What's in here

```
spec/openproposal-3.0.md   The normative draft. The single source of truth.
examples/                  Worked examples from § 6, as parseable YAML.
schema/                    Machine-readable schema (coming — see schema/README.md).
docs/                      Comment process, open questions, disposition log.
```

## How to comment

**You do not need to be an IAB Tech Lab member to comment.** All you need is a
GitHub account.

Pick the route that matches what you have to say:

| You want to… | Do this |
| :--- | :--- |
| Flag something unclear, wrong, or missing | [Open a **Comment**](../../issues/new?template=comment.yml) |
| Propose specific normative wording | [Open a **Change request**](../../issues/new?template=change-request.yml), or send a pull request against `spec/openproposal-3.0.md` |
| Answer one of the 7 open questions | Comment on that question's [tracking issue](docs/open-questions.md) |
| Report what happened when you tried to implement it | [Open **Implementation feedback**](../../issues/new?template=implementation-feedback.yml) |
| Ask a question rather than raise an issue | Use [Discussions](../../discussions) |

Every comment filed during the comment period gets a written disposition —
accepted, accepted with modification, rejected with reason, or deferred — logged
in [docs/disposition-log.md](docs/disposition-log.md). See
[docs/comment-process.md](docs/comment-process.md) for the full process.

## Reading the spec

Three things to understand before the field tables make sense:

1. **No inheritance.** Every line item is fully self-contained. A field never
   takes its value from the parent proposal or a sibling line item.
2. **Every field carries exactly one mutability marker** (§ 3) — `immutable`,
   `seller-set`, `selectable`, `settable`, `supplied`, `requestable` or
   `derived`. The marker is what tells a buying agent whether it can act
   unilaterally.
3. **Composition is constraint satisfaction, not negotiation.** Of 71 fields,
   only 3 require a round trip with the counterparty. That ratio is the design
   claim the draft is asking you to test.

## Downstream standards

OpenProposal does not replace IAB Tech Lab execution standards — each line item
lands in the one its `transaction_mechanism` maps to (OpenDirect 2.1, Deals API,
OpenRTB 2.6). See § 1.1.

## Schemas

Machine-readable schemas are coming. They are not published with this first
draft, because the comment period is still deciding questions that shape
them. Until then, [`examples/`](examples/) is the best reference for shape. See
[schema/README.md](schema/README.md).

## For maintainers

Before this repository is announced, work through
[docs/repo-setup.md](docs/repo-setup.md). It covers the settings that cannot
be committed — branch protection, Discussions, labels, the tagged draft — and
the placeholders that must be filled, starting with the licence.

## Licence and IPR

The OpenProposal specification is licensed under a
[Creative Commons Attribution 3.0 License](https://creativecommons.org/licenses/by/3.0/).
Code in `scripts/` and `.github/workflows/` is licensed under
[Apache-2.0](LICENSE-CODE). Full terms and the disclaimer are in
[LICENSE](LICENSE).

By submitting anything to this repository you license it to IAB Tech Lab under
the same Creative Commons licence. IAB Tech Lab members are also subject to the
[IAB Tech Lab IPR Policy](https://iabtechlab.com/ipr-iab-techlab/acknowledge-ipr/).
Read [CONTRIBUTING.md](CONTRIBUTING.md#ipr) before filing anything.
