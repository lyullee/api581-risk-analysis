# 네이티브 제트와 API581 소스 분할 연결

Part3 §§5.3,5.7,5.8.5–5.8.6,5.9의 외부 확산 경계다.
SLABx1.0.8 HorizontalJet/VerticalJet, 선택 SLABx-LH2 0.2.0 승화/결빙·plume-width 보정을 사용한다.
이는 소스 API 매핑 검증이며 현장 모델 인증이 아니다. 기존 프로세스 격리·버전/코드 지문을 유지한다.

## 입력과 네이티브 처리

native_jet_centreline/native_jet_footprint는 수평 하류 또는 수직 상승 방향을 받는다.
총유량은 순수 방출물의 증기+액적 질량유량, 액적분율은1미만 질량분율이다.
팽창 후 대기압 출구 면적·온도·높이를 별도로 확인해야 한다. 상류 구멍 면적을 무조건 출구로 쓰지 않는다.
기본 상수 물성 매핑은101325Pa만 지원하며 속도는q/(rho_source·area)로 네이티브에서 계산한다.
출구 반폭은 기하학적 값이다. 풀의 반폭을 제트의 native half_width=1m와같은 물리량으로 표시하지 않는다.

네이티브는 비등점 아래 순수 증기를 비등점으로 올리고 액적이 있으면 온도를 비등점으로 고정한다.
require_consistent는 모순 온도를 거부하고 allow_native_clamp는 그 처리를 명시적으로 허용한다.
요청/사용 온도와 source_temperature_clamped를 반환한다. EOS/에너지 일치의 자동 증명이 아니다.
추가 액적 rainout/kinetic evaporation 옵션을 암묵적으로 켜지 않는다.

수직 출구 밀도가 대기 이하인 부력 상승 분기는 Briggs effective-source 변환으로
SLABx VerticalJet에 연결되며, 상승 높이·유효 소스 상태를 native diagnostics로 반환한다.
별도 plume 모델이나 임의 안전계수로 대체하지 않는다. 임의 yaw/하향/충돌·carrier 포함
handoff·LH2 physical-transition은 미연결이다.

## 분할에서 입력 유도

partitioned_jet_centreline/partitioned_jet_footprint는 SourcePartition과제트 형상/조건을 받는다.
유량·조성·지속시간의 중복 입력은 거부한다.

- native q = jet_total_rate_kg_s
- native liquid_fraction = entrained_liquid_mass_fraction
- native duration = jet_total_mass_kg / jet_total_rate_kg_s

풀 유량을 다시 제트에 더하거나 제트 총유량을 순수 증기량으로 오인하지 않는다.
빈 제트/양의 지속시간 없는 재고는 empty_jet_source,순수 액체는 unsupported_engine_source_domain,
엄격 온도 기준과분할 조성 충돌은 native_source_state_inconsistent로 실패한다.
기존 인쇄식/질량보존 해석·외부 flash/rainout 근거는 입력과제한사항에 보존한다.

## 근접장과 면적

수평 인계는x=1m,수직은 상승 계산 이후다. native_initial_downwind_distance_m과
native_near_field_status=not_reconstructed_before_native_handoff를 반환한다.
인계 전 전체 근접장을 재구성했다고 주장하지 않는다. 평면은 native downstream 표본 격자의 삼각형 보간이다.
첫 격자에서 기준 초과면 upwind 경계 검열로 면적null이다. 다른 경계와LH2 전제 위반 차단도 유지한다.
closed_on_supplied_grid는 공급 격자의 닫힘이며 근접장까지 포함한 완전한 피해영역 인증이 아니다.
좁은 제트의 횡격자/도메인 수렴은 별도로 확인해야 한다.

## 검증

17개 신규 기본 테스트로 입력·액적 제한·온도 선택·빈 소스 차단·동일 분할의 입력 유도·중복 입력 거부를 확인했다.
전체 11,848개 회귀 테스트가 통과했으며 3개는 환경 의존 항목으로 skip됐다.
실제 검증은 scripts/verify_native_jet.py로 수행한다.

- 수평/수직 각각 직접 native 위치·농도 배열의 정확한 일치.
- 출구 속도·native at_y 배열 일치, 인계 경계 면적 검열.
- 요청250K/액적.2의 실제231K 고정, 수직 부력 Briggs effective-source native 배열 일치.
- LH2 수평 실제 실행·전제 진단.
- 같은 분할→native와독립 native 입력의 정확한 일치, 분할 평면 실행.

시험 propane 입력의 수평 기준 거리는21.97525m였다.
반폭30m/횡257노드의 표본 면적은15.57067m2,분할 예제는28.35085m2였다.
이는 명시한 입력·격자의 재현성 앵커이며 실험 오차/현장 안전면적 검증이 아니다.
외부 코드 지문은 NATIVE_DISPERSION_VALIDATION.md와같고 실행 결과에도 포함한다.
실제 EOS/팽창/플래시·전체 근접장·시간변동·구름 질량·임의 방향/충돌·현장 적용성은 남아 있다.
