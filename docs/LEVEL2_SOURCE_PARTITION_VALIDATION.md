# Level2 방출상·rainout·액적 소스 분할 검증

기준: 제공된 API RP581 제3판(2016), Part3 §5.3와§5.7.2–5.7.3,
식3.95–102(PDF541–543),STEP7.3–7.6(PDF545).
식3.98–102는 원본 페이지 렌더링과 대조했다.

## 공개 함수

`api581.api.release`에 다음6개 독립 함수와 정적 입출력 모델을 추가했다.

| 함수 | 계산 |
| --- | --- |
| `level2_release_phase` | 저장압/포화압/대기압에 따른 방출구 상 판정 |
| `level2_orifice_rate` | 판정 상의 이상기체·액체·보수적2상 rate |
| `kletz_rainout_fraction` | 입력 플래시 분율로 Kletz rainout |
| `rainout_rate_split` | 가중 후 전체 rate→풀/제트 |
| `jet_liquid_entrainment` | 명시한 기준의 제트 내부 액적 분율 |
| `level2_source_partition` | 풀·제트·증기·액적의 rate와질량 |

압력은 절대Pa,질량은kg,유량은kg/s다. 분율은 질량 기준이며 조성의 몰분율과 다르다.
방출구의 상은 저장상 또는 최종 대기 플래시 후 상과 같은 개념이 아니다.

## 상 판정과 보수적2상 rate

식3.95–97의 엄격한 내부 영역은 다음과 같이 판정한다.

- Psat>Ps>=Patm: vapor.
- Ps>Psat>Patm: two_phase.
- Ps>=Patm>Psat: liquid.

인쇄 부등식은 Psat=Ps에서 vapor/two_phase가 중복되고 Psat=Patm은 양쪽 엄격 부등식에서 빠진다.
이 경계는 상None과 경계 상태를 반환한다. rate 계산에 사용하려면
`qualified_boundary_phase`와공백 아닌`boundary_phase_source`를 같이 넣어야 한다.
명확하게 판정한 상과 모순되는 선택은 거부한다.
Ps=Patm은 구동 압력0으로 분리해 상을 추정하지 않고 rate0을 반환한다.
Ps<Patm은 이 배출 모델의 영역 밖이다.

vapor는 기존 이상기체 식3.6/3.7을 재사용한다.
liquid는 기존 식3.3을 사용한다. two_phase는§5.3.4가 허용한 보수적 액체식 근사로 계산하며
출력 `rate_method=liquid_conservative_two_phase`로 구별한다.
이는 HEM/Omega·실제유체·플래시 유동을 구현한 것이 아니다.
포화압과 필요한 기체/액체 물성은 사용자가 확정한다.

## Rainout와제트/풀

Kletz 식3.98–99는 `rainout=max(0,1-2*flash_fraction)`이다.
플래시 분율은 별도 물성 해석의 입력이며 이 함수가 플래시를 풀지 않는다.
대상 유체·2상 상태에 대한 경험 상관식의 적용성은 별도 검증 대상이다.

풀 rate는 전체 가중 후 rate×rainout,제트 rate는전체 rate×(1-rainout)이다.
제트에는 액적이 포함될 수 있으므로 제트 총 rate를 순수 증기 rate로 간주하면 안 된다.
풀 유입은 이후 풀 증발 모델의 입력으로 사용할 수 있다. 풀 증발량을 여기서 자동 가산하지 않는다.

## 인쇄 액적식과 별도 질량수지 해석

식3.102의 분자는 **stored_liquid_fraction × flash_fraction**으로 인쇄되어 있다.
`api581_printed`는 이를 분모(1-rainout)로 나눈 값을 재현한다.
원문 분율의 의미를 임의로 빼기식으로 수정하지 않는다.
결과가0–1 밖이면 독립 진단 함수가 수치를 보존하되 `physical_range=False`이고,
실제 소스 분할 함수는 이 결과를 사용하지 않는다.

`post_flash_mass_balance`는 별도로 공급한 **플래시 후 전체 증기 질량분율**을 사용한다.
증기+rainout<=1을 확인하고 남은 제트 안에서 증기/액체 분율을 구한다.
경계에서 나눗셈이1을미세하게 초과하는 부동소수점 오차만1로제한한다.
이 해석은 독립적인 보존 관계이며 API 공인 정오표나 EOS 결과라고 주장하지 않는다.

예를 들어 저장 액체분율1,플래시분율.8,rainout0이면 인쇄식의 제트 액체분율은.8이다.
별도 플래시 후 증기분율.8을 넣은 질량수지 해석은 액체분율.2를 준다.
따라서 두 기준을 조용히 교환하지 않는다. **인쇄식 결과가0–1 안에 있어도
EOS가 제공한 플래시 후 조성과 일치함을 증명한 것은 아니다.**

rainout1이면 제트의 질량분율 분모가0이므로 조성은None이다.
분할 결과의 제트 rate·질량은0이다. 이때 양수 플래시 후 증기를 동시에 공급하면 질량수지 해석은 거부한다.
단순히 증기분율0이나1을 임의 지정해 실제 제트가 존재하는 것처럼 표현하지 않는다.

## 소스·확산 연결

`level2_source_partition`은 조정된 전체 rate와제한된 방출 질량을 별도 입력으로 받는다.
두 값은 호출자가 검지/차단·재고·방출시간에 맞게 공급해야 한다.
풀+제트=전체,제트 증기+제트 액체=제트라는 rate/질량 보존을 확인했다.
입력에는 rainout 근거와플래시 물성 근거를 보존한다.

`examples/source_partition_handoff.py`는 보수적2상 오리피스와 기존`magnitude`를 연결하고
Kletz·명시적 질량수지 기준을 사용해 풀·제트를 분할한다.
풀은 비등 증발 함수로 연결하고 제트 총 rate/증기분율로 `DispersionRequest`초안을 준비한다.
풀과제트의 위치·온도·시간 이력을 하나의 소스로 조용히 합치지 않는다.
실제 엔진 실행은 하지 않으며 slabx/slabx-lh2 상태는 계속`not_configured`다.
증기분율이None인 완전 rainout은 제트 요청을 만들지 않아야 한다.

## 검증과 남은 범위

`tests/test_source_partition.py`는 상별 압력 조건·포화압 경계·근거 있는 선택·영 구동 압력,
기존 액체/이상기체식 대조,Kletz7조건,rate 보존,두 액적 기준의 차이,
인쇄식 비물리 값의 진단/사용 거부,조성·rate·질량 보존,완전 rainout/증기와근거 누락을 검증한다.
실제 EOS/플래시·응축·실험 rainout·액적 크기/후속 증발·HEM/Omega·LH2 적용성·네이티브 엔진 매핑은 남아 있다.
