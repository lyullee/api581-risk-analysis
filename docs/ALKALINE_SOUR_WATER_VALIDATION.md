# 알칼리 사워워터 부식률 검증

기준: 제공된 API RP 581 제3판(2016), Part 2 Annex 2.B §7,
Tables 7.1/7.2/7.2M, PDF 378–381쪽 및 감육 분류 Table 1.2(PDF 323쪽).
원문 그림을 확인하여 표와 수식을 전사했다. 독립 공학 인증을 의미하지 않는다.

공개 진입점은 `api581.api.properties.h2s_partial_pressure`와
`api581.api.damage`의 다음 일곱 함수다.

| 함수 | 역할 |
|---|---|
| alkaline_sour_water_nh4hs_estimate | 원문 농도 근사식과 불일치 정책 |
| alkaline_sour_water_velocity_selection | 2상 기상/액체 충만 액상 유속 선택 |
| alkaline_sour_water_base_rate | SI/US 농도·유속 표 40셀 |
| alkaline_sour_water_pressure_adjustment | H₂S 부분압 보정·음수 계수 0 처리 |
| alkaline_sour_water_assessment | 적용성 확인부터 부식률·원문 감육 분류 |
| alkaline_sour_water_thinning_assessment | 동일 유속·부식률의 적격 감육 DF 연결 |
| sour_water_assessment | 공통 수분/pH 스크린으로 산성·알칼리 정량 경로 선택 |

농도는 0–1 질량분율, H₂S 기체 조성은 몰분율, 압력은 절대 Pa,
유속은 m/s, 최종 부식률은 m/year다. 원문 SI/US 표의 반올림 차이를 보존한다.
농도 2/5/10/15 wt%, SI 유속 3.05/4.57/6.10/7.62/9.14 m/s를 사용한다.
보간·주변 최대값 정책은 명시적으로 선택하며 표 외삽은 거부한다.

Table 7.1의 H₂S 과잉 분기는 NH₃가 아닌 **3 × H₂S**로 인쇄되어 있다.
기본값은 해당 분기를 거부하며 원문 그대로 사용할 경우 별도 근거가 필요하다.
정확히 H₂S=2×NH₃인 경계도 원문 분기가 없어 별도 정책·근거가 필요하다.
측정/이온 공정모델의 농도를 직접 제공할 수 있다. 근사값이 질량분율 1을
넘으면 진단값을 보존하되 통합 표 조회는 범위 오류로 거부한다.

압력 보정의 SI 기준은 345 kPa, 하부/상부 분모는 173/276 kPa다.
US 기준은 50 psia, 분모는 25/40 psia다. 음수 보정 계수는 원문대로
0으로 처리하고 원래 계수와 처리 여부를 출력한다. 이 0은 손상 부재의 증명이 아니다.
일반/국부 분류 임계값 6.1 m/s와 20 ft/s의 차이도 정책으로 보존한다.

신규 테스트 41개는 모든 표 셀, 농도 경계와 불일치 거부, 상별 유속,
압력 양쪽 분기·0 처리, SI/US 임계값, 수분/pH/재질 적용성,
통합 경로 일치 및 감육 연결을 검증한다.
[실행 예제](../examples/alkaline_sour_water_to_thinning.py)는 10wt%, 기상 7.62m/s,
H₂S 621kPa에서 기본 1.09mm/year × 2 = 2.18mm/year,
20mm 초기 벽두께·2년의 손실분율 0.218을 확인한다.

미완료: 혼합화학/EOS, 온도·탄화수소/수분비의 독립 정량 보정,
타재질 확장, 습윤 H₂S 균열 등 다른 손상기구의 자동 통합과 현장 검증.
HCl 정량 경로는 후속 확장에서 연결했다([검증 기록](HCL_VALIDATION.md)).

2026-10-24 검증 체크포인트: 전체 1608개 테스트 통과, 390개 함수/18개 분야.
wheel을 별도 환경에 재설치하여 모든 공개 함수의 타입·스키마·제한사항,
패키지 구현 현황·코드 지문 및 통합 예제를 확인했다. 해당 환경에는 FastAPI가 없다.
빌드 파일은 `dist/api581_engine-0.1.0-py3-none-any.whl`, 326665 bytes,
SHA-256 `a9a2b7bbe7749e40ca22ca46ede401aede6ca54ff2afdd29f9ea508a670eba97`.
