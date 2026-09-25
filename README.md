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
them. They will follow the first revision, after the comment period closes on
2026-10-22. Until then, [`examples/`](examples/) is the best reference for
shape. See [schema/README.md](schema/README.md).

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

OpenProposal Specification by IAB Tech Lab is licensed under a Creative Commons Attribution 3.0 License. To view a copy of this license, visit [creativecommons.org/licenses/by/3.0/](https://creativecommons.org/licenses/by/3.0/) or write to Creative Commons, 171 Second Street, Suite 300, San Francisco, CA 94105, USA.

By submitting an idea, specification, software code, document, file, or other material (each, a "Submission") to the OpenProposal repository, to any member of the IAB Tech Lab working group responsible for OpenProposal, or to the IAB Tech Lab in relation to OpenProposal / AAMP 3.0 you agree to and hereby license such Submission to the IAB Tech Lab under the Creative Commons Attribution 3.0 License and agree that such Submission may be used and made available to the public under the terms of such license. If you are a member of the IAB Tech Lab then the terms and conditions of the [IPR Policy](https://iabtechlab.com/ipr-iab-techlab/acknowledge-ipr/) may also be applicable to your Submission, and if the IPR Policy is applicable to your Submission then the IPR Policy will control in the event of a conflict between the Creative Commons Attribution 3.0 License and the IPR Policy.

Software code in this repository (scripts/ and .github/workflows/) is licensed under the Apache License, Version 2.0. See [LICENSE-CODE](LICENSE-CODE).

Read [CONTRIBUTING.md](CONTRIBUTING.md#ipr) before filing anything.

## Disclaimer

THE STANDARDS, THE SPECIFICATIONS, THE MEASUREMENT GUIDELINES, AND ANY OTHER MATERIALS OR SERVICES PROVIDED TO OR USED BY YOU HEREUNDER (THE "PRODUCTS AND SERVICES") ARE PROVIDED "AS IS" AND "AS AVAILABLE," AND IAB TECHNOLOGY LABORATORY, INC. ("TECH LAB") MAKES NO WARRANTY WITH RESPECT TO THE SAME AND HEREBY DISCLAIMS ANY AND ALL EXPRESS, IMPLIED, OR STATUTORY WARRANTIES, INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AVAILABILITY, ERROR-FREE OR UNINTERRUPTED OPERATION, AND ANY WARRANTIES ARISING FROM A COURSE OF DEALING, COURSE OF PERFORMANCE, OR USAGE OF TRADE. TO THE EXTENT THAT TECH LAB MAY NOT AS A MATTER OF APPLICABLE LAW DISCLAIM ANY IMPLIED WARRANTY, THE SCOPE AND DURATION OF SUCH WARRANTY WILL BE THE MINIMUM PERMITTED UNDER SUCH LAW. THE PRODUCTS AND SERVICES DO NOT CONSTITUTE BUSINESS OR LEGAL ADVICE. TECH LAB DOES NOT WARRANT THAT THE PRODUCTS AND SERVICES PROVIDED TO OR USED BY YOU HEREUNDER SHALL CAUSE YOU AND/OR YOUR PRODUCTS OR SERVICES TO BE IN COMPLIANCE WITH ANY APPLICABLE LAWS, REGULATIONS, OR SELF-REGULATORY FRAMEWORKS, AND YOU ARE SOLELY RESPONSIBLE FOR COMPLIANCE WITH THE SAME, INCLUDING, BUT NOT LIMITED TO, DATA PROTECTION LAWS, SUCH AS THE PERSONAL INFORMATION PROTECTION AND ELECTRONIC DOCUMENTS ACT (CANADA), THE DATA PROTECTION DIRECTIVE (EU), THE E-PRIVACY DIRECTIVE (EU), THE GENERAL DATA PROTECTION REGULATION (EU), AND THE E-PRIVACY REGULATION (EU) AS AND WHEN THEY BECOME EFFECTIVE.
