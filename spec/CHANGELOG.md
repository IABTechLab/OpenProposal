# Changelog

Changes to the OpenProposal specification. Every normative entry references the
issue that caused it, so the comment record and the spec history line up.

## [Unreleased]

- § 2.1, § 5.2 — `placement` on the line item states what every impression
  is, in AdCOM 1.0 and OpenRTB 2.6 terms: rewarded, interstitial, video
  placement subtype, skippability, playback, API frameworks and refresh.
  `plcmt` is REQUIRED for video ads. Breaking
  ([#89](https://github.com/IABTechLab/OpenProposal/issues/89)).

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
