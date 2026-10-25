# Account for seller fees after selecting one price

Discussion wording for [#94](https://github.com/IABTechLab/OpenProposal/issues/94)
and [#115](https://github.com/IABTechLab/OpenProposal/issues/115), against draft
`44dfaaf618736219426c311ec997b6d37e94b950`. The arithmetic also exercises the
final-rate reading discussed in [#30](https://github.com/IABTechLab/OpenProposal/issues/30).
This is a proposed profile, not an adopted requirement or an OpenProposal wire
validator. The normative specification is unchanged.

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

## Proposed wording for sections 3.1, 5.6 and 5.6.1

This wording assumes adoption of the alternative-selection rule in #94.

`pricing[]` entries are alternative prices. A commitment MUST resolve to
exactly one entry under that rule. An implementation MUST NOT sum alternative
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

`min_spend` and budget bounds apply to the seller total on the same basis as
`agreed_rate`. The selected entry's currency applies to rates, flat charges and
budget bounds. No currency conversion is implied. Informative unit estimates MUST NOT
be rounded in a way that changes the committed amount or authorizes extra spend.

## Arithmetic inputs do not establish acceptance

The adapter consumes resolved, field-qualified adjustments that are not already
included. Its provisional #30 calculation starts with the chosen `gross_rate`,
adds applicable `delta_cpm`, then multiplies by `(1 + delta_pct)` factors.
`0.20` means a 20 percent increase. Flat charges remain separate.

If the caller supplies an already accepted final-rate counter, that rate replaces
the composed rate without applying option rate deltas again. The caller must
have established acceptance for the bound proposal revision and selection.
`selection_key` is an opaque fixture binding, not an acceptance protocol.

The adapter does not evaluate floor eligibility. Every successful result carries
`floor_check: not_checked`. A posted floor is checked only for numeric shape and
nonnegativity. In particular, an explicitly accepted USD 19 rate against a posted
USD 20 floor remains USD 19 in the calculation. The floor does not veto acceptance
already established by the caller.

How a counter resolves automatically, how selected adjustments compose the floor,
and how seller assent is authenticated remain in #30. That discussion proposes
applying rate adjustments to the base floor. This profile neither adopts that
proposal nor silently compares a final rate with an uncomposed floor. A successful
calculation never authorizes a commitment, reservation or agreed order.

## Scope and reproduction

```
python3 scripts/check_pricing_fixtures.py
python3 scripts/check_pricing_fixtures.py --json
```

[`fixtures/pricing/cases.json`](../../fixtures/pricing/cases.json) contains fixed
expected outcomes independent of the calculator. Decimal strings and rational
outputs avoid binary floating point rounding. `"1000/3"` is an exact informative
quantity, not a proposed JSON wire type. Currency checks cover agreement and
shape, not ISO-4217 membership. The caller supplies a mechanism-eligible choice.

The profile implements CPM, CPMV and CPC on a tax-exclusive basis only. That
fixture limit does not decide the normative tax basis. It rejects tax-inclusive
inputs, #103 print adjustments and flat credits. It cannot infer a mandatory fee
that is not represented by the resolved options. General fee objects, tax amounts,
invoice rounding and cost-method extensions need separate decisions. Impression
bounds are checked only for CPM; clicks and viewable impressions are not silently
treated as the same quantity. Unsupported cases are not declarations that an
OpenProposal document is invalid.

If the fee wording is adopted, update the affected body sections, field
descriptions in Appendices A and B, and committed examples together. The executable
profile is supporting discussion evidence, not a replacement for those changes.
