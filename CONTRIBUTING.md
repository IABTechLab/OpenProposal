# Contributing to OpenProposal

OpenProposal (AAMP 3.0) is in **public comment**. This document explains how to
comment, what we do with your comment, and the terms you are agreeing to when
you file one.

**You do not need to be an IAB Tech Lab member to comment.** Anyone with a
GitHub account may file an issue or a pull request.

---

## 1. Before you file

- Read the current draft: [`spec/openproposal-3.0.md`](spec/openproposal-3.0.md).
- **Search existing issues.** Someone may already have raised it; add to their
  thread rather than opening a duplicate, so the disposition covers one
  discussion, not five.
- Check [docs/open-questions.md](docs/open-questions.md). If your point lands on
  one of the seven questions the draft explicitly asks, comment there.

## 2. Pick the right route

| Route | Use it for | Where it lands |
| :--- | :--- | :--- |
| **Comment** issue | Something is unclear, wrong, internally inconsistent, or missing. You are not proposing wording. | Triaged, dispositioned, logged |
| **Change request** issue | You are proposing specific normative wording, a new field, a changed marker, or a removal. | Triaged, dispositioned, logged |
| **Open question** comment | You are answering one of the 7 questions in § 8. | Feeds the resolution of that question |
| **Implementation feedback** issue | You built against the draft and hit something. **This is the most valuable kind of comment we receive.** | Triaged with priority |
| **Pull request** | You want to supply the exact diff for a change already discussed. | Reviewed against its issue |
| **Discussion** | You have a question, or want to think out loud before filing. | No disposition; not part of the formal record |

> Only **issues and pull requests** form the formal comment record. Discussions
> do not. If a discussion produces a real point, file it as an issue so it gets
> a disposition.

## 3. What makes a comment actionable

The comments that change the spec have these in common. The issue forms ask for
them, but the short version:

- **Cite the section.** `§ 5.6.1 commitment`, not "the commitment bit".
- **Say what breaks.** A concrete scenario — a seller, a buyer, a field, and the
  wrong outcome — beats a general objection. "A seller offering the same
  inventory as both PG and PMP cannot express different floors per mechanism,
  because `pricing[]` sits above `transaction_mechanism`" is actionable. "The
  pricing model is too simple" is not.
- **Say what you'd do instead**, even roughly. A rejected alternative is more
  useful to the working group than an unanswered complaint.
- **Declare your interest.** Tell us whether you are commenting as a buyer,
  seller, SSP, DSP, ad server, measurement vendor, agency or individual. It does
  not weight your comment, but it tells us where the draft is being read from.

## 4. Pull requests against the spec

Editorial fixes (typos, broken links, table formatting, a marker in Appendix A
that disagrees with the body) — send the PR directly, no issue needed.

Normative changes — **open an issue first.** A PR that changes what the spec
requires, without a discussion behind it, will be asked to back up into one. The
working group has to be able to show why a requirement changed.

Rules for any spec PR:

- One logical change per PR.
- If you touch a field, update **both** the body section **and** Appendix A and
  Appendix B. The body is normative; the appendices are generated from it and
  must not drift.
- If you touch a field that appears in an example, update
  [`examples/`](examples/) too.
- Use RFC 2119 keywords deliberately. MUST, SHOULD and MAY are not synonyms.

## 5. What happens next

Every issue filed during the comment period gets a disposition. See
[docs/comment-process.md](docs/comment-process.md) for the timeline, who
adjudicates, and what each disposition means.

## 6. IPR

<a name="ipr"></a>

**Read this before filing.**

- The specification is licensed under a
  [Creative Commons Attribution 3.0 License](https://creativecommons.org/licenses/by/3.0/).
  Code in `scripts/` and `.github/workflows/` is licensed under Apache-2.0
  ([LICENSE-CODE](LICENSE-CODE)). Full terms are in [LICENSE](LICENSE).
- By submitting an idea, specification, software code, document, file, or other
  material (a "Submission") — including an issue, comment, or pull request — you
  license that Submission to IAB Tech Lab under the Creative Commons
  Attribution 3.0 License, agree it may be made available to the public under
  that licence, and confirm you have the right to make it.
- If you are a member of IAB Tech Lab, the
  [IAB Tech Lab IPR Policy](https://iabtechlab.com/ipr-iab-techlab/acknowledge-ipr/)
  may also apply to your Submission, and where it applies it controls in the
  event of a conflict with the Creative Commons Attribution 3.0 License.
- **Do not file anything you consider confidential.** This repository is public.
  Rate cards, deal terms, client names and inventory data filed here are public
  the moment you press submit. Anonymise your examples.

## 7. Code of conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Debate
the specification, not the people commenting on it.
