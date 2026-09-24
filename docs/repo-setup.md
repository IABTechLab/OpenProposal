# Repository setup checklist

Everything in this list is a **GitHub settings change that cannot be committed
to the repository.** The comment period opened on 2026-09-22; items still
unchecked are outstanding.

## Must do

- [x] **Replace `LICENSE`.** Specification: CC BY 3.0; code: Apache-2.0
      (`LICENSE-CODE`). `CONTRIBUTING.md § 6` and `GOVERNANCE.md` updated to
      match.
- [ ] **Fill every `TBD`.** Grep for it:
      `grep -rn 'TBD' --include='*.md' --include='*.yml' .`
      The working group, the chair(s), the decision rule, the adjudication
      dates and the conduct contact are still placeholders.
- [x] **Set the default branch to `main`** and make it the published draft.
- [ ] **Replace `.github/CODEOWNERS`** with the real team or usernames. A public
      comment period needs a named owner who responds.

## Repository settings

- [x] **Visibility: public.** It is the announced comment channel
      (`iabtechlab.com/AAMPv3` redirects here).
- [ ] **Issues: on.** They are the formal comment record.
- [ ] **Discussions: on.** For questions and thinking out loud.
      `.github/ISSUE_TEMPLATE/config.yml` already links to it, so the link is
      dead until you enable it. Suggested categories:
      *Questions*, *Ideas*, *Show and tell (implementations)*, *Announcements*
      (maintainers post only).
- [ ] **Wiki: off.** Everything normative belongs in `spec/`, under review.
- [ ] **Projects: on** if you want a triage board (see below).
- [ ] **Blank issues: disabled** — already set in `config.yml`, so every comment
      arrives on a form with a section and a perspective attached.

## Branch protection on `main`

- [ ] Require a pull request before merging.
- [ ] Require at least 1 approving review; require review from Code Owners.
- [ ] Dismiss stale approvals on new commits.
- [ ] Require status checks to pass: `Examples parse`, `Issue forms parse`,
      `Appendix A matches the body`.
- [ ] Require branches to be up to date before merging.
- [ ] Require conversation resolution before merging.
- [ ] Block force pushes and deletions. **The comment record must not be
      rewritable.**

## Labels

- [ ] Create the labels in [`.github/labels.yml`](../.github/labels.yml), by
      hand or with a label-sync action. Triage depends on them, and the
      disposition labels are what make the log reproducible.

## Tracking issues

- [ ] **File the seven open-question issues** and fill the links in
      [`open-questions.md`](open-questions.md). Label each `open-question` and
      pin them. These are where you most want comments to land, so they need to
      exist before anyone arrives.
- [ ] **Pin a "Start here" issue** stating the comment period dates, linking the
      draft and the process, and saying that no membership is required to
      comment.

## Triage board (optional but recommended)

A project board with columns *Filed → Triaged → Under discussion → Dispositioned
→ Landed*. Custom fields for `section` and `disposition`. The value is that at
the end of the period you can show the queue was worked, not just that issues
were closed.

## Releases and tagging

- [ ] **Tag the draft the day the comment period opens** — e.g.
      `v3.0-draft-1` — and link the tag in the announcement. Comments must point
      at a frozen artifact; "the draft" moves.
- [ ] Publish a GitHub Release against the tag with the comment-period dates in
      the body.
- [ ] Tag again at the close of the period, and again for the revised draft.

## Announcement

- [ ] Link the **tag**, not `main`.
- [ ] State the closing date.
- [ ] State explicitly that non-members may comment — otherwise most of the
      market assumes it cannot.
- [ ] Point at the seven open questions, not just the spec. Asking a specific
      question gets a specific answer; "thoughts welcome" gets silence.

## During the period

- [ ] Triage and label within 5 business days of filing (the commitment in
      [`comment-process.md`](comment-process.md)). Triage is not resolution —
      label it, confirm it was received, move on.
- [ ] Keep [`disposition-log.md`](disposition-log.md) current rather than
      reconstructing it at the end.
- [ ] Never delete an issue. Close with a reason.

## Relationship to the Google Doc

The doc this spec came from should be **set to view-only, or retired, with a
pointer to this repository**, the moment the comment period opens. Two live
copies of a normative draft, one of them with its own comment thread, is the
single most reliable way to lose comments and end up unable to say which version
anyone was reading.
