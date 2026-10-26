# 선택 사건의 면적 위험 기여분

`api581.api.risk.area_event_contribution(AreaEventContributionInput(...))`는
독립적인 면적·빈도·확률 입력으로 선택 사건의 연간 면적 위험 기여분을 계산한다.
누락 사건을0으로 채워 전체 사건수목이 완성되었다고 주장하지 않는다.

입력은 `annual_release_frequency_per_year`, `weather_probability_given_release`,
`event_probability_given_release_weather`, 원시 `equipment_area_m2`/`personnel_area_m2`,
`probability_source`다. 확률의 조건은 각각 P(기상|누출), P(사건|누출,기상)이다.
그 곱은 누출 조건부 결합확률이며 기상과 사건의 독립성을 가정하지 않는다.
입력 면적과 누출빈도에는 이 두 확률이 미리 적용되어 있으면 안 된다.

출력은 결합확률, 선택 사건 연간빈도, 사건·기상 가중 면적,
설비/인명 및 그 최댓값의 위험 기여분(㎡/년)이다.
예를 들어 누출빈도0.01/년, 기상확률0.25, 사건확률0.2, 인명 면적80㎡이면
선택 사건 빈도0.0005/년, 가중 면적4㎡, 인명 위험 기여분0.04㎡/년이다.
생략한 다른 기상·사건·구멍의 영향이나 개인/사회적 위험·금전 위험을 뜻하지 않는다.

## 열역학부터 위험 기여분까지

`risk.flashed_pool_flash_fire_contribution(FlashedPoolFlashFireContributionInput(...))`는
`fire`에 [정상 풀 플래시 화재 입력](FLASHED_BOILING_POOL.md)을 받고,
`component_type`, `hole`, `management_score`, `total_damage_factor`, `damage_factor_source`,
`hole_release_basis`와 위 두 확률/근거를 받는다.
[실행 예제](../examples/flashed_pool_risk_contribution.py)는 공통 Context와 모든 입력을 보여준다.
공개 중첩 타입은 `risk.FlashedBoilingPoolFlashFireInput`으로도 접근할 수 있다.

선택한 비탱크 부품/구멍 GFF×공급 DF×관리계수로 연간 누출빈도를 계산하고,
순수 액체 플래시→rainout→정상 풀→native LFL 면적→화재→위험 기여분을 연결한다.
`hole_release_basis`는 지정 구멍과 입력 방출률/질량의 대응 근거다.
이 API가 구멍의 수력학·검출/차단·재고량·손상 적용성을 자동 산정하지는 않는다.
원시 화재 면적과 가중 면적을 모두 유지하며 조건부 확률과 빈도를 중복 적용하지 않는다.

`python scripts/verify_native_flashed_pool_risk.py`는 실제 CoolProp8.0.0/SLABx1.0.8 경로를 검증한다.
DRUM/small GFF8e-6/년, DF2, 관리점수500의 관리계수1로 누출빈도1.6e-5/년을 얻는다.
조건부 기상0.25와 사건0.2의 선택 사건 빈도는8e-7/년이다.
사건확률0일 때 원시 면적을 보존하고 위험만0으로 계산하며,
경계가 잘린 화재 면적은 위험 기여분으로 발급하지 않는 것도 검증한다.

범위는 `selected_hole_weather_steady_pool_flash_fire`다.
초기 과도·동시 제트·종료 후 풀과 다른 사건/기상/구멍은 미평가로 남는다.
모든 구멍의 최종 API581 위험평가나 완성된 자산 위험으로 해석하지 않는다.
