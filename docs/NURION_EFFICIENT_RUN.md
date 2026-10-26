# Nurion 효율 실행 기록

무분별한 중복 array 실행을 방지하기 위해 specialized shard 0–9만 실행한
효율 프로파일의 독립 receipt다. 전체 64-shard canonical receipt를 대체하지
않으며, 변경된 코드의 영향영역과 선택 의존성 계약을 빠르게 재검증하는 용도다.

## 실행

- Run ID: `20261026T014258Z-parallel-a9107d2f`
- PBS array: `24201961[].pbs`
- Receipt: `tmp/nurion-efficient-20261026T014258Z.json`
- 범위: import, release, fixtures, digital twin, catalog, contract, performance,
  full regression, sqlite 제외 regression, digital-twin stress
- 결과: **10/10 passed**, failed 0, timed out 0

## 핵심 결과

- full regression: `11846 passed, 3 skipped`
- sqlite 제외 regression: `11783 passed, 1 skipped`
- reference fixtures: `106 passed, 2 optional-engine skipped`
- catalog tests: 15 passed; contract tests: 50 passed
- catalog validation: 7.063572 s
- digital-twin stress: 1,000 requests, 74.4278 requests/s

`optional_engine_missing` skip은 Nurion 이미지에 CoolProp가 없는 경우에만
적용된다. 계산 오류를 성공으로 바꾸는 fallback이 아니며, native SlabX/LH2
검증은 별도 native suite와 canonical 64-shard receipt에서 추적한다.

이 receipt는 제출 시점의 11,846-test payload를 보존한다. 이후 추가된
Nurion-submit profile guard 테스트 2개는 현재 로컬 기준(11,848 tests)에는
포함되지만 이 과거 receipt에는 포함되지 않는다.
