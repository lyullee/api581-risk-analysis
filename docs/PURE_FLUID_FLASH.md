# 순수 유체 플래시 API

선택 설치: `pip install api581-engine[flash]`.
`api581.api.properties.pure_fluid_flash(PureFluidFlashInput(...))`로 호출한다.
필수 입력은 fluid, storage_pressure_pa_abs, final_pressure_pa_abs,
method(isentropic/isenthalpic), qualification_basis다.
저장 상태는 `storage_temperature_k` 또는 `storage_vapor_mass_fraction` 중 정확히 하나로 정의한다.
전자는 단상 PT 상태, 후자는 압력과 평형 증기 질량분율로 지정한 포화 상태다.
두 값을 동시에 제공하거나 모두 생략하면 입력 검증에서 거부한다.
CoolProp8.0.0이 없는 기본 환경에서는 optional_engine_missing 오류를 반환한다.

원문 Part3 §5.1.3/STEP1.3(PDF539–541)의 순수 유체 경로다.
프로판1MPa/300K→101325Pa 등엔트로피 기준 결과는231.036214644K,
평형 증기 질량분율0.3442614682다. 실제 선택 엔진으로 공개 타입 API 호출을 확인했다.
입력·저장 좌표·선택 엔진 부재 검증16개 테스트가 통과했다.

출력은 최종 평형 증기 질량분율이며, 저장 유체에서 추가 기화한 비율과 다를 수 있다.
`storage_phase`와 `storage_vapor_mass_fraction`은 저장 상태를 나타내며,
`vapor_mass_fraction_change`는 최종 분율에서 저장 분율을 뺀 부호 있는 차이다.
이 차이는 증기 질량분율 변화이며 별도의 비평형 기화 속도나 rainout 비율이 아니다.
저장 액체/기체의 분율은 각각0/1로 분류한다. 포화 PT로 상태를 확정할 수 없거나
액체/기체로 분류할 수 없는 초임계 저장 상태는 명시적으로 거부한다.
압력·분율 입력은 삼중점 압력 이상/임계압 미만의 순수 유체 평형에 한정하고,
0/1 끝점과 그 사이의 분율을 허용한다. `storage_temperature_k` 출력은 EOS로 정한 저장 온도이며
`storage_state_basis`는 `pressure_temperature`/`pressure_quality`로 입력 경로를 식별한다.
기존 API581 rainout/jet 분할의 flash_mass_fraction에 무조건 대입하지 않는다.
초기2상의 평형 플래시도 최종 분율과 부호 있는 차이를 반환한다. 혼합물·LH₂ 검증은 남아 있다.
현재 단계는 순수 유체 한정 백엔드 공개이며 전체 유체/EOS 검증 완료가 아니다.

추가 실제 엔진 검증: 두 플래시 방법의 프로판 기준값, 단상 액체/기체의 증기분율0/1,
Air/R410A 의사순수 유체 거부를 확인했다. 이름 형식만으로 순수 유체를 판정하지 않고
엔진의 pure 메타데이터를 확인한다. 재현: `python scripts/verify_native_flash.py`(flash 선택 의존성 필요).
427개 API의 타입·스키마·패키지 구현 현황·코드 지문·기존 예제도 재빌드 wheel 설치 환경에서 검증했다.

## 액체 플래시와 방출 분할 연결

`api581.api.release.pure_liquid_flash_partition(PureLiquidFlashPartitionInput(...))`는
위 플래시 입력에 `adjusted_mass_rate_kg_s`, `released_mass_kg`, `equation_basis`,
`atmospheric_partition_basis`를 더해 사용한다. 초기 액체 상태만 허용한다.
질량과 유량은 검출·차단·재고 제한을 적용한 값을 넣으며, 최종 압력의 대기 조건 적용 근거를 명시한다.
Kletz rainout과 풀/제트 분할을 연결하고 플래시 상태 및 각 성분의 질량·유량을 반환한다.
`equation_basis='api581_printed'`는 식(3.102)의 인쇄식을 유지한다.
`post_flash_mass_balance`는 별도로 표시한 질량보존 해석이며 공식 정오표로 주장하지 않는다.
증기분율이0.5보다 큰 프로판 사례에서 두 해석의 차이와 질량·유량 합계를 실제 엔진으로 검증했다.
기체/초기2상 저장 상태는 이 액체 전용 방출 분할 연결에서 거부한다.
압력·분율0으로 지정한 포화 액체는 허용한다. 초기2상의 rainout/액적 조성 연결은 남아 있다.

## 초기2상 평형 플래시

```python
from api581.api import properties

result = properties.pure_fluid_flash(properties.PureFluidFlashInput(
    fluid="Propane", storage_pressure_pa_abs=1e6,
    storage_vapor_mass_fraction=.9, final_pressure_pa_abs=101325.,
    method="isentropic", qualification_basis="Qualified pure-propane equilibrium EOS basis",
))
```

이 사례의 최종 증기분율은0.8857022756860086이며 변화는 음수다.
응축을0으로 잘라내거나 최종 분율을 새로 증발한 비율로 표기하지 않는다.
`scripts/verify_native_flash.py`는 두 방법×네 초기 분율에서 초기 혼합물 보존량과
최종 상태 보존량을 대조하고, 포화 PT 모호성·압력 범위·액체 전용 연결 거부를 검증한다.
