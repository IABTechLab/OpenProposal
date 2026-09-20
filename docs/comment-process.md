# Public comment process

How a comment on the OpenProposal draft becomes a change to the specification —
or a documented decision not to change it.

## Timeline

| Phase | Dates | What happens |
| :--- | :--- | :--- |
| **1. Comment period opens** | `TBD` | Draft frozen at a tagged version. Announcement published. Issues open. |
| **2. Comment period** | `TBD` → `TBD` | Anyone may file. Maintainers triage and label within 5 business days of filing, but do not resolve. Recommended minimum: 30 days; 45 for a draft of this size. |
| **3. Comment period closes** | `TBD` | No new comments enter the formal record. Later issues are labelled `post-comment` and considered for the following draft. |
| **4. Adjudication** | `TBD` → `TBD` | Working group works the queue. Every open comment gets a disposition. |
| **5. Disposition published** | `TBD` | [disposition-log.md](disposition-log.md) published in full. Commenters notified on their issue. |
| **6. Revised draft** | `TBD` | New draft tagged. Either ratification or a second comment period, depending on how much moved. |

> **Maintainers: fill every `TBD` above before announcing.** A public comment
> period with no closing date is not a comment period.

## Dispositions

Every comment in the formal record resolves to exactly one of these. The label
is applied to the issue and the reasoning is written in the closing comment.

| Disposition | Label | Meaning |
| :--- | :--- | :--- |
| **Accepted** | `disposition:accepted` | The change is made as proposed. |
| **Accepted with modification** | `disposition:accepted-modified` | The point is valid; the fix differs from what was proposed. The closing comment says how and why. |
| **Rejected** | `disposition:rejected` | No change. The closing comment gives the reason. "Out of scope" is only a reason if it says what the right scope is. |
| **Deferred** | `disposition:deferred` | Valid, but not for 3.0. The closing comment names the workstream or version it goes to. |
| **Duplicate** | `disposition:duplicate` | Covered by another issue, linked. The disposition on that issue governs. |
| **Withdrawn** | `disposition:withdrawn` | The commenter withdrew it. |

Rules the working group holds itself to:

1. **No comment is closed without a written reason.** Closing an issue with a
   reaction emoji is not a disposition.
2. **The commenter is notified** on their own issue, not only in the log.
3. **A rejection names the tradeoff.** If a proposal was rejected because it
   would break something else, say what.
4. **Implementation feedback outranks opinion.** A comment from someone who
   built against the draft and hit a wall carries more weight than a comment
   about how the draft reads.

## Who adjudicates

`TBD — name the working group, its chair(s), and the quorum or consensus rule
used to resolve a contested comment. Commenters are entitled to know who decided
and on what basis.`

Maintainers with write access are listed in
[`.github/CODEOWNERS`](../.github/CODEOWNERS).

## Labels

Triage labels, applied on filing:

| Label | Meaning |
| :--- | :--- |
| `comment` | General comment on the draft |
| `change-request` | Proposes specific normative wording |
| `open-question` | Relates to one of the 7 questions in § 8 |
| `implementation-feedback` | From someone who built against the draft |
| `editorial` | Typo, formatting, broken link — no normative effect |
| `normative` | Changes what the spec requires |
| `breaking` | Would break an implementation already built to the draft |
| `needs-info` | Cannot be dispositioned as filed; waiting on the commenter |
| `post-comment` | Filed after the comment period closed |

Section labels (`section:3-mutability`, `section:5.6-commercial`, …) are applied
so the working group can work the queue by area.

## Traceability

The record of the comment period is:

- the issues themselves, which are never deleted;
- [disposition-log.md](disposition-log.md), the summary table;
- the git history of `spec/openproposal-3.0.md`, where every normative commit
  references the issue that caused it.

A change to the spec with no issue behind it should not be in the history.
