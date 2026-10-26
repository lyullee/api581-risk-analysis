# 개발 상태

2026-10-25. 세션 목표는 진행 중이며 API 581 전체 구현 완료로 표시하지 않는다.

## 구현된 실행 기반

잔여 범위는 [검토 큐](REMAINING_WORK_REVIEW.md)에서도 추적한다. 원본 목차 상태의 미구현 표지는
일부 상위 절에서 API 연결 누락을 포함하므로 실제 미구현 계산 수로 해석하지 않는다.

- import 기반 Python 라이브러리. 공개 진입점은 `api581.api.<분야>.<함수>`.
- 509개 계산의 정적 타입 함수·입출력 모델과 JSON Schema 계약. HTTP 실행 경로는 제거했다.
- 선언형 워크플로: 앞 계산 출력을 참조해 통합 실행, 실패 시 최종 성공 결과 미발급.
- 공통 설비·부품 ID, 관측시각, 상관 ID, 입력 원본 리비전.
- 입력 스냅샷, 코드 지문, 판본·수식 출처, 제한사항, SQLite 실행 이력.
- 2016년 원문 목차에서 추출한 861개 조항 항목과 부분 구현/미구현 상태. Part 1 PDF TOC 중간 빈 페이지를 보존해 §7·§8까지 포함한다.
- 런타임 `coverage_summary()`에서도 절별 `technical_scope_review`/`supporting_text_review` 분류와 상태 집계를 보존하며, wheel 설치 후에도 동일 ledger를 조회할 수 있다.
- `review_queue()`와 `calculation_evidence()`로 절→계산 및 계산→절 역방향 추적을 필터 가능한 Python API로 제공한다. 외부 평가는 범위에서 제외하며 상태는 `software_verified_external_review_out_of_scope`로 명시한다.
- `coverage_summary()`는 표준 절 연결이 없는 4개 보조 항목(`release/integrate-profile`, `reliability/poisson-probability`, `dispersion/native-engine-capabilities`, `risk/portfolio`)도 별도 목록으로 반환한다.
- `coverage_summary()`는 계산별 `validation_counts`와 명시적 `scope_boundary_count`도 반환해 애플리케이션이 검증 수준과 지원 경계를 별도 표시할 수 있다.
- `coverage_summary()`의 `validation_by_domain`은 18개 분야별 native fixture/software-only 및 직접 테스트 참조 수를 제공해 QA 우선순위를 계산 가능하게 한다.
- `coverage_summary()`의 `scope_status_counts`는 Part/Annex 7개 범위별 절 상태를 제공하며, release verifier가 합계를 861개 원문 heading과 대조한다.
- `calculation_evidence()`는 `software_test_modules`를 통해 직접 계산 ID를 참조하는 테스트 모듈을 함께 반환하며, 매핑은 `docs/software-test-evidence.json`과 wheel 내부 manifest로 고정한다.
- 현재 manifest는 509개 계산 중 129개에 대해 직접 테스트 모듈 참조를 보존하고, 그중 20개는 공개 `evaluate()` 경계를 실제 호출한 모듈까지 별도 기록한다. 나머지 380개는 공통·간접 회귀 검증으로만 분류한다.
- 등록된 509개 계산 모두 `limitations`를 보유한다. 원문 절 연결이 없는 API 520 utility 계산은 출처를 임의 생성하지 않고 engineering utility로 별도 분류한다.
- `audit_coverage()`가 계산 제한사항 누락도 release 불변조건으로 검사한다.
- `reference-fixture-evidence.json`은 frequency/generic·adjusted, release/type, risk/matrix·assessment-from-damage, consequence final-area, flash-fire, management factor, Weibull, Poisson 확률, 선형 release 적분, 원형 누출공 면적, 실측 두께감소 부식률, 포트폴리오 위험 합산, four-hole 통합 위험평가, bundle material factor/교체비, Level 2 jet/pool 결합/final area의 독립 산술 fixture 19건을 별도 기록하며, native 검증으로 승격하지 않는다.
- `scripts/verify_reference_fixtures.py`가 19개 fixture를 public registry로 재실행해 expected output과 비교하며 CI release gate에 포함된다.
- Part 1 §2-§3의 원문 참고문헌 22개, 정의 80개, 약어 125개는 `api581.standard` 읽기 전용 조회 API와 패키지 JSON으로 제공한다. 이는 문서/용어/보고서 연계용이며 계산 적용성 판정을 대체하지 않는다.
- 동일 모듈의 `StandardSection`/`sections()`는 861개 절의 상태, 범위, 연결 계산 ID, 다음 증거 요구를 typed 형태로 노출한다.
- `standard.documentary_coverage()`는 Part 1 §2-§3 메타데이터가 추출된 6개 heading과 전체 supporting-text 검토 큐(170개, 그중 원문 상태 `not_implemented` 76개)를 분리해 반환한다. 메타데이터 추출을 계산 절 해석 완료로 간주하지 않는다.
- `standard.supporting_text_review()`는 76개 supporting-text 절마다 PDF/TОC locator, canonical extracted-page SHA-256, 분류, next action, 계산 링크를 typed 형태로 제공하며 동일 데이터를 wheel 내부에도 패키징한다.
- 각 미연결 항목에 `origin`과 `reason`(`engineering_utility` 또는 `adapter_contract`)을 함께 반환해 표준 계산 누락과 의도적인 보조 경계를 구분한다.
- `audit_coverage()`는 계산·절 수, ID 무결성, 기술 절 미구현, 기술 절의 계산 링크 누락, review category 유효성, 미연결 보조 분류를 CI/배포 전 구조 검사로 재실행할 수 있으며, 통과는 표준 적합성 인증이 아니다.
- `audit_coverage()`는 `optional_native_*` 계산이 native evidence manifest와 검증 스크립트에 연결되어 있는지도 확인한다.
- [재현 가능한 검증 명령](VERIFICATION_COMMANDS.md)에 inventory 생성·schema 동기화·전체 테스트·wheel smoke·대표 실행 경계를 기록한다.
- `scripts/verify_release.py --write-evidence`는 계산/절 수, 상태 집계, audit checks와 Python·digital-twin Schema·coverage의 SHA-256을 `docs/release-evidence.json`에 고정한다. 이는 재현성 증거이지 API 581 적합성 인증은 아니다.
- 기준 PDF `API-581-2016.pdf`가 존재하는 환경에서는 원문 파일명·크기·SHA-256도 같은 manifest에 기록해 추출 inventory의 문서 fingerprint를 보존한다.
- 계산 Schema와 digital-twin Schema는 `src/api581/data/`에 함께 패키징되며, 문서본과 wheel용 패키지본의 hash 동기화도 release gate에서 검사한다.
- `api581.schema`는 설치된 wheel에서 두 Schema를 경로 탐색 없이 읽는 accessor와 packaged hash 조회 API를 제공한다.
- `properties/mixture-molecular-weight`는 Part 3 §4.1.2·§4.9.4의 대표유체/독성 혼합물 입력 준비 근거를 갖는 `api581_input_preparation` 계산으로 분류하며, Level 2 flash나 대표유체 선택과 혼동하지 않는다.
- 일반 slabx/slabx-lh2 시간 프로파일 계약은 초안. 별도 native_pool_centreline은 선택 설치한 SLABx1.0.8/LH2 0.2.0 실제 지면 풀 API를 프로세스 격리해 실행한다. 엔진 부재·버전 불일치·전제 위반·경계 미도달을 명시한다.
- capability 호출 경계는 `api581.dispersion.capabilities()`(일반 계약 상태)와 `api581.api.dispersion.native_engine_capabilities()`(typed 설치/version/importability probe)로 구분한다.
- `scripts/check_doc_api_paths.py`가 README·검증 명령·자동 생성 MODULE_CATALOG의 구체적인 `api581.*` 참조 685개를 실제 import 경로와 대조한다.
- `.github/workflows/verify.yml`이 계약 재생성, release audit, 문서 경로 검사, pip check, 전체 pytest, wheel Schema/evidence smoke test를 GitHub push/PR에서 실행한다.
- `.github/workflows/publish.yml`은 Release published 이벤트에서만 build·twine 검사를 거쳐 PyPI Trusted Publishing을 수행하도록 준비되어 있다. 실제 업로드와 PyPI 프로젝트 설정은 외부 계정/Release 운영 단계다.
- [PyPI 릴리스 절차](PYPI_RELEASE.md)에 Trusted Publisher 설정, tag/version 검사, 독립 검증 범위 분리를 기록한다.
- `dispersion/native-engine-capabilities`는 distribution 버전뿐 아니라 `slabx`/`slabx_lh2` 모듈 importability도 별도 반환한다. 설치 metadata만 존재하고 실제 import가 깨진 환경을 `available`로 오인하지 않는다.
- 배포 버전이 일치해도 native module import가 실패하면 `engine_status="not_importable"`로 승격해 `available`과 구분한다.
- 디지털 트윈 measurement/request/response envelope은 재귀적 immutable payload와 frozen Pydantic 모델로 고정해 provenance 캡처 후 설비 ID·입력·측정값을 실행 중 변경할 수 없게 한다. immutable wrapper는 process batch pickle 복원도 지원한다.
- `risk/portfolio`는 컴포넌트별 연간 빈도·면적·재무 위험 기여와 합계를 동시에 반환하며, 중복 컴포넌트 ID와 통화/상호배타 근거 누락을 입력 계약에서 차단한다.
- immutable envelope은 `model_dump(mode="json")`에서 일반 JSON dict/list로 직렬화되어 event bus·DB 저장 경계를 유지한다.
- `partition_requests()`·`build_batch_plan()`·`merge_batch_responses()`로 HPC/작업큐 호스트가 요청을 결정론적으로 shard하고, 누락·중복을 검증한 뒤 원래 순서로 재조립할 수 있는 `api581-batch-1` manifest 계약을 제공한다. 스케줄러·재시도·저장은 호스트 책임이다.
- `TwinBatchPlan.verify_requests()`는 작업 제출 직전 request payload hash·shard·순서를 manifest와 재검증해 큐 경계에서 변조/잘못된 재시도를 거부한다.
- `TwinBatchShard.payload_hash`와 `execute_batch_shard()`는 worker가 전체 batch를 보지 않고도 자기 shard의 입력 순서·payload hash를 검증하게 하며, 완료 후 `merge_batch_responses()`로 호스트가 재조립한다.
- `calculation_evidence()`는 native SLABx 계산에 `docs/NATIVE_ENGINE_EVIDENCE.json`과 해당 검증 스크립트까지 역방향 연결해 절 링크와 실행 provenance를 함께 조회하게 한다.
- `calculation_evidence()`의 `validation_level`은 일반 계산(`software_tested_only`)과 SLABx/CoolProp fixture가 실제 재실행된 계산(`native_engine_fixture_verified`)을 구분한다. 외부 평가·공식 제3자 인증은 이 프로젝트 범위에 포함하지 않는다.
- `validation_queue(validation_level=...)`는 같은 구분을 전체 계산 목록에 적용해 QA·릴리스 파이프라인이 미검증 계산을 직접 수집할 수 있게 한다.
- `validation_queue(domain=..., validation_level=..., direct_test=...)`는 특정 분야의 native/software 및 직접/간접 검증 큐만 조합해 추출할 수 있게 한다.
- `validation_queue(public_test=...)`는 테스트 파일의 문자열 참조가 아니라 공개 `evaluate()` 경계를 실제 호출한 계산만 별도로 선별한다.
- `coverage_summary()['validation_by_domain']`에도 분야별 공개 경계 직접 호출/미호출 수를 제공해 통합 위험평가 우선순위를 확인할 수 있다.
- SLABx buoyant vertical-rise는 Briggs effective-source 분기를 통해 native engine에 연결되며, 독립 fixture와 native suite에서 검증된다. API 520 sizing은 `api520/*` typed utility API로 편입됐다.
- `docs/release-evidence.json`에도 `validation_counts`를 기록해 배포 시점의 software-only/native-fixture 검증 분포를 고정한다.
- `TwinCalculationResponse.validation_evidence`가 같은 계산별 evidence 연결을 response envelope에 보존해, 디지털 트윈 consumer가 별도 catalog 조회 없이 결과와 검증 근거를 함께 저장할 수 있다.
- `TwinCalculationResponse.validation_level`도 함께 보존해 native fixture 검증과 software-only 검증을 worker 결과만으로 구분한다.
- `TwinCalculationResponse.from_result()`는 result의 검증 수준과 계산 evidence manifest가 다르면 `twin_contract_mismatch`로 투영을 거부한다.
- `CalculationResult.validation_evidence`도 같은 연결을 직접 Python API 호출 결과에 포함해, typed API와 twin envelope의 provenance 경계를 일치시킨다.
- `api581.evidence.ValidationEvidence` TypedDict로 manifest·packaged manifest·검증 스크립트 필드를 고정해 IDE/정적 타입 검사에서도 provenance 계약을 확인할 수 있다.
- 새 wheel smoke 환경에서 `api581.evidence.native_engine_evidence()`와 native probe response의 packaged manifest 연결을 실제 설치 후 확인했다.
- 보존된 `tmp/dispersion-native` 환경(SLABx 1.0.8, slabx-LH2 0.2.0, CoolProp 8.0.0)에서 실제 native 검증 스크립트를 재실행했다. 중심선·제트·평면 footprint·독성·flash/pool risk 경로의 직접 native 배열 비교, 경계 검열, LH2 premise 차단, 프로세스 격리와 provenance 지문 검사를 통과했다. 이 결과는 해당 fixture/엔진 버전의 소프트웨어 연동 증거이며 현장 적용성·표준 적합성 인증은 아니다.
- `scripts/verify_native_suite.py`는 지정된 native Python 환경에서 9개 선택 엔진 검증 스크립트를 순서대로 실행하고 stdout/stderr·종료 상태를 단일 JSON 실행 보고서로 보존한다.

