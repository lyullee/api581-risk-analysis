# 아민 균열 선별 API

Part2 §7.3(PDF179쪽)의 탄소강/저합금강 및 산성가스 처리 아민 노출 조건을 구현한다.
`api581.api.damage.amine_cracking_screening(AmineCrackingScreeningInput(...))`은
material, acid_gas_treating_amine_present, screening_basis를 받는다.
아민 농도·종류·통상 온도·rich 서비스·PWHT만으로 선별에서 제외하지 않는다.
선별 탈락은 절차 범위 밖이며 다른 균열이나 전체 DF0을 의미하지 않는다.

`amine_cracking_screened_assessment(AmineCrackingScreenedAssessmentInput(...))`는
screening, 기존 SCC Assessment 형태의 cracking, susceptibility_and_inspection_basis를 받는다.
cracking에는 susceptibility, confirmed_cracking, unrepaired_cracks,
years_since_qualifying_inspection, inspections(a/b/c/d)를 넣는다.
감수성은 Figure7.1 또는 전문가 평가로 독립 확인해야 한다. 이 API는 그 그림을 자동 구현하지 않는다.
실제 금속온도·열추적·스팀아웃·용액 조성/이력을 검토한 근거와
§7.6.3의 적격 검사 기간·효과성 근거를 명시한다.

확인된 균열은high로 올리고 미보수 균열은FFS 오류를 우선 반환한다.
선별 탈락은 통합 계산에서 오류로 처리하며0DF를 발급하지 않는다.
Table7.2,Table6.3 및 식(2.26)의 기존 계산 경로를 재사용한다.
별도 아민 부식률 모듈은 감육용이므로 이 균열 감수성 판단을 대체하지 않는다.

검증: `python -m pytest tests/test_amine_screening.py -q`.
재질/노출6조합, 알려진 low SVI10·검사1A 기본DF1·2년 승수,
확인 균열high SVI1000·기본DF50,FFS 우선·선별 탈락·근거를 검증했다.
위 두 API의 범위에는 Figure7.1 자동 판정이 포함되지 않는다. 아래의 별도 API에서 제공한다.

## Figure7.1 자동 감수성 판정

`damage.amine_figure_susceptibility(AmineFigureSusceptibilityInput(...))`는
confirmed_cracking, unrepaired_cracks, stress_relieved, solution,
amine_group, maximum_metal_temperature_k, heat_traced,
steamed_out_before_water_flush, applicability_basis를 받는다.
solution은 fresh/rich/lean/lean_and_rich, amine_group은 mea_or_dipa/dea/other_treating_amine이다.
PDF183쪽 Figure7.1을 렌더링하여 분기를 대조했고 Table7.1에 따라 양쪽 노출은lean으로 처리한다.
확인 균열high, 미보수FFS, 유효 응력제거none 분기가 용액/온도 분기보다 우선한다.

인쇄된100/140/180°F를 정확히K로 환산한다. MEA/DIPA는 >180°F high,
100..180°F medium, 그 아래는 열추적/스팀아웃 시medium, 아니면low다.
DEA는 >180°F medium,140..180°F low, 그 아래는 열추적/스팀아웃 시low, 아니면none이다.
기타 처리 아민은 >180°F 또는 열추적/스팀아웃 시low, 아니면none이다.
fresh/rich만 노출된 경우 Figure7.1의 비lean 분기로none을 반환하되 다른 수소 손상을 제외하지 않는다.

`damage.amine_figure_assessment(AmineFigureAssessmentInput(...))`는
screening, service(위 입력), years_since_qualifying_inspection, inspections(a/b/c/d),
inspection_basis로 전체 Figure→SVI→검사→경과시간DF를 실행한다.
혼합 아민 그룹 분류·실제 최대 금속온도·유효 열처리·적격 검사 등은 자격 입력이다.
재현: `python -m pytest tests/test_amine_figure.py -q`.
14개 테스트에서 온도18사례, 저온 가열6사례와 노출/균열/FFS 및 DF 연결을 검증했다.
전체 유체 화학·현장 적합성이나 SSC/HIC/SOHIC 자동 적용성은 아직 포함하지 않는다.

공개 실행 예제: `python examples/amine_figure_assessment.py`.
DEA/lean·rich 동시 노출과 정확히180°F의 경계에서low, SVI10, 기본DF1,
2년 DF약2.14355를 확인한다. 추가 검증은 경계 바로 아래/위의 인접 부동소수점K값을 사용해
100/140/180°F 비교가 역환산 반올림으로 뒤집히지 않는지 확인한다.
해당 예제는 별도 wheel 설치 환경에서도 실제 실행한다.
