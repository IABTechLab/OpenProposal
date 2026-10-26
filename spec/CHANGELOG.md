# Changelog

Changes to the OpenProposal specification. Every normative entry references the
issue that caused it, so the comment record and the spec history line up.

## [Unreleased]

- § 5.5 — `time_zone` on the line item is the clock for `daypart` and
  `frequency_cap.period`: an IANA time zone name or `viewer_local`, REQUIRED
  with either. A `daypart` window is `{ days[], start, end }` in civil time,
  with `end` exclusive and later than `start`; a window that crosses midnight
  is two windows. `frequency_cap.period` is a calendar period in `time_zone`.
  Breaking ([#111](https://github.com/IABTechLab/OpenProposal/issues/111)).

## [3.0-draft-1] — 2026-09-22

Initial draft published for public comment. Ported from the working-group
document with no normative changes.

Notable from earlier working drafts:

- `audience_pricing` is **removed**, generalised into the `pricing` key on any
  `selectable` field (§ 3.1).
- Per-field mutability markers introduced (§ 3). See open question OQ-1.
- Explicit no-inheritance rule (§ 2): line items are fully self-contained.
- `channel` added as the line item discriminator; `committed_metrics[]`
  generalised to `{ metric, value, basis }` tuples, rather than a schema fork
  per channel.