## CLSCC SI 감수성·DF 통합

최신 전체 검증: 509개 독립 Python 함수,19개 분야,11,848개 통과·3개 건너뜀.
대표 실행 검증: `python_composition.py`, `python_workflow.py`, `level2_risk_assessment.py`, `tank_bottom_corrosion_to_risk.py`, `tank_geometry_to_risk.py`, `prd_leakage_assessment.py`, `two_phase_event_risk.py`가 모두 exit code 0으로 실행됐다. Native SLABx/CoolProp 예제는 선택 설치·엔진 검증 범위로 별도 분리한다.
Table 4.2/4.2M 대표 유체 29개 행의 MW·밀도·비점·상태·AIT와 note 1/2/3 Cp 식을 독립 API로 제공한다. 표의 --- 값은 추정하지 않고 명시적으로 null/제한으로 반환한다.
Part 3 §4.1.3의 산·가성 유체는 비가연·비독성·인체 접촉 위험 조건에서 ACID/액체/산 splash 경로를 선택하는 독립 API로 추적한다.
`level1/release-to-acid`는 이 선택을 controlled release·inventory·detection/isolation·산 splash 면적까지 조합한다.
`level1/release-to-toxic`는 controlled release의 이론 누출률을 독성 성분·비점화확률·완화 크레딧과 연결하며, 가연성 감소율을 독성원에 재사용하지 않는다.
`level1/toxic-mixture-consequence`는 §4.9.12에 따라 성분별 면적 중 최대값만 반환하고 독성 cloud 면적을 합산하지 않는다.
`level1/toxic-hole-summary`는 각 hole에서 성분 최대값을 선택한 뒤 §4.9.14의 GFF 가중 평균을 계산한다.
`level1/release-to-steam`은 controlled release를 Steam NFNT personnel consequence와 연결하며 equipment area는 0으로 명시한다.
디지털 트윈 요청 envelope는 `measurement_snapshot()`으로 센서 ID·값·단위·시각·품질·불확실성을 손실 없이 adapter에 제공하며, 명시적 `inputs`를 자동 변경하지 않는다.
`execute_requests()`는 여러 자산/시나리오 요청을 입력 순서대로 보존한다. serial/thread/process 실행 모드를 제공하며, process 모드는 GIL 독립 CPU 병렬화와 향후 슈퍼컴퓨터·배치 실행기 연결 시에도 요청 단위 provenance를 유지한다. 대규모 process batch에는 검증된 `chunksize`를 지정해 IPC 오버헤드를 줄일 수 있고, 잘못된 청크 값은 계약 오류로 차단한다.
Annex 2.B §14.2.1/§14.2.2는 AST 바닥 토양측·제품측 부식률 방정식을 각각 독립 API로 노출하며, 보정계수와 기준률을 명시적으로 입력받고 적용 범위를 자동 추정하지 않는다.
Annex 2.B §11.1.6은 스케일·퇴적·biomass/MIC·저유속 요인 플래그를 정성 API로 노출하며, 원문에 없는 보정계수나 정량 부식률을 생성하지 않는다.
`risk/assessment-from-damage`는 개별 mechanism DF를 `damage/combine`으로 결합한 뒤 GFF·management factor·네 개 hole consequence를 risk로 연결한다.
`frequency/pof-method-selection`은 Part 2 §3.2의 structural/statistical/expert/combined 방법론과 자격 근거를 기록하며, 숫자 POF를 임의로 생성하지 않는다.
`properties/mixture-representative-fluid`는 Part 3 Annex A §3.1.2의 혼합물 몰분율·대표 유체 선택을 독립 API로 제공하며, 비관련 성분을 보존적으로 제외하고 Level 2 권고 경계를 명시한다.
`inspection/thinning-effectiveness`는 Part 2 Annex C §2.C.8 표의 일반/국부 감육·침습/비침습 검사 범주 A-E를 독립 분류 API로 제공하며, 검사 품질·위치·기법 미검증은 E로 명시한다.
`inspection/scc-effectiveness`는 Part 2 Annex C §2.C.9 SCC 검사효과 표의 용접 SCC와 CLSCC/PTA 범주를 분리해 분류하며, 원문에 없는 CLSCC/PTA 비침습 A등급을 생성하지 않는다.
`inspection/external-effectiveness`는 Part 2 Annex C §2.C.10 외부부식·외부 CLSCC·CUI·CUI-CLSCC 검사효과를 분류하고, CUI-CLSCC 비제거 단열의 원문상 부재한 등급을 E로 보존한다.
`inspection/buried-effectiveness`는 Part 2 Annex C §2.C.7 매설 설비의 침습/비침습 검사 증거묶음을 A-E로 분류하며, CP·토양자료·굴착·NDE 근거 없이는 검사 credit을 생성하지 않는다.
`inspection/prd-effectiveness`는 Part 2 Annex C §2.C.3 PRD/rupture disk 검사효과를 A-E로 분류하며, rupture disk의 원문상 A등급 부재를 유지한다.
`inspection/lining-effectiveness`는 Part 2 Annex C §2.C.6 비금속 라이닝 검사효과를 분류하며, 비침습 A등급 부재와 라이닝 DF에 직접 사용하지 않는다는 원문 제한을 유지한다.
`inspection/tube-bundle-uncertainty`는 Part 2 Annex C §2.C.4.1의 A=5%, B=10%, C=20%, D=30%, E=50% 추가 불확실성 매핑을 반환하며 Weibull/PoF 곡선을 임의 변경하지 않는다.
`inspection/ast-effectiveness`는 Part 2 Annex C §2.C.5 AST shell internal/external 및 tank bottom 검사효과 표를 side별 증거로 분류한다.
`inspection/effectiveness-category`는 Part 2 Annex C §2.C.2의 공통 A-E 범주·순서·검사 credit 허용 여부를 중앙 메타데이터로 반환한다.
`inspection/effectiveness-summary`는 Part 2 §3.4.3에 따라 SCC 계열의 A-D 검사 이력을 등가 counts로 결합하고 E 검사는 credit하지 않는다.
`damage/measured-corrosion-rate`는 Part 2 Annex B §1.1-§1.2의 두께 차이 기반 직접 부식률을 계산하며, 두께 증가 입력은 기준 불일치로 명시적 오류 처리한다.
공통선별온도를SI표에연결하고염화물이온구간/pH·검사·경과시간DF를제공한다.
확인균열high·미보수FFS·US/SI혼합거부·원문공유경계오류를검증했다.
[계약](CLSCC_SCREENING.md). 전체문서구현은계속진행중이다.

## CLSCC 적용성 선별

최신 전체 검증: 466개 독립 Python 함수,18개 분야,11568개 테스트 통과.
Part2 §12.3 재질·실제/잠재wet-chloride·엄격한온도조건을독립API로추가했다.
SI/US인쇄경계차이와정확한경계/인접값·노출조건을검증했다.
[계약](CLSCC_SCREENING.md). 감수성/DF통합과전체문서구현은진행중이다.
목차상태는부분409/미구현384이다.

## PASCC Figure11.1과 DF 통합

최신 전체 검증: 465개 독립 Python 함수,18개 분야,11560개 테스트 통과.
운전/정지노출·Table11.2·자격있는정지보호1단계감소와DF연결2개API를추가했다.
확인균열high우선·미보수FFS·재질군일치조건을포함한다.
[계약과검증](PASCC_SCREENING.md). 현장보호조치적합성및전체문서구현은진행중이다.

## PASCC 황노출·재질 선별

최신 전체 검증: 463개 독립 Python 함수,18개 분야,11549개 테스트 통과.
Part2 §11.3 오스테나이트계SS/니켈합금·황화합물노출선별API를추가했다.
[계약](PASCC_SCREENING.md). 정지조건/완화조치와감수성·DF통합은별도평가다.
목차상태는부분404/미구현389이며전체문서구현은진행중이다.

## ACSCC 선별·수질·DF 통합

최신 전체 검증: 462개 독립 Python 함수,18개 분야,11542개 테스트 통과.
선별/감수성의 동일pH·수분을요구하고확인균열high·미보수FFS를적용하는DF통합API를추가했다.
[입력과검증](ACSCC_SCREENING.md). 현장적용성및전체문서구현은진행중이다.

## ACSCC 수치pH/탄산염 감수성

최신 전체 검증: 461개 독립 Python 함수,18개 분야,11539개 테스트 통과.
Table10.2 수치pH와 탄산염/PWHT 감수성을 연결하고 공유pH8/9 정책을 명시한다.
P/M알칼리도만의 탄산염 측정은 거부한다. [계약](ACSCC_SCREENING.md).
자동DF통합과 전체문서 구현은 남아 있다.

