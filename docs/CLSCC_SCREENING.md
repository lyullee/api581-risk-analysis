# CLSCC 적용성 선별

`api581.api.damage.clscc_screening(ClsccScreeningInput(...))`은Part2 §12.3(PDF207쪽)을구현한다.
입력:material(austenitic_stainless_steel/other_material),actual_or_potential_wet_chloride_exposure,
operating_temperature_k,temperature_basis(printed_si/printed_us_converted),exposure_basis.
오스테나이트계SS,실제/잠재염화물과물노출,운전온도엄격히>38°C또는>100°F를모두요구한다.
인쇄SI/US경계가다르므로기준을명시하며정확한경계에서는온도조건을통과하지않는다.
업셋·잔류수압시험수·냉각탑비산·보온재/공정노출을포함한근거가필요하다.
농도하한이나Ni함량으로자동제외하지않고벌크농도의국부농축을추정하지않는다.
선별탈락은관찰균열의FFS평가를대체하거나전체DF0을뜻하지않는다.
검증:`python -m pytest tests/test_clscc_screening.py -q`의8개테스트로
경계/인접K값·재질/노출·단위반올림차이·근거를확인한다.
`damage.clscc_susceptibility(ClsccSusceptibilityInput(...))`는개별Table12.2M(SI)및Table12.2(US)감수성을제공한다.
`temperature_basis`를반드시선택하며,인쇄표의온도행을그대로적용하고행사이보간하지않는다.
SI의pH>10/93°C중복경계는`ambiguous_source`로거부하고,US의pH>10/200°F행은별도로정의한다.

## SI 선별→감수성→DF 통합

`damage.clscc_qualified_assessment(ClsccQualifiedAssessmentInput(...))`는screening,
ph_over_10,chloride_band_ppm(1-10/11-100/101-1000/>1000),chemistry_basis,
confirmed_cracking,unrepaired_cracks,years_since_qualifying_inspection,
inspections(a/b/c/d),inspection_basis를받는다.
선별온도와동일한온도를선택한Table12.2M또는Table12.2에사용하며SI/US기준을혼합하지않는다.
염화물이온의국부농도구간/pH와검사적격성은근거입력이다.
확인균열high,미보수FFS,선별탈락오류및pH>10/93°C공유경계오류를유지한다.
벌크농도농축·농도빈구간보간·전체위험은산정하지않는다.
검증:`python -m pytest tests/test_clscc_qualified.py tests/test_clscc_screening.py -q`의19개테스트.
50°C/pH≤10/11-100ppm/검사1A/2년은SVI500,기본DF25,DF약53.58867이다.
US200°F/pH>10행과SI93°C중복경계도각각검증한다.
