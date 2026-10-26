"""Optional CoolProp reference probe; not an implemented API581 flash API."""
import json
from pathlib import Path
import CoolProp
from CoolProp.CoolProp import PropsSI, PhaseSI

fluid='Propane'
p0,t0,p1=1e6,300.,101325.
cases=[]
for method,key in [('isentropic','Smass'),('isenthalpic','Hmass')]:
    conserved=PropsSI(key,'P',p0,'T',t0,fluid)
    temperature=PropsSI('T','P',p1,key,conserved,fluid)
    quality=PropsSI('Q','P',p1,key,conserved,fluid)
    recovered=PropsSI(key,'P',p1,key,conserved,fluid)
    assert abs(recovered-conserved)<=max(1.,abs(conserved))*1e-9
    assert 0<=quality<=1
    cases.append(dict(method=method,conserved_property=key,conserved_value_si=conserved,
        flashed_temperature_k=temperature,vapor_mass_fraction=quality,
        flashed_phase=PhaseSI('P',p1,key,conserved,fluid)))
result=dict(scope='Pure-fluid reference experiment only; not an API581 public implementation or mixture/LH2 validation',
    source='API5812016 Part3 §5.1.3 and STEP1.3,PDF539-541',engine='CoolProp',version=CoolProp.__version__,
    fluid=fluid,storage_pressure_pa_abs=p0,storage_temperature_k=t0,ambient_pressure_pa_abs=p1,cases=cases)
path=Path('docs/flash-reference-probe.json')
path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