## ACSCC 적용성 선별

최신 전체 검증: 460개 독립 Python 함수,18개 분야,11529개 테스트 통과.
Part2 §10.3 재질/알칼리수pH 및FCCU 황감소/질소증가 검토 API를 추가했다.
정확한pH7.5경계·독립 원료변경·수분/pH 일치·근거14개 사례를 검증했다.
[계약과 제한](ACSCC_SCREENING.md). 감수성 구간 자동 연결 및 전체문서 구현은 남아 있다.
목차 상태는 부분403/미구현390이다.

## HIC/SOHIC 경험 기반 모니터링 대체

최신 전체 검증: 459개 독립 Python 함수,18개 분야,11515개 테스트 통과.
Table9.5 note의 경험계수 대체를 독립 API 및 통합DF에 추가했다.
표 계수와 선택 계수를 구분하고 곱셈/중복 적용을 방지한다.
활성 모니터링·대체 근거·기본값 보존 및0.5/1/3/10 대체계수를 검증했다.
[계약](SSC_SCREENING.md). 전체 문서 구현은 진행 중이다.

## HIC/SOHIC-H₂S 감수성·모니터링·DF 연결

최신 전체 검증: 458개 독립 Python 함수,18개 분야,11507개 테스트 통과.
탄소강 환경/황/제품/PWHT/시안화물 감수성과 모니터링DF 통합2개 API를 추가했다.
확인 균열의환경/최종high 및 알려진 손상의 외부 보수/FFS 근거를 요구한다.
[입력·제한·검증](SSC_SCREENING.md). 경험 기반 모니터링 대체계수 및 전체문서 구현은 남아 있다.

## HIC/SOHIC-H₂S 적용성 선별

최신 전체 검증: 456개 독립 Python 함수,18개 분야,11498개 테스트 통과.
Part2 §9.3 wet-H₂S/강재 선별을 HIC/SOHIC 전용 공개API로 제공한다.
12조건 조합·노출 근거·SSC와 구분된 출력 계약을 검증했다.
[범위 및 후속 연결](SSC_SCREENING.md). 저합금강 선별을 탄소강 표 적용성으로 확대하지 않는다.
목차 상태는 부분402/미구현391이며 전체 문서 구현은 진행 중이다.

## SSC 환경·경도·시안화물·DF 연결

최신 전체 검증: 455개 독립 Python 함수,18개 분야,11485개 테스트 통과.
환경 심각도와 경도/PWHT 후 감수성에 시안화물1단계 상향을 적용하는 독립 API와 선별/DF 통합을 추가했다.
보정은 환경 등급을 바꾸지 않으며high 상한·표의 빈 구간/공유 경계·균열/FFS 조건을 검증했다.
[계약 및 검증](SSC_SCREENING.md). 현장 화학/검사 자격과 전체 손상 평가를 자동 판정하지 않는다.

## SSC 재질·물·H₂S 적용성 선별

최신 전체 검증: 453개 독립 Python 함수,18개 분야,11465개 테스트 통과.
Part2 §8.3의 모든 농도 wet-H₂S/강재 선별 API를 추가하고12조건 조합 및 근거를 검증했다.
[계약과 남은 연결](SSC_SCREENING.md). 환경·경도·시안화물 상향·DF 통합은 후속 작업이다.
목차 상태는 부분401/미구현392이며 전체 문서 구현은 진행 중이다.

## Figure7.1 아민 균열 감수성 자동 판정

최신 전체 검증: 452개 독립 Python 함수,18개 분야,11452개 테스트 통과.
PDF183쪽 흐름도를 시각 대조하여 감수성과 DF 연결2개 API를 추가했다.
정확한 Fahrenheit 경계·아민 그룹·lean/rich 동시 노출·열추적/스팀아웃·균열/응력제거 우선순위를 검증했다.
[계약과 검증](AMINE_CRACKING_SCREENING.md). 현장 조건/검사 자격 및 기타 수소 손상 평가는 별개다.
목차 상태는 부분400/미구현393이며 전체 문서 구현은 진행 중이다.

## 아민 균열 재질·노출 선별과 DF 연결

최신 전체 검증: 450개 독립 Python 함수,18개 분야,11432개 테스트 통과.
Part2 §7.3 재질/모든 농도 산성가스 처리 아민 노출 선별과 독립 감수성 기반 DF 연결2개 API를 추가했다.
확인 균열high·미보수FFS 우선·선별 탈락 오류 및 알려진 SVI/검사/경과시간 결과를 검증했다.
[입력과 한계](AMINE_CRACKING_SCREENING.md). Figure7.1 감수성 자체의 자동 판정은 남아 있다.
목차 상태는 부분398/미구현395이며 전체 문서 구현은 진행 중이다.

## 가성소다 균열 선별·감수성·DF 연결

최신 전체 검증: 448개 독립 Python 함수,18개 분야,11422개 테스트 통과.
재질/노출 선별, 자격 있는 Figure6.2 분기, 기존 SCC DF 연결3개 API를 추가했다.
24개 영역/농도/열추적/스팀아웃 분기와 과거high 유지·전문가 재평가·미보수 FFS 거부를 검증했다.
[근거 및 제한](CAUSTIC_SCREENING.md), [Python 예제](../examples/caustic_screened_assessment.py).
Figure6.1 영역 입력은 독립 판정 근거를 요구하며 그래프 자동 수치 판정은 남아 있다.
목차 상태는 부분397/미구현396이며 전체 문서 구현 완료를 뜻하지 않는다.

## 기준 두께·기간·검사 이력의 감육 연결

최신 전체 검증: 445개 독립 Python 함수,18개 분야,11379개 테스트 통과.
Part2 §4.5.5/§4.5.6의 공급/측정 기준, UTC 경과기간, 기간 내 적격 A-D 검사 횟수를3개 API로 제공한다.
측정 기준 재설정은 품질·정확도·근거를 요구하며 기준 시점 검사 포함 정책은 명시 선택한다.
부식률 선택·prior·강도·조건과 연결하여 별도 수동 age/count 없이 DF를 계산한다.
[계약과 검증](THINNING_HISTORY.md), [Python 예제](../examples/thinning_history_assessment.py).
목차 상태는 부분395/미구현398이다. 검사 자동 효과성 판정·공정 변경 감지·전체 문서 구현은 남아 있다.

## 공통 감육률 선택과 검사 유형 연결

최신 전체 검증: 442개 독립 Python 함수,18개 분야,11359개 테스트 통과.
Part2 §4.5.2/§4.5.4의 측정률 우선·기구 간 최대률·국부 검사 유형 우선 규칙을2개 API로 제공한다.
부식률 지배 기구와 검사 유형 지배 기구를 분리하며0측정률·동률·기간/근거·모니터링을 검증했다.
선택된 동일률을 공통 벽/강도·검사·조건으로 비AST 감육 DF까지 연결한다.
[계약과 검증](THINNING_RATE_SELECTION.md), [Python 예제](../examples/multiple_thinning_mechanisms.py).
목차 상태는 부분393/미구현400이다. 기구 자동 적용성·측정 시계열 판정·전체 문서 구현은 남아 있다.

## 경험 기반 사용자 정의 감육 사전확률

최신 전체 검증: 440개 독립 Python 함수,18개 분야,11348개 테스트 통과.
Part2 §4.5.3의 사용자 정의 prior 경로를 공통 검사 모델에 추가하고 독립 사전확률 선택 API를 제공한다.
기존 신뢰도3행은 유지하며 맞춤3상태 확률·경험 근거·상호 배타 선택·합/범위를 검증한다.
확률0을 임의 하한 없이 처리하고 대량 검사에서도 안정적인 Bayes 갱신을 확인했다.
[근거 및 계약](CUSTOM_THINNING_PRIOR.md), [감육 전파 예제](../examples/custom_thinning_prior.py).
목차 상태는 부분391/미구현402다. 자동 경험 자료 보정·신뢰도 판정 및 전체 문서 구현은 남아 있다.

## 지하수 부식 지침과 감육 연결

최신 전체 검증: 439개 독립 Python 함수,18개 분야,11328개 테스트 통과.
Annex2.B §11.3.3(PDF405쪽) TKS7종 합산·공급 부식률 분류·전문가 평가·감육 연결4개 API를 추가했다.
원문이 TKS 수치와 부식률 관계를 제공하지 않으므로 임의의 변환식/경계는 구현하지 않는다.
SI/US 반올림 차이·중간 공유 경계 정책·미입력/비유한값·독립 부식률 보존·모니터링 제한을 검증했다.
[근거 및 검증 범위](GROUNDWATER_VALIDATION.md), [Python 예제](../examples/groundwater_to_thinning.py).
목차 상태는 부분390/미구현403이며, 상위 절 근거 집계를 포함하므로 계산 완성률을 뜻하지 않는다.

## 선택 사건의 빈도·면적 위험 기여분 연결

최신 전체 검증: 435개 독립 Python 함수,18개 분야,11315개 테스트 통과.
독립 사건/기상 면적 위험 기여분과 선택 구멍 GFF→공급 DF/관리계수→EOS/native 화재→위험 기여분2개 API를 추가했다.
누출 조건부 기상확률과 누출/기상 조건부 사건확률을 명시하고 빈도·확률의 중복 적용을 방지한다.
알려진 수치, 확률/빈도0·1 경계, 입력 근거, native 경계 잘림 전파와 사건확률0의 원시 면적 보존을 검증했다.
[정의·범위](SELECTED_EVENT_RISK.md), [실행 예제](../examples/flashed_pool_risk_contribution.py).
이 결과는 선택 정상 풀 시나리오의 기여분이다. 전체 사건/기상/구멍 및 초기 과도·제트 등은 미평가다.

## 정상 풀 농도 영역과 플래시 화재 연결

최신 전체 검증: 433개 독립 Python 함수,18개 분야,11301개 테스트 통과.
EOS/rainout/정상 풀에서 native 평면 농도장과 LFL 플래시 화재 면적까지2개 API를 추가했다.
프로판의 footprint/fire 면적 일치·0.25 설비 면적 매핑·횡방향 격자 민감도·경계 잘림 거부를 실제 엔진으로 검증했다.
정상 수소/LH2 평면장·화재 매핑도 확인했으며 실험/현장 적합성 주장은 하지 않는다.
[입력·출력 및 한계](FLASHED_BOILING_POOL.md), [Python 예제](../examples/flashed_pool_flash_fire.py).
선택한 정상 풀 사건만 계산한다. 초기 과도·동시 제트·점화/GFF 가중·최종 위험 통합은 남아 있다.

## EOS·풀 증발·native 확산의 정상 구간 통합

최신 전체 검증: 431개 독립 Python 함수,18개 분야,11296개 테스트 통과.
순수 액체 플래시→Kletz rainout/분할→정상 비등 풀→격리 native 중심선1개 API를 추가했다.
포화 증기 비열을 보강하여 상수 물성의 상태·단위를 일치시키고, 초기 미모델링 풀 질량과 제트 질량을 분리한다.
정상 구간 시간·면적·평균시간·무 rainout 조건을 검증했다.
실제 프로판/SLABx1.0.8 및 정상 수소/slabx-lh2 0.2.0 경로와 질량 회계를 확인했다.
[계약 및 제한](FLASHED_BOILING_POOL.md), [Python 예제](../examples/flashed_boiling_pool.py).
중심선 연결 검증이며 초기 과도·동시 제트·면적/위험 통합·현장/LH₂ 실험 검증은 남아 있다.

