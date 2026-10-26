# 플래시에서 정상 비등 풀 확산까지

`api581.api.dispersion.flashed_boiling_pool_centreline`은 독립적으로 제공하는
순수 액체 플래시, Kletz rainout, 풀/제트 분할, 비등 풀 정상상태 및 native 중심선 계산을 연결한다.
입력 모델은 `FlashedBoilingPoolCentrelineInput`이며 프론트엔드나 HTTP 서버는 필요 없다.
[실행 예제](../examples/flashed_boiling_pool.py)는 모든 입력과 공통 Context 사용법을 보여준다.
선택 설치는 `pip install api581-engine[flash,slabx-lh2]`이며 baseline만 쓸 때는 `[flash,slabx]`다.

최종 압력과 대기압은 검증한 native 매핑의101325Pa다.
저장 상태는 액체여야 하며 검출/차단·재고 제한을 적용한 일정 방출률과 총 방출 질량을 받는다.
풀 공급률은 rainout 부분으로 한정한다. 비등점보다 높은 지면 온도,
정상 풀 면적의 현장 한도, 공급 기간보다 짧은 정상상태 도달시간을 요구한다.
비비등 풀, 무 rainout, 면적/시간 부족은 명시적으로 실패한다.

native에 넘기는 일정 증기원은 정상상태 도달 후부터 공급 종료까지다.
`steady_window_start_s`는 누출 시작 후 정상상태 도달시간,
`steady_window_duration_s`는 나머지 공급 기간이다. native 자체 시간 원점은 이 정상 구간의 시작이다.
`steady_evaporated_mass_kg`와 `startup_unmodeled_pool_mass_kg`를 구분하며,
후자는 정상상태 이전의 풀 공급 질량으로서 이 모델이 증발/축적 이력을 풀었다는 뜻이 아니다.
정상 구간 질량+초기 미모델링 풀 질량=풀 rainout 질량이며 제트 질량은 별도로 유지한다.
초기 과도 풀, 공급 종료 후 잔류 풀, 동시 제트의 확산·합산 농도는 계산하지 않는다.

포화 액체/증기 비열, 액체 밀도, 증발잠열, 비등점과 분자량을 native 상수 물성으로 매핑한다.
`native_property_basis`는 포화점 물성을 상수로 사용하는 공학적 적용 근거를 요구한다.
저장 상태 밀도나 벌크2상 밀도를 포화 액체 밀도로 사용하지 않는다.
평균시간은 정상 구간 길이를 넘을 수 없다. 농도 기준은 명시 입력이며 자동 LFL/독성 판정은 하지 않는다.

`python scripts/verify_native_flash_pool.py`로 실제 CoolProp8.0.0,
SLABx1.0.8 및 slabx-lh2 0.2.0 연결을 재현한다.
프로판 기준 사례의 정상 구간은 약59.6186초이며 미모델링 초기 풀 공급 질량은 약0.2376kg다.
정상 수소25K/1MPa 사례에서도 native LH2 경로, 전제 진단과 질량 회계를 확인했다.
이는 소프트웨어 연결 검증이다. 수소의 스핀 조성·극저온 열전달·실험/현장 적합성을 검증하지 않는다.
LH2 전제 위반 또는 경계 잘림은 기존 native 계약대로 최종 거리값을 무효화한다.
`flashed_boiling_pool_centreline`의 출력 범위는 중심선이며 영향 면적·화재/독성 결과·최종 위험으로 확대 해석하지 않는다.

## 2차원 영역과 플래시 화재

`dispersion.flashed_boiling_pool_footprint(FlashedBoilingPoolFootprintInput(...))`는 같은 입력에
`crosswind_half_span_m`, `crosswind_points_per_side`를 더해 native 평면 농도장을 계산한다.
공급 격자의 삼각형 선형 보간 초과면적이며 중심선 거리를 원형 면적으로 바꾸지 않는다.
경계 초과나 LH2 전제 위반 시 `threshold_area_m2`는None이며 진단용 면적/농도장은 유지한다.

`dispersion.flashed_boiling_pool_flash_fire(FlashedBoilingPoolFlashFireInput(...))`는
추가로 `criterion_role='qualified_lfl'`과 지면 수용점 `receptor_height_m=0.`를 요구한다.
호출자가 유체별 LFL과 평균시간 적용을 정당화해야 하며, 이 선언이 그 기준을 자동 검증하지는 않는다.
유효한 LFL 초과면적을 인명 영향 면적으로, 그0.25배를 설비 영향 면적으로 반환한다.
영역이 경계에서 잘리거나 전제 위반이면 화재 결과를 발급하지 않는다.
점화 확률·사건수목·GFF·손상계수는 적용하지 않으며 전체 위험을 반환하지 않는다.

[실행 예제](../examples/flashed_pool_flash_fire.py)와
`python scripts/verify_native_flashed_pool_footprint.py`는 실제 두 native 엔진 연결을 재현한다.
프로판 예제에서 횡방향257/513노드의 면적은 약136.92/136.22㎡다.
이 차이는 횡방향 격자 민감도 확인이며 하류 격자·평균시간·전체 수렴 또는 물리적 검증을 뜻하지 않는다.
동일한 기준/격자의 footprint와 fire 면적 일치, 의도적 경계 잘림 거부 및 정상 수소/LH2 경로를 검증했다.
초기 과도 풀·동시 제트·종료 후 풀의 영향은 여전히 포함하지 않는다.
