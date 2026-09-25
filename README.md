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
| **Short link** | [iabtechlab.com/AAMPv3](https://iabtechlab.com/AAMPv3) (points to this repository) |
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

## About this repository

`main` always holds the current draft. Each published draft is tagged; the
draft announced for public comment is
[`v3.0-draft-1`](https://github.com/IABTechLab/OpenProposal/releases/tag/v3.0-draft-1).
Changes to `main` go through pull requests, and every normative change is
recorded in [spec/CHANGELOG.md](spec/CHANGELOG.md) with the issue behind it.

## How to comment

**You do not need to be an IAB Tech Lab member to comment.** All you need is a
GitHub account.

Commenting and deciding are separate. Anyone may comment; the working group
reviews every comment and decides its disposition. See
[GOVERNANCE.md](GOVERNANCE.md) for who is on the working group and how
decisions are made.

Pick the route that matches what you have to say:

| You want to… | Do this |
| :--- | :--- |
| Flag something unclear, wrong, or missing | [Open a **Comment**](https://github.com/IABTechLab/OpenProposal/issues/new?template=comment.yml) |
| Propose specific normative wording | [Open a **Change request**](https://github.com/IABTechLab/OpenProposal/issues/new?template=change-request.yml), or send a pull request against `spec/openproposal-3.0.md` |
| Answer one of the 7 open questions | Comment on that question's [tracking issue](docs/open-questions.md) |
| Report what happened when you tried to implement it | [Open **Implementation feedback**](https://github.com/IABTechLab/OpenProposal/issues/new?template=implementation-feedback.yml) |
| Ask a question rather than raise an issue | Use [Discussions](https://github.com/IABTechLab/OpenProposal/discussions) |

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

## Contributors and governance

OpenProposal is developed by an IAB Tech Lab working group. Roles, the decision
rule and how comments are adjudicated are in [GOVERNANCE.md](GOVERNANCE.md) and
[docs/comment-process.md](docs/comment-process.md).

## Contact

For more information, or to get involved, email
[support@iabtechlab.com](mailto:support@iabtechlab.com).

## About IAB Tech Lab

The IAB Technology Laboratory is a nonprofit research and development
consortium charged with producing and helping companies implement global
industry technical standards and solutions. The goal of the Tech Lab is to
reduce friction associated with the digital advertising and marketing supply
chain while contributing to the safe growth of an industry.

Learn more at [iabtechlab.com](https://iabtechlab.com).

## For maintainers

[docs/repo-setup.md](docs/repo-setup.md) lists the settings that cannot be
committed — branch protection, Discussions, labels, the tagged draft — and the
placeholders still to be filled.

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

## Disclaimer

The specification and all related materials are provided "as is" and "as
available", without warranty of any kind. They do not constitute business or
legal advice. The full disclaimer is in [LICENSE](LICENSE).
