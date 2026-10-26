# 검증 명령

이 문서는 API 581 계산 코드·source inventory·배포 wheel을 같은 기준으로
검증하기 위한 재현 가능한 명령 모음이다. 모든 명령은 저장소 루트에서 실행한다.
GitHub Actions의 `.github/workflows/verify.yml`도 동일한 계약 생성·감사·테스트·wheel
smoke gate를 실행한다. 공개 checkout에 원문 PDF가 없는 경우 PDF fingerprint 비교만
생략되고, 계산/Schema/coverage 검증은 계속 수행된다.
CI는 추가로 순수 Python 통합 예제 8개를 실행하며, SLABx/CoolProp 선택 의존성 예제는
외부 엔진 capability 검증 단계로 분리한다.
`.github/workflows/publish.yml`은 GitHub Release가 published일 때만 build·`twine check`
후 PyPI Trusted Publishing으로 업로드한다. `v` 접두사를 제외한 Release tag가
`pyproject.toml`의 project version과 일치하지 않으면 업로드하지 않는다.
이 작업은 로컬에서 업로드하지 않는다.
로컬 배포물 형식 검증은 `python -m build`와 `python -m twine check dist/*`로 수행한다.
원문 PDF에서 Part 1 표준 metadata를 재생성하려면 `python -m pip install -e ".[source]"` 후
`python scripts/build_standard_metadata.py`를 실행한다. 이 명령은 PDF SHA-256도 metadata에 기록한다.

## 생성 산출물

```powershell
.venv\Scripts\python.exe scripts\build_python_api.py
.venv\Scripts\python.exe scripts\export_contracts.py
.venv\Scripts\python.exe scripts\build_inventory.py
.venv\Scripts\python.exe scripts\build_remaining_work.py
```

생성 결과는 runtime registry와 API 581 2016 source-heading inventory를 동기화한다.
`build_inventory.py`는 원문 목차 861개 절을 보존하며, `build_remaining_work.py`는
기술 범위와 supporting-text 검토 상태를 분리한다.
`export_contracts.py`는 계산 계약과 함께 `docs/digital-twin.schema.json`을 생성한다.
두 Schema는 `src/api581/data/`에도 복사되어 wheel에 포함되며, release gate가
문서본과 패키지본의 hash 일치를 검사한다.

## 구조 감사와 회귀 테스트

```powershell
.venv\Scripts\python.exe -c "import api581; print(api581.audit_coverage())"
.venv\Scripts\python.exe scripts\verify_release.py
.venv\Scripts\python.exe scripts\verify_release.py --write-evidence
.venv\Scripts\python.exe scripts\check_doc_api_paths.py
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m pip check
```

현재 기준 기대값은 계산 API 509개, 표준 절 861개, current local 전체 테스트 11,848개 통과(3개 건너뜀)이다. Nurion receipt는 64개 shard와 16,000개 input-matrix 결과를 별도로 보존한다.

Nurion 제출은 기본적으로 효율 프로파일(0–9 specialized shard)이다:
`python scripts/nurion_parallel_submit.py --profile efficient`. 중복 회귀와
16,000-case matrix를 포함하는 64-shard 실행은 명시적인
`--profile exhaustive`에서만 수행한다. `docs/completion-matrix.json`은
canonical exhaustive와 efficient regression을 별도 요구사항으로 추적한다.

소스 checkout에서도 `python scripts/nurion_input_matrix.py --shard-index 0 --shard-count 32 --cases-per-shard 500 --seed 581`와 `python scripts/digital_twin_stress.py`를 별도 설치 없이 실행할 수 있다. Nurion payload에서는 staged wheel이 동일한 계산 경계를 제공한다.
`coverage_summary()`의 `validation_by_domain` 합계는 계산 API 509개,
`scope_status_counts` 합계는 표준 절 861개와 일치해야 한다. `verify_release.py`가
이 두 총계 불변조건을 자동 검사한다.
`standard.documentary_coverage()`와 `release-evidence.json.documentary_coverage`는
메타데이터로 추출된 heading 6개, supporting-text 검토 170개, 원문 상태
`not_implemented` 76개를 구분한다.
`scripts/check_unimplemented_bodies.py`는 계산 함수의 우발적인 `pass`/빈 본문을
release gate에서 차단하며, 상속 전용 입력 모델 두 곳만 명시적으로 허용한다.

