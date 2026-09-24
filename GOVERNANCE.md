# Governance

> **This document is a scaffold. Maintainers must fill the `TBD` sections before
> the repository is announced.** A public comment period without a named
> decision-maker and a stated decision rule is not credible — the first question
> a commenter asks is "who decides, and how do I know my comment was read?"

## What this repository is

The working repository for the OpenProposal object model, part of AAMP 3.0, at
IAB Tech Lab. It holds the draft specification, the public comment record, and
the disposition of every comment received.

## Roles

| Role | Who | What they can do |
| :--- | :--- | :--- |
| **Working group** | `TBD` | Decides dispositions. Approves normative changes. |
| **Chair(s)** | `TBD` | Runs the process. Breaks deadlock per the decision rule below. |
| **Editor(s)** | `TBD` | Holds the pen on `spec/`. Merges approved changes. Keeps the appendices in sync with the body. |
| **Maintainers** | `TBD` | Triage and label issues, merge editorial PRs, keep the disposition log current. |
| **Commenters** | Anyone with a GitHub account | File issues and pull requests. No membership required. |

Write access is defined in [`.github/CODEOWNERS`](.github/CODEOWNERS).

## Decision rule

`TBD — how a contested comment resolves. Name the standard (consensus, rough
consensus, a vote with a stated quorum), who is eligible to participate in it,
and what happens when the working group cannot agree.`

Whatever the rule, these hold:

1. **Every comment gets a written disposition.** No issue is closed without a
   reason. See [docs/comment-process.md](docs/comment-process.md).
2. **The body of the spec is normative.** Appendices are generated from it. CI
   fails if they drift.
3. **No normative change lands without an issue behind it.** The history has to
   show why a requirement changed.
4. **Implementation feedback outranks opinion.** Evidence from someone who built
   against the draft carries more weight than a reading of it.

## Anti-trust and IPR

Participants are reminded that this is a forum of competitors. Do not discuss
pricing, rate-setting, market allocation, or refusals to deal. Comments on the
spec concern what the object model can *express*, never what anyone should
charge.

The illustrative rates in [`examples/`](examples/) are fictional and exist to
demonstrate field shape.

IPR terms are in [CONTRIBUTING.md § 6](CONTRIBUTING.md#ipr) and
[LICENSE](LICENSE). IAB Tech Lab members are also subject to the
[IAB Tech Lab IPR Policy](https://iabtechlab.com/ipr-iab-techlab/acknowledge-ipr/).

## Changing this document

Via pull request, approved by the chair(s).
