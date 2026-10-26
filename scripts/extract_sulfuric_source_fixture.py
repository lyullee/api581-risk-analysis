"""Extract visually checked 2016 sulfuric tables; runtime data and fixture share extraction."""
import hashlib
import json
import re
from pathlib import Path
from pprint import pformat

text=Path('tmp/pdfs/API-581-2016.txt').read_text(encoding='utf-8')
pages={n:text.split(f'=== PDF PAGE {n} ===')[1].split('=== PDF PAGE')[0] for n in range(365,373)}
def rows(body,width,count):
    result=[]
    for line in body.splitlines():
        line=re.sub(r'(\d)\s+\.(\d)',r'\1.\2',line)
        line=re.sub(r'(?<=\d),(?=\d)', '.',line)
        try: values=[float(v) for v in line.split()]
        except ValueError: continue
        if len(values) in (width+1,width+2):
            result.append(values[-width:])
    assert len(result)==count,(width,count,len(result))
    return result

def split(page,marker):
    return pages[page].split(marker,1)
cs_tail,ss304us=split(368,'Table 2.8.5.3')
ss304si,ss316us=split(369,'Table 2.B.5.4')
ss316si,a20us=split(370,'Table 2.8.5.5')
a20si,c276us=split(371,'Table 2.8.5.6')
c276si,b2=split(372,'Table 2.B.5.7 -')
b2us,b2si=b2.split('Table 2.B.5.7M',1)
raw={
    'carbon_steel':(rows(pages[365],9,32)+rows(pages[366],9,12),rows(pages[367],9,32)+rows(cs_tail,9,12)),
    'ss_304':(rows(ss304us,9,12),rows(ss304si,9,12)),
    'ss_316':(rows(ss316us,9,12),rows(ss316si,9,12)),
    'alloy_20':(rows(a20us,12,11),rows(a20si,12,11)),
    'alloy_c276':(rows(c276us,12,8),rows(c276si,12,8)),
    'alloy_b2':(rows(b2us,12,4),rows(b2si,12,4))}
concentrations={
    'carbon_steel':[100,98,96,93.5,91,87,83,78,72.5,67,62],
    'ss_304':[98,92.5,87,82,75,65,50,30,15,8,3.5,2],
    'ss_316':[98,92.5,87,82,75,65,50,30,15,8,3.5,2],
    'alloy_20':[98,92.5,85,70,55,45,35,25,15,8,5],
    'alloy_c276':[98,92.5,85,75,55,20,8,5], 'alloy_b2':[75,45,32.5,25]}
temperatures={
    'carbon_steel':([42,59.5,91,122.5],[6,15,33,50]),
    'ss_304':([86,104.5,140.5],[30,40,60]),'ss_316':([86,104.5,140.5],[30,40,60]),
    'alloy_20':([100,125,163.5,195.5],[38,52,70,91]),
    'alloy_c276':([125,137.5,162.5,187.5],[52,59,73,86]),'alloy_b2':([125,137.5,162.5,187.5],[52,59,73,86])}
tables={};cells=[]
for material,(us,si) in raw.items():
    cs=material=='carbon_steel';ss=material.startswith('ss_')
    velocities=[0,1,2,3,4.5,6.5,8.5,11.5,12] if cs else [2,6,7] if ss else [3,8.5,10]
    velocities_si=velocities if cs else [.61,1.83,2.13] if ss else [.91,2.59,3.05]
    nt=len(temperatures[material][0]);nv=len(velocities)
    for unit_index,data in enumerate((us,si)):
        unit='printed_si' if unit_index else 'printed_us_converted'
        cube=[]
        for i,c in enumerate(concentrations[material]):
            cube.append([data[i*nt+t] if cs else data[i][t*nv:(t+1)*nv] for t in range(nt)])
        tables[material+'_'+unit]=dict(concentrations=[c/100 for c in concentrations[material]],
            temperatures_k=[t+273.15 if unit_index else (t-32)*5/9+273.15 for t in temperatures[material][unit_index]],
            velocities_m_s=velocities_si if unit_index else [v*.3048 for v in velocities],rates=cube)
        for i,c in enumerate(concentrations[material]):
            for t in range(nt):
                for v in range(nv):
                    cells.append(dict(material=material,unit_basis=unit,acid_mass_fraction=c/100,
                        maximum_temperature_k=tables[material+'_'+unit]['temperatures_k'][t],
                        velocity_m_s=tables[material+'_'+unit]['velocities_m_s'][v],native_rate=cube[i][t][v],
                        disputed_304_cell=material=='ss_304' and c==75 and t==1 and v==2,
                        expected_rate_m_year=cube[i][t][v]*(.001 if unit_index else .0000254)))
assert len(cells)==1776
Path('src/api581/_sulfuric_tables.py').write_text('"""2016 sulfuric source tables; see scripts/extract_sulfuric_source_fixture.py."""\nTABLES = '+pformat(tables,width=120,sort_dicts=False)+'\n',encoding='utf-8')
Path('tests/fixtures/sulfuric_source_tables.json').write_text(json.dumps(dict(
    source_pdf_sha256=hashlib.sha256(Path('API-581-2016.pdf').read_bytes()).hexdigest(),
    note='Runtime tables and fixture share source extraction. OCR spaced/decimal-comma punctuation normalized after rendering review. SI CS velocity labels literal;30499mpy/2.51mm/y retained.',cells=cells),indent=2)+'\n',encoding='utf-8')
print('Sulfuric physical cells:',len(cells))