## 초기2상 저장 유체의 플래시 확장

최신 전체 검증: 430개 독립 Python 함수,18개 분야,11291개 테스트 통과.
기존 플래시 입력을 압력·온도 또는 압력·평형 증기 질량분율 중 하나로 확장했다.
두 방법×네 초기 분율에서 혼합물 보존량/최종 상태를 확인하고, 응축에 따른 음수 분율 변화를 보존한다.
입력 모호성·분율 범위·포화 PT·포화 압력 범위를 검증했다.
[계약과 실제 엔진 재현](PURE_FLUID_FLASH.md). 초기2상의 rainout/액적 조성 연결 및 혼합물·LH₂ 검증은 남아 있다.

## 순수 유체 포화 물성과 풀 증발 연결

최신 전체 검증: 430개 독립 Python 함수,18개 분야,11282개 테스트 통과.
압력/온도 기준 포화 물성2개 API로 기포점·이슬점·증기압·포화 밀도·액체 비열·증발잠열·분자량을 제공한다.
실제 CoolProp8.0.0에서 물/프로판의 기준값·왕복·Clapeyron 관계와 상태 범위 거부를 확인했다.
[사용 및 검증 한계](PURE_FLUID_SATURATION.md), [비등/비비등 풀 연결 예제](../examples/saturation_to_pool.py).
포화 물성은 저장/임의 플래시 상태 물성과 구분한다. 혼합물·LH₂·현장 검증은 남아 있다.

## 순수 유체 플래시 계산 확장

최신 전체 검증: 428개 독립 Python 함수,18개 분야,11278개 테스트 통과.
선택 의존성 CoolProp8.0.0으로 등엔트로피/등엔탈피 플래시를 공개 타입 API로 제공한다.
저장/최종 증기 질량분율과 부호 있는 분율 변화를 구분한다.
실제 엔진에서 프로판 기준값·보존량·액체/기체·의사순수 및 미분류 초임계 저장 상태 거부를 검증했다.
[사용 및 한계](PURE_FLUID_FLASH.md). 액체 저장 상태는 Kletz rainout/풀·제트 분할까지 연결했다. 인쇄식/질량보존 해석을 명시 선택한다. 혼합물·LH₂·초기2상·저장 기체 응축 연결 검증은 남아 있다.

## 고온 황화·나프텐산 부식률과 감육 연결 확장

최신 검증: 426개 독립 Python 함수,18개 분야,11266개 테스트 통과.
재질/Mo·표 축·기본률·유속·TAN 분류와 통합/감육7개 API를 추가했다.
9표군3840셀 조회와 온도 구간·재질별 축·Mo 미상·첫TAN 확장·100ft/s 경계 및 감육 연결을 검증했다.
[검증 기록](SULFIDIC_VALIDATION.md)과 [Python 예제](../examples/sulfidic_to_thinning.py)를 제공한다.
전사/조회 검증 한계를 기록했다. 동역학·표 밖 모델·현장 적용성과 전체 손상기구 자동 통합은 미완료다.

## 고온 H₂S/H₂ 부식률과 감육 연결 확장

최신 검증: 419개 독립 Python 함수, 18개 분야, 7405개 테스트 통과.
6표군·16재질의 온도/H₂S·유체 곡선과 통합/감육4개 API를 추가했다.
전사1920셀 조회·몰분율/몰%·공유 재질·무탄화수소 곡선·감육 연결을 검증했다.
[검증 기록](H2SH2_CORROSION_VALIDATION.md)과 [Python 예제](../examples/h2sh2_to_thinning.py)를 제공한다.
목차793항목은 부분 구현352개·미구현441개다. 목차에는 설명/참고문헌도 있어 계산 구현률로 환산하지 않는다.
전체 문서 완료가 아니며 공학 검증·통합·현장 적용성과 미구현 범위가 남아 있다.

## 황산 부식률과 감육 연결 확장

최신 검증: 415개 독립 Python 함수, 18개 분야, 5461개 테스트 통과.
6재질 표 축·3축 부식률·감육 분류와 통합/감육5개 API를 추가했다.
전사1776셀 조회와 SI탄소강 유속 헤더·30499셀·B-2 산화제·3축 보간을 검증했다.
다른 감육/모니터링 유속 기준은 유지하면서 같은 물리 조건으로 연결한다.
[검증 기록](SULFURIC_VALIDATION.md)과 [Python 예제](../examples/sulfuric_to_thinning.py)를 제공한다.
전사 검증과 조회 테스트의 한계를 기록했다. 피막/불순물 동역학·산화성B-2 모델·전체 손상기구 통합은 미완료다.

## 아민 부식률과 감육 연결 확장

최신 검증: 410개 독립 Python 함수, 18개 분야, 3665개 테스트 통과.
활성 아민 부하·오염물 행·농도 계수·탄소강/스테인리스 표와 통합/감육8개 API를 추가했다.
탄소강1152셀·스테인리스16셀의 조회를 검증하고 부하/농도 공백·MDEA 단위 차이·4wt% 경계를 명시했다.
탄소강 농도 보정은 한 번 적용하고 같은 유속 분류를 감육 모니터링에 사용한다.
[검증 기록](AMINE_CORROSION_VALIDATION.md)과 [Python 예제](../examples/amine_to_thinning.py)를 제공한다.
셀 fixture와 런타임 표의 추출 경로 공유 한계를 기록했다. 극한 조건·평형/열화 동역학·전체 손상기구 통합은 미완료다.

## 불산 부식률과 감육 연결 확장

최신 검증: 402개 독립 Python 함수, 18개 분야, 2457개 테스트 통과.
농도 선택·탄소강 유속/잔류원소·Alloy400 산화제 표와 통합/감육6개 API를 추가했다.
원문380셀을 별도 추출 fixture와 대조하고 뒤바뀐 흐름도 표 번호·일반/국부 본문 차이를 명시했다.
무수 HF에 자유수 없음→0을 적용하지 않으며,81wt% 초과 표 확장은 적격 근거와 표지를 요구한다.
[검증 기록](HF_VALIDATION.md)과 [Python 예제](../examples/hf_to_thinning.py)를 제공한다.
스케일 성장/파괴·초기 노출·희석 동역학·별도 균열과 전체 손상기구 자동 통합은 미완료다.

## 희염산 부식률과 사워워터 HCl 경로 확장

최신 검증: 396개 독립 Python 함수, 18개 분야, 2056개 테스트 통과.
염화물/pH 순·역변환, 탄소강/스테인리스·고합금 표와 통합/감육6개 API를 추가했다.
원문392개 물리 셀을 별도 추출 fixture와 대조하고 농도 공백·역산 선택·산화제 분기를 검증했다.
사워워터 공통 선택에서 HCl 정량 계산을 실행하며 같은 분리 수상의 pH/농도 일치를 확인한다.
[검증 기록](HCL_VALIDATION.md)과 [Python 예제](../examples/hcl_to_thinning.py)를 제공한다.
농염산·응축/퇴적 동역학·틈부식/SCC·현장 적용성과 전체 손상기구 자동 통합은 미완료다.

## 알칼리 사워워터와 산성/알칼리 통합 선택 확장

최신 검증: 390개 독립 Python 함수, 18개 분야, 1608개 테스트 통과.
H₂S 부분압·NH₄HS 농도·상별 유속·기본40셀·압력 보정과 통합/감육8개 API를 추가했다.
NH₄HS 원문 과잉 분기·미지정 경계는 기본 거부하고 명시적 정책·근거를 요구한다.
공통 수분/pH 스크린에서 산성·알칼리 부식률을 선택하며 동일 유속·부식률로 감육에 연결한다.
[검증 기록](ALKALINE_SOUR_WATER_VALIDATION.md)과 [Python 예제](../examples/alkaline_sour_water_to_thinning.py)를 제공한다.
HCl·혼합화학/EOS·타재질 확장·현장 적합성과 전체 손상기구 자동 통합은 미완료다.

## 산성 사워워터 부식률과 감육 연결 확장

최신 검증: 382개 독립 Python 함수, 18개 분야, 1567개 테스트 통과.
pH/염화물 분기·기본40셀·산소/유속·타재질 상한과 통합/감육8개 API를 추가했다.
pH 중성·표 공백·염화물 기준·타재질 본문/그림 차이는 명시적 정책으로 처리한다.
고산소/고유속의 국부부식 검토와 sour-water 모니터링의 동일 유속을 확인한다.
[검증 기록](ACID_SOUR_WATER_VALIDATION.md)과 [Python 예제](../examples/acid_sour_water_to_thinning.py)를 제공한다.
혼합화학·다른 절 정량 연결·실제 재질/검사와 모든 손상기구의 자동 위험 통합은 미완료다.

## 고온 산화율과 일반 감육 연결 확장

최신 검증: 374개 독립 Python 함수, 18개 분야, 1528개 테스트 통과.
11재질·24온도·SI/US 산화 표와 산소/온도 스크린·부식률·감육 연결5개 API를 추가했다.
표528위치의318수치와210미제공을 보존하고 대시를0 또는 허용온도로 해석하지 않는다.
첫 표 이전 공백·보간·설계온도 강도 입력과 산화 모니터링 기구의 적합성을 명시한다.
[검증 기록](OXIDATION_VALIDATION.md)과 [Python 예제](../examples/oxidation_to_thinning.py)를 제공한다.
크리프·박리/열이력·실제 재질/노출과 모든 손상기구의 자동 위험 통합은 미완료다.

## CO₂ 흐름도 스크리닝과 감육 연결 확장

최신 검증: 369개 독립 Python 함수, 18개 분야, 1498개 테스트 통과.
부분압·질량유량/Re, Cr13% 재질·탄화수소/수분20%/유속1m/s·이슬점/자유수 분기와 통합7개 API를 추가했다.
습윤/수분30% 기본가정과 원문 면제 표지를 보존하고 수분 불확실성을 자동 건조로 처리하지 않는다.
저Cr 스테인리스를 저합금강으로 자동 재분류하지 않으며 하위 모델과 동일한 온도/유속을 확인한다.
[검증 기록](CO2_SCREENING_VALIDATION.md)과 [Python 예제](../examples/co2_screened_to_thinning.py)를 제공한다.
실제 습윤/재질·센서 불확실성·다상 검증과 모든 손상기구의 자동 위험 통합은 미완료다.

## CO₂ 부식과 감육 연결 확장

최신 검증: 362개 독립 Python 함수, 18개 분야, 1453개 테스트 통과.
CO₂ 상대습도·이슬점·온도-pH98셀·pH3식·퓨가시티·Re/마찰/전단응력·글리콜/억제제와 부식률/감육13개 API를 추가했다.
140°C 통합 범위와150°C 단독 표,80–90°C 급변,273 분모·글리콜 성분 정의 차이를 명시한다.
자유수/CO₂ 부재의0은 CO₂ 특이 부식률이며 미계산 중간값은null이다.
[검증 기록](CO2_CORROSION_VALIDATION.md)과 [Python 예제](../examples/co2_corrosion_to_thinning.py)를 제공한다.
다상/EOS·습윤/재질 면역 분기·실제 억제제 효과·현장 적용성과 전체 위험 자동 통합은 미완료다.

