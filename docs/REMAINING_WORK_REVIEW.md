# 잔여 범위 검토 큐

`python scripts/build_remaining_work.py`로 [전체 검토 큐](remaining-work.json)를 생성한다.
861개 원문 목차 항목을 모두 유지하며 기존 API 연결의 유효성·ID 중복·항목 수를 확인한다.
입력 coverage 파일 SHA-256을 기록하여 보고서의 기준 상태를 식별한다.

현재509개 API·861개 목차 항목 기준 상태는 부분 구현785항목·미구현76항목이다. 기술 범위 절은 기존 계산 API와 연결됐으며, 남은 미구현은 지원 문서·참고문헌·표현 항목이다. Scope·Overview·Description of Damage도 적용 API의 evidence로 연결했고, 순수 참고문헌·nomenclature·정의 항목은 계산으로 오인하지 않고 supporting-text 상태를 유지한다. Part 1 §7·§8의 누락 목차 페이지와 PRD·튜브 번들 overview/table/figure 근거도 inventory에 포함했다.
현재 제목 기반 검토 분류는 기술 범위 검토 부분685/미구현0, 지원 문서 검토 부분100/미구현76이다.
현재 `not_implemented` 76개를 원문 제목별로 재검토한 결과 모두 `supporting_text_review`이며, References/Normative/Informative, Nomenclature, Scope/Overview, Description of Damage 같은 서술·근거 항목이다. 이 목록에서 추가적인 수치 계산 API 후보는 확인되지 않았고, 계산 부재와 문서 근거 미완료를 계속 별도로 추적한다.
이전 보고서의 351/270·54/118 수치는 목차 parser가 Part 1 §7·§8을 누락하던 과거 checkpoint이며 현재 기준값으로 사용하지 않는다.
이는 제목 기반 작업 정리이며 어느 항목도 목표에서 제외하지 않는다.
기술 범위 분류에도 표·그림·상위 제목이 있어 계산 개수나 소요시간으로 환산할 수 없다.

점검에서 드러난 제한: `not_implemented`가 실제 계산 부재와 항상 같지는 않다. 지원 절의 `next_evidence_needed`는 이제 references/normative, 용어·약어, 적용범위, 손상 메커니즘 유형별로 구체화되어 검토 큐에서 바로 사용할 수 있다.
예를 들어 Part2 §4의 상위 THINNING 제목은 하위 절과 감육 API 근거를 집계하여 부분 구현으로 보강했다.
따라서 후속 검토는 원문 요구사항, 직접/하위 절 API 연결, 검증 근거를 함께 대조해야 한다.
상위 제목을 새 계산으로 중복 구현하거나 하위 함수가 있다는 이유만으로 완료로 바꾸지 않는다.
JSON의 각 항목에 이 검토를 위한 다음 증거 요구를 기록했다.

이 보고서는 규격 구현률·완료율·공학 인증을 제공하지 않는다.
상위 절에는 assigned_calculation_ids와 descendant_calculation_ids를 분리하고,
descendant_evidence_clause_ids에 기존 연결이 있던 하위 절만 기록한다.
형제 절·다른 Part의 같은 번호는 포함하지 않는다. 다섯 회귀 테스트로 이 경계를 검증했다.
반복 집계에서도 상속 근거가 직접 연결로 승격되지 않으며, 하위 근거를 제거하면 상위의 오래된 주장도 제거한다.
부분355/미구현438에서 부분385/미구현408로 바뀐 것은 연결 근거 보강이며 새 계산30개 구현을 뜻하지 않는다.
재빌드 wheel의 별도 설치 후479개 타입·스키마·패키지 구현 현황·예제 검증도 통과했다.
