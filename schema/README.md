# Machine-readable schema

**Coming.** Schemas are not published with this first draft; they will follow
the first revision after the comment period closes.

The draft in [`../spec/openproposal-3.0.md`](../spec/openproposal-3.0.md) is
prose and tables. A JSON Schema is deliberately not published alongside this
first draft, because publishing one now would freeze decisions the comment
period exists to make — in particular:

- whether per-field mutability belongs in the object at all (OQ-1), which
  determines whether a `selectable` field is an object with `available[]` /
  `included[]` / `deltas` or a bare value;
- whether the `environments.available[]` list survives contact with real inventory (OQ-7).

A schema will follow the first revision. Until then, the parseable examples in
[`../examples/`](../examples/) are the best available reference for shape, and
the body of the spec is normative where they disagree.

If you have built a schema against the draft, please file
[implementation feedback](https://github.com/IABTechLab/OpenProposal/issues/new?template=implementation-feedback.yml) —
what you had to decide in order to write it is exactly the information the
comment period needs.
