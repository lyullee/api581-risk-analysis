# PASCC 선별

`api581.api.damage.pascc_screening(PasccScreeningInput(...))`은Part2 §11.3(PDF201쪽)을구현한다.
입력은material(austenitic_stainless_steel/nickel_based_alloy/other_material),
sulfur_bearing_compounds_exposure,exposure_basis다.
적격재질과황화합물노출이함께있으면evaluate_pascc=True를반환한다.
운전중건조·저온·저탄소/안정화강종이나정지시세척/질소퍼지만으로선별에서제외하지않는다.
정지시공기/수분노출과완화조치는별도평가한다. 선별통과가모든Table11.2재질/열처리셀의적용을뜻하지않는다.
기존pascc_susceptibility와pascc DF는독립호출가능하며자격있는통합연결은남아있다.
검증:`python -m pytest tests/test_pascc_screening.py -q`의재질/노출6조합과근거거부7사례.
선별탈락은전체DF0이나재질면역을뜻하지않는다.

## Figure11.1 및 DF 통합

PDF206쪽 흐름도를렌더링하여운전/정지중S·O₂·H₂O노출과RP0170보호분기를확인했다.
`pascc_figure_susceptibility`는alloy(기존PasccSusceptibility),
sulfur_oxygen_water_during_operation/shutdown,qualified_rp0170_downtime_protection,
선택적protection_basis,confirmed_cracking,unrepaired_cracks,service_alloy_basis를받는다.
노출없음은none,노출있음은Table11.2이며자격있는보호는high→medium→low→none한단계감소다.
확인균열은보호/노출보다우선high,미보수균열은FFS오류다.
RP0170의실제이행적합성은자동검증하지않는다.
`pascc_qualified_assessment`는screening,service(위입력),years_since_qualifying_inspection,
inspections(a/b/c/d),inspection_basis를받아기존DF까지연결한다.
니켈재질선별과H/L-grade300SS·321SS전용표행의모순은거부한다.
혼합명명표행의실제합금일치는service_alloy_basis로독립확인해야한다.
재현:`python -m pytest tests/test_pascc_figure.py -q`의6개사례.
3감수성감소,균열/노출우선,FFS/보호근거및SVI500/1A/2년DF약53.58867을검증했다.

실행예제:`python examples/pascc_qualified_assessment.py`.
정지보호로medium→low를한번적용하고SVI50/검사1A/2년DF약6.43064를얻는다.
독립pascc호출과통합DF가같고니켈재질/SS전용표행모순3건및미보수FFS전파를검증했다.
이예제는별도설치wheel환경에서도실행한다.
