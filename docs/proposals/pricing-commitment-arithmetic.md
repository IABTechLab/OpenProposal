# Resolve one price and account for seller fees once

Implementation feedback for [#30](https://github.com/IABTechLab/OpenProposal/issues/30),
[#94](https://github.com/IABTechLab/OpenProposal/issues/94) and
[#115](https://github.com/IABTechLab/OpenProposal/issues/115), against draft
`44dfaaf618736219426c311ec997b6d37e94b950`.

This is a proposed calculation profile with executable discussion vectors.
It is not an adopted requirement, an OpenProposal schema, or evidence of a
defect in a deployed implementation. Its fixture keys are an adapter format.

## The proposals currently produce incompatible results

#94 makes `pricing[]` entries alternatives and selects exactly one.
#115 puts seller-billed fees into additional `pricing[]` entries and includes
them in `commitment.amount`. Treating a fee as another alternative does not
add it to the selected price. Summing all rows instead loses #94's choice of
cost method, currency and transaction mechanism.

There is also an arithmetic consequence. At USD 25 CPM, a USD 50,000 spend
commitment containing a USD 2,500 production fee leaves USD 47,500 for media:

```
media_spend   = 50,000 - 2,500 = 47,500 USD
derived_units = 47,500 / 25 * 1,000 = 1,900,000 impressions
```

Computing units from the whole commitment gives 2,000,000 impressions. Those
units cost USD 50,000 before the fee, for a seller total of USD 52,500.
Therefore #115's statement that `derived_units` is unaffected needs revision
if `amount` includes charges not included in the unit rate.

## Proposed wording for joint resolution

This wording assumes adoption of the alternative-selection part of #94.
It supplies the missing fee basis in #115 and clarifies the counter described
in #30. The working group can decide these pieces together without adopting
the entire cost-method vocabulary.

### Sections 3.1 and 5.6: select the price and compose the rate

`pricing[]` entries are alternative prices, not additive charges. A commitment
MUST resolve to exactly one entry under the selection rule in #94. Only that
entry determines the cost method, rate, floor and currency. An implementation
MUST NOT sum alternative entries to compute the buyer's charge.

A selected option's `delta_flat` is a one-time seller charge for that line
item commitment. It MUST NOT enter the unit rate or be represented as another
alternative price solely to make it additive. A cost already included in the
unit rate MUST NOT also be added as a flat charge. Each selected option that
is not already included contributes its charge once.

Unless a final-rate counter has been accepted, the composed rate is the chosen
entry's `gross_rate`, plus applicable `delta_cpm` values, then multiplied by
each applicable `(1 + delta_pct)` factor. For this proposal, `delta_pct` is a
decimal fraction: `0.20` means a 20 percent increase. `delta_cpm` applies only
to CPM and CPMV. Flat charges are outside this calculation.

An accepted counter stated as the final composed rate MUST become
`agreed_rate` without reapplying the option rate adjustments. It MUST be bound
to the proposal revision, chosen price and resolved selections to which the
seller assented. A changed selection or revision requires a new applicable
acceptance. This rule does not prescribe an acceptance protocol. The floor
comparison uses that same final composed rate. A final-rate counter does not
waive separately identified flat charges unless the accepted terms explicitly
change those charges.

### Section 5.6.1: define the spend basis

For `basis = spend`, `amount` is the total pre-tax amount payable to the seller
for this line item, including applicable seller flat charges. It excludes
amounts payable by the buyer to other parties. When the selected cost method
has a unit rate, the amount available for those units is:

```
flat_charges = sum of applicable one-time seller charges
media_spend  = commitment.amount - flat_charges
derived_units = media_spend / agreed_rate * rate_per
```

`rate_per` is 1,000 for CPM and CPMV, and 1 for CPC. The agreed rate MUST be
positive. Flat charges MUST NOT exceed the spend commitment. Zero remaining
media spend yields zero informative units and still has to satisfy any
applicable minimum-unit requirement.

For `basis = units`, the committed units remain binding and the corresponding
seller total is:

```
media_spend  = commitment.amount / rate_per * agreed_rate
seller_total = media_spend + flat_charges
```

`min_spend` and budget bounds apply to the seller total on the same pre-tax
basis. Impression bounds apply only when the quantity is actually measured
in impressions; clicks or viewable impressions MUST NOT silently be treated
as the same quantity. The selected entry's currency applies to the rate,
flat charges and budget bounds. No currency conversion is implied.

The calculations above do not round informative quantities. A displayed
rounded estimate MUST NOT change the committed amount or imply additional
authorized spend. Invoice rounding and minor-unit settlement need a separate
rule if they are to be interoperable.

### Deliberate limits of this first proposal

- This profile addresses seller fees already expressible through selected
  `delta_flat` options. It does not invent a general fee object. If #115 needs
  mandatory charges that cannot use that structure, their representation
  needs a separate decision. They cannot be silently omitted.
- The proposed `billing.tax_inclusive` branch of #115 needs a tax amount or a
  deterministic tax calculation before its units can be derived. The runner
  rejects that branch rather than assuming tax is zero.
- #103's print discounts and surcharges introduce separate calculation bases.
  Its `value_pct` and conditions are not interpreted by this profile.
- Cost methods other than CPM, CPMV and CPC are not implemented here. An
  unsupported profile case is not a declaration that an OpenProposal is
  invalid. Extension definitions and transaction-mechanism eligibility stay
  with #94.
- A passing calculation establishes arithmetic consistency only. It does
  not establish seller acceptance, inventory reservation or an agreed order.

## Worked counter example

A base CPM of USD 30 plus USD 4, USD 1.50 and USD 3 option adjustments gives
USD 38.50. If the seller accepts USD 30 as the final rate for those selections,
the rate is USD 30. Applying the adjustments again incorrectly restores
USD 38.50. A separate USD 2,500 flat fee remains outside that rate: one million
committed impressions cost USD 32,500 in total.

## Reproduce the vectors

```
python3 scripts/check_pricing_fixtures.py
python3 scripts/check_pricing_fixtures.py --json
```

The corpus is [`fixtures/pricing/cases.json`](../../fixtures/pricing/cases.json).
Expected outcomes are fixed independently of the calculator. Cases cover
alternative selection, fee-inclusive spend, unit commitments, counters,
currency, floors, bounds, percentage composition and unsupported semantics.

Adapter inputs contain only the already resolved selected adjustments that
are not included in the base price. They do not extract selections from a
proposal or implement #22. Adjustment IDs are field-qualified to avoid
counting the same resolved adjustment twice. The caller has already confirmed
mechanism eligibility and seller acceptance of any `accepted_counter`.
`selection_key` is an opaque test binding, not an OpenProposal field or an
implementation of revision authentication.

Decimal strings and exact rational outputs avoid hidden binary floating point
rounding. For example, `"1000/3"` means the exact informative quantity one
thousand divided by three. This is a fixture convention, not a proposed JSON
wire type. Currency checks cover agreement and shape, not ISO-4217 membership.

No normative body or field index is changed by this discussion corpus. If
the wording is adopted, update sections 3.1, 5.6 and 5.6.1, the affected field
descriptions in Appendices A and B, and the committed examples together.