디지털 트윈 batch 예제는 `.\\.venv\\Scripts\\python.exe examples\\digital_twin_hpc_batch.py`로 실행한다. 예제 자체가 source checkout의 `src` 경로를 bootstrap한다.
`audit_coverage()['ok']`가 `True`여야 하며, 이는 내부 inventory 무결성만 증명하고
API 581 적합성 인증이나 독립 공학 검증을 의미하지 않는다.
`check_doc_api_paths.py`는 자동 생성 `MODULE_CATALOG.md`까지 포함해
구체적인 public import 경로 685개를 확인한다.
`--write-evidence`는 계산·절·Schema·coverage 파일의 SHA-256을
`docs/release-evidence.json`에 고정해 배포 검토 자료로 남긴다. 저장소에
`API-581-2016.pdf`가 있으면 원문 PDF의 파일 크기와 SHA-256도 함께 기록한다.
원문 PDF가 존재할 때는 그 SHA-256이 packaged coverage inventory의
`source_sha256`와 일치하지 않으면 명령이 실패한다.
명령 출력의 `source_hash_matches_coverage`도 같은 결과를 직접 표시한다.
`verify_release.py`는 체크인된 `docs/NATIVE_ENGINE_EVIDENCE.json`도 검사해
지정된 SLABx/LH2/CoolProp 버전과 9개 native 검증 실행의 통과 상태를 고정한다.
또한 `docs/COMPLETION_AUDIT.md` 존재 여부와 hash를 release evidence에 기록한다.

보존된 native 환경에서 전체 선택 엔진 suite를 재실행하려면 다음처럼 실행한다.

```powershell
tmp\dispersion-native\Scripts\python.exe scripts\verify_native_suite.py `
  --python tmp\dispersion-native\Scripts\python.exe `
  --write-report tmp\native-suite-run.json
```

suite는 9개 native 검증 스크립트를 순서대로 실행하고, 각 stdout/stderr와 종료 상태를
하나의 재현 보고서에 보존한다. 선택 의존성이 없는 기본 CI에서는 실행하지 않는다.

## wheel smoke test

```powershell
.venv\Scripts\python.exe -m pip wheel --no-deps --no-build-isolation . --wheel-dir dist
.venv\Scripts\python.exe -m pip install --no-index --no-deps --find-links dist --target tmp\package-smoke api581-engine
```

wheel 대상 환경에서 `import api581`, `coverage_summary()`,
`calculation_evidence()`, `audit_coverage()`를 다시 호출해 source 환경과 같은 결과인지 확인한다.
디지털 트윈 배치 계약은 설치된 wheel에서 `build_batch_plan()`의
`api581-batch-1` JSON manifest와 shard 순서를 추가로 확인한다.
wheel smoke에서는 packaged reference-fixture manifest(19개)와 `risk/assessment`
four-hole fixture도 재실행해, 배포 후 통합 위험평가 산술 경계를 확인한다.

## 대표 실행 경계

```powershell
.venv\Scripts\python.exe examples\prd_to_risk.py
.venv\Scripts\python.exe examples\digital_twin_risk_assessment.py
```

SLABx/slabx-lh2와 CoolProp 예제는 선택 의존성 및 외부 엔진 상태를 먼저
`api581.dispersion.capabilities()`로 확인한다. typed native probe는
`api581.api.dispersion.native_engine_capabilities()`를 사용한다. 엔진이 없을 때 fallback physics를
사용하지 않으며, 결과를 성공으로 간주하지 않는다.