## 냉각수 처리수 상한·실측 우선 경로 확장

최신 검증: 349개 독립 Python 함수, 18개 분야, 1403개 테스트 통과.
처리수<3/<15mpy 상한, 기타재질 명목0.5mpy, 실측 우선 선택과 감육 연결5개 API를 추가했다.
상한을 보수적 검토값으로 사용했는지 출력에 보존하며, 적격 실측0도 모델보다 우선한다.
일회통과 처리의 본문/그림 차이와 잘못된 식 번호를 기록했다.
[검증 기록](COOLING_RATE_SELECTION_VALIDATION.md)과 [Python 예제](../examples/cooling_rate_selection_to_thinning.py)를 제공한다.
현장 약품 효과·측정 대표성·모든 손상기구 적용성 검증은 미완료다.

## 냉각수 부식률과 감육 연결 확장

최신 검증: 344개 독립 Python 함수, 18개 분야, 1368개 테스트 통과.
냉각수 C1–C4·포화pH·LSI/RSI·기본 부식률·온도·유속·해수·쿠폰 피팅과 담수/감육 통합11개 API를 추가했다.
SI 헤더 중복·온도 중복행/ΔT 차이·pH 누락/모호 셀은 명시적 정책과 근거로 처리하며 자동 수정하지 않는다.
본문 가정의 pH·MIC·침전물·재질 범위를 확인하고 억제제 크레딧은 이 경로에서 적용하지 않는다.
[검증 기록](COOLING_WATER_VALIDATION.md)과 [Python 예제](../examples/cooling_water_to_thinning.py)를 제공한다.
약품처리 경로·MIC/침전·타재질·현장 적용성·전체 위험 자동 통합은 미완료다.

## 라이닝 연령·기본DF·지배 감육 확장

최신 검증: 333개 독립 Python 함수, 18개 분야, 1287개 테스트 통과.
표5.4·5.5의225셀, A/B 검사 연령 갱신, 상태·유효 모니터링 및 모재 감육 최솟값의6개 API를 추가했다.
유기 사용기간/마지막 검사 기간의 원문 차이와 첫해/보간 정책을 명시한다.
유기 환경·온도·시공 가정 확인과 센서 효과 근거를 요구하고 라이닝에 임의0.1 하한을 적용하지 않는다.
[검증 기록](LINING_VALIDATION.md)과 [Python 예제](../examples/lining_to_governing_damage.py)를 제공한다.
실제 열화율·검사/시공 적합성·모재 손상 적용성의 자동 판정은 미완료다.

## 감육 모니터링·국부 배관 조건 보정 확장

최신 검증: 327개 독립 Python 함수, 18개 분야, 1235개 테스트 통과.
실제 표4.8의33셀·병용 예외, 모니터링 계획·경험 대체,
주입/혼합점·데드레그·표적 검사 조건과 무클래딩/클래딩 통합8개 API를 추가했다.
유속은 정확한ft/s 환산 경계를 쓰고 아민은 사용자 분류·근거를 받는다.
모니터링 계수의 중복 가중과 부적격 계획의 자동 크레딧을 방지한다.
[검증 기록](THINNING_CONDITIONS_VALIDATION.md)과 [Python 예제](../examples/thinning_conditions_to_damage.py)를 제공한다.
현장 기구·검사·센서 계획의 효과와 자동 적용성 판정은 미완료다.

## 클래딩·용접 오버레이와 설계 최소두께 감육 확장

최신 검증: 319개 독립 Python 함수, 18개 분야, 1189개 테스트 통과.
식(2.11),(2.14),(2.15)의 소진 전후 손실과 식(2.17)의 설계·구조 최소두께 강도비,
클래딩/무클래딩 통합DF5개 API를 추가했다. 총 시작두께의 일치와 명시적 강도비 선택을 적용한다.
0부식률 보호층은 소진시간null의 해석적 확장으로 구분하고, 원문 유한 계산과의 차이를 추적한다.
[검증 기록](CLAD_THINNING_VALIDATION.md)과 [위험 연결 예제](../examples/clad_thinning_to_risk.py)를 제공한다.
자동 재질별 부식률·코드 두께·FFS·가변 이력·현장 적용성 검증은 미완료다.

## AST 바닥 감육DF와 위험 연결 확장

최신 검증: 314개 독립 Python 함수, 18개 분야, 1156개 테스트 통과.
AST 식(2.12), 전용 표4.7 전체105셀, 최대1회 검사, 용접·유지관리·침하 보정과
양면 부식률부터 감육DF·소스·피해·연간 재정위험까지8개 API를 추가했다.
표 행 사이 처리 정책을 명시하고 Art>1은 외삽하지 않는다.
통합 위험은 다른 손상기구 배제 근거가 있는 감육 전용 범위이며 RPB 조건을 일치시킨다.
[검증 기록](TANK_BOTTOM_THINNING_VALIDATION.md)과 [Python 예제](../examples/tank_bottom_corrosion_to_risk.py)를 제공한다.
현장 검증·라이닝/코팅·자동 검사계획·모든 손상기구와 전체 탱크 위험은 미완료다.

## AST 바닥 양면 부식률 확장

최신 검증: 306개 독립 Python 함수, 18개 분야, 1096개 테스트 통과.
Annex2.B §14.3의 기준 부식률·9종 보정/조건·양면 합성·통합 계산12개 API를 추가했다.
CP 검사 근거, SI/US 반올림 차이, 비저항 공유 경계, RPB 조건과 최소2mpy 권고를 명시한다.
[검증 기록](TANK_BOTTOM_CORROSION_VALIDATION.md)과 [Python 예제](../examples/tank_bottom_corrosion.py)를 제공한다.
AST 전용 감육 DF와 현장 검증은 미완료이며 기존 위험 API에는 검증된 DF가 별도로 필요하다.

## 현재 계산 범위

| 분야 | 구현 내용 | 남은 범위 |
|---|---|---|
| 빈도 | 장비 GFF 조회, 관리계수, DF 보정 빈도, 탱크 인쇄 총합 보존·식3.208 총합 | 탱크 인쇄 총합의 공식 정오 확정, 자산별 적용성 자동 판정 |
| 신뢰도 | Weibull CDF/생존율/위험률/분위수, MTTF 변환, 상수빈도 기간확률, PRD 표·환경·과압·요구빈도·검사 갱신·누설 피해·복수 압력·위험·서비스 날짜, 번들 수명자료·교체계획 | PRD 용량설계·다중 장치 의존고장·전체 이력 eta 갱신 자동화, 번들 매칭·형상 적합·Fisher 신뢰구간·불확실성 |
| 손상 | 감육·라이닝 보정, SCC 9기구, 외면부식·CUI 부식률·코팅·Bayesian DF, 외면/CUI CLSCC 감수성·DF, 배관 기계피로, HTHA 부분압·일부 탄소강 스크리닝, 취성파괴·템퍼·885°F·시그마 DF | 전체 재질·운전 스크리닝, 아민/가성 도표, CUI CLSCC 감수성 보정, HTHA 재질 확장·취성 재질/적용성 자동 판정·템퍼 추정식 해석·피로 수명해석 |
| 누출 | 액체·이상기체·점도·재고·차단·유량 적분, Level2 상/보수적2상 액체식·Kletz rainout·제트/풀/증기/액적 분할, 비등/비비등 풀 증발·정상 지원 조건 | 실제유체·HEM/Omega2상·감압 과도·배관수력·동적 풀/배수·EOS/플래시·실험/LH2 적용성 |
| 화재 | 제트 복사출력/열유속/피해반경, 풀 연소율·혼합물·면적·형상·복사·거리, 파이어볼 질량·크기·복사율·표면출력·수용점 복사·피해반경, 플래시화재 면적 | 풀/파이어볼 원문 형상계수·거리 해석 확정, 실험·LH2 적용성 검증 |
| 사건 | 가연성 상별 유량·점화 상관식·AIT 한계·명시적 온도 기준·표5.3·2상 가중·단일상/2상 누출/순간 파열 트리·상관된max(jet,pool) | 온도/가중 원문 해석 확정, 연속 파열·현장/LH2 검증 |
| 저장탱크 | AST 유체·토양 표,수리전도도·침투,누출공 수,코스/바닥 재고,쉘/바닥3구간 유동,검지·유출량,환경/지하수 배분·쉘/바닥 환경 COF·수리·생산손실·정지·재정 COF·외부DF 기반 부품별 연간 위험 | 전체 탱크 손상/소스 자동화·코스 공간 중첩/공통원인·동적 배수·원문 불일치·현장 검증 |
| 폭발·독성 | TNT/VCE/물리폭발/BLEVE·NFNT 집계, Table4.14 27종 조회·25종 probit/역산, 시간별 노출 적분 확장, Level2 독성 시간·혼합물 기준·성분 최대·4공 집계 | 폭압 곡선·노출 모델 실험 검증, 과열·플래시/EOS·파편 효과, 실제 확산 엔진 연결·공간 컨투어/노출 시간평균·기준 자동 선택 |
| COF | Type0·Pyrophoric 및 Type1 10종 가연성 계수·계산, 검지·차단·완화, HF/H2S·암모니아/염소·추가10종 독성, NFNT, 네 누출공 집계, 수리비·정지기간·재질·유출물성 표, 5분야 재정피해 통합 | 순간 HF 절편 원문 해석, 추가10종 순간 독성(원문 미제공), 운전조건 물성, 탱크 전체 소스/면적 자동화 |
| 통합 | GFF/Fms/외부 DF·COF 결합, Level2 5사건·독성/NFNT·기구별4공 평균·최종식·5재정 항목·연간 위험, 사용자 위험행렬, 목표 최초 초과 탐색 | 장비자료부터 전 손상기구·전 사건을 계산하는 완전 자동 평가, 실제 확산·미래 손상 예측·NDE 계획 최적화 |

API 개수와 조항 인벤토리 수로 구현 완료율을 산정하지 않는다. 현재 어떤 조항도 완전 검증 완료 상태로 표시하지 않는다. 독립 API에서 조합 가능한 기능이 있더라도 해당 장 전체의 스크리닝·보정·예제 검증이 완료되었다는 뜻은 아니다.

## 검증 상태

자동 테스트는 수치 앵커, 질량·확률 보존, 경계 연속성, 검사 확률 갱신, API 검증·이력·워크플로 실패 처리 등을 검증한다. 실제 최신 테스트 결과는 `python -m pytest -q`로 확인한다.

첫 개발 체크포인트: 85개 테스트 통과. 실제 로컬 HTTP로 5단계 기체누출→제트화재→위험도 예제를 실행하고 SQLite에서 같은 실행 결과를 다시 조회했다. OpenAPI 57개 경로(독립 계산 49개 포함)를 확인했으며 wheel 패키지 빌드도 통과했다.

두 번째 체크포인트: 독립 계산 57개, 테스트 113개 통과. Type 0 가연성 계수표의 비어 있지 않은 셀을 API 계약으로 검사하고, 블렌딩 경계·질량 제한·원시 계산과 통합 계산의 일치를 확인했다. 계산 코드 지문을 프로세스 시작 시 고정해 실행 중 파일 변경을 실행 코드로 오인하지 않도록 개선했다.

