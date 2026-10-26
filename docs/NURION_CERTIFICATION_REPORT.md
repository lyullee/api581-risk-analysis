# Nurion 병렬 검증 보고서

## 실행 식별자

- PBS array: `24188939[].pbs`
- Run ID: `20261025T113434Z-parallel-reconciled`
- Remote payload: `/scratch/r1021a02/api581_parallel/20261025T113434Z-parallel`
- 수집 파일: `tmp/nurion-parallel-20261025T113434Z-reconciled-latest.json`

## 결과 요약

| 검증 영역 | 결과 |
|---|---:|
| PBS shards | 64/64 passed |
| 전체 Python 회귀 | 11,751 passed |
| compatibility 회귀(SQLite 제외) | 11,717 passed |
| catalog 회귀 | 13 passed |
| SlabX/digital-twin contract | 48 passed |
| reference fixtures | 19 passed |
| native evidence contract | 9 runs passed |
| release/provenance metadata gate | passed; reconciled receipt, manifest hashes, native manifest identity |
| catalog validation 성능 | 6.49 s |
| digital-twin stress | 1,000 requests, 40 shards, 70.04 req/s |
| failed/timed-out shards | 0/0 |

## 해석 기준

이 보고서는 API 구현의 결정론적 소프트웨어·계약·fixture·성능 재현성을
증명한다. API-RP-581 공식 적합성, 설비별 현장 적용성, 독립 공학 인증 또는
SlabX/LH2 물리 모델의 실험적 유효성 인증을 대체하지 않는다.

## 확장 배열 세부 결과

- PBS array: `24188939[].pbs`
- Run ID: `20261025T113434Z-parallel-reconciled`
- Evidence: `tmp/nurion-parallel-20261025T113434Z-reconciled-latest.json`
- 64/64 shards passed; failed/timed-out/running: 0/0/0
- Full Python regression: 11,751 passed
- Compatibility regression excluding sqlite: 11,717 passed
- Input invariant matrix: 32 shards × 500 = 16,000 cases passed
- Digital-twin stress: 1,000 requests passed
- Calculation traceability: 509 registered calculations, 10 intentionally unlinked API 520 engineering utilities, 0 unreferenced calculations.
- PBS stage-out anomaly: none in the final green run.

이 확장 배열은 최신 software reproducibility evidence다. 공식 API 581
인증이나 독립 공학 검토의 대체물로 해석하지 않는다.

## 재현 명령

```powershell
.\.venv\Scripts\python.exe scripts/nurion_parallel_submit.py --profile exhaustive
.\.venv\Scripts\python.exe scripts/nurion_parallel_collect.py `
  <RUN_ID> --shards 64 --output tmp/nurion-parallel-report.json
```

최종 release gate는 `scripts/verify_release.py`, `scripts/check_unimplemented_bodies.py`,
전체 pytest, `scripts/verify_native_suite.py`를 함께 통과해야 한다.
