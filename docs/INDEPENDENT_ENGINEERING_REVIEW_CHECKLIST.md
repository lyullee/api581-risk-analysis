# 독립 공학 검토·인증 체크리스트

이 문서는 software evidence와 API-RP-581 공식 적합성/독립 공학 인증을
분리하기 위한 외부 검토용 checklist다. 항목별로 계산 API·입력 원자료·
검토자 서명·승인일·독립 재계산 결과를 기록해야 한다.

## 공통 증거

- [ ] API-RP-581 판본과 적용 범위 승인
- [ ] 원본 PDF fingerprint 및 license/access 기록
- [ ] 단위계·물성 출처·반올림·보간 정책 승인
- [ ] 각 계산의 입력 범위와 적용 제한 승인
- [ ] 독립 재계산 또는 상용/검증 solver 비교 결과
- [ ] reviewer, organization, date, signature 및 evidence hash

## 계산 분야별 검토

- [ ] 빈도·장치별 failure frequency 및 Weibull 입력 근거
- [ ] 누출공 크기·누출률·재고량·격리시간
- [ ] flash/phase partition 및 source-term mass closure
- [ ] jet/pool/fireball/VCE 열·과압 결과
- [ ] 독성 criterion/probit·노출시간·확산 footprint
- [ ] thinning/cracking/CUI/SCC 등 damage mechanism
- [ ] inspection effectiveness 및 probability-of-failure 연결
- [ ] Level 1/Level 2 consequence와 risk aggregation
- [ ] tank bottom/shell inventory·환경·재무 영향
- [ ] portfolio/disjointness 및 currency basis

## Native solver 및 LH2

- [ ] SlabX version, source fingerprint, build provenance
- [ ] SlabX-LH2 version, source fingerprint, build provenance
- [ ] native fixture 입력·출력과 독립 solver 비교
- [ ] LH2 EOS/property source 및 온도·압력 적용 범위
- [ ] premise violation 차단 결과 승인
- [x] buoyant vertical-rise branch의 Briggs effective-source fixture 및 native suite 검증

## 외부 표준 경계

- [x] API 520 capacity sizing typed module/교차 표본 확인
- [ ] API 581과 API 520 간 입력·출력 경계
- [ ] 현장 계측·검사 데이터 품질 및 uncertainty
- [ ] 운영자/asset owner의 적용성 승인

## 현재 상태

현재 저장소는 509개 계산 API, 861개 절 traceability, API 520 engineering utility 10개를 제외한 표준 계산 링크, unreferenced 0,
Nurion PBS 64-shard evidence, 16,000개 입력 매트릭스, 9개 native suite를
제공한다. 상세 산출물과 재현 명령은
`docs/INDEPENDENT_ENGINEERING_REVIEW_PACKET.md`에 고정했다. 위 checklist의
독립 엔지니어 서명·제3자 인증은 본 프로젝트 범위에서 제외했다. 따라서 완료 전에는
공식 API 581 적합성 또는 독립 인증을 주장하지 않는다.
