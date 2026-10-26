# API RP 581 Risk Analysis Module

An unofficial, independently authored Python implementation of API-RP-581
risk-based inspection calculations and composable risk workflows.

> **Important legal and engineering notice**
>
> This project is not affiliated with or endorsed by the American Petroleum
> Institute. `API`, `API RP 581`, and related marks belong to their respective
> owners. The repository does not redistribute API standards or purchased
> source documents. Obtain the applicable standard under your own license.
> Results are software calculations, not a fitness-for-service decision,
> inspection release, operating authorization, or safety certification.
> Applicability, input quality, engineering assumptions, and site acceptance
> remain the user's responsibility.

## What this package provides

The package is published as `api581-engine` and imported as `api581`.
The project display name is **API RP 581 Risk Analysis Module**.

- 509 typed calculation registrations with Pydantic input/output contracts
- 861 API-RP-581 source-section records with section → calculation → test
  traceability
- Individual calculations and composable integrated workflows
- Level 1/Level 2 consequence and risk composition boundaries
- Four representative release-hole paths, effects, financial consequence,
  probability/frequency and portfolio aggregation APIs
- Optional SLABx 1.0.8 and SLABx-LH2 0.2.0 process-isolated adapters
- API 520 capacity-sizing utilities kept as a clearly separated companion
  namespace
- Digital-twin schemas, catalog queries, validation evidence and JSON receipts
- Reproducible local and Nurion PBS verification scripts

The current release is software-verified with external evaluation explicitly
out of project scope. It is not a third-party API conformity certificate.

## Install

```bash
python -m pip install api581-engine
```

For development and the full test suite:

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

Optional capabilities:

```bash
python -m pip install -e ".[source]"      # read local PDF source metadata
python -m pip install -e ".[flash]"       # CoolProp pure-fluid routes
python -m pip install -e ".[slabx]"       # SLABx 1.0.8 adapter
python -m pip install -e ".[slabx-lh2]"   # SLABx-LH2 0.2.0 boundary
```

The optional native packages are never silently replaced by an alternate
engine. Missing packages produce an explicit capability status or a typed
optional-engine error.

## Quick start

Every public calculation has a typed `*Input` model and a typed result. The
registry, schemas and catalog are available without learning internal module
layout.

```python
from api581 import Context
from api581.api import release

result = release.gas(
    release.GasInput(
        diameter_m=0.0254,
        upstream_pressure_pa_abs=1_000_000,
        temperature_k=300,
        molecular_weight_kg_kmol=23,
        heat_capacity_ratio=1.3,
    ),
    context=Context(asset_id="pipe-001"),
)

print(result.outputs.mass_rate_kg_s)
print(result.references)
print(result.limitations)
print(result.validation_evidence)
```

For a discoverable interface:

```python
from api581 import calculation_catalog, calculation_evidence

for item in calculation_catalog(domain="risk"):
    print(item.calculation_id, item.title, item.python_path)

print(calculation_evidence("risk/assessment"))
```

## Complete module map

All calculation IDs, Python paths, input/output schemas, references,
limitations and direct-test links are in [`docs/MODULE_CATALOG.md`](docs/MODULE_CATALOG.md)
and `src/api581/data/python-api.schema.json`.

| Domain | Scope |
|---|---|
| `frequency` | generic, adjusted and management/system failure frequencies |
| `damage` | thinning, cracking, corrosion, HTHA, brittle, fatigue and mechanism screening |
| `inspection` | effectiveness, equivalence, history and coverage factors |
| `reliability` | Poisson, Weibull, renewal and failure-history primitives |
| `release` | gas/liquid/two-phase release rates, holes, isolation and source partition |
| `properties` | representative fluids, mixtures, saturation and flash contracts |
| `effects` | jet fire, pool fire, flash fire, fireball, BLEVE, blast and radiation |
| `events` | ignition, mitigation, PRD and event-tree primitives |
| `consequence` | release, toxic, flammable, environmental and financial consequence composition |
| `financial` | repair, cleanup, business interruption and monetary aggregation |
| `risk` | POF/COF integration, risk matrices, portfolio and damage handoff |
| `planning` | target crossing and inspection-planning primitives |
| `level1` | Level 1 flammable/toxic consequence summaries |
| `level2` | Level 2 source, scenario, dispersion and consequence summaries |
| `prd` | relief-device history, leakage, failure and consequence boundaries |
| `tank` | atmospheric-tank inventory, shell/bottom thinning, environment and finance |
| `dispersion` | grids, source handoff and optional SLABx/SLABx-LH2 native boundaries |
| `api520` | companion pressure-relief capacity and sizing utilities; outside the API-581 clause ledger |

