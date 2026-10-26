# 여러 감육기구의 부식률·검사 유형 선택

원문 Part2 §4.5.2,§4.5.4(PDF150–151쪽)에 따라 계산한 개별 부식률을 공통 감육 계산에 연결한다.
`api581.api.damage.thinning_rate_selection(ThinningRateSelectionInput(...))`은
각 기구의 측정률/계산률/전문가 추정률에서 적용률을 선택한다.

입력 `mechanisms`는 하나의 부품·평가 표면·현행 공정 계획기간에 적용 가능한 기구 전체다.
각 항목은 `mechanism_id`, `thinning_type`(general/local), 선택적으로 `measured`와 `fallback`을 받는다.
둘 중 하나 이상의 부식률이 필요하며 기구 ID는 중복될 수 없다.
`applicability_and_period_basis`로 기구 목록과 공통 평가기간의 적합성을 명시한다.

대표성이 확인된 측정률은 같은 기구의 계산/추정 fallback보다 우선한다. 명시적인 측정률0도 유효하다.
측정률에는 `representative_for_current_period=True`와 측정 근거가 필요하다.
대표성이 없는 측정값을 조용히 버리고 fallback으로 대체하지 않는다.
측정값이 없으면 호출자가 지정한 calculated/estimated fallback을 사용한다.
원문은 이 둘 사이의 일률적인 우선순위를 정하지 않으므로 자동으로 순서를 만들지 않는다.
사용하지 않은 fallback은 결과에서 무시 여부를 표시하며 선택률에 영향을 주지 않는다.

모든 기구의 선택률 중 최댓값을 전체 적용률로 사용하고 합산하지 않는다.
최대률을 주는 기구는 `governing_rate_mechanism_ids`에 모두 보고한다.
동시에 어느 적용 기구라도local이면 검사 유형은local이다.
`governing_type_mechanism_ids`는 검사 유형을 지배하는 기구 목록이며 최대률 기구와 다를 수 있다.
기구별 선택률·선택 출처·fallback 무시 여부도 반환한다.

`damage.thinning_selected_mechanisms(ThinningSelectedMechanismsInput(...))`는
`selection`에 위 요청을 넣고 공통 벽두께·경과기간·강도·검사·조건을 더해 비AST 무클래드 DF를 계산한다.
일반적인 여러 기구 조합에서는 Table4.8의other 모니터링 행을 요구한다.
한 기구의 산/사워워터 크레딧을 다른 기구까지 적용하지 않으며 경험 기반 대체는 기존 명시 자격 경로를 유지한다.
특정 기구에 대한 모니터링 매핑은 해당 개별 기구 API에서 별도로 사용할 수 있다.
사용자 정의 사전확률도 공통 검사 입력으로 전달할 수 있다.

원문은 평가기간에 일정한 부식률을 가정하고 현행 공정의 장기 대표률을 권장한다.
이 API는 CML 시계열을 회귀하거나 공정 변경·단기 측정값의 적합성을 자동 판정하지 않는다.
서로 다른 표면의 손실, 클래드 순차 손실, 여러 손상기구의 최종 DF 합성은 이 최대률 선택과 별개다.
누락된 기구가 없거나 비적용임을 자동 증명하지 않으며 부품 전체 위험을 반환하지 않는다.

재현: `python -m pytest tests/test_thinning_selection.py -q`,
`python examples/multiple_thinning_mechanisms.py`.
예제는 일반 기구의 측정0.3mm/년이 계산0.5mm/년을 대체하고,
국부 기구의 추정0.2mm/년과 비교해 적용률0.3mm/년·검사 유형local을 선택한다.
10mm/5년의 손실분율은0.15, 예제 검사·강도 조건의 DF는약0.961996이다.
0측정률, 동률의 모든 기구, 입력 순서, 중복/누락·기간 근거 및 모니터링 제한을 검증했다.
