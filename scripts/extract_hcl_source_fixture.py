"""Independent extraction of visually checked source table rows for regression fixtures."""
import hashlib
import json
import re
from pathlib import Path

source = Path('tmp/pdfs/API-581-2016.txt').read_text(encoding='utf-8')
cells = []
for page, width, count, group_size, materials in [
    (326,5,14,14,['carbon_steel']), (327,5,14,14,['ss_304']),
    (328,5,9,3,['alloy_825','alloy_625','alloy_c276']),
    (329,9,6,3,['alloy_b2','alloy_400'])]:
    body = source.split(f'=== PDF PAGE {page} ===')[1].split('=== PDF PAGE')[0]
    rows = []
    for line in body.splitlines():
        match = re.search(r'(?<![\w.])(0\.50|0\.75|1\.0)\s+',line) if page >= 328 else re.match(r'^\s*\d',line)
        if match is None:
            continue
        values = []
        for token in line[match.start():].split():
            try:
                values.append(float(token))
            except ValueError:
                break
        if len(values) == width:
            rows.append(values)
    assert len(rows) == count*2, (page,len(rows))
    for i,row in enumerate(rows):
        si = i >= count
        j = i % count
        material = materials[j//group_size]
        for column,rate in enumerate(row[1:]):
            tindex = column//2 if page == 329 else column
            cells.append(dict(material=material,unit_basis='printed_si' if si else 'printed_us_converted',
                maximum_temperature_k=([38,52,79,93][tindex]+273.15) if si else (([100,125,175,200][tindex]-32)*5/9+273.15),
                ph=row[0] if page < 328 else None,
                chloride_mass_fraction=row[0]/100 if page >= 328 else None,
                oxidants_present=bool(column%2) if page == 329 else None,
                source_page=page,native_rate=rate,expected_rate_m_year=rate*(.001 if si else .0000254)))
assert len(cells) == 392
destination = Path('tests/fixtures/hcl_source_tables.json')
destination.parent.mkdir(exist_ok=True)
destination.write_text(json.dumps(dict(source_pdf_sha256=hashlib.sha256(Path('API-581-2016.pdf').read_bytes()).hexdigest(),
    note='Source-text rows independently extracted and checked against rendered PDF325-330. Physical cells; shared grades tested separately.',cells=cells),indent=2)+'\n',encoding='utf-8')
print('Source fixture:',len(cells),'physical cells')
