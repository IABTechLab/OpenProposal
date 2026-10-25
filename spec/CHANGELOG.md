# Changelog

Changes to the OpenProposal specification. Every normative entry references the
issue that caused it, so the comment record and the spec history line up.

## [Unreleased]

- § 2.1, § 5.1, § 5.2 — `channel` and `environments` are defined in AdCOM 1.0
  terms. Each impression has one `channel`, the first match in § 5.1.1, and
  each environment is a set of distribution channels and device types.
  `audio_streaming` is removed, and the Summary Representation carries
  `environments.available[]`
  ([#90](https://github.com/IABTechLab/OpenProposal/issues/90)).

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
