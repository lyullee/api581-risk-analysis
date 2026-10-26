"""Extract independent, visually checked 2016 HF table fixtures from local source text."""
import hashlib
import json
import re
from pathlib import Path

text = Path('tmp/pdfs/API-581-2016.txt').read_text(encoding='utf-8')
cells = []
for page in (376,377):
    body = text.split(f'=== PDF PAGE {page} ===')[1].split('=== PDF PAGE')[0]
    rows = []
    for line in body.splitlines():
        if page == 376:
            match = re.search(r'(?:<\s*10|2\s*10|210|<\s*3\.05|2\s*3\.05)\s+',line)
            if not match:
                continue
            # OCR splits1.78 in the SI86C low-velocity row; visually checked p376.
            numbers = re.findall(r'\d+(?:\.\d+)?',line[match.end():].replace('1 .78','1.78'))
            if len(numbers) == 9:
                rows.append([float(v) for v in numbers])
        else:
            if not re.search(r'\b(?:No|Yes)\b',line):
                continue
            values = [float(v) for v in re.findall(r'\d+(?:\.\d+)?',line)]
            if len(values) == 9:
                values = values[1:] # merged temperature in leftmost cell
            if len(values) == 8:
                rows.append(values)
    expected = 28 if page == 376 else 16
    assert len(rows) == expected,(page,len(rows))
    half = expected//2
    for i,row in enumerate(rows):
        si = i >= half
        pair = (i%half)//2
        branch = (i%half)%2
        temps = ([27,41,60,66,75,86,93] if si else [80,105,140,150,167.5,187.5,200]) if page == 376 else ([27,52,79,93] if si else [80,125,175,200])
        temperature = temps[pair]+273.15 if si else (temps[pair]-32)*5/9+273.15
        for j,native in enumerate(row):
            concentration = [1,2,5,6,63,64,80,81,81][j]/100
            cells.append(dict(source_page=page,material='carbon_steel' if page == 376 else 'alloy_400',
                unit_basis='printed_si' if si else 'printed_us_converted',maximum_temperature_k=temperature,
                hf_mass_fraction=concentration,velocity_m_s=(0. if not branch else (3.05 if si else 10*.3048)) if page == 376 else None,
                residual_category=('high' if j==8 else 'low') if page == 376 and j>=7 else None,
                aerated_or_oxidants_present=bool(branch) if page == 377 else None,
                native_rate=native,expected_rate_m_year=native*(.001 if si else .0000254)))
assert len(cells) == 380
Path('tests/fixtures/hf_source_tables.json').write_text(json.dumps(dict(
    source_pdf_sha256=hashlib.sha256(Path('API-581-2016.pdf').read_bytes()).hexdigest(),
    note='Independent source-text extraction checked against rendered PDF376-377. OCR1 .78 explicitly normalized to visually confirmed1.78.',
    cells=cells),indent=2)+'\n',encoding='utf-8')
print('HF source fixture:',len(cells),'physical cells')
