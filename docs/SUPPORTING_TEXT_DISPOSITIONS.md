# Supporting-text disposition ledger

`supporting-text-review.json`의 76개 항목은 계산 API 누락이 아니라 API-RP-581의
참조·용어·범위·damage-description 헤더입니다. 각 항목은 다음 처분 정책으로
추적합니다.

| 분류 | 처분 | 증적 경계 |
|---|---|---|
| `metadata_reference_review` (27) | 표준 메타데이터의 references로 보존 | `src/api581/data/standard-metadata.json` |
| `metadata_terminology_review` (28) | definitions/acronyms 메타데이터로 보존 | `src/api581/data/standard-metadata.json` |
| `workflow_scope_review` (11) | catalog scope 및 통합 workflow 경계로 보존 | `src/api581/catalog.py`, `docs/IMPLEMENTATION_ROADMAP.md` |
| `engineering_damage_review` (10) | 공개 worked-example 데이터와 해당 Annex 2.B mechanism API의 qualification/FFS 경계로 처분 | `docs/engineering-damage-review-draft.json`, `src/api581/data/coverage.json` |

이 ledger는 해당 헤더를 임의의 계산식으로 변환하지 않는다. 따라서 supporting-text
queue의 76개 원문 disposition 수치는 보존되며, public-data review receipt에서
66개 machine-reviewed와 10개 public-data reviewed로 구분한다. 외부 평가·독립
서명은 프로젝트 범위에서 제외한다. 계산 API 구현·직접 테스트 공백과는 별도 지표다.
