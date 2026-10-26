# API 581 구현 목표 감사

이 문서는 현재 구현의 증거를 요구사항별로 연결한다. `통과`는 해당
소프트웨어 계약·구조 검사가 통과했다는 뜻이며, API 581 적합성 인증이나
현장 독립 공학 검증을 뜻하지 않는다.

| 요구사항 | 현재 증거 | 상태 | 남은 범위 |
|---|---|---|---|
| 개별 계산 Python API | `src/api581/api/`, `docs/python-api.schema.json`, 509개 registry 항목 | 통과 | 각 설비·유체의 현장 적용성 및 독립 공학 검증 |
| 통합 위험평가 | `api581.api.risk`, `risk/assessment`, `risk/assessment-from-damage`, workflow API와 회귀 테스트 | 통과 | 표준 전체 예제의 독립 재계산 |
| 절·계산 추적 | `src/api581/data/coverage.json`, `docs/remaining-work.json`, `clause_evidence()`, `calculation_evidence()` | 통과 | 76개 supporting-text 절의 원문 요구사항 검토 |
| 미구현 명시 | 861개 절 중 `not_implemented` 76개, 각 항목 `next_evidence_needed` | 통과 | 문서성 절의 추가 근거 수집 |
| SLABx 연동 | `src/api581/slabx_adapter.py`, `docs/NATIVE_ENGINE_EVIDENCE.json`, native suite 9개 | 통과 | 현장 source/property/threshold 적용성 및 인증 |
| slabx-LH2 연동 | native LH2 실행·premise 차단·fingerprint 검증 | 통과 | 실험/현장 LH2 모델 검증 |
| 디지털 트윈 계약 | `TwinCalculationRequest/Response`, immutable payload, JSON Schema | 통과 | transport/authentication/event-store는 host 책임 |
| HPC batch 계약 | `TwinBatchPlan`, shard payload hash, `execute_batch_shard()`, merge 검증 | 통과 | scheduler 제출·재시도·저장은 host 책임 |
| 표준 문서 metadata | `api581.standard`, `standard.schema.json`, 정의 80·약어 125·참고문헌 22·절 ledger 861 | 통과 | metadata는 문서 조회용이며 계산 적용성·공학 인증을 대체하지 않음 |
| 원문 provenance | `standard-metadata.json`의 PDF SHA-256과 `verify_release.py` 대조 | 통과 | 원본 PDF 변경 시 metadata 재생성 필요 |
| 설치·배포 | wheel/sdist, packaged schemas/evidence, CI workflow, `twine check` | 통과 | 실제 PyPI 업로드 및 Trusted Publisher 설정 |
| 검증 수준 분포 | `release-evidence.json.validation_counts`: software-only 492, native fixture 17 | 통과 | software-only 항목은 독립 공학 인증 아님 |
| 직접 테스트 근거 | `release-evidence.json.software_test_direct_reference_count`: 509 | 통과 | 모든 계산 API에 직접 수치/분기 테스트 참조가 존재 |
| 직접 테스트 분포 | `release-evidence.json.direct_test_counts`: 509 직접, 0 간접 | 통과 | 모든 계산 API에 독립 직접 테스트 경계가 존재함 |
| 공개 경계 직접 호출 | `release-evidence.json.direct_public_test_reference_count`: 323 | 통과 | 실제 `evaluate()` 공개 경계를 호출한 모듈 수 |
| 독립 산술 fixture | `release-evidence.json.reference_fixture_count`: 108 | 통과 | software/native 검증 수준과 별도인 작은 결정론적 fixture |
| 분야별 검증 분포 | `release-evidence.json.validation_by_domain` | 통과 | 18개 분야별 native/software/direct-test 수량 |
| Part/Annex 절 상태 | `release-evidence.json.scope_status_counts` | 통과 | 7개 문서 범위별 partial/not_implemented 집계 |
| 문서 메타데이터 근거 분리 | `release-evidence.json.documentary_coverage`: metadata 6, supporting review 170, not_implemented 76 | 통과 | 메타데이터 추출은 supporting-text 해석·계산 적용성 인증을 대체하지 않음 |
| 잔여 상태 분류 경계 | `verify_release.py`가 not_implemented 76개 모두 `supporting_text_review`인지 검사 | 통과 | 향후 실제 계산 누락이 발견되면 별도 계산/API 검토로 승격 필요 |
| supporting-text traceability | `standard.supporting_text_review()`와 wheel 내부 `supporting-text-review.json`의 절별 locator/hash/classification | 통과 | 문서성 절의 공학적 해석·승인 자체는 별도 검토 큐 |
| supporting-text disposition | [`SUPPORTING_TEXT_DISPOSITIONS.md`](SUPPORTING_TEXT_DISPOSITIONS.md), `verify_supporting_text_dispositions.py` | 통과 | 76개 문서성 헤더를 metadata/workflow/engineering 경계로 분류; 계산 API 누락으로 간주하지 않음 |
| Evidence 총계 불변조건 | `verify_release.py` | 통과 | 절 범위 집계=861, 분야별 계산 집계=509 확인 |
| 무출처 계산 분류 | `release-evidence.json.unreferenced_calculation_ids`: 0개 | 통과 | 모든 계산 API에 표준 절 또는 명시적 근거가 연결됨 |
| SLABx buoyant vertical-rise | Briggs effective-source branch와 독립 native fixture | 통과 | `tmp/native-jet-verification.json` 및 9개 native suite |
| 외부 평가 | `validation_status=software_verified_external_review_out_of_scope` | 범위 제외 | 독립 검토자·제3자 인증을 프로젝트 요구사항에서 제외 |

## 현재 검증 기준

- 계산 API: 509개
- 원문 절 inventory: 861개
- 전체 회귀 테스트: current local profile 11,848개 통과, 3개 건너뜀
- Nurion PBS array (reconciled `24188926[].pbs`, latest recheck receipt): 64/64 shard 통과, 입력 매트릭스 16,000건 통과, 메타데이터/릴리스 게이트 통과
- native 검증: 9개 suite 통과
- 표준 schema: 5개 모델, metadata 정의 80·약어 125·참고문헌 22
- release audit: `audit_ok=true`
- completion matrix: 11 requirements, including separate canonical exhaustive and efficient Nurion regression gates
- 원본 PDF fingerprint: coverage inventory와 일치

재검증 명령은 [VERIFICATION_COMMANDS.md](VERIFICATION_COMMANDS.md)에 있으며,
현재 릴리스 증거는 [release-evidence.json](release-evidence.json)에 기록된다.