세 번째 체크포인트: 독립 계산 70개, 테스트 137개 통과. 암모니아·염소 독성의 SI 표 앵커와 시간별 곡선 보간, 독성 유량·노출시간, NFNT·완화·비용 계산을 검증했다. 네 누출공의 유형별 가중평균 후 최종 최대 피해면적을 선택하는 순서를 회귀 테스트로 고정했다. 독성 표의 시간 범위 밖 외삽 및 산/가성액 상관식의 개발 압력 범위 밖 적용은 거부한다.

네 번째 체크포인트: 독립 계산 79개, 테스트 152개 통과. 원문의 2001 USD 수리비·재질계수·정지기간·유출물성 표와 5분야 재정피해 통합 계산을 추가했다. 통화변경 시 정지기간 불변성을 검증했으며, NA 정지기간과 비영 고장빈도의 충돌은 사용자 보정값 없이 계산하지 않는다. 유출물성 표의 액체 밀도는 운전 기체 밀도와 구분한다.

다섯 번째 체크포인트: 독립 계산 98개, 테스트 179개 통과. SCC 기구별 심각도 지수, 검사등가·최상위 등급·횟수, 시간 보정과 HIC/SOHIC 모니터링 보정을 연결했다. 감수성 표의 경도·황 함량·PWHT·온도 경계와 PASCC 재질·열처리 조건을 검증했다. 미보수 균열은 FFS 필요 오류로 처리하며 원문 pH 범위의 공백과 93 C 중복 경계는 추정으로 채우지 않는다. 감수성 조회만으로 전체 재질·운전 적용성 검토가 완료되지는 않는다.

여섯 번째 체크포인트: 독립 계산 109개, 테스트 199개 통과. 외면부식·CUI의 SI 부식률 표·선형/시간가중 보간, 설계·접면·보온재·상태 보정, 코팅 보호기간과 검사 갱신 DF를 연결했다. 내부 감육의 0.1 하한을 외면 DF에 잘못 적용하지 않도록 검증했다. 외면·CUI CLSCC는 내부 CLSCC와 다른 심각도 지수 및 코팅기간을 사용한다. SI/US 부식률 불일치와 CUI 강도비 식의 Min/Max 불일치는 명시적으로 보류한다.

주요 구현 수식·표는 원문 PDF를 페이지 이미지로 렌더링해 대조했다. 전체 규격 예제의 독립 재계산, 설비별 적용성 검토, 실제 slabx 회귀 비교, LH2 적용성 검증은 아직 완료되지 않았다. 소프트웨어 테스트 통과를 공학적 인증으로 표시하지 않는다.

## 다음 개발 순서

1. 현 API의 독립 참조 사례와 원문 예제 데이터를 확충하고, 조항 인벤토리의 줄바꿈·표 번호를 수동 대조한다.
2. Level 1 Type 1·나머지 독성·비용표와 물성 자동선택을 추가하고, 입력부터 네 누출공·비용까지 전체 COF 경로를 확장한다.
3. SCC·외면손상·HTHA·취성·피로를 적용성 판정과 함께 확장한다.
4. 풀화재·파이어볼 기하 해석과 적용성 검증을 보강하고 VCE·BLEVE·물리폭발·독성 피해를 확장한다.
5. PRD·열교환기 번들·AST 전용 평가 경로, 부식률 부속서, 검사 효과성·예측·계획을 확장한다.
6. slabx 계열 실제 실행 명세를 받으면 어댑터 및 검증 사례를 연결한다. 그동안 다른 계산 개발은 진행 가능하다.
7. 디지털 트윈 호스트에서 직접 호출할 Python 계약과 버전 호환성을 검증한다. 이벤트 수집·작업·접근제어는 호스트 책임이다.

## 원문 해석 보류

`src/api581/data/coverage.json`의 `source_discrepancies`에서 표 합계·단위·교차참조·사건확률 표기 불일치를 추적한다. 해석이 불명확한 셀은 API에서 거부하거나 모델의 선택 가정을 응답 제한사항에 명시한다.

## Python API 전환 확인

115개 공개 계산 함수, 206개 테스트 통과. 별도 가상환경에서 wheel 설치 후 기체 누출 계산,
함수 목록·조항 자료 조회를 확인했다. 설치 환경에는 FastAPI가 없다.

사용자가 요청한 import 기반 패키지 구조로 전환했다. FastAPI/uvicorn/httpx 의존성,
서버 실행 진입점과 OpenAPI 계약을 제거했다. 공개 함수는 타입 있는 입력과 `CalculationResult[Output]`를 사용한다.
기존 계산 검증을 유지하면서 Python 호출·스키마·메타데이터·조합·선택 저장 테스트로 전환했다.
배포 wheel에는 계산 코드와 조항 인벤토리를 포함하며 원문 PDF는 포함하지 않는다.
실제 GitHub/PyPI 게시는 수행하지 않았다.

## 취성 손상기구 확장

127개 독립 Python 함수, 291개 테스트 통과.

- 취성파괴: Table 20.3 기준온도, 20.4M/20.5M 두께·PWHT 기본계수,
  얇은 부품 OR 8가지 운전이력 조건의 FSE 보정, 전체 DF 조합.
- 템퍼 취화: J/X-bar 조성계수, X-bar 전이온도 변화, 제작 연도별 보수적 변화량,
  제공된 delta-FATT와 최소 가압온도에 따른 DF. 취성 FSE를 템퍼 DF에 적용하지 않는다.
- 885°F 취화: 전이온도 기준 표 조회와 +56 K 초과의 명시적 0 행.
- 시그마 취화: 함량 분류와 평가온도별 DF. 원문에 없는 1% 이하 분류는 거부한다.
- 기본계수와 선형 보간, 경계, 보정 조건 각각, 기구 간 최대값 선택 및 빈도 연결을 검증했다.

모든 표 함수는 범위를 검사하고, 선형 보간은 호출자가 명시적으로 선택한다.
J→delta-FATT의 인쇄 지수, SCE 수식, 템퍼 제작 연대별 C/F 온도차 불일치와 1988년 공백은
조항 인벤토리에 기록했다. 임의로 원문을 고치거나 모호한 조건을 자동 판정하지 않는다.

## PRD·번들 확장

150개 독립 Python 함수, 367개 테스트 통과. 신규 분야 `prd`와 `bundle`을 추가했다.

- PRD: FAIL/LEAK 기본 Weibull, 폐쇄 토출·소프트시트 보정, 환경 계수의 중복 배제,
  설정압·과압 보정, 요구빈도, 단일 검사 갱신, 보호설비 LOC와 사건 연간빈도.
- 번들: 고정 beta Weibayes 갱신, 실패·중도절단 자료, 예측 실패점 추가,
  두께/ERL 수명, 수명 연장, 재질 표 41행, 교체비·피해, 범주·목표 나이,
  생존 조건부 연기 경제성, 유한 격자 교체 비용 최적화.
- 원문 예제의 eta 22.16년·27.2년, 검사 갱신 eta 17.9년을 재현했다.
- 중첩 입력 타입도 공개 모듈에서 import할 수 있다. Python 조합 예제 2개를 추가했다.

원문의 500°F 환경 경계 공백, 남은 두께 분율과 식(1.72)의 불일치,
연기 결정 부등호의 본문/식 불일치, 중복된 표8.5 번호, 일/연 비용 단위를 기록했다.
번들 확률과 PRD 누설 CDF를 연간빈도로 자동 취급하지 않는다.

남은 범위: PRD 누설 피해·위험 통합·복수 장치, 검사 이력의 정비/교체 기준일 관리,
번들 라이브러리 매칭·형상 추정·Fisher 하한·검사 불확실성 곡선 및 이를 이용한 전체 검사 계획.
이 체크포인트는 Part1 §7/§8 전체 검증 완료를 뜻하지 않는다.

## PRD 누설·위험·서비스 이력 확장

163개 독립 Python 함수, 410개 테스트 통과.

- 누설률·발견시간 표·회수 계수·재고 손실·수리비 기준·생산 손실·통합 COF.
- 본문 2사건과 표7.15의 3사건 계산을 명시적으로 선택. 원문 불일치를 결과 입력과 계산 출처에 기록.
- 복수 PRD 면적 기반 압력 보정과 Fop용 원 압력 보존.
- 보호설비별 사건 합산 후 설비 간 최대 FAIL 위험, 누설 위험, 차원을 명시한 통합 결과.
- 설치/검사/정비/교체/설계 변경 날짜, 사용연수와 통계 이력/검사 갱신 시작 경계.

본문식 1%와 표7.15 보통 누설10%의 차이, 정확30분과 반올림 .021일,
재고 손실 단계의 교차참조 오류를 조항 자료에 추가했다.
단순 검사로 사용연수를 초기화하지 않으며 정비·교체의 as-new 가정과 구분한다.
복수 장치의 압력 저감 계수는 독립 실패확률 곱이나 실제 설계 용량 검증을 대체하지 않는다.

남은 PRD 범위에는 API520 유량/오리피스 설계, Table7.2/7.3 요구사건·최대압력 자동 선택,
전체 검사 이력 eta 자동 갱신, 의존고장·공통원인에 대한 확장 검증 및 설비별 완전한 Part3 COF 생성이 있다.

## Type1·독성 COF 확장

174개 독립 Python 함수. 469개 테스트 통과.

- 10종 Type1 가연성 SI 계수, 설비/인체 단일 계산, 조합 계산, 소스부터 피해면적까지 연결.
- Pyrophoric의 Type0 표를 추가하고 HF 가연성 빈 셀을 명시적으로 유지.
- HF/H2S log 상관식, 5~60분 면적 보간, H2S 순간 누출 및 근거 있는 HF 절편 제공 경로.
- SI Table4.13M 추가10종 연속 독성, 물질·상·시간 적용 범위 및 N/A 보존.
- 독성 질량분율·이론 누출률·시간·완화·원문 IDLH 스크리닝 조합.
- H2S 네 누출공의 가연성/독성 → 가중 최종면적 → 재정피해 → 연간 위험 Python 예제.

순간 HF `d=33,606`은 원문이 불명확하여 자동 수정하지 않는다. 추가10종의 순간 독성 상관식은
원문에도 없으며 외부 확산/Level2 경로가 필요하다. Type1의 미기재 셀도 임의로0으로 채우지 않는다.
Table4.13 미국 단위 표의 불명확한 숫자는 SI 표4.13M을 직접 사용하여 우회했으며,
HF/H2S처럼 미국 단위 상수를 사용하는 경우에만 환산을 수행한다.

소프트웨어 테스트와 예제 실행은 설비 적용성·모델 자체의 독립 공학 인증과 구분한다.

## 풀화재 형상·복사 확장

183개 독립 Python 함수, 493개 테스트 통과.

- 물 분압·대기 투과율, 몰 분율 혼합 연소율.
- Thomas 길이·무차원 풍속·화염 기울기와 표면 방사열.
- 인쇄식 및 기하 적분 대조식의 수직/수평/최대 형상계수.
- 표면/축 거리 해석을 명시한 열유속·임계 거리·피해 면적 및 전체 풀화재 조합.
- 독립 표면 적분4조건, 단위·습도 백분율·기하/거리 선택·임계값 잔차·영역 경계·수치 오류를 검증.

