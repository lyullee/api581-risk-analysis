# 순수 유체 포화 물성 API

선택 설치 `pip install api581-engine[flash]`는 검증한 CoolProp8.0.0을 설치한다.
Part3 §5.1.3–5.1.4 STEP1.4 및 §5.7.4.2–5.7.4.3(PDF540–541,544)에 필요한
순수 유체의 비등점·증기압을 각각 독립 Python API로 제공한다.

```python
from api581.api import properties

result = properties.pure_fluid_saturation_pressure(
    properties.PureFluidSaturationPressureInput(
        fluid="Propane", pressure_pa_abs=101325.,
        qualification_basis="Qualified pure-propane EOS applicability basis",
    )
)
print(result.outputs.bubble_temperature_k)
```

`pure_fluid_saturation_temperature(PureFluidSaturationTemperatureInput(...))`는
`pressure_pa_abs` 대신 `temperature_k`를 받는다. 나머지 입력은 동일하다.
두 함수는 포화 압력, 기포점·이슬점 온도, 포화 액체/증기 밀도,
포화 액체/증기 정압비열, 증발잠열, 분자량(kg/kmol), 엔진 버전을 반환한다.
순수 유체의 기포점·이슬점은 같다. 물성은 공존 곡선에서 평가하며
저장 상태나 임의 플래시 상태의 물성으로 대체해서는 안 된다.

[풀 증발 연결 예제](../examples/saturation_to_pool.py)는 프로판의 비등 풀과
물의 비비등 풀을 구분하고 기존 정적 풀 증발 API에 물성을 전달한다.
비비등 풀의 지면 온도 증기압과 식(3.105)의 저장 온도 입력을 구분한다.
지속 공급과 면적 조건을 통과해야 사용할 수 있는 증기원을 반환하는 기존 제한을 유지한다.

실제 엔진 검증은 `python scripts/verify_native_saturation.py`로 재현한다.
두 유체의 대기압 비등점, 압력↔온도 왕복, Clapeyron 관계,
의사순수 유체 거부, 삼중점 아래·임계점 경계 거부 및 두 풀 예제를 확인했다.
이는 EOS 내부 일관성과 API 연결 검증이며 전체 유체의 실험적 검증은 아니다.
혼합물·고체/준안정 상태·초임계 포화는 지원하지 않는다. 삼중점 이상/임계점 미만만 허용한다.
LH₂, 현장 전열·풀 퍼짐·독성/가연성·연소열 검증은 이 API에 포함되지 않는다.
