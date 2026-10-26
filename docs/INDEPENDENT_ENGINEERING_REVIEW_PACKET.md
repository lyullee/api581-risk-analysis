# API 581 독립 공학 검토 패킷

이 패킷은 소프트웨어 검증 결과를 독립 공학 검토자에게 전달하기 위한
고정된 입력 목록이다. 이 패킷만으로 API-RP-581 적합성 또는 설비별 FFS
인증을 주장하지 않는다. 검토자는 원문 판본, 적용 설비, 단위계, 입력 물성,
독립 재계산 및 서명 결과를 별도로 승인해야 한다.

## 기준 소프트웨어 증거

| 항목 | 현재 증거 |
|---|---|
| 계산 API | 509 typed calculations; `src/api581/data/python-api.schema.json` |
| 표준 절 ledger | 861 headings; `src/api581/data/coverage.json` |
| 양방향 traceability | 509 calculations, 0 unreferenced, 10 intentionally unlinked API 520 engineering utilities; `docs/release-evidence.json` |
| 일반 회귀 | current local 11,848 passed, 3 skipped |
| Nurion 회귀 | reconciled run `20261025T113434Z-parallel-reconciled`, 64/64 passed |
| Nurion 효율 회귀 | `tmp/nurion-efficient-20261026T014258Z.json`, 10/10 specialized shards passed |
| Nurion broad matrix | 16,000 generated invariant cases passed |
| native evidence | 17 calculations, 9 native verification scripts; latest `tmp/native-suite-latest.json` passed |
| release artifacts | `tmp/release-final-20261025br`, fresh wheel/sdist with regenerated packaged schemas, typed supporting-text locator/data, direct-test queue, synchronized native evidence, and wheel-data byte gate; repository payload-staging, source-fingerprint, and review-packet gates passed separately, `twine check` passed, hashes pinned in `docs/release-manifest.json` |
| requirement matrix | `docs/completion-matrix.json` separates passed software/native gates from the 76-clause supporting-text review queue |

## 독립 검토자가 재현할 명령

```powershell
python scripts/verify_release.py
python scripts/check_unimplemented_bodies.py
python scripts/check_doc_api_paths.py
python scripts/verify_supporting_text_queue.py
python scripts/verify_reference_fixtures.py
python -m pytest -q
python scripts/verify_native_suite.py --timeout-seconds 300
```

Nurion 원격 증거는 [64-shard reconciled receipt](../tmp/nurion-parallel-20261025T113434Z-reconciled-latest.json)를
사용한다. 각 shard의 host, return code, stdout/stderr receipt을 보존하고,
재실행 시 새 run ID와 archive hash를 기록한다.

## 검토자 서명 대상

- [ ] API-RP-581 2016 3rd-base 판본·원문 fingerprint·사용권 확인
- [ ] 각 계산의 식, 표 셀, 단위 변환, 보간·경계 정책 독립 재계산
- [ ] 누출률·재고량·flash/source-term 질량보존 확인
- [ ] frequency/POF, damage, inspection effectiveness, COF 및 risk aggregation 확인
- [ ] SlabX/SlabX-LH2 버전·source fingerprint·물성·premise 승인
- [x] API 520 capacity sizing typed module 및 교차 표본 연결
- [x] buoyant vertical-rise branch의 Briggs effective-source fixture 및 native suite 검증
- [ ] 설비별 운전자료·검사자료·FFS 결과와 uncertainty 승인
- [x] 외부 reviewer/organization/date/signature 요구사항 제외를 명시

## 인증 상태

현재 상태는 `software_verified_external_review_out_of_scope`다. 사용자 결정에 따라 독립 엔지니어 서명/제3자 인증은 프로젝트 요구사항과 릴리스 범위에서 제외했다.
