# 선택적 실제 SLABx/SLABx-LH2 풀 연결

API581 Part3의 확산 모델 경계에 맞춘 외부 엔진 어댑터다. API581 수식 자체의 대체 구현이 아니다.
공개 함수는 `api581.api.dispersion.native_pool_centreline`, 입력/출력 모델은 NativePoolCentrelineInput/Output이다.
기본 런타임 의존성은 계속 Pydantic뿐이다. 네이티브 엔진은 pyproject의 slabx/slabx-lh2 extra로 선택 설치한다.

## 소스에서 확인한 매핑

검토한 로컬 프로젝트의 패키지 소스를 작업 폴더 tmp에 복사하여 별도 환경에 설치했다.
원본 엔진 저장소를 수정하지 않았다. 게시·다운로드 상태에 대한 주장이 아니라 이 소스 버전의 계약 검증이다.

- SLABx1.0.8: core.source.EvaporatingPool, core.plume.run_dispersion,
  submodels.atmosphere.Atmosphere, thermo.base.Substance/LegacyThermo/water_backend,
  post.concentration.concentration_field.
- SLABx-LH2 0.2.0: water_ice.with_sublimation, plume_width.plume_width_coupling,
  diagnostics.premise_summary.

공개 분자량 kg/kmol은 native kg/mol로 변환하고 습도 fraction은 native percent로 변환한다.
소수 기준 분자량 변환으로 native kg/mol 소수 리터럴과의1ULP 차이를 피한다.
이 작은 차이도 native 적응 격자를 바꿀 수 있어 직접 호출 비교에서 같은 물리 수치의 표기를 명시했다.
기타 입력은 이름에 있는 SI 단위를 그대로 넘긴다. 정상 비등점의 단순 물성 매핑은101325Pa로 제한한다.

## 지원 범위와 결과

상수·유한시간의 지면 순수 증발 증기 풀만 지원한다. vapor_source_rate는 액체 공급량이 아니라 증발 증기량이다.
원시 물성·기상·거칠기·안정도·풀 면적·지속/평균시간·농도 기준과 근거를 명시한다.
엔진이 없는 경우 engine_not_configured, 버전 불일치는 unsupported_engine_version,
계산 실패·타임아웃·프로토콜/출력 계약 위반을 각각 오류로 구분한다. 대체 확산식을 실행하지 않는다.

결과는 native 시간평균 중심선 volume fraction, 위치 배열, native 보간 거리, 경계 상태다.
Native distance_to가 기준에 도달하지 않아 NaN을 반환하면 not_reached와 null로 정규화한다.
마지막 노드에서도 기준 이상이면 boundary_censored이며 유효 threshold_distance_m은null이다.
native_threshold_distance_m은 원시 진단 거리를 보존한다. 피격 면적·LFL면적·구름 질량을 계산하지 않는다.
중심선 거리를 원의 반지름으로 바꿔 피해면적을 만드는 처리는 없다.

native x_max는 plume 격자 한계이고 puff가 그 너머로 이동할 수 있다.
따라서 plume_distance_limit_m으로 이름을 정하고 별도 puff_time_limit_s를 native t_max에 전달한다.
null t_max는 native 자동 puff시간을 보존한다. 실제 grid 최대 거리도 별도 반환한다.
used_source_area_m2와 effective_source_half_width_m은 엔진의 소스 확장을 추적한다.

LH2는 승화/결빙 보정 wrapper를 사용하고 plume-width 보정 여부를 필수 선택한다.
매번 새 Python subprocess에서 계산해 전역 패치가 호스트/다른 요청에 영향을 주지 않도록 한다.
1.25 등의 LFL 안전계수를 자동 적용하지 않는다.
LH2의 w_vertical/u_horizontal 전제가 위반되면 premise_violated와 유효 거리null을 반환한다.
중심선과 원시 보간은 진단용으로 보존한다. 전제 통과는 실험/현장 적합성 검증이 아니다.
기본 SLABx에는 이 LH2 전제를 임의 적용하지 않고 not_evaluated로 표시한다.

## 실행 검증

기본 회귀 테스트929개에는15개 신규 입력/프로토콜/오류 검증이 포함된다.
선택 의존성 없는 환경에서 수행하므로 대체 엔진의 수치 결과를 테스트용으로 생성하지 않는다.
실제 엔진 검증은 `scripts/verify_native_dispersion.py`를 선택 의존성이 설치된 Python으로 별도 실행한다.

- 직접 native 호출과 어댑터의 위치·농도 배열이 정확히 일치하고 보간 거리도 일치.
- 습도·분자량 단위 매핑, 기준 미도달 NaN→null, 마지막 격자 경계 검열.
- plume한계100m 이후 puff의 실제 격자가 계속 이어짐을 확인.
- LH2 실제 실행, 낮은 풍속에서 전제 위반과 유효 거리 차단.
- 두 LH2 보정 모드의 동시 subprocess 실행, 반복 결과 일치, 호스트 모듈 전역 함수 불변.

검증 환경: SLABx1.0.8,SLABx-LH2 0.2.0,NumPy2.3.5,SciPy1.18.1,CoolProp8.0.0.
명시적 예제 물성의 기본 풀 기준 거리는448.634787m, LH2는11.606286m였다.
LH2 낮은 풍속 예제의 최대 속도비는8.935795로 위반이다.
이 수치는 시험 입력의 매핑 재현성이며 실험 오차·현장 안전거리의 인증이 아니다.

외부 엔진 Python 소스 SHA256은 실행 결과에도 포함한다.
검증한 SLABx 지문: cce58647c6f3d741ef125a790032d521f09ebd636f1b4a9188e89f8a812fae8a.
LH2 지문: a7e27d03ae1f145acf779c07d2e6dbae9e99e8c73f77e690c25c0c6098fb0dd4.

일반 `api581.dispersion.DispersionRequest`는 별도 가변 프로파일/면적 계약 초안으로 남는다.
그 프로파일을 이 풀로 자동 축약하지 않는다. 실제 제트·시간소스·EOS/플래시·공간 컨투어·질량 적분,
LH2 source ledger/physical transition·LH2PoolX·현장 센서동화는 아직 연결되지 않았다.

후속 확장의 별도 native_pool_footprint/native_pool_flash_fire는 실제 횡방향 평면 면적과
플래시화재 연결을 지원한다. 이 문서의 중심선 전용 계약은 그대로 유지한다.
[공간 면적 검증](NATIVE_FOOTPRINT_VALIDATION.md)에 지원 범위와 경계 검열을 구분했다.
