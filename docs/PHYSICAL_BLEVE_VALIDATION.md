# 물리폭발·BLEVE·Level2 NFNT 검증 기록

제공된 API RP 581 제3판(2016)의 Part3 §5.10, 식3.192–201,
PDF568–572쪽을 기준으로 한다. 식3.192·195 및 NFNT 최대 면적 식은 원본 페이지 렌더링과 대조했다.
Annex3.B C29·C30은 PDF648쪽, 압력·kmol·기체상수 단위는 기호표 PDF576·578쪽을 사용한다.

## 공개 함수와 SI 단위

| Python 함수 | 계산 |
| --- | --- |
| `effects.physical_explosion_tnt` | 증기 공간의 Brode 에너지와 TNT 등가량 |
| `release.bleve_flashed_amount` | 액체 질량·플래시 질량 분율·분자량 → 플래시 kg·kmol |
| `effects.bleve_liquid_tnt` | 플래시 액체의 팽창 에너지와 TNT 등가량 |
| `effects.physical_explosion_consequence` | 파열 증기 폭발의 거리·면적 |
| `effects.bleve_consequence` | 액체/2상 BLEVE의 거리·면적 |
| `consequence.level2_nfnt_case` | 한 누출공의 최대 면적·비점화 확률 적용 |
| `consequence.level2_nfnt_summary` | 네 누출공의 GFF 가중 평균 |

모두 `api581.api` 아래 타입이 지정된 함수·입력 모델·결과 모델을 사용한다.
에너지·TNT 질량·피해거리·면적은 각각 J,kg,m,m²다. HTTP 실행 경로는 없다.

## 증기 공간의 에너지

식3.192는 `W_TNT=C29*V*(Ps-Patm)/(k-1)`이다.
원문 압력은 kPa이며 C29는4.303e-4이다. 공개 API의 압력은 Pa이므로
다음과 같이 계산한다.

`E_vapor=V_m3*(Ps_Pa-Patm_Pa)/(k-1)`

`W_vapor=4.303e-7*E_vapor`

압력은 모두 절대압이다. Ps<Patm은 거부하고 같으면 에너지0이다.
비열비는1보다 커야 한다. 체적은 저장 **증기 공간**의 체적이며 액체를 포함한 전체 용기 체적을 넣지 않는다.
STEP10.2의 식3.204 참조는 잘못 연결되어 있어 실제 물리폭발 에너지 식3.192를 따른다.
계수를 현대 TNT 연소열 값으로 조용히 대체하지 않는다.

## 액체 BLEVE의 에너지

기호표의 `nv`는 kg-mol, 즉 **kmol**이다. R은 인쇄된8314J/(kmol·K)를 사용한다.
분자량은 kg/kmol이다. 따라서 플래시 질량 kg을 분자량으로 나눈 값이 kmol이 된다.
mol을 kmol로 잘못 입력하면 에너지가1000배 달라진다.

`E_liquid=nv_kmol*8314*Ts_K*ln(Ps_abs/Patm_abs)`

`W_liquid=9.76e-8*E_liquid`

압력 비는 단위가 소거되며 자연로그를 사용한다. 작은 양의 과압에서는 `log1p`로
유효숫자를 보존하고 극단적인 압력 비에서는 로그의 차를 사용해 비 자체의 오버플로를 피한다.
Ts는 저장 온도다. 플래시 분율은 사용자가 공급하며 이 함수는 EOS/과열 액체 플래시를 풀지 않는다.
nv는 기존 증기 공간의 몰수를 포함하지 않는다.

두 상이 공존할 때에는 원문 STEP10.3에 따라 별도로 계산한
`W_total=W_liquid+W_vapor`를 폭압 곡선에 전달한다.
C29와 C30이 다르므로 두 에너지를 먼저 합쳐 동일 계수를 곱하지 않는다.
피해 면적을 더하는 것도 아니다. 액체 부분과 증기 부분의 에너지·등가량을 출력에 따로 남긴다.

## 파열·거리·확률

폭압은 기존 `blast.py`의 구간 검사와 TNT 곡선을 재사용한다.
`fit_domain`은 계산 구간과 공학 근거가 필수이며 유효성의 실험 검증을 대신하지 않는다.
설비 기준은34,500Pa, 인체 기본값은 STEP10.2·10.3의 probit5=건물 붕괴 확률50%이다.
다른 기준은 명시적으로 입력할 수 있다. 이 확률은 직접 사망률을 뜻하지 않는다.

`hole`이 `rupture`일 때만 사건 TNT 등가량과 면적을 발생시킨다.
다른 누출공은 `not_rupture`, 사건 등가량0, 거리·면적0을 반환한다.
이때 용기의 잠재 저장 에너지와 `potential_tnt_equivalent_mass_kg`는 유지한다.
잠재 에너지가 물리적으로 사라진 것처럼 표시하지 않기 위해
`event_tnt_equivalent_mass_kg`와 구분했다.
파열이지만 저장 에너지가0이면 `no_explosion`이다.

폭압 결과는 **사건 조건부 면적**이다. 여기서 비점화 확률을 미리 곱하지 않는다.
BLEVE 뒤의 파이어볼 열복사·연소 에너지·점화 여부는 별도 API의 범위다.

## NFNT 최대 선택과 네 누출공 평균

식3.198–199를 그대로 사용한다.

`CA_equipment=p_nonignition*max(CA_physical,CA_bleve)`

`CA_personnel=p_nonignition*max(CA_physical,CA_bleve,CA_steam_chemical)`

입력은 가중 전 사건 면적이다. 최대 선택 후 비점화 확률을 한 번 곱한다.
비파열 누출공에 물리폭발/BLEVE의 양수 면적을 입력하면 거부한다.
증기/화학 누출 면적은 §5.10.4에 따라 기존 Level1 함수를 사용한다.
NFNT 집계는 비점화 확률 자체를 추정하지 않는다.

식3.200–201은 위 결과의 GFF 가중 평균이다. `small,medium,large,rupture`가 각각 하나씩 필요하다.
빈도0인 누출공도 명시하며 전체 빈도는 양수여야 한다.
DF/Fms 보정 실패빈도를 GFF 대신 넣지 않는다.
예제의 연간 면적 위험은 별도로 각 누출공의 보정 빈도×조건부 면적을 합산한다.
재정피해를 평가하지 않은 예제이므로 재정 위험도0을 실제 무위험으로 해석하면 안 된다.

## 검증과 남은 범위

`tests/test_physical_explosion.py`는 Decimal 원문 kPa 직접 계산·고정밀 자연로그,
kmol 변환·작은 과압·극단 압력 비·증기/액체 합산·질량 스케일링·파열 게이트,
최대 선택·비점화 중복 가중 방지·4공 GFF 평균·영 에너지·수치 언더플로를 확인한다.

`examples/bleve_nfnt.py`는 가정한 고온수 용기의 플래시분에서 시작해
액체/증기 BLEVE, 물리폭발, 증기 누출, NFNT, 연간 면적 위험까지 실행한다.
플래시 분율·유량·방출량·DF는 예시 입력이며 계산으로 추정된 값이 아니다.

실제 유체 EOS·플래시 예측·과열/가압 적용성, 비이상 열역학·파편·반사압·구조 손상,
폭압 곡선 유효범위와 LH2 실험 검증은 미완료다.
소프트웨어 테스트 통과를 전체 API581 구현 완료나 공학 인증으로 주장하지 않는다.
