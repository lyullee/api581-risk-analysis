# 사용자 정의 감육 사전확률

원문 Part2 §4.5.3(PDF150–151쪽)은 Table4.5의 권장 사전확률 외에도 실제 경험과
두께 측정 신뢰도에 근거한 사용자 정의 사전확률을 허용한다. PDF151쪽을 시각 대조했다.
기존 low/medium/high 선택은 유지하고 공통 `Posterior` 모델에 이 경로를 추가했다.

```python
from api581.api import damage

result = damage.thinning_posterior(damage.ThinningPosteriorInput(
    custom_prior_probabilities=[.3, .3, .4],
    custom_prior_basis="Owner-qualified actual experience and thickness-confidence basis",
    inspections_a=1,
))
```

`confidence` 또는 `custom_prior_probabilities` 중 정확히 하나를 지정한다.
사용자 정의 경로는 비어 있지 않은 `custom_prior_basis`가 필수다.
세 값은 상태1/2/3의 확률이며 각각 기대 부식률의1/2/4배 상태다.
각 값은0..1의 유한값이고 합은1이어야 한다. 합의 반올림 오차1e-9만 정규화한다.
다른 합을 자동 보정하거나 사전확률을 현장 데이터에서 자동 추정하지 않는다.

`damage.thinning_prior_selection(ThinningPriorSelectionInput(...))`은 같은 선택 입력을 받아
적용된 사전확률, table4_5/qualified_custom 경로, 표 신뢰도 및 확률0인 상태 번호를 독립적으로 반환한다.
사전확률0은 양의 검사 우도로 갱신해도0이다. 임의 확률 하한을 넣지 않으며
모든 상태가0인 벡터는 거부한다. 극단적인 사전확률 선택의 적합성은 호출자가 정당화해야 한다.

공통 검사 입력을 쓰는 무클래드·클래드·개별 부식 감육 조합에도 적용된다.
출력 사후확률·DF의 기존 형태는 유지하고 입력 스냅샷에 선택/근거를 기록한다.
검사 기간 적격성, 일반/국부 검사 범위 및 신뢰도 적합성은 기존 자격 조건을 유지한다.
맞춤 사전확률이 검사 횟수·효과성·부식률을 바꾸거나 추가 검사 크레딧을 만들지는 않는다.

재현: `python -m pytest tests/test_custom_thinning_prior.py -q`,
`python examples/custom_thinning_prior.py`.
기본3행 보존, 알려진 Bayes 결과, 확률0과 대량 검사 수의 수치 안정성,
중복/누락/합/범위/근거 검증 및 부식→감육 전파를 확인했다.
예제에서 같은 벽 손실·부식률과 검사1A를 유지한 채 prior만[.3,.3,.4]로 바꾸면
DF는 약7.32377→83.00613으로 변한다. 이는 민감도 예제이며 경험 자료의 실제 보정 결과가 아니다.
