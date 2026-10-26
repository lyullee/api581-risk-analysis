# PyPI 릴리스 절차

이 프로젝트는 `.github/workflows/publish.yml`에서 PyPI Trusted Publishing을 사용한다.
로컬에 PyPI token을 저장하거나 `twine upload`를 직접 실행하지 않는다.

## 최초 1회 계정 설정

1. PyPI에 `api581-engine` 프로젝트를 생성하거나, 프로젝트가 이미 존재하면 관리자 권한을 확인한다.
2. PyPI 프로젝트의 Trusted Publisher에 GitHub repository, workflow 파일
   `.github/workflows/publish.yml`, GitHub environment(사용하는 경우)를 등록한다.
3. GitHub Actions가 `id-token: write` 권한을 사용할 수 있는지 확인한다.
4. Release를 게시하기 전에 GitHub Actions의 `verify.yml`이 성공했는지 확인한다.

## 릴리스

1. `pyproject.toml`의 `project.version`을 변경한다.
2. 변경된 버전으로 `python -m build`와 `python -m twine check dist/*`를 실행한다.
3. `python scripts/verify_release.py --write-evidence`와 전체 테스트를 실행한다.
4. `v<version>` 형식의 Git tag와 GitHub Release를 만든다. 예: `v0.1.0`.
5. Release를 `published`로 전환하면 workflow가 tag와 project version을 비교한 뒤 wheel/sdist를 PyPI에 게시한다.

태그 버전이 `pyproject.toml`과 다르면 workflow가 업로드 전에 실패한다. API 581
계산의 독립 공학 검증 상태와 supporting-text 잔여 범위는 릴리스와 별도로 검토해야 한다.
