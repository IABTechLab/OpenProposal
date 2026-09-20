# Machine-readable schema

**Not yet published.**

The draft in [`../spec/openproposal-3.0.md`](../spec/openproposal-3.0.md) is
prose and tables. A JSON Schema is deliberately not published alongside this
first draft, because publishing one now would freeze decisions the comment
period exists to make — in particular:

- whether per-field mutability belongs in the object at all (OQ-1), which
  determines whether a `selectable` field is an object with `available[]` /
  `included[]` / `pricing` or simply a value;
- whether `catalog_ref` stays (OQ-2), which determines whether every field is a
  `oneOf` between an inline value and a reference;
- whether the `environments[]` enum survives contact with real inventory (OQ-7).

A schema will follow the first revision. Until then, the parseable examples in
[`../examples/`](../examples/) are the best available reference for shape, and
the body of the spec is normative where they disagree.

If you have built a schema against the draft, please file
[implementation feedback](../../../issues/new?template=implementation-feedback.yml) —
what you had to decide in order to write it is exactly the information the
comment period needs.