인쇄된 수직 형상계수의 두 항과 거리 정의는 기하학적 대조와 차이가 있다.
자동으로 정오표로 취급하지 않고 명시적 선택지와 출처 제한사항으로 관리한다.
`docs/POOL_RADIATION_VALIDATION.md`에 식·거리·독립 적분·외부 기준 문서·경계 결과 해석을 기록했다.

남은 범위: 모델 자체의 실험·LH2 적용성, 연료별 그을음 차폐, 지형·화염 직접 접촉,
전체 Level2 사건 경로, 풀 증발/확산과 실제 slabx 계열 연동 및 나머지 폭발·독성 계산.

## 파이어볼 복사·피해거리 확장

188개 독립 Python 함수, 516개 테스트 통과.

- 가연성 질량, 구형 형상계수, 수용점 열유속, 임계 거리·피해 면적, 파열 파이어볼 전체 조합의 5개 API 추가.
- 기존 직경·높이·지속시간·압력 기반 방사율·표면 방사열과 연결한다.
- 원문 거리식과 높이를 반영한 구형 해석을 필수 선택값으로 구분하고 결과·해시에 남긴다.
- 독립 구 표면 적분 4조건, 상수 투과율의 해석적 역산, 수증기 투과율의 임계값 잔차를 대조했다.
- 영 질량·영 에너지·원점에서 임계값 미만·탐색 범위 부족·반복 비수렴·수치 언더플로를 구분한다.

`docs/FIREBALL_RADIATION_VALIDATION.md`에 원문 불일치와 거리·수용면 방향·대기 경로의 정의를 기록했다.
독립 적분은 기하 구현의 대조이며 모델의 실험 검증이나 API 정오표 승인을 뜻하지 않는다.
VCE 폭압 곡선·BLEVE·확산/독성·전체 사건 경로와 LH2 적용성 검증은 남아 있다.

## VCE TNT 폭압·피해거리 확장

195개 독립 Python 함수, 551개 테스트 통과.

- Hopkinson 환산 거리, 인쇄된 역로그 폭압 곡선, 실제 거리의 측면 입사 과압.
- 건물 붕괴 probit와 목표 확률의 압력 역산. 후속 STEP8.14 대조에 따라 통합 기본값은 probit5(50%)로 보완했다.
- 구간 내 임계 압력 거리·면적과 질량→TNT→인체/설비 피해의 조합.
- 필수 `fit_domain`: 계산 구간·공학 근거를 기록하고 구간 전체의 양수·단조 감소 성질을 검사한다.
- 80자리 Decimal 독립 직접 합산, 질량 세제곱근/면적 스케일링, 역산 잔차와 비물리 구간·영 질량·비수렴을 검증했다.

원문 C26=100은 kPa 환산이다. 공개 함수는 Pa를 사용하며 원문 다항식에 지수함수를 추가하지 않는다.
건물 붕괴 확률은 개방 공간의 직접 사망률·폐출혈 확률과 구분한다.
`docs/VCE_BLAST_VALIDATION.md`에 상세 근거를 기록했다.
별도 환경에 wheel을 설치해 공개 함수·스키마·인벤토리 및 실행 예제를 확인했다.
곡선 유효구간의 실험 검증, BLEVE·물리폭발·확산·독성 노출·LH2 적용성은 미완료다.

## 물리폭발·BLEVE·Level2 NFNT 확장

202개 독립 Python 함수, 578개 테스트 통과.

- 파열 증기 공간 Brode 에너지, 액체 플래시 kmol 준비, BLEVE 액체 에너지와 별도의 TNT 환산.
- 물리폭발/BLEVE의 파열 전용 거리·면적. BLEVE는 기존 증기 공간과 액체 플래시분을 합산한다.
- 비파열 사건은 폭발 면적0과 `not_rupture`를 반환하되 잠재 저장 에너지/등가량을 보존한다.
- NFNT 최대 면적 선택·비점화 확률·네 누출공 GFF 가중을 독립 API로 제공한다.
- 예제는 플래시분→BLEVE/물리폭발→증기 누출→NFNT→DF/Fms 보정 연간 면적 위험으로 연결한다.
- Decimal 단위 대조, kPa/Pa와 kmol/mol 혼동, 액체/증기 합산, 파열 게이트, 확률 중복 가중과 4공 집계를 검증했다.

이 단계에서 VCE 세부 STEP8.14의 probit5를 확인하여 통합 VCE 인체 목표의 기본값을50%로 보완했다.
기존 명시적 목표 입력은 유지되며 문서·스키마를 함께 수정했다.
`docs/PHYSICAL_BLEVE_VALIDATION.md`에 계수·압력·몰 단위·집계와 미검증 범위를 기록했다.
폭압 곡선 실험 검증·실제 플래시/EOS·과열 적용성·파편 및 LH2 적용성은 미완료다.

## Level2 독성 노출·후처리 확장

210개 독립 Python 함수, 635개 테스트 통과.

- Table4.14 27종 조회와25종의 ppm·초 단위 상수 농도 probit/확률 기준 역산.
- methanol/styrene의 미제공 probit는 오류 처리하며 기준 값의 빈 칸을0으로 채우지 않는다.
- 시간별 종별 농도의 거듭제곱 적분. 이전 값 유지/선형 농도 보간을 필수 선택하고 확장 모델로 표시한다.
- 전체 혼합물 유량 기준 독성 방출 시간·독성 몰분율 기준 보정·성분별 최대 면적·비점화·4공 GFF 평균.
- 27종 순·역산, 원문 수치 앵커, 독립 Simpson 적분3조건, 비선형 거듭제곱·영 노출·로그 영역·수치 범위·중복 가중을 검증했다.

`docs/LEVEL2_TOXIC_VALIDATION.md`에 역사적 표·단위·노출 확장과 미검증 범위를 기록했다.
예제는 가정한 농도 이력으로 Python 연결 경로를 보여주며 slabx/slabx-lh2가 실행된 결과가 아니다.
실제 확산 연결, 기준 우선순위의 자동 선택, 공간 컨투어·농도 시간평균과 설치별 적용성 검증은 남아 있다.

## Level2 사건·기구·재정 위험 조합

216개 독립 Python 함수,16개 분야,656개 테스트 통과.

- 5개 가연성 사건의 완전 확률 검사와 원래 면적의 확률 가중.
- 같은 비점화 확률을 공유한 독성·NFNT의 기구별 면적 및 명시적 독성 비적용 근거.
- 기구별 GFF 평균 뒤 식3.202–204의 가연성 가산·비점화 최대·설비/인체 최대 선택.
- 종합 평가는 부품 GFF·Fms·공급 DF·Level2 최종 면적·5재정 항목·연간 위험을 연결한다.
- 원문 식과 Level1의 차이, 최대/평균 순서가 달라지는 반례, 사건 확률 보존, 적용성 생략,
  재정 비용·DF0·타입/부품 일치·오버플로를 검증했다.

`docs/LEVEL2_ASSESSMENT_VALIDATION.md`에 원문 식·단계 순서·통합 경계를 기록했다.
새 예제는 계산한 제트/파이어볼/VCE/물리폭발과 공급 구름 자료·사건확률에서 재정 위험까지 실행한다.
전체 장비자료 자동 분석, 실제 확산·2상 사건확률 추론·손상 적용성·설치별 검증은 남아 있다.

## 미점화 풀 증발 소스항 확장

223개 독립 Python 함수,16개 분야,683개 테스트 통과.

- 표5.2M의4종 지표면 물성·비등/비비등/온도 경계 판정.
- 원문 식3.103의π지수·증기 체적유량·정상 도달시간 및 식3.104의반경.
- 비등 정상상태는 증기밀도로 체적유량을 구하고 공급시간·부지 면적의 지원 여부를 구분한다.
- 비비등 식3.105의압력·온도 단위와 풍속/반경 지수, 평형 반경 및 유한 평형 부재.
- 원문 수치·독립 US 상관식 단위 대조·순/역산·스케일링·정상 지원 실패·영 소스를 검증했다.

`docs/POOL_EVAPORATION_VALIDATION.md`에 증기/액체 체적유량 차이와 C15 단위 경계를 기록했다.
지원되지 않는 정상상태는 확산 입력용 유량None으로 반환한다. 원문식을 시간별 질량수지 모델로 주장하지 않는다.
실제 성장/배수·공급 중단 후 증발·EOS/플래시·현장 및 LH2 검증과 확산 엔진 연결은 남아 있다.

## Level2 방출상·rainout·액적 분할 확장

229개 독립 Python 함수,16개 분야,717개 테스트 통과.

- 저장압/포화압의 방출상 판정, 중복·누락 경계, 원문 보수적 액체식의2상 유량.
- Kletz rainout·제트/풀 유량, 인쇄식/플래시 후 질량수지 기준의 액적 동반율.
- 소스 분할은 원문 근거를 보존하고0–1 밖 인쇄식 조성의 사용을 거부한다.
- 완전 rainout의 제트 조성은None이며 풀/제트·제트 내 증기/액적 질량·유량 보존을 검증했다.
- 예제는 오리피스→검지/차단·재고→Kletz→상별 분할→풀 증발과 액적 제트 확산 요청 초안으로 연결한다.

`docs/LEVEL2_SOURCE_PARTITION_VALIDATION.md`에 식3.102의 인쇄식과 별도 질량수지 해석을 기록했다.
후자를 공인 정오표로 주장하지 않는다. 원문 경계 상 선택·플래시 성상은 사용자가 근거와 함께 확정한다.
실제 EOS/플래시·HEM/Omega·액적 크기/후속 증발과 네이티브 slabx 매핑·검증은 남아 있다.

## Level2 점화·조건부 사건 확률 확장

237개 독립 Python 함수,16개 분야,754개 테스트 통과.

- 가연성 상별 유량, 인화점/유량 상온 확률, AIT 최대, 온도 보간과 표5.3의4행.
- 원문 C16=30.89K와 사용자 근거 온도를 필수 기준으로 구분한다.
- 인쇄2상 액체 가중과 별도 근거의 증기 가중을 선택하고 출처에 기록한다.
- 단일상 누설/파열 트리는 그림의 VCE 경로·여사건을 사용하고5개 사건+비점화 확률을 보존한다.
- 그림5.3 순간 누설 파이어볼은 본문과의 차이를 명시한 면적 집계 선택으로 연결한다.
- 고정밀 직접 합산8조건, 표/AIT 앵커, 온도 경계, 원문/해석 차이,6개 그림 경로와 영 소스를 검증했다.

통합 위험 예제의 수동 사건확률을 점화 모델 계산값으로 교체했다.
`docs/IGNITION_VALIDATION.md`에 원문 불일치·가정·계산 순서와 후속2상 트리 범위를 기록했다.
완전2상 트리, 연속 파열, 경험 확률의 현장/LH2 적용성 검증은 남아 있다.

## 2상 점화·상관 즉시점화 분기 확장

241개 독립 Python 함수,16개 분야,779개 테스트 통과.

- 조건부 파이어볼 여부와2상 누설/순간 파열 트리, 액체/증기 점화 조합.
- 연속2상 누설은제트/풀 최대를 하나의즉시점화 분기로표현한다.
- 설비/인체 최대 면적을 각각 선택하고 한 번만 가중하여 기존4공·재정 위험 평가에 연결한다.
- 순간 파열 파이어볼 분율은 식3.123의1이 기본이며 근거 없는 분할값을 만들지 않는다.
- 2상 트리 경로·확률 보존·중복분기 거부·phase별 계산·수동 가중·전체 평가·영 소스·양수 유량 언더플로를 검증했다.

