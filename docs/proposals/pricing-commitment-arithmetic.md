# Account for seller fees after selecting one price

Discussion wording for [#94](https://github.com/IABTechLab/OpenProposal/issues/94)
and [#115](https://github.com/IABTechLab/OpenProposal/issues/115), first written
against draft `44dfaaf618736219426c311ec997b6d37e94b950`. The arithmetic also
exercises the rate derivation discussed in
[#30](https://github.com/IABTechLab/OpenProposal/issues/30). This is a discussion
profile, not an OpenProposal wire validator. The specification is normative, and
its § 3.1, § 5.6, and § 5.6.5 state the arithmetic.

## The fee interpretation changes the available media spend

#94 treats `pricing[]` entries as alternatives. #115 adds seller fees as extra
entries and includes them in `commitment.amount`. An extra alternative cannot
simultaneously be an additive fee. Summing all entries instead loses the choice
of cost method, currency and transaction mechanism.

At USD 25 CPM, a USD 50,000 commitment containing a USD 2,500 production fee
leaves USD 47,500 for media:

```
media_spend   = 50,000 - 2,500 = 47,500 USD
derived_units = 47,500 / 25 * 1,000 = 1,900,000 impressions
```

Two million impressions would cost USD 50,000 before the fee, or USD 52,500
in total. Therefore #115's statement that `derived_units` is unaffected needs
revision if `amount` includes charges outside the unit rate.

## Wording for sections 3.1, 5.6 and 5.6.5

The specification carries most of this wording. Three points stay proposals here:
that a cost already in the unit rate isn't charged again, the sign rules on the
agreed rate, and the limit on rounding unit estimates.

`pricing[]` entries are alternative prices. A commitment MUST resolve to
exactly one entry. An implementation MUST NOT sum alternative
entries to compute the buyer's charge.

A selected option's `delta_flat` is a one-time seller charge for that line
item commitment. It MUST NOT enter the unit rate or become another pricing
alternative. A seller fee MUST NOT be a `pricing[]` entry. A cost already
included in the unit rate MUST NOT also be added as a flat charge. Each selected option that is not
already included contributes its charge once.

For `basis = spend`, `amount` is the seller total, on the same terms as
`agreed_rate`, including selected `delta_flat` charges (section 3.1). This does
not choose gross or net commission treatment, or decide the tax question in
#115. For a selected unit-rate method:

```
flat_charges  = sum of applicable one-time seller charges
media_spend   = commitment.amount - flat_charges
derived_units = media_spend / agreed_rate * rate_per
```

`rate_per` is 1,000 for CPM and CPMV, and 1 for CPC. For `basis = spend`, the
agreed rate MUST be positive. Flat charges MUST NOT exceed the spend commitment.
Zero remaining media spend yields zero informative units and still has to satisfy any
applicable minimum-unit requirement.

For `basis = units`, the committed units remain binding. The agreed rate MAY
be zero for added-value units, and MUST NOT be negative:

```
media_spend   = commitment.amount / rate_per * agreed_rate
seller_total  = media_spend + flat_charges
```

`commitment_bounds.spend` applies to the seller total on the same basis as
`agreed_rate`. The selected entry's currency applies to rates, flat charges and
spend bounds. No currency conversion is implied. `pricing[].unit_bounds` counts the
selected entry's own unit. Informative unit estimates MUST NOT be rounded in a way
that changes the committed amount or authorizes extra spend.

## Arithmetic inputs do not establish acceptance

The adapter consumes resolved, field-qualified adjustments that are not already
included. It starts with the chosen `list_rate`, adds applicable `delta_cpm`, multiplies
by `(1 + delta_fraction)` factors, and rounds once, half up, to 6 decimal places.
`0.20` means a 20 percent increase. Flat charges remain separate.

A negotiated rate is the `list_rate` of the next `version` (§ 5.6), so the adapter has
no separate input for an accepted rate, and options in effect apply their deltas to
the granted `list_rate`. A `list_rate` of USD 21.50 with USD 8.50 in `delta_cpm` gives
USD 30, and a `delta_fraction` of `0.20` on top gives USD 36.

The adapter does not evaluate `min_rate`, which is a hint (§ 5.6). Every successful
result carries `min_rate_check: not_checked`. A `min_rate` is checked only for numeric
shape and nonnegativity. In particular, a USD 19 `list_rate` against a USD 20
`min_rate` remains USD 19 in the calculation.

A successful calculation never authorizes a commitment, reservation or agreed order.

## Scope and reproduction

```
python3 scripts/check_pricing_fixtures.py
python3 scripts/check_pricing_fixtures.py --json
```

[`fixtures/pricing/cases.json`](../../fixtures/pricing/cases.json) contains fixed
expected outcomes independent of the calculator. Decimal strings and rational
outputs avoid binary floating point rounding. `"77/2"` is an exact rate, not a
proposed JSON wire type. `derived_units` rounds down to a whole unit (§ 5.6.5).
Currency checks cover shape, not ISO-4217 membership. The caller supplies a
mechanism-eligible choice.

The profile implements CPM, CPMV and CPC on a tax-exclusive basis only. That
fixture limit does not decide the normative tax basis. It rejects tax-inclusive
inputs, #103 print adjustments and flat credits. It cannot infer a mandatory fee
that is not represented by the resolved options. General fee objects, tax amounts,
invoice rounding and cost-method extensions need separate decisions. Unsupported
cases are not declarations that an OpenProposal document is invalid.

The vectors test this adapter's arithmetic. They read neither the specification nor
the examples. `scripts/check_examples.py` recomputes the examples against the tables.
