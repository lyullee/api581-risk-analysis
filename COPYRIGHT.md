# Copyright review record

## Included

- Original Python source under `src/`
- Original tests, examples, schemas, catalog and validation notes
- Generated JSON evidence containing identifiers, hashes, counts and links
- Public worked-example values used as clearly labelled fixtures

## Excluded from public distribution

The following local files are source documents or educational materials whose
redistribution rights have not been established. They are ignored by Git and
must not be uploaded to GitHub, PyPI or Zenodo:

- API-581, API-580, API-520 and API-510 standards or scans
- PDF/DOCX copies of standards, purchased reports and course materials
- Any source document containing copied tables or substantial standard text
- Local runtime databases, Nurion work directories, build products and tokens

The `.gitignore` rules intentionally exclude `*.pdf`, `*.doc`, `*.docx`,
runtime/build directories and credential-like files. Provenance uses hashes and
source locators instead of redistributing the source documents.

## Implementation policy

Numerical methods are independently authored from documented equations and
publicly available worked examples. Standard-derived constants and table cells
are kept only where necessary for the implementation and are accompanied by
source references and limitations. The project does not reproduce standard
chapters, figures or tables as a substitute for purchasing the standard.

This is a software copyright and distribution review, not legal advice. Before
commercial redistribution, obtain counsel's review of the final release and
the jurisdictions in which it will be distributed.