`docs/TWO_PHASE_EVENT_VALIDATION.md`와`examples/two_phase_event_risk.py`에 연결 경계를 기록했다.
해당 예제의 피해면적·플래시 물성·가중 기준·DF·가격은 사용자 가정이다.
연속 파열·원문 해석 확정·실제 EOS/확산·실험/현장/LH2 적용성은 남아 있다.

## AST 수리·재고·유출량 확장

254개 독립 Python 함수,17개 분야,822개 테스트 통과.

- 탱크 대표 유체7종·토양8종,원문 경계 순서를 보존한 전도도 평균·제품 보정·침투속도.
- 바닥 작은 누출공 개수,코스 하단 기준·바닥 전체 재고,상수 수두 쉘 방출률.
- 바닥 Bernoulli/Giraud/전이식의SI구간·RPB 수두·명시적 전이식 누출공 개수 기준.
- 쉘 지름 경계와바닥 RPB/기초 중복을 구분한 검지시간,재고 제한 누출·전체 재고 파열량.
- 표·단위·3구간·SI/US 유량 대조·구간 등호·원문 누락·검지 선택·부피/질량을 검증했다.

`docs/TANK_SOURCE_VALIDATION.md`에 단위·C37 구간 차이·전이식 개수·mass=Bbl 문제와 선택 기준을 기록했다.
탱크 GFF·환경 피해·최종 COF/위험·동적 배수·현장 및 LH2 적용성은 미완료다.


## AST 환경피해·바닥 수리비 확장

261개 독립 Python 함수,17개 분야,856개 테스트 통과.

표6.6 추정비용·지표 순차 배분·지하수 도달/하부토양 배분·쉘/바닥 환경비용·파열만 지름 보정한 바닥 수리비의7개 API를 추가했다.
4공 GFF 합계로 한 번 가중하며,탱크 표의 불일치하는 합계는 자동 사용하지 않는다.
원문의 탐지시간 분모와 표6.6의 가격연도 미명시를 제한사항으로 보존한다.
수동 앵커·부피 보존·경계·가중·통화 불변성과 설치된 wheel의 정적 타입/스키마 계약을 검증했다.
docs/TANK_ENVIRONMENT_VALIDATION.md와examples/tank_environment.py에 경계와 예제를 기록했다.
전체 재정 COF·탱크 GFF·부품별 위험·현장/LH2 검증은 미완료다.


## AST 부품 재정피해·연간 위험 확장

267개 독립 Python 함수,17개 분야,878개 테스트 통과.

탱크 GFF 인쇄 총합과 식3.208 합계를 함께 반환하며 계산에는 합산 기준을 명시한다.
탱크 전용 정지기간·바닥/쉘 재정피해·외부 DF 기반 부품별 연간 위험의6개 API를 추가했다.
바닥은 주변설비·인명 비용 비적용,쉘은5항목 재정피해를 집계한다.
USD2001 환산 정지 상관식·같은 통화/가격 근거·GFF 중복 가중 방지·NA 보정·양수 언더플로를 검증했다.
전체 탱크 자동 손상/소스/면적 생성·공통원인·현장/LH2 검증은 미완료다.

## Annex2.B 토양측 부식률·감육 연결

294개 독립 Python 함수,18개 분야,1043개 테스트 통과.

토양 기본 부식률3프로필·저항률5구간·온도·CP5조건·코팅9종/나관·독립 식2.B.21·부식률 조합·감육 연결8개 API를 추가했다.
인쇄 SI/US 차이·저항률 겹침·저항률의 기본값 포함 여부와 코팅 인자별 적용을 명시한다.
식2.B.22의13.5 인쇄 결과와 실제8.1 곱을 구분하고 공식 정오로 단정하지 않는다.
50개 신규 테스트로 표·단위·경계·중복 보정·독립/통합 감육 일치와 수치 범위를 검증했다.
목차 추적은 토양 계산 조항을 직접 연결하며,손상 설명·예방·참고문헌까지 구현된 것으로 넓혀 표시하지 않는다.
이 조합은 단일 상수 부식률의 비탱크 무클래딩 내압 부품이다. AST바닥·코팅/CP 변화 이력·기타 화학 부식률·현장 검증은 미완료다.
[토양 검증](SOIL_CORROSION_VALIDATION.md)과 [예제](../examples/soil_corrosion_to_thinning.py)에 근거를 기록했다.

## 독성 기준·네이티브 지면 피해 연결

286개 독립 Python 함수,18개 분야,993개 테스트 통과.

2016 독성 기준 우선순위/시간 선택과 실제 지면 TWA 독성 피해 연결2개 API를 추가했다.
probit50·시간별 표·외부 후보를 같은 우선순위면 명시적으로 선택하고 상위 후보 제외 근거를 요구한다.
몰분율 기준 보정·비점화 한 번 가중·§3.186 지속시간·선택 노출/평균창과 지면 조건을 적용한다.
독성/플래시화재 전용 네이티브 연결은0m를 요구한다. 일반 농도장 높이 선택은 유지한다.
27개 추가 회귀 검증과 실제 염소 native 배열·평면·기준·확률 매핑 및잘림/짧은 노출 차단 검증을 통과했다.
실제 시간이력의 비선형 dose·짧은 펄스·혼합물 열역학/종별 확산·현장 적합성은 미완료다.
[검증](NATIVE_TOXIC_VALIDATION.md)과 [예제](../examples/native_toxic_pool.py)에 해석과 제한을 기록했다.

## 실제 제트·소스 분할 연결

284개 독립 Python 함수,18개 분야,966개 테스트 통과.

실제 수평/수직 제트 중심선·평면과 API581 소스 분할의 네이티브 연결4개 API를 추가했다.
같은 분할의 제트 총유량·액적분율·질량에서 지속시간을 계산하며 요청/사용 온도·유도 속도·근접장 상태를 반환한다.
미구현 수직 부력·빈 제트·순수 액체·온도 충돌은 명시적 오류로 구분한다.
17개 신규 기본 테스트와 실제 수평/수직·LH2·직접 배열 일치·평면·분할 연결 검증을 통과했다.
팽창/플래시/EOS·근접장·임의 방향/충돌·LH2 physical-transition·현장 적합성은 미완료다.
[검증 기록](NATIVE_JET_VALIDATION.md)과 [예제](../examples/partitioned_native_jet.py)에 범위를 기록했다.

## 실제 평면 농도장·면적·플래시화재 연결

280개 독립 Python 함수,18개 분야,949개 테스트 통과.

선형 삼각형 격자 면적·실제 native at_y 평면장·유효 LFL면적→플래시화재3개 API를 추가했다.
독립 해석해의 면적/수렴과 입력·프로토콜·플래시 연결 차단의20개 추가 테스트를 검증했다.
실제 엔진에서는 원시 횡농도 배열 일치·대칭·횡격자 세분화·횡경계 잘림·LH2 전제 위반·플래시 면적 매핑을 별도 검증했다.
유효 면적은 경계/전제 위반이면null이며 진단 면적을 보존한다. 플래시 연결은 그런 면적을0으로 대체하지 않고 실패한다.
이는 공급 격자의 보간 면적이며 연속 컨투어의 정확해·현장 검증·전체 격자 수렴을 보장하지 않는다.
원시 제트/시간소스·EOS·구름 질량·독성 기준 자동 연결·현장/LH2 검증은 미완료다.
[공간 검증](NATIVE_FOOTPRINT_VALIDATION.md)과 [예제](../examples/native_pool_flash_fire.py)에 경계를 기록했다.

## 실제 SLABx/SLABx-LH2 선택적 풀 연결

277개 독립 Python 함수,18개 분야,929개 테스트 통과.

일반 시간 프로파일 초안과 구분하여 실제 EvaporatingPool→run_dispersion→concentration_field 경로를 연결했다.
SLABx1.0.8/LH2 0.2.0 소스 매핑을 확인하고 프로젝트 내 별도 환경에서 두 엔진을 실행했다.
LH2 보정은 별도 프로세스에 격리하며 직접 엔진 농도 배열 일치·경계 검열·전제 위반 차단·동시 실행/호스트 전역 불변성을 검증했다.
API 코드 지문 외에 엔진 버전과 Python 소스 지문도 결과에 포함한다.
물성·기상·증발량·농도 기준은 명시적 외부 입력이다. 2차원 면적·구름 질량·가변 소스·제트/EOS 연결과 현장/LH2 적용성 검증은 미완료다.
[네이티브 검증](NATIVE_DISPERSION_VALIDATION.md)과 [호출 예제](../examples/native_dispersion_pool.py)에 범위를 기록했다.

## AST 쉘 사건·면적·위험 연결 확장

276개 독립 Python 함수,17개 분야,914개 테스트 통과.

방유제 풀 복사·AST 쉘 Level2 사건/4공 집계·치수/소스와 외부 피해면적의 통합 재정위험4개 API를 추가했다.
방유제 제한은 연소 풀만/피해면적도 제한의 필수 해석 기준을 받으며 원래 복사 면적·거리를 보존한다.
AST NFNT를 입력에서 제외하고 연속 방출·비점화 독성 가중·공별 GFF 평균 후 Level2 합산을 적용한다.
비점화·GFF 중복 가중,0풀·빈 코스·비적용 파이어볼·동일 방유제 기준과 독립/통합 일치를 검증했다.
실제 확산·자동 점화/독성 기준·전체 탱크 중첩·EOS·현장/LH2 검증은 미완료다.
[쉘 검증 기록](TANK_SHELL_VALIDATION.md)과 [호출 예제](../examples/tank_shell_source_to_risk.py)에 경계를 기록했다.

## AST 치수·토양부터 소스·위험까지 확장

272개 독립 Python 함수,17개 분야,897개 테스트 통과.

표6.3/6.4의 대표 공 선정2개,쉘/바닥 소스 연결2개,바닥 치수·토양부터 재정위험까지 통합1개 API를 추가했다.
파열 대표지름은 이미지의 D/4를 사용하며,분모가 누락된 텍스트 추출을 따르지 않는다.
소스 계산은 유체·토양/물 기준→전도도/침투·공 수→재고/유량→탐지/방출 부피/질량을 연결한다.
바닥 파열 유량/지속시간은 원문 미정의로null,파열 방출량은 전체 재고다.
바닥 통합은 같은 소스의 GFF·검지시간·유출량·침투속도에서 환경피해·수리·생산손실·연간 위험을 계산한다.
개별 함수 조합과 통합 결과 일치·공 수·D/4·빈 코스/RPB·단위·수치 경계를 검증했다.
외부 DF/가격 적합성,전체 탱크 공통원인·쉘 자동 면적·과도 배수·현장/LH2 검증은 미완료다.
[검증 기록](TANK_SOURCE_COMPOSITION_VALIDATION.md)과 [호출 예제](../examples/tank_geometry_to_risk.py)에 근거를 기록했다.
docs/TANK_FINANCIAL_VALIDATION.md와examples/tank_financial_risk.py에 검증과 부품 경계를 기록했다.
