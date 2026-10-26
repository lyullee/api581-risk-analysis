# 감육 기준 두께·평가기간·검사 이력

원문 Part2 §4.5.5–4.5.6(PDF151–152쪽)은 기준 두께와 시작일을 일치시키고
평가기간에 수행된 검사만 크레딧에 포함하도록 설명한다.
공개 함수는 `api581.api.damage` 아래에서 개별 호출하거나 통합할 수 있다.

| 함수 | 역할 |
| --- | --- |
| `thinning_assessment_period` | 공급 두께/설치일 또는 적격 측정 두께/검사일로 두께·경과기간 계산 |
| `thinning_inspection_history` | 같은 기준과 기간으로 A–D 검사 횟수 및 제외 사유 계산 |
| `thinning_history_assessment` | 기간·검사 이력·선택 부식률·prior·강도·조건을 감육 DF까지 연결 |

`baseline_type='furnished'`는 `furnished_thickness_m`와 `installed_at`를 사용한다.
`baseline_type='measured'`는 `measured_baseline`의 두께·검사 시점을 사용하며 공급 두께 입력과 혼용하지 않는다.
측정 기준은 고품질 검사, 높은 측정 정확도 신뢰 및 재설정 근거를 요구한다.
원문의 장기 손실 불일치, 공정 변경, 기준 두께 불일치 등 재설정 판단은 자동으로 추정하지 않는다.
설치≤측정 기준≤평가 시점이어야 하며 공급 두께 기준에서는 설치≤평가 시점을 요구한다.

모든 시각은 시간대가 있어야 하며 UTC로 비교·차감한다.
`days_per_year`와 `period_and_year_basis`는 명시적 연 환산 관례/기간 근거다.
표준이365.25일을 유일한 환산값으로 지정한 것으로 주장하지 않는다.
오프셋 전환 구간에서도 벽시계 차이가 아닌 실제 경과시간을 사용한다.

검사 기록에는 고유 ID, 실제 수행 시각, 효과성a/b/c/d/e, 부품·기구 적격 여부 및 근거가 필요하다.
기준 이전, 평가 이후, 부적격 검사 및 E등급은 크레딧에서 제외하고 사유를 남긴다.
기준 검사 ID가 기록에 다시 나타나면 수행 시각이 일치해야 한다.
동일 ID의 중복은 거부하며 효과성을 NDE 이름만으로 자동 지정하거나 등가 검사 횟수로 변환하지 않는다.
입력 기록이 실제 수행된 검사라는 사실·커버리지는 호출자가 정당화해야 한다.

원문은 기준일과 정확히 같은 시점의 검사에 대한 별도 포함 규칙을 주지 않는다.
`baseline_boundary_policy`의 include_baseline_time/exclude_baseline_time으로 명시 선택한다.
기준 두께 설정 검사를 사전정보와 검사 크레딧으로 중복 활용해도 되는지는 이 정책의 적용 근거에 포함해야 한다.
평가 시점과 정확히 같은 시점의 적격 검사는 포함한다.

통합 요청에는 `history`, [부식률 선택](THINNING_RATE_SELECTION.md)의 `selection`,
[기본/맞춤 prior](CUSTOM_THINNING_PRIOR.md)의 `prior`, `strength`, `conditions`, `qualification_basis`를 넣는다.
경과연수·검사 횟수를 별도로 입력하지 않으며 이력에서 계산한 값을 그대로 사용한다.
강도식의 시작 두께는 선택된 기준 두께와 같아야 한다.
일반/국부 검사 범위와 부식률의 공통 기간 적합성, 기타 모니터링 행 조건은 기존 자격 경로를 유지한다.

재현: `python -m pytest tests/test_thinning_history.py -q`,
`python examples/thinning_history_assessment.py`.
예제는2021년 측정 기준부터2025년 평가까지4년(365.25일 관례), 적격 B1/C1만 인정한다.
기준10mm·부식률0.3mm/년의 손실분율0.12와 예제 DF약0.721092를 얻는다.
UTC 동치·오프셋 전환·시각 경계·품질/정확도·충돌/중복·기준 두께 일치 및 Bayes 연결을 검증했다.
공정 변경 자동 감지, 검사 계획, 클래드/AST, 시계열 부식률 추정 또는 전체 자산 위험평가는 포함하지 않는다.
