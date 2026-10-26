# API 581 구현·인증 실행 로드맵

이 문서는 API-RP-581 2016 3rd-base 전체 구현 목표를 코드·표준 절·검증
증거 단위로 추적하기 위한 실행 기준선이다. 통과한 소프트웨어 테스트는
공식 API 581 적합성 또는 독립 공학 인증을 의미하지 않는다.

## 기준선

| 항목 | 현재 기준 | 증거 |
|---|---:|---|
| 등록 계산/API | 509 | `src/api581/data/python-api.schema.json`, `api581.list_calculations()` |
| 추적 표준 절 | 861 | `src/api581/data/coverage.json` |
| native fixture 검증 | 17 계산 / 9 scripts, latest run 9/9 passed | `docs/NATIVE_ENGINE_EVIDENCE.json`, `tmp/native-suite-latest.json` |
| reference fixture | 19 | `scripts/verify_reference_fixtures.py` |
| 일반 전체 회귀 | 11,848 passed, 3 skipped | current local pytest profile |
| qualified native 회귀 | 11,846 passed, 3 skipped | latest efficient Nurion profile; local profile includes two additional guard tests |
| Nurion array | Latest reconciled run: **64/64 shard passed**, 32 input-matrix shards / 16,000 cases passed, metadata/release/provenance gates passed against fresh package artifacts. | `tmp/nurion-parallel-20261025T113434Z-reconciled-latest.json` |
| release audit | `audit_ok=true` | `docs/release-evidence.json` |

## 구현 gate

각 계산 항목은 다음 gate를 순서대로 통과해야 한다.

1. **API gate** — typed input/output, 단위·범위·오류 계약, 공개 API 경로.
2. **Source gate** — 표준 절·공식·표 셀·해석 basis와 양방향 traceability.
3. **Software gate** — 정상·경계·오류·단위변환·결정론 테스트.
4. **Fixture gate** — 독립 산술 fixture 또는 qualified native fixture.
5. **Integration gate** — 빈도→방출→결과→영향→위험 통합 workflow.
6. **Nurion gate** — PBS array 재현 실행, receipt, timeout, hash, 성능 기록.
7. **Release gate** — wheel/sdist, clean install, schema/evidence hash, audit.

## 우선 구현 순서

1. 빈도·누출·재고량·상(phase) 선택 및 방출 source partition.
2. jet/pool/fireball/VCE 및 독성·확산 consequence chain.
3. damage mechanism·inspection effectiveness·POF 연결.
4. Level 1/Level 2 및 portfolio risk 통합.
5. SlabX/SlabX-LH2 source/property/threshold 경계와 native fixture 확장.
6. API 520 및 SLABx native 경계의
   별도 qualified module 여부 결정.

## Nurion 실행 정책

- 모듈·fixture·계약·성능·전체 회귀를 PBS array로 동시에 실행한다.
- 각 shard는 `.status`, `.meta`, `.out`, `.err`를 남긴다.
- `scripts/nurion_parallel_collect.py`로 원격 결과를 하나의 JSON evidence로
  수집한다.
- timeout과 환경 의존성은 실패로 숨기지 않고 별도 상태로 기록한다.
- 전체 목표 완료 전에는 goal을 complete로 표시하지 않는다.

## 현재 명시적 잔여 범위

- 861개 절 중 76개는 supporting-text review가 남아 있다.
- API 520 capacity sizing은 `api520/*` typed Python API로 편입됐으며 제조사 인증·API 526 오리피스 선택은 별도 입력/검토 경계다.
- SLABx buoyant vertical-rise branch는 Briggs effective-source 변환으로 지원되며 native fixture로 검증된다.
- software-tested 항목은 독립 공학 인증이 아니다.