Each domain has focused validation notes under [`docs/`](docs/), including
the acid/sour/amine/CO2/HF/HCl/sulfidic mechanisms, tank routes, two-phase
events, native dispersion, radiation, blast, inspection and thinning models.

## Integrated workflow

The library deliberately separates calculations from orchestration. Use
individual functions for auditable steps, or use `Workflow`, `Step` and
`run_workflow` for a declarative graph. A risk assessment consumes explicitly
qualified damage factors and four-hole consequence outputs; it does not invent
plant applicability, inspection data, material properties or FFS conclusions.

```python
from api581.workflow import Step, Workflow, run_workflow

workflow = Workflow(steps=[
    Step(id="release", calculation_id="release/gas", input={...}),
    Step(id="risk", calculation_id="risk/assessment", input={...}),
])
result = run_workflow(workflow)
```

See [`examples/`](examples/) for direct composition, risk handoff, tank,
source partition, native dispersion, toxic and inspection-planning examples.

## SLABx and SLABx-LH2 boundary

Native engines are optional and process-isolated. The adapter records package
version/importability, source fingerprints, actual grid extent, censoring and
premise diagnostics. It does not claim that a native result is a site model,
does not apply an invented LH2 safety factor, and does not silently fall back
to another dispersion engine. See:

- [`docs/NATIVE_DISPERSION_VALIDATION.md`](docs/NATIVE_DISPERSION_VALIDATION.md)
- [`docs/NATIVE_JET_VALIDATION.md`](docs/NATIVE_JET_VALIDATION.md)
- [`docs/NATIVE_FOOTPRINT_VALIDATION.md`](docs/NATIVE_FOOTPRINT_VALIDATION.md)
- [`docs/NATIVE_ENGINE_EVIDENCE.json`](docs/NATIVE_ENGINE_EVIDENCE.json)

## Verification and reproducibility

Local release verification:

```powershell
python scripts/final_audit.py
python scripts/verify_provenance.py
python scripts/verify_completion_matrix.py
python -m twine check tmp/release-final-20261025br/*
```

Current evidence includes:

- 11,848 passing tests and 3 optional skips
- 108 reference fixtures
- 509/509 direct test references
- canonical Nurion PBS receipt: 64/64 shards passed
- efficient Nurion receipt: 10/10 shards passed
- 16,000 broad input invariant cases
- native suite: 9/9 scripts passed
- 66 supporting-text clauses machine-reviewed and 10 public-data reviewed

The reproducibility and handoff record is in:

- [`docs/FINAL_AUDIT.md`](docs/FINAL_AUDIT.md)
- [`docs/COMPLETION_AUDIT.md`](docs/COMPLETION_AUDIT.md)
- [`docs/completion-matrix.json`](docs/completion-matrix.json)
- [`docs/release-manifest.json`](docs/release-manifest.json)
- [`docs/DEVELOPMENT_STATUS.md`](docs/DEVELOPMENT_STATUS.md)
- [`docs/VERIFICATION_COMMANDS.md`](docs/VERIFICATION_COMMANDS.md)

## Copyright and public-release boundary

The public release contains original implementation code, original
documentation, generated schemas, hashes and test receipts. It intentionally
does **not** include API standard PDFs, DOCX files, purchased tables or copied
standard text. Source-document filenames, byte counts and SHA-256 fingerprints
are retained only as provenance metadata where needed.

Read [`NOTICE.md`](NOTICE.md) and [`COPYRIGHT.md`](COPYRIGHT.md) before
redistributing or adding fixtures. The Apache-2.0 license applies to original
repository work only; it does not license API standards or third-party source
documents.

## Development handoff

Start with [`docs/DEVELOPMENT_STATUS.md`](docs/DEVELOPMENT_STATUS.md), then
read [`docs/MODULE_CATALOG.md`](docs/MODULE_CATALOG.md),
[`docs/completion-matrix.json`](docs/completion-matrix.json), and the final
audit receipt. New calculations must register a typed input/output contract,
references, limitations, direct tests and both directions of traceability.
Do not commit local source PDFs, credentials, runtime databases, Nurion working
directories or generated build folders.

## License

Original code and documentation are licensed under [Apache License 2.0](LICENSE).
See [`NOTICE.md`](NOTICE.md) for trademarks, standards and third-party-source
boundaries.
