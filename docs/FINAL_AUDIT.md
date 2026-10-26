# 독립 실행 최종 audit

전체 release gate와 회귀 테스트를 하나의 JSON 보고서로 재현하려면 저장소 루트에서
다음을 실행한다.

```powershell
python scripts/final_audit.py
```

기본 출력은 `tmp/final-audit-latest.json`이며, release 후보에는 이 보고서의 hash가
manifest evidence로 고정된다. `--skip-tests`는 구조 gate만 확인할 때만 사용하고,
배포 후보 검증에서는 full pytest를 포함한 기본 실행을 사용한다.

manifest가 최종 보고서 hash를 고정하므로 provenance 검증은 보고서 생성 후 별도로
실행한다. 배포 순서는 `final_audit.py` → `build_release_manifest.py` →
`verify_provenance.py`이다.
