# ACSCC 선별

Part2 §10.3(PDF196쪽)의 재질/환경 및FCCU 공급원료 변경 검토를 구현한다.
`api581.api.damage.acscc_screening(AcsccScreeningInput(...))`의 입력은
material,water_present,선택적water_ph,fccu_feed_sulfur_reduced,
fccu_feed_nitrogen_increased,screening_basis다.
탄소강/저합금강에서 물의pH>7.5 또는FCCU 원료의 황감소/질소증가가 평가 검토를 유발한다.
정확히pH7.5는 엄격한>조건을 통과하지 않는다. 원료 변경은 독립 검토 사유이며 수분/탄산염 존재 증명이 아니다.
물 존재 시pH를 요구하고 물 부재 시pH를 생략한다.
결과는evaluate_acscc,material_in_scope,evaluation_triggers로 모든 검토 사유를 유지한다.
H₂S 최저농도,시안화물 영향,탄산염 농도나PWHT 크레딧을 임의 추론하지 않는다.
기존acscc_susceptibility와acscc DF는 독립 호출 가능하며 자동 통합의pH 구간 경계 해석은 남아 있다.
재현: `python -m pytest tests/test_acscc_screening.py -q`.
재질3종×pH3조건,두 독립 원료변경,수분/pH/근거 충돌 등14개 사례를 검증했다.
선별 탈락은 전체 손상0이나 재질 면역을 뜻하지 않는다.

## 수치 pH와 감수성 표 연결

`damage.acscc_water_susceptibility(AcsccWaterSusceptibilityInput(...))`는
water_ph,carbonate_ppm,pwht,traditional_alkalinity_only,
carbonate_measurement_basis,service_fabrication_basis와 선택적shared_ph_boundary_policy를 받는다.
Table10.2(PDF199쪽) 공유pH8/9는lower_ph_row/higher_ph_row를 명시한다.
pH7.5는표의7.5_to_8에 속하며선별의엄격한>7.5조건과구분한다.
100ppm탄산염은고농도열이다. 전통적인P/M알칼리도만으로탄산염을산정한입력은note1에따라거부한다.
결과는감수성,선택pH구간,공유경계여부다. 자동DF통합은후속작업이다.
재현:`python -m pytest tests/test_acscc_water.py -q`의10개테스트로표행,탄산염경계,PWHT,
공유pH정책,알칼리도거부와미사용정책을확인한다.

## 공통 수질의 감수성→DF 연결

`damage.acscc_qualified_assessment(AcsccQualifiedAssessmentInput(...))`는screening,
water(위감수성입력),confirmed_cracking,unrepaired_cracks,
years_since_qualifying_inspection,inspections(a/b/c/d),inspection_basis를받는다.
선별과감수성pH가정확히같아야한다. 원료변경은검토사유지만수분없는조건에서
Table10.2를적용할수있다는뜻은아니므로수질없는통합은거부한다.
확인균열은PWHT의none판정보다우선하여effective_susceptibility를high로적용한다.
원래수질감수성과유효감수성은별도로보고한다. 미보수균열은FFS오류를우선반환한다.
검사효과성/적격경과기간은ACSCC전용근거가필요하며전체위험을산출하지않는다.
검증:`python -m pytest tests/test_acscc_qualified.py -q`.
pH8.5/탄산염100ppm/비PWHT/검사1A/2년은SVI1000,기본DF50,DF약107.17735다.
수질불일치,수분없는원료변경,균열우선및FFS거부를검증했다.
