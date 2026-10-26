# API-581 Public-Data Engineering Review Record

External evaluation and reviewer signatures are explicitly out of scope for
this software project. The ten Part 2 Annex B damage-description clauses are checked
against the local API-581 source PDF and publicly available API-581 worked
example data. This record is an internal, reproducible evidence record—not a
third-party certification claim.

## Public sources

- Trinity Bridge worked example: API-581 pressure-vessel V-07 data
- Local `API-581-2016.pdf` source page fingerprints
- `docs/engineering-damage-review-draft.json`

## Clause coverage

| Clause group | Count | Status |
|---|---:|---|
| Annex B damage descriptions | 10 | public-data reviewed |
| External reviewer/signature | 0 | out of scope |

The machine-verifiable receipt is generated and checked by:

```powershell
python scripts/build_engineering_damage_review_draft.py
python scripts/verify_engineering_damage_review_draft.py
```
