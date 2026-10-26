# SSC 선별

`api581.api.damage.ssc_screening(SscScreeningInput(...))`은 Part2 §8.3(PDF184쪽)을 구현한다.
입력은 material(carbon_steel/low_alloy_steel/other_material), water_present,
h2s_present, exposure_basis다. 탄소강/저합금강에 물과H₂S가 모두 있으면
농도에 관계없이 SSC 감수성 평가 대상으로 반환한다.

본문의1ppm 사례를 선별 최저 농도로 사용하지 않는다.
경도·PWHT·온도·pH도 이 선별의 제외 기준이 아니다.
노출 여부는 국부·업셋 조건을 포함해 호출자가 확인한다.
선별 탈락은 이 절차 범위 밖이며 전체DF0·재질 면역 또는FFS 합격을 뜻하지 않는다.

기존 `wet_h2s_environment`는 Table8.2 환경 심각도와 시안화물 상향 필요 여부를 제공한다.
기존 `ssc_susceptibility`는 Table8.3의 실측 Brinnell 경도/PWHT 판정이다.
다음 두 API가 시안화물 후속 감수성 상향과 선별→환경→경도→DF 통합을 제공한다.
표의pH 빈 구간과1000ppm 공유 경계는 기존 명시적 오류를 유지한다.

재현: `python -m pytest tests/test_ssc_screening.py -q`.
재질3종×물2상태×H₂S2상태의12조합과 비어 있는 노출 근거 거부를 검증했다.

## 환경·경도·시안화물·DF 연결

`damage.ssc_qualified_susceptibility(SscQualifiedSusceptibilityInput(...))`는
 environment(water_ph,h2s_in_water_ppm,cyanides_present), measured_brinnell_hardness,
pwht, service_basis를 받는다. Table8.2 환경 등급을 Table8.3에 적용한 후,
pH>8.3,H₂S>1000ppm,시안화물 존재 조건에서 감수성을none→low→medium→high 한 단계 올린다.
high에서 상한을 유지하며 환경 심각도는 바꾸지 않는다.
출력은 환경 등급,보정 전후 감수성과 시안화물 보정 여부를 구분한다.

`damage.ssc_qualified_assessment(SscQualifiedAssessmentInput(...))`는
screening,service(위 입력),confirmed_cracking,unrepaired_cracks,
years_since_qualifying_inspection,inspections(a/b/c/d),inspection_basis를 받는다.
확인 균열은최종high를 강제하고 미보수 균열은FFS 오류를 우선 반환한다.
선별 탈락은오류이며0DF를 만들지 않는다.
실측 Brinnell·열처리·수중 화학종·SSC 전용 검사 기간과 커버리지는 자격 입력이다.

재현: `python -m pytest tests/test_ssc_qualified.py -q`.
16개 사례에서none→low를 포함한 보정/상한,조건 경계,pH 빈 구간/1000ppm 중첩,
SVI·기본DF·나이승수 및 균열/FFS/선별 연결을 검증했다.
수중pH8.5/H₂S2000ppm,시안화물,PWHT,실측220HB 예제는
moderate 환경·보정 전none·보정 후low,SVI1,검사1A 기본DF1을 얻는다.
이 구현이 실제 화학종·시안화물 효과의 현장 적합성이나전체 손상을 검증하지는 않는다.

실행 예제: `python examples/ssc_qualified_assessment.py`.
실측237HB/비PWHT/시안화물 사례에서moderate 환경→medium→high→SVI100,
검사1A/2년의DF약10.71773을 얻는다. 별도 설치 wheel에서도 이 예제를 실행한다.
추가 검증은200/237HB의 정확한 경계와 인접 부동소수점 값,
독립 환경/경도/SSC 호출과 통합DF의 일치를 확인한다.

## HIC/SOHIC-H₂S 별도 선별

`damage.hic_h2s_screening(HicH2sScreeningInput(...))`는 같은 재질/물/H₂S/근거 입력으로
Part2 §9.3(PDF189쪽)을 평가한다. 반환값은 evaluate_hic_sohic_h2s와screening_reason이다.
원문의 선별 조건은SSC와 같지만 후속 감수성·황 함량·제품 형태·모니터링 모델은 별개다.
저합금강도 선별 대상이지만 Table9.3 탄소강 표를 자동으로 적용할 수 있다고 주장하지 않는다.
낮은 황 함량·seamless 제품·PWHT만으로 선별 제외하지 않는다.
기존 HIC/SOHIC 감수성·DF 함수와의 자격 있는 전체 연결은 후속 작업이다.
재현: `python -m pytest tests/test_hic_h2s_screening.py -q`의13개 조건/근거 검증.

## HIC/SOHIC-H₂S 자격 감수성과 DF 통합

`damage.hic_h2s_qualified_susceptibility`는 environment,steel_sulfur_weight_percent,
product_form(plate_or_welded/seamless_or_extruded_pipe),pwht,confirmed_cracking,service_basis를 받는다.
황 함량은 질량분율이 아닌wt%다. 정확히0.01wt%는저황 분기다.
Table9.2 환경→Table9.3 재질→시안화물 감수성1단계 상향을 적용한다.
확인 균열은 §9.6.4 STEP1 환경high 및 §9.5 최종 감수성high를 적용하며 원래 환경은 진단값으로 유지한다.

`damage.hic_h2s_qualified_assessment`는 screening,service,known_blisters_or_cracks,
ffs_disposition,선택적ffs_basis,years_since_qualifying_inspection,inspections(a/b/c/d),
monitoring(none/process_variables/hydrogen_probes/both),inspection_monitoring_basis를 받는다.
알려진 손상은 repaired/qualified_ffs_basis 처분과근거를 요구하고 not_required이면FFS 오류다.
확인 균열은 알려진 손상으로도 명시해야 한다. 이API가FFS를 수행하거나 처분 적합성을 인증하지 않는다.
통합은 탄소강만 지원하며 저합금강의 Table9.3 적용은 자동 허용하지 않는다.
모니터링 계수1/2/2/4를한 번 적용한다. 경험 기반 대체계수는 아래의 명시 경로로 선택할 수 있다.

재현: `python -m pytest tests/test_hic_qualified.py -q`.
황 경계,시안화물,확인 균열환경/최종high,모니터링4조건,FFS,저합금강 거부 및원문 빈구간을 검증했다.

`hic_h2s_monitoring_selection`은 monitoring과 선택적experience_factor/experience_basis를 받는다.
Table9.5 또는 양의 유한 경험계수 하나를 선택하고 table_monitoring_factor와monitoring_factor_source를 구분한다.
기본표와 경험계수를 곱하지 않는다. 활성 모니터링과 비어 있지 않은 근거가 필요하다.
원문은 대체계수의 숫자 범위를 주지 않으므로 상하한을 발명하지 않는다.
같은 두 선택 필드는hic_h2s_qualified_assessment에서도 사용할 수 있다.
