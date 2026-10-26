# 독립 Python 계산 API 목록

자동 생성: `scripts/export_contracts.py`.
입력 모델을 생성해 함수에 전달한다. 반환값은 `CalculationResult[Output]`이며 `result.outputs.<필드>`로 계산값을 읽는다.

현재 509개. 함수 개수는 API 581 전체 구현률을 뜻하지 않는다.

## `api581.api.frequency.generic`

Component generic failure frequencies

계산 ID: `frequency/generic`

출처: Part 2 Table 3.1; PDF p147

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |

출력: `by_hole_per_year`, `total_per_year`

적용 범위: Non-tank lookup. Tank rows with differing printed/summed totals are exposed separately by tank/generic-frequency using eq3.208. HEXTUBE is not a 2016 table entry.

## `api581.api.frequency.management_factor`

Management systems factor

계산 ID: `frequency/management-factor`

출처: Part 2 §3.5.4 eqs (2.9)-(2.10); PDF p145

| 입력 | 필수 | 타입 |
|---|---|---|
| `score` | 예 | `<class 'float'>` |

출력: `score_percent`, `management_factor`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.frequency.adjusted`

Damage-adjusted annual failure frequency

계산 ID: `frequency/adjusted`

출처: Part 1 eq (1.1); Part 2 eq (2.1)

| 입력 | 필수 | 타입 |
|---|---|---|
| `generic_frequency_per_year` | 예 | `<class 'float'>` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `management_factor` | 예 | `<class 'float'>` |

출력: `annual_failure_frequency`, `unit`

적용 범위: DF is supplied by caller; this endpoint does not assess damage applicability.

## `api581.api.frequency.pof_method_selection`

Probability-of-failure methodology selection

계산 ID: `frequency/pof-method-selection`

출처: Part 2 §3.2; PDF p142

| 입력 | 필수 | 타입 |
|---|---|---|
| `method` | 예 | `typing.Literal['structural_reliability', 'statistical_generic_data', 'expert_judgment', 'combined']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `uncertainty_quantified` | 예 | `<class 'bool'>` |

출력: `method`, `qualification_basis`, `uncertainty_quantified`, `numeric_pof_route`

적용 범위: Records the API 581 method route and qualification evidence; it does not calculate a structural reliability probability, fit a statistical distribution, or convert expert judgment into a numeric POF. Numeric Level 1 POF remains frequency/adjusted using GFF×DF×FMS.

## `api581.api.damage.combine`

Governing and total damage factors

계산 ID: `damage/combine`

출처: Part 2 §3.4.2 eqs (2.2)-(2.8); PDF pp142-143

| 입력 | 필수 | 타입 |
|---|---|---|
| `thinning` | 예 | `<class 'float'>` |
| `lining` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `external` | 예 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `scc` | 예 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `htha` | 예 | `<class 'float'>` |
| `fatigue` | 예 | `<class 'float'>` |
| `brittle_fracture` | 예 | `<class 'float'>` |
| `temper_embrittlement` | 예 | `<class 'float'>` |
| `embrittlement_885f` | 예 | `<class 'float'>` |
| `sigma_embrittlement` | 예 | `<class 'float'>` |
| `thinning_external_distribution` | 예 | `typing.Literal['local', 'general']` |

출력: `governing_thinning`, `governing_external`, `governing_scc`, `governing_brittle`, `total_damage_factor`

적용 범위: Caller must identify applicable mechanisms; empty lists mean explicitly no applicable mechanism.

## `api581.api.inspection.equivalent`

Equivalent inspection counts

계산 ID: `inspection/equivalent`

출처: Part 2 §3.4.3; PDF p143

| 입력 | 필수 | 타입 |
|---|---|---|
| `mechanism` | 예 | `typing.Literal['scc', 'external_clscc', 'cui_clscc', 'htha']` |
| `a` | 예 | `<class 'int'>` |
| `b` | 예 | `<class 'int'>` |
| `c` | 예 | `<class 'int'>` |
| `d` | 예 | `<class 'int'>` |

출력: `a`, `b`, `c`, `d`

적용 범위: Not applicable to thinning or external corrosion; E inspections cannot be upgraded.

## `api581.api.inspection.effectiveness_summary`

Combine inspection effectiveness history into highest category and equivalent counts

계산 ID: `inspection/effectiveness-summary`

출처: Part 2 §3.4.3; Part 2 Annex C §2.C.2; PDF pp143,443-445

| 입력 | 필수 | 타입 |
|---|---|---|
| `mechanism` | 예 | `typing.Literal['scc', 'external_clscc', 'cui_clscc', 'htha']` |
| `categories` | 예 | `list[typing.Literal['A', 'B', 'C', 'D', 'E']]` |

출력: `mechanism`, `highest_effectiveness_category`, `inspection_count`, `creditable_inspection_count`, `counts`, `equivalent_counts`, `e_inspection_count`, `qualification_status`

적용 범위: Applies the printed A-D equivalence rule used for SCC-family mechanisms: two lower-category inspections promote one step; E inspections never receive credit. It does not assess whether the individual inspection method satisfies an Annex C table. Categories must already be qualified by a mechanism-specific inspection API or owner-user review. No date, coverage, age escalation or inspection effectiveness inference is performed here.

## `api581.api.reliability.weibull`

Two-parameter Weibull reliability

계산 ID: `reliability/weibull`

출처: Part 1 eq (1.2), §8.3.2 eq (1.56)

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `characteristic_life_years` | 예 | `<class 'float'>` |
| `age_years` | 예 | `<class 'float'>` |

출력: `cumulative_failure_probability`, `survival_probability`, `hazard_per_year`, `hazard_singular_at_origin`

적용 범위: User-supplied parameters only; PRD environmental and inspection adjustments not included.

## `api581.api.reliability.weibull_quantile`

Time to a Weibull failure probability

계산 ID: `reliability/weibull-quantile`

출처: Part 1 §8.3.2 eq (1.57)

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `characteristic_life_years` | 예 | `<class 'float'>` |
| `probability` | 예 | `<class 'float'>` |

출력: `age_years`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.reliability.weibull_from_mttf`

Convert mean life to Weibull characteristic life

계산 ID: `reliability/weibull-from-mttf`

출처: Part 1 §8.3.4.2

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `mean_life_years` | 예 | `<class 'float'>` |

출력: `characteristic_life_years`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.reliability.poisson_probability`

Constant-frequency period probability

계산 ID: `reliability/poisson-probability`

출처: Part 1 §4.1 Probability of Failure; Part 1 §4.1.2 Generic Failure Frequency Method

| 입력 | 필수 | 타입 |
|---|---|---|
| `annual_failure_frequency` | 예 | `<class 'float'>` |
| `duration_years` | 예 | `<class 'float'>` |

출력: `period_failure_probability`

적용 범위: Assumes a constant-rate Poisson process; not the GFF frequency itself.

## `api581.api.release.hole_size_selection`

Release hole class and representative diameter

계산 ID: `release/hole-size-selection`

출처: Part 3 §4.2, Table 4.4/Table 4.4M; PDF p518

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole_diameter_m` | 예 | `<class 'float'>` |
| `component_diameter_m` | 예 | `<class 'float'>` |
| `diameter_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `selected_hole`, `representative_diameter_m`, `lower_bound_m`, `upper_bound_m`, `diameter_basis`, `source_table`

적용 범위: The measured opening is supplied in metres; diameter_basis selects the printed SI millimetre or US inch boundaries. Exact upper boundaries belong to the lower class. Rupture representative diameter is min(component diameter, 406 mm/16 in); this class selection does not calculate an orifice rate or infer component geometry.

## `api581.api.release.detection_isolation_rating`

Table 4.5 detection and isolation system classification

계산 ID: `release/detection-isolation-rating`

출처: Part 3 Table 4.5; PDF p519

| 입력 | 필수 | 타입 |
|---|---|---|
| `detection_type` | 예 | `typing.Literal['process_instrumentation', 'outside_envelope_detector', 'visual_or_marginal']` |
| `isolation_type` | 예 | `typing.Literal['automatic_instrument_or_detector', 'remote_operator', 'manual_valve']` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `detection_rating`, `isolation_rating`, `detection_type`, `isolation_type`, `qualification_basis`

적용 범위: Maps only the printed qualitative descriptions to A/B/C. It does not inspect plant instrumentation, coverage, response time or proof-test data; those remain owner-qualified evidence in qualification_basis.

## `api581.api.release.orifice_area`

Circular release area

계산 ID: `release/orifice-area`

출처: Part 3 eq (3.8)

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |

출력: `area_m2`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.release.viscosity_factor`

Liquid viscosity correction

계산 ID: `release/viscosity-factor`

출처: Part 3 eq (3.4); PDF p485

| 입력 | 필수 | 타입 |
|---|---|---|
| `reynolds_number` | 예 | `<class 'float'>` |

출력: `viscosity_factor`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.release.liquid`

Liquid orifice mass release rate

계산 ID: `release/liquid`

출처: Part 3 §4.3.2 eq (3.3); PDF p485

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |
| `upstream_pressure_pa_abs` | 예 | `<class 'float'>` |
| `downstream_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `density_kg_m3` | 예 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `viscosity_factor` | 기본값/선택 | `<class 'float'>` |

출력: `mass_rate_kg_s`, `area_m2`, `regime`

적용 범위: Steady upstream state; no line friction, flash fraction or pool evaporation calculation.

## `api581.api.release.gas`

Sonic or subsonic ideal-gas release

계산 ID: `release/gas`

출처: Part 3 §4.3.3 eqs (3.5)-(3.7); PDF p486

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |
| `upstream_pressure_pa_abs` | 예 | `<class 'float'>` |
| `downstream_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `temperature_k` | 예 | `<class 'float'>` |
| `molecular_weight_kg_kmol` | 예 | `<class 'float'>` |
| `heat_capacity_ratio` | 예 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |

출력: `mass_rate_kg_s`, `area_m2`, `regime`, `critical_downstream_upstream_ratio`, `transition_pressure_pa_abs`

적용 범위: Ideal gas, constant upstream state; not a two-phase or real-gas near-critical model.

## `api581.api.properties.heat_capacity_ratio`

Ideal-gas specific heat ratio

계산 ID: `properties/heat-capacity-ratio`

출처: Part 3 eq (3.1)

| 입력 | 필수 | 타입 |
|---|---|---|
| `cp_j_mol_k` | 예 | `<class 'float'>` |

출력: `heat_capacity_ratio`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.release.available_inventory`

Maximum available mass

계산 ID: `release/available-inventory`

출처: Part 3 §4.4.2 eqs (3.10)-(3.11); PDF p487

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_mass_kg` | 예 | `<class 'float'>` |
| `inventory_group_mass_kg` | 예 | `<class 'float'>` |
| `release_rate_kg_s` | 예 | `<class 'float'>` |
| `eight_inch_rate_kg_s` | 예 | `<class 'float'>` |

출력: `added_mass_kg`, `available_mass_kg`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.release.type`

Continuous or instantaneous release classification

계산 ID: `release/type`

출처: Part 3 §4.5.2 eq (3.12); PDF p488

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |
| `theoretical_rate_kg_s` | 예 | `<class 'float'>` |
| `available_mass_kg` | 예 | `<class 'float'>` |

출력: `release_type`, `time_to_4536kg_s`

적용 범위: Uses the text's rounded 4536 kg threshold.

## `api581.api.release.magnitude`

Adjusted release rate, duration and mass

계산 ID: `release/magnitude`

출처: Part 3 §4.7 eqs (3.13)-(3.15); PDF p490

| 입력 | 필수 | 타입 |
|---|---|---|
| `theoretical_rate_kg_s` | 예 | `<class 'float'>` |
| `reduction_fraction` | 예 | `<class 'float'>` |
| `available_mass_kg` | 예 | `<class 'float'>` |
| `maximum_duration_s` | 예 | `<class 'float'>` |

출력: `adjusted_rate_kg_s`, `duration_s`, `released_mass_kg`

적용 범위: Detection reduction and maximum duration supplied by caller, not yet selected from Tables 4.6/4.7.

## `api581.api.release.detection_isolation`

Detection/isolation release reduction and maximum leak duration

계산 ID: `release/detection-isolation`

출처: Part 3 §4.6.2-§4.6.6, Tables 4.6/4.7M; PDF pp488-490,520

| 입력 | 필수 | 타입 |
|---|---|---|
| `detection_rating` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation_rating` | 예 | `typing.Literal['A', 'B', 'C']` |
| `hole_size` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `theoretical_rate_kg_s` | 예 | `<class 'float'>` |
| `available_mass_kg` | 예 | `<class 'float'>` |

출력: `release_reduction_fraction`, `adjusted_rate_kg_s`, `maximum_leak_duration_s`, `duration_s`, `released_mass_kg`, `detection_rating`, `isolation_rating`, `hole_size`

적용 범위: Uses the printed SI Table 4.7M hole classes (6.4, 25 and 102 mm). A rupture hole has no maximum duration in Table 4.7M, so its instantaneous released mass is the available mass and duration is null. Ratings are supplied after the qualitative Table 4.5 screening; no detector/isolation hardware classification is inferred.

## `api581.api.release.integrate_profile`

Integrate a piecewise-linear release profile

계산 ID: `release/integrate-profile`

출처: Part 3 §4.7.3 Calculation of Release Rate and Mass; Part 3 §5.7.3 Calculation of Jet Release Rate and Pool Release Rate

| 입력 | 필수 | 타입 |
|---|---|---|
| `points` | 예 | `list[api581.release.TimePoint]` |
| `available_mass_kg` | 예 | `<class 'float'>` |

출력: `released_mass_kg`, `duration_s`

적용 범위: Profile supplied externally; not a vessel blowdown solver. Inventory exceedance is rejected, not clipped.

## `api581.api.properties.mixture_molecular_weight`

Mole-weighted mixture and mass fractions

계산 ID: `properties/mixture-molecular-weight`

출처: Part 3 §4.1.2, §4.9.4; mixture molecular-weight and mass-fraction inputs

| 입력 | 필수 | 타입 |
|---|---|---|
| `components` | 예 | `list[api581.release.MixtureComponent]` |

출력: `molecular_weight_kg_kmol`, `mass_fractions`

적용 범위: Mole fractions and component molecular weights are supplied by the caller; this does not select a representative fluid or perform Level 2 thermodynamic flash.

## `api581.api.effects.jet_fire_power`

Jet fire radiated power

계산 ID: `effects/jet-fire-power`

출처: Part 3 §5.8.3.2 eq (3.152); PDF p554

| 입력 | 필수 | 타입 |
|---|---|---|
| `mass_rate_kg_s` | 예 | `<class 'float'>` |
| `heat_of_combustion_j_kg` | 예 | `<class 'float'>` |
| `radiative_fraction` | 기본값/선택 | `<class 'float'>` |

출력: `radiated_power_w`

적용 범위: SI radiated power; external applicability validation required for LH2.

## `api581.api.effects.jet_fire_flux`

Point-source jet fire received radiation

계산 ID: `effects/jet-fire-flux`

출처: Part 3 eqs (3.153)-(3.154); PDF p554

| 입력 | 필수 | 타입 |
|---|---|---|
| `radiated_power_w` | 예 | `<class 'float'>` |
| `distance_m` | 예 | `<class 'float'>` |
| `atmospheric_transmissivity` | 예 | `<class 'float'>` |

출력: `received_flux_w_m2`

적용 범위: Far-field point source at grade; flame impingement and near field not represented.

## `api581.api.effects.jet_fire_distance`

Jet fire threshold radius and consequence area

계산 ID: `effects/jet-fire-distance`

출처: Part 3 eqs (3.140), (3.152)-(3.156)

| 입력 | 필수 | 타입 |
|---|---|---|
| `radiated_power_w` | 예 | `<class 'float'>` |
| `threshold_w_m2` | 예 | `<class 'float'>` |
| `transmissivity_model` | 예 | `typing.Literal['constant', 'api_water_vapor']` |
| `atmospheric_transmissivity` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `water_partial_pressure_pa` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `threshold_distance_m`, `consequence_area_m2`, `transmissivity_at_distance`

적용 범위: Constant transmissivity is an explicitly supplied approximation; api_water_vapor uses distance-dependent attenuation capped at physical maximum 1. Water-vapor mode uses eq (3.140) exponent -0.09 with C19=1.085 and pressure in kPa; the base-edition table labels C19 dimensions with exponent 0.092, recorded as a source discrepancy. Point source at grade; LH2-specific validation outstanding.

## `api581.api.effects.flash_fire`

Flash fire consequence areas

계산 ID: `effects/flash-fire`

출처: Part 3 §4.8.2.3, §5.8.6

| 입력 | 필수 | 타입 |
|---|---|---|
| `area_within_lfl_m2` | 예 | `<class 'float'>` |

출력: `personnel_area_m2`, `equipment_area_m2`

적용 범위: LFL footprint must come from a validated dispersion model.

## `api581.api.effects.pool_fire_area`

Pool burning area and radius

계산 ID: `effects/pool-fire-area`

출처: Part 3 eqs (3.131)-(3.134); PDF pp550-551

| 입력 | 필수 | 타입 |
|---|---|---|
| `liquid_rate_kg_s` | 예 | `<class 'float'>` |
| `burning_rate_kg_m2_s` | 예 | `<class 'float'>` |
| `available_liquid_mass_kg` | 예 | `<class 'float'>` |
| `density_kg_m3` | 예 | `<class 'float'>` |
| `pool_depth_m` | 기본값/선택 | `<class 'float'>` |
| `site_maximum_area_m2` | 예 | `<class 'float'>` |

출력: `burning_area_m2`, `inventory_limited_area_m2`, `pool_area_m2`, `pool_radius_m`

적용 범위: Pool geometry only; burning rate supplied by caller; surface radiation/view factors not included. Site limit is mandatory.

## `api581.api.consequence.power_law_area`

Level 1 consequence power-law primitive

계산 ID: `consequence/power-law-area`

출처: Part 3 eqs (3.16)-(3.17)

| 입력 | 필수 | 타입 |
|---|---|---|
| `coefficient_a` | 예 | `<class 'float'>` |
| `exponent_b` | 예 | `<class 'float'>` |
| `release_magnitude` | 예 | `<class 'float'>` |
| `magnitude_unit` | 예 | `typing.Literal['kg/s', 'kg']` |
| `coefficient_source` | 예 | `<class 'str'>` |

출력: `area_m2`, `coefficient_source`

적용 범위: Caller-supplied SI coefficients only; does not select reference fluid or perform Type 0 blending. Not a complete Level 1 COF.

## `api581.api.events.leakage_tree`

Single-phase leakage event tree

계산 ID: `events/leakage-tree`

출처: Part 3 §5.8.1.6, Figure 5.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `phase` | 예 | `typing.Literal['vapor', 'liquid']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `ignition_probability` | 예 | `<class 'float'>` |
| `immediate_given_ignition` | 예 | `<class 'float'>` |
| `vce_given_delayed` | 예 | `<class 'float'>` |

출력: `terminal_probabilities`, `probability_sum`

적용 범위: Leakage only, not rupture Figure 5.4; branch probabilities supplied by caller. Two-phase tree deferred.

## `api581.api.effects.toxic_probit`

User-parameterized toxic probit

계산 ID: `effects/toxic-probit`

출처: Part 3 §5.9.2

| 입력 | 필수 | 타입 |
|---|---|---|
| `intercept` | 예 | `<class 'float'>` |
| `slope` | 예 | `<class 'float'>` |
| `concentration_exponent` | 예 | `<class 'float'>` |
| `concentration` | 예 | `<class 'float'>` |
| `exposure_duration` | 예 | `<class 'float'>` |
| `concentration_unit` | 예 | `<class 'str'>` |
| `duration_unit` | 예 | `<class 'str'>` |
| `coefficient_source` | 예 | `<class 'str'>` |

출력: `probit`, `effect_probability`

적용 범위: Coefficient units must match supplied concentration/time. This generic utility uses caller-qualified coefficients; Table4.14 species calculations are separately available through toxic-species-probit.

## `api581.api.effects.pool_burning_rate`

Pool fire surface mass burning rate

계산 ID: `effects/pool-burning-rate`

출처: Part 3 eqs (3.128)-(3.129), Annex 3.B C17; PDF pp550,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `heat_of_combustion_j_kg` | 예 | `<class 'float'>` |
| `latent_heat_j_kg` | 예 | `<class 'float'>` |
| `boiling` | 예 | `<class 'bool'>` |
| `specific_heat_j_kg_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `boiling_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `ambient_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `burning_rate_kg_m2_s`

적용 범위: Empirical pool burning correlation; LH2 applicability not validated. Does not model unignited pool evaporation.

## `api581.api.effects.fireball_geometry`

Fireball diameter, height and duration

계산 ID: `effects/fireball-geometry`

출처: Part 3 eqs (3.158)-(3.161), Annex 3.B C22-C24; PDF pp555,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `flammable_mass_kg` | 예 | `<class 'float'>` |

출력: `diameter_m`, `center_height_m`, `duration_s`

적용 범위: Instantaneous rupture fireball model; no continuous-release fireball. Empirical exponents follow printed 0.333/0.167.

## `api581.api.effects.fireball_radiative_fraction`

Fireball pressure-based radiative fraction

계산 ID: `effects/fireball-radiative-fraction`

출처: Part 3 eq (3.163), Annex 3.B C25; PDF pp555,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `burst_pressure_pa_abs` | 예 | `<class 'float'>` |

출력: `radiative_fraction`

적용 범위: Raw correlation; results above 1 are rejected rather than silently capped. Applicability must be independently established.

## `api581.api.effects.fireball_emissive_power`

Fireball surface emissive power

계산 ID: `effects/fireball-emissive-power`

출처: Part 3 eq (3.162); PDF p555

| 입력 | 필수 | 타입 |
|---|---|---|
| `flammable_mass_kg` | 예 | `<class 'float'>` |
| `heat_of_combustion_j_kg` | 예 | `<class 'float'>` |
| `radiative_fraction` | 예 | `<class 'float'>` |
| `diameter_m` | 예 | `<class 'float'>` |
| `duration_s` | 예 | `<class 'float'>` |

출력: `surface_emissive_power_w_m2`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.effects.vce_tnt_equivalence`

VCE TNT equivalent mass

계산 ID: `effects/vce-tnt-equivalence`

출처: Part 3 eq (3.169); PDF pp557-558

| 입력 | 필수 | 타입 |
|---|---|---|
| `flammable_cloud_mass_kg` | 예 | `<class 'float'>` |
| `combustion_heat_j_kg` | 예 | `<class 'float'>` |
| `explosion_yield` | 예 | `<class 'float'>` |
| `tnt_heat_j_kg` | 예 | `<class 'float'>` |
| `tnt_heat_source` | 예 | `<class 'str'>` |

출력: `tnt_equivalent_mass_kg`

적용 범위: TNT heat is mandatory: original text J/kg and Btu/lb values are inconsistent. Cloud mass definition and yield must be consistent. Blast pressure and distances require separate caller-qualified fit-domain inputs; equivalence alone does not establish blast-curve applicability.

## `api581.api.consequence.expected`

Conditional event-weighted consequence

계산 ID: `consequence/expected`

출처: Part 3 §5.8.7, §5.11

| 입력 | 필수 | 타입 |
|---|---|---|
| `outcomes` | 예 | `list[api581.risk.Outcome]` |
| `currency` | 예 | `<class 'str'>` |

출력: `equipment_area_m2`, `personnel_area_m2`, `financial_consequence`, `currency`

적용 범위: Inputs must be mutually exclusive complete terminal outcomes, already conditional on the same release/weather case.

## `api581.api.risk.aggregate`

Aggregate disjoint release-scenario risks

계산 ID: `risk/aggregate`

출처: Part 1 §4.3.1 eqs (1.6)-(1.8)

| 입력 | 필수 | 타입 |
|---|---|---|
| `scenarios` | 예 | `list[api581.risk.RiskScenario]` |
| `currency` | 예 | `<class 'str'>` |

출력: `annual_failure_frequency`, `equipment_area_risk_m2_per_year`, `personnel_area_risk_m2_per_year`, `area_risk_m2_per_year`, `financial_risk_per_year`, `currency`, `frequency_weighted_equipment_area_m2`, `frequency_weighted_personnel_area_m2`

적용 범위: Scenarios must be disjoint; each consequence is conditional and already event/weather weighted. No individual/societal risk calculation.

## `api581.api.risk.assessment`

Compose GFF, Fms, supplied DF and supplied hole consequences

계산 ID: `risk/assessment`

출처: Part 1 §4.1, §4.3; Part 2 §3.3, §3.5.4

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |
| `management_score` | 예 | `<class 'float'>` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `damage_factor_source` | 예 | `<class 'str'>` |
| `consequences` | 예 | `list[api581.risk.HoleConsequence]` |
| `consequence_source` | 예 | `<class 'str'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `integration_scope`, `management_factor`, `generic_frequencies`, `scenarios`, `risk`

적용 범위: Integration boundary: DF and COF supplied externally; not a complete asset damage/COF assessment. All four holes required.

## `api581.api.risk.assessment_from_damage`

Compose damage mechanisms, GFF, management factor and hole consequences

계산 ID: `risk/assessment-from-damage`

출처: Part 1 §§4.1,4.3; Part 2 §§3.4.2,3.5.4; Part 3 consequence inputs

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |
| `management_score` | 예 | `<class 'float'>` |
| `damage` | 예 | `<class 'api581.pof.GoverningDamage'>` |
| `damage_factor_source` | 예 | `<class 'str'>` |
| `consequences` | 예 | `list[api581.risk.HoleConsequence]` |
| `consequence_source` | 예 | `<class 'str'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `integration_scope`, `management_factor`, `generic_frequencies`, `scenarios`, `risk`, `damage_factor`

적용 범위: Damage mechanism inputs are still owner-qualified outputs from the individual Part 2 APIs. This composition performs the governing/total damage-factor combination and risk weighting; it does not infer applicability, inspection effectiveness, consequence areas or currency assumptions.

## `api581.api.consequence.financial_total`

Sum non-overlapping financial consequence categories

계산 ID: `consequence/financial-total`

출처: Part 3 §4.12

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_repair_cost` | 예 | `<class 'float'>` |
| `surrounding_equipment_cost` | 예 | `<class 'float'>` |
| `business_interruption_cost` | 예 | `<class 'float'>` |
| `injury_cost` | 예 | `<class 'float'>` |
| `environmental_cost` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |

출력: `financial_consequence`, `currency`, `cost_basis_year`

적용 범위: Category costs supplied by caller; repair/downtime/cleanup submodels not yet implemented.

## `api581.api.risk.matrix`

Owner-defined risk matrix classification

계산 ID: `risk/matrix`

출처: Part 1 §4.3.2

| 입력 | 필수 | 타입 |
|---|---|---|
| `frequency_per_year` | 예 | `<class 'float'>` |
| `consequence` | 예 | `<class 'float'>` |
| `frequency_boundaries` | 예 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `consequence_boundaries` | 예 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `risk_cells` | 예 | `list[list[str]]` |
| `policy_id` | 예 | `<class 'str'>` |

출력: `frequency_category`, `consequence_category`, `risk_label`, `policy_id`

적용 범위: No built-in universal acceptance limits; equality is assigned to the higher category.

## `api581.api.planning.target_crossing`

First target crossing on a supplied risk curve

계산 ID: `planning/target-crossing`

출처: Part 1 §4.4

| 입력 | 필수 | 타입 |
|---|---|---|
| `points` | 예 | `list[api581.risk.RiskPoint]` |
| `target` | 예 | `<class 'float'>` |
| `metric` | 예 | `typing.Literal['financial_per_year', 'area_m2_per_year', 'frequency_per_year', 'damage_factor']` |

출력: `status`, `crossing_years`, `horizon_years`

적용 범위: Linear interpolation between supplied points; does not generate DF forecasts or select NDE effectiveness. Unresolved crossings between samples remain possible.

## `api581.api.damage.thinning_wall_loss`

Unclad fractional wall loss

계산 ID: `damage/thinning-wall-loss`

출처: Part 2 eq (2.13)

| 입력 | 필수 | 타입 |
|---|---|---|
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |

출력: `wall_loss_fraction`

적용 범위: No cladding/weld overlay; not AST-bottom equation (2.12).

## `api581.api.damage.flow_stress`

Thinning flow stress

계산 ID: `damage/flow-stress`

출처: Part 2 eq (2.16)

| 입력 | 필수 | 타입 |
|---|---|---|
| `yield_strength_pa` | 예 | `<class 'float'>` |
| `tensile_strength_pa` | 예 | `<class 'float'>` |
| `weld_efficiency` | 예 | `<class 'float'>` |

출력: `flow_stress_pa`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.damage.thinning_strength_ratio`

Internal-pressure thinning strength ratio

계산 ID: `damage/thinning-strength-ratio`

출처: Part 2 eq (2.18); PDF p154

| 입력 | 필수 | 타입 |
|---|---|---|
| `differential_pressure_pa` | 예 | `<class 'float'>` |
| `diameter_m` | 예 | `<class 'float'>` |
| `flow_stress_pa` | 예 | `<class 'float'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `shape` | 예 | `typing.Literal['cylinder', 'sphere', 'head']` |

출력: `strength_ratio`

적용 범위: Internal hoop pressure only; not suitable when external pressure or structural loads govern.

## `api581.api.damage.thinning_prior_selection`

Table4.5 or qualified customized thinning damage-state prior

계산 ID: `damage/thinning-prior-selection`

출처: Part2 §4.5.3; Table4.5; PDF pp150-151,163

| 입력 | 필수 | 타입 |
|---|---|---|
| `confidence` | 기본값/선택 | `typing.Literal['low', 'medium', 'high'] | None` |
| `custom_prior_probabilities` | 기본값/선택 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])]] | None` |
| `custom_prior_basis` | 기본값/선택 | `str | None` |

출력: `prior_probabilities`, `prior_source`, `confidence`, `zero_prior_state_indices`

적용 범위: Exactly one low/medium/high table row or three owner-qualified prior probabilities for damage states1/2/3 (rate factors1/2/4). Source permits customization from actual experience and confidence in thickness measurements; no automatic calibration or general-to-local applicability inference. Custom sum tolerance1e-9 removes only rounding by normalization. A zero prior cannot be revived by subsequent positive-likelihood inspections; no probability floor is invented.

## `api581.api.damage.thinning_posterior`

Bayesian thinning damage-state probabilities

계산 ID: `damage/thinning-posterior`

출처: Part 2 eqs (2.19)-(2.20), Tables 4.5-4.6; PDF pp154,163

| 입력 | 필수 | 타입 |
|---|---|---|
| `confidence` | 기본값/선택 | `typing.Literal['low', 'medium', 'high'] | None` |
| `custom_prior_probabilities` | 기본값/선택 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])]] | None` |
| `custom_prior_basis` | 기본값/선택 | `str | None` |
| `inspections_a` | 기본값/선택 | `<class 'int'>` |
| `inspections_b` | 기본값/선택 | `<class 'int'>` |
| `inspections_c` | 기본값/선택 | `<class 'int'>` |
| `inspections_d` | 기본값/선택 | `<class 'int'>` |

출력: `posterior_probabilities`

적용 범위: Counts must include only inspections eligible in the assessed period; no equivalent-count conversion. Prior is exactly one confidence table row or qualified customized three-state probabilities per section4.5.3. Zero custom prior remains zero; no floor or automatic calibration.

## `api581.api.damage.thinning_base`

Thinning reliability indices and base damage factor

계산 ID: `damage/thinning-base`

출처: Part 2 eqs (2.21)-(2.22); PDF p155

| 입력 | 필수 | 타입 |
|---|---|---|
| `wall_loss_fraction` | 예 | `<class 'float'>` |
| `strength_ratio` | 예 | `<class 'float'>` |
| `posterior` | 예 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])]]` |
| `cov_wall_loss` | 기본값/선택 | `<class 'float'>` |
| `cov_strength` | 기본값/선택 | `<class 'float'>` |
| `cov_pressure` | 기본값/선택 | `<class 'float'>` |

출력: `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`

적용 범위: Excludes AST bottoms; final adjustment factors applied separately.

## `api581.api.damage.thinning_adjust`

Apply thinning damage factor adjustments

계산 ID: `damage/thinning-adjust`

출처: Part 2 eq (2.23); PDF pp155-156

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_damage_factor` | 예 | `<class 'float'>` |
| `injection_point_factor` | 예 | `<class 'float'>` |
| `deadleg_factor` | 예 | `<class 'float'>` |
| `welded_construction_factor` | 예 | `<class 'float'>` |
| `maintenance_factor` | 예 | `<class 'float'>` |
| `settlement_factor` | 예 | `<class 'float'>` |
| `online_monitoring_factor` | 예 | `<class 'float'>` |

출력: `thinning_damage_factor`

적용 범위: Caller supplies applicable factors; does not determine AST eligibility or monitoring category.

## `api581.api.damage.thinning_unclad`

Compose unclad non-AST thinning damage calculation

계산 ID: `damage/thinning-unclad`

출처: Part 2 §4.5.7 eqs (2.13), (2.18)-(2.23)

| 입력 | 필수 | 타입 |
|---|---|---|
| `wall` | 예 | `<class 'api581.thinning.WallLoss'>` |
| `strength` | 예 | `<class 'api581.thinning.StrengthRatio'>` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `injection_point_factor` | 예 | `<class 'float'>` |
| `deadleg_factor` | 예 | `<class 'float'>` |
| `online_monitoring_factor` | 예 | `<class 'float'>` |

출력: `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`

적용 범위: Non-AST, unclad, internal-pressure-governed components only. Flow stress and corrosion rate are caller-supplied. Automatic corrosion mechanism/monitoring selection is not included.

## `api581.api.damage.scc_base`

SCC base damage factor lookup

계산 ID: `damage/scc-base`

출처: Part 2 Table 6.3; PDF p175

| 입력 | 필수 | 타입 |
|---|---|---|
| `severity_index` | 예 | `typing.Literal[0, 1, 10, 50, 100, 500, 1000, 5000]` |
| `inspection_grade` | 예 | `typing.Literal['A', 'B', 'C', 'D', 'E']` |
| `inspection_count` | 예 | `<class 'int'>` |

출력: `base_damage_factor`

적용 범위: Severity and highest equivalent inspection category supplied by caller. Count >6 is not extrapolated. Ambiguous E/500 cell is rejected.

## `api581.api.damage.caustic_severity`

Caustic cracking severity index

계산 ID: `damage/caustic-severity`

출처: Part 2 Table 6.2; PDF p174

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |

출력: `severity_index`

적용 범위: This low-level severity lookup accepts qualified susceptibility; use damage/caustic-screening, damage/caustic-figure-susceptibility or damage/caustic-screened-assessment for the implemented material/exposure and Figure 6.2 routing. It does not infer applicability from chemistry.

## `api581.api.damage.caustic_escalation`

Caustic cracking time escalation

계산 ID: `damage/caustic-escalation`

출처: Part 2 §6.6.3 eq (2.25); PDF p173

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_damage_factor` | 예 | `<class 'float'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |

출력: `damage_factor`

적용 범위: Age must follow qualifying A/B/C inspection or repair criteria; detected unrepaired cracks require a separate FFS evaluation.

## `api581.api.damage.lining_adjust`

Lining condition and monitoring adjustment

계산 ID: `damage/lining-adjust`

출처: Part 2 eq (2.24), Table 5.6; PDF pp167,171

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_damage_factor` | 예 | `<class 'float'>` |
| `condition` | 예 | `typing.Literal['good', 'average', 'poor']` |
| `effective_online_monitoring` | 예 | `<class 'bool'>` |

출력: `condition_factor`, `monitoring_factor`, `lining_damage_factor`

적용 범위: Base DF supplied by caller; lining-type/age Tables 5.4/5.5 not selected automatically.

## `api581.api.level1.mitigation`

Flammable consequence mitigation factor

계산 ID: `level1/mitigation`

출처: Part 3 Table 4.10; PDF p525

| 입력 | 필수 | 타입 |
|---|---|---|
| `system` | 예 | `typing.Literal['inventory_blowdown', 'deluge_and_monitors', 'monitors', 'foam', 'none']` |
| `isolation_class` | 예 | `typing.Literal['A', 'B', 'C']` |

출력: `mitigation_fraction`

적용 범위: Select one applicable measure; no unsupported combination/stacking of credits.

## `api581.api.level1.toxic_source`

Toxic component rate and mass

계산 ID: `level1/toxic-source`

출처: Part 3 eqs (3.61)-(3.62); PDF p497

| 입력 | 필수 | 타입 |
|---|---|---|
| `theoretical_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `toxic_mass_fraction` | 예 | `<class 'float'>` |

출력: `toxic_rate_kg_s`, `toxic_mass_kg`

적용 범위: Use theoretical rate, without flammable detection magnitude reduction. Explicit toxic mitigation, if justified, is a separate input adjustment.

## `api581.api.level1.toxic_duration`

Toxic release exposure duration

계산 ID: `level1/toxic-duration`

출처: Part 3 §4.9.10 eq (3.67)

| 입력 | 필수 | 타입 |
|---|---|---|
| `available_mass_kg` | 예 | `<class 'float'>` |
| `theoretical_rate_kg_s` | 예 | `<class 'float'>` |
| `detection_maximum_duration_s` | 예 | `<class 'float'>` |

출력: `duration_s`

적용 범위: One-hour cap; detection magnitude reduction does not apply to toxic source rate.

## `api581.api.level1.toxic_area`

Ammonia/chlorine toxic consequence area

계산 ID: `level1/toxic-area`

출처: Part 3 eqs (3.65)-(3.66), §4.9.11, Table 4.12M; PDF pp498,526

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['ammonia', 'chlorine']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `toxic_rate_kg_s` | 예 | `<class 'float'>` |
| `toxic_mass_kg` | 예 | `<class 'float'>` |
| `duration_s` | 예 | `<class 'float'>` |
| `nonignition_probability` | 예 | `<class 'float'>` |

출력: `unweighted_personnel_area_m2`, `personnel_area_m2`

적용 범위: Continuous curves support 5-60 minutes only; interpolate areas between duration curves, never extrapolate. Explicit nonignition probability supplied; no IDLH screening or spray credit selection.

## `api581.api.level1.steam_area`

Steam leak personnel consequence area

계산 ID: `level1/steam-area`

출처: Part 3 eqs (3.69)-(3.71),(3.76); Annex 3.B C9,C10; PDF pp502,647

| 입력 | 필수 | 타입 |
|---|---|---|
| `adjusted_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |

출력: `continuous_area_m2`, `instantaneous_area_m2`, `instantaneous_weight`, `personnel_area_m2`, `equipment_area_m2`

적용 범위: Level 1 steam burn correlation; no equipment damage area.

## `api581.api.level1.acid_caustic_area`

Acid/caustic splash personnel consequence

계산 ID: `level1/acid-caustic-area`

출처: Part 3 eqs (3.72)-(3.75); Annex 3.B C4B,C8,C11; PDF pp502,647

| 입력 | 필수 | 타입 |
|---|---|---|
| `adjusted_rate_kg_s` | 예 | `<class 'float'>` |
| `differential_pressure_pa` | 예 | `<class 'float'>` |

출력: `personnel_area_m2`, `equipment_area_m2`, `coefficient_g`, `exponent_h`

적용 범위: Empirical correlation developed at approximately 15,30,60 psig. Reject extrapolation outside 103.4-413.7 kPa differential. Source has inconsistent C4/C4B naming; uses lb/s conversion 2.205.

## `api581.api.consequence.final_area`

Final Level 1 consequence areas

계산 ID: `consequence/final-area`

출처: Part 3 §§4.9.12,4.11 eqs (3.81)-(3.84)

| 입력 | 필수 | 타입 |
|---|---|---|
| `flammable_equipment_area_m2` | 예 | `<class 'float'>` |
| `flammable_personnel_area_m2` | 예 | `<class 'float'>` |
| `toxic_personnel_areas_m2` | 예 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `nfnt_personnel_area_m2` | 예 | `<class 'float'>` |

출력: `equipment_area_m2`, `personnel_area_m2`, `consequence_area_m2`

적용 범위: Inputs must be evaluated on the same basis; multiple toxic species use maximum, not area addition.

## `api581.api.consequence.hole_weighted`

Generic-frequency weighted four-hole consequence

계산 ID: `consequence/hole-weighted`

출처: Part 3 eqs (3.27)-(3.28),(3.68),(3.78),(3.86),(3.88),(3.94)

| 입력 | 필수 | 타입 |
|---|---|---|
| `holes` | 예 | `list[api581.consequences.HoleValue]` |
| `value_unit` | 예 | `<class 'str'>` |

출력: `weighted_value`, `value_unit`

적용 범위: All four holes required; value may be area, repair cost, outage or spill volume. Already conditional consequences; no second event weighting.

## `api581.api.financial.surrounding_damage`

Surrounding equipment damage cost

계산 ID: `financial/surrounding-damage`

출처: Part 3 eq (3.87)

| 입력 | 필수 | 타입 |
|---|---|---|
| `equipment_area_m2` | 예 | `<class 'float'>` |
| `replacement_cost_per_m2` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `cost`, `currency`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.financial.production_loss`

Business interruption cost

계산 ID: `financial/production-loss`

출처: Part 3 eq (3.90)

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_outage_days` | 예 | `<class 'float'>` |
| `surrounding_outage_days` | 예 | `<class 'float'>` |
| `production_cost_per_day` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `cost`, `currency`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.financial.injury`

Potential injury cost

계산 ID: `financial/injury`

출처: Part 3 eq (3.91)

| 입력 | 필수 | 타입 |
|---|---|---|
| `personnel_area_m2` | 예 | `<class 'float'>` |
| `population_density_per_m2` | 예 | `<class 'float'>` |
| `cost_per_injury` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `cost`, `currency`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.financial.spill_cleanup`

Liquid spill remediation volume and cost

계산 ID: `financial/spill-cleanup`

출처: Part 3 eqs (3.93)-(3.94), expressed in m3

| 입력 | 필수 | 타입 |
|---|---|---|
| `released_mass_kg` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |
| `evaporated_fraction` | 예 | `<class 'float'>` |
| `cleanup_cost_per_m3` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `remediation_volume_m3`, `cost`, `currency`

적용 범위: Caller must screen liquid phase, boiling point and ignition eligibility; evaporation fraction supplied. Cost basis is per m3, not per barrel.

## `api581.api.financial.hole_total`

Four-hole financial consequence and annual risk roll-up

계산 ID: `financial/hole-total`

출처: Part 3 §§4.11-4.12; eqs (3.86)-(3.94)

| 입력 | 필수 | 타입 |
|---|---|---|
| `holes` | 예 | `list[api581.consequences.HoleFinancial]` |
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |

출력: `currency`, `cost_basis_year`, `total_generic_frequency_per_year`, `per_hole`, `frequency_weighted_financial_consequence`, `annual_financial_risk`

적용 범위: All five cost categories are caller-qualified on one currency and cost basis year. Per-hole generic frequencies must be disjoint and already include the applicable GFF basis; no second ignition or weather weighting is applied. The API does not infer damage applicability, release hydraulics, cleanup unit costs, or currency escalation.

## `api581.api.level1.hf_h2s_toxic_coefficients`

HF/H2S native toxic log-correlation coefficients

계산 ID: `level1/hf-h2s-toxic-coefficients`

출처: Part3 Table4.11; eqs(3.63)-(3.64); PDF pp497-498,525

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['hf', 'h2s']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `duration_s` | 기본값/선택 | `<class 'float'>` |
| `hf_instantaneous_intercept` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), AllowInfNan(allow_inf_nan=False)])] | None` |
| `intercept_qualification` | 기본값/선택 | `str | None` |

출력: `c`, `d`, `native_magnitude_unit`, `native_area_unit`, `si_mass_multiplier`, `si_area_multiplier`, `source_cell_status`

적용 범위: Native log10 correlation uses lb/s or lb and ft2; conversion factors2.205 and.0929 returned. Continuous lookup requires a printed duration node. HF instantaneous d is printed33,606: returned as33606 with ambiguous_print status, never silently changed to3.3606. Qualified caller override is explicit and traceable.

## `api581.api.level1.hf_h2s_toxic_area`

HF/H2S duration-dependent toxic consequence area

계산 ID: `level1/hf-h2s-toxic-area`

출처: Part3 §4.9.6,§4.9.11; eqs(3.63)-(3.64); Table4.11; PDF pp497-499,525

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['hf', 'h2s']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `duration_s` | 기본값/선택 | `<class 'float'>` |
| `hf_instantaneous_intercept` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), AllowInfNan(allow_inf_nan=False)])] | None` |
| `intercept_qualification` | 기본값/선택 | `str | None` |
| `toxic_rate_kg_s` | 예 | `<class 'float'>` |
| `toxic_mass_kg` | 예 | `<class 'float'>` |
| `nonignition_probability` | 예 | `<class 'float'>` |

출력: `unweighted_personnel_area_m2`, `personnel_area_m2`

적용 범위: Gas/vapor toxic consequence assumption. Continuous 5-60minute curves interpolate areas, not coefficients. Nonignition weighting applies once. Positive instantaneous HF mass requires qualified intercept override because printed33,606 is unresolved. No extrapolation or automatic spray/IDLH credit.

## `api581.api.level1.misc_toxic_coefficients`

Miscellaneous continuous toxic SI coefficients

계산 ID: `level1/misc-toxic-coefficients`

출처: Part3 §4.9.8; Table4.13M; PDF pp498-499,529-530

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['alcl3', 'co', 'hcl', 'nitric_acid', 'no2', 'phosgene', 'tdi', 'ee', 'eo', 'po']` |
| `release_phase` | 예 | `typing.Literal['gas', 'liquid', 'powder']` |
| `duration_s` | 예 | `<class 'float'>` |

출력: `e`, `f`, `native_rate_unit`, `native_area_unit`, `si_mass_multiplier`, `si_area_multiplier`

적용 범위: Ten chemicals, printed SI kg/s and m2 coefficients. Exact printed duration nodes only. AlCl3 powder uses gas-column coefficients for all positive durations per §4.9.8. N/A cells never become zero. Uses SI table directly rather than guessing inconsistent US punctuation/exponents or reconverting US coefficients.

## `api581.api.level1.misc_toxic_area`

Ten additional chemical continuous toxic consequence areas

계산 ID: `level1/misc-toxic-area`

출처: Part3 §4.9.8,§4.9.11; eq(3.65); Table4.13M; PDF pp498-499,529-530

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['alcl3', 'co', 'hcl', 'nitric_acid', 'no2', 'phosgene', 'tdi', 'ee', 'eo', 'po']` |
| `release_phase` | 예 | `typing.Literal['gas', 'liquid', 'powder']` |
| `duration_s` | 예 | `<class 'float'>` |
| `release_type` | 기본값/선택 | `typing.Literal['continuous']` |
| `toxic_rate_kg_s` | 예 | `<class 'float'>` |
| `nonignition_probability` | 예 | `<class 'float'>` |

출력: `unweighted_personnel_area_m2`, `personnel_area_m2`

적용 범위: Continuous only; no invented instantaneous correlation. Printed SI coefficients used directly; no additional unit conversion. N/A cells block interpolation that touches them. AlCl3 powder is duration-independent for positive duration. Caller qualifies phase and nonignition probability; no automatic spray credit.

## `api581.api.level1.toxic_cutoff`

Historical Level1 toxic concentration screening

계산 ID: `level1/toxic-cutoff`

출처: Part3 §4.9.9; PDF p499

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['hf', 'h2s', 'ammonia', 'chlorine']` |
| `concentration_ppm_on_idlh_basis` | 예 | `<class 'float'>` |

출력: `idlh_ppm`, `requires_toxic_evaluation`

적용 범위: 2016 printed IDLH values: HF30,H2S100,NH3 300,Cl10ppm. Stored-fluid concentration must be on matching IDLH ppm basis, not silently inferred from mass fraction. At or below cutoff evaluation is not required by this source rule. Not a current occupational exposure limit or an atmospheric dispersion safety claim.

## `api581.api.level1.toxic_mitigation`

Apply explicit toxic source mitigation credits

계산 ID: `level1/toxic-mitigation`

출처: Part3 §4.9.13; PDF pp499-500

| 입력 | 필수 | 타입 |
|---|---|---|
| `rate_reduction_fraction` | 기본값/선택 | `<class 'float'>` |
| `duration_reduction_fraction` | 기본값/선택 | `<class 'float'>` |
| `mass_reduction_fraction` | 기본값/선택 | `<class 'float'>` |
| `toxic_rate_kg_s` | 예 | `<class 'float'>` |
| `toxic_mass_kg` | 예 | `<class 'float'>` |
| `duration_s` | 예 | `<class 'float'>` |

출력: `toxic_rate_kg_s`, `toxic_mass_kg`, `duration_s`

적용 범위: Owner-qualified reductions only; no fixed default water-spray efficiency. Rate/duration apply to continuous release, mass to instantaneous. These are not the flammable Table4.6 detection magnitude credit. The caller controls the explicit credit basis and avoids applying the same measure twice.

## `api581.api.level1.toxic_component_consequence`

Compose toxic source/duration/mitigation and per-component area

계산 ID: `level1/toxic-component-consequence`

출처: Part3 §4.9; eqs(3.61)-(3.67); Tables4.11-4.13

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['hf', 'h2s', 'ammonia', 'chlorine', 'alcl3', 'co', 'hcl', 'nitric_acid', 'no2', 'phosgene', 'tdi', 'ee', 'eo', 'po']` |
| `release_phase` | 예 | `typing.Literal['gas', 'liquid', 'powder']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `theoretical_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `toxic_mass_fraction` | 예 | `<class 'float'>` |
| `available_mass_kg` | 예 | `<class 'float'>` |
| `detection_maximum_duration_s` | 예 | `<class 'float'>` |
| `nonignition_probability` | 예 | `<class 'float'>` |
| `mitigation` | 기본값/선택 | `<class 'api581.level1_toxic.MitigationCredits'>` |
| `concentration_ppm_on_idlh_basis` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `hf_instantaneous_intercept` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), AllowInfNan(allow_inf_nan=False)])] | None` |
| `intercept_qualification` | 기본값/선택 | `str | None` |

출력: `toxic_rate_kg_s`, `toxic_mass_kg`, `duration_s`, `unweighted_personnel_area_m2`, `personnel_area_m2`, `unmitigated_duration_s`, `screening_applied`, `requires_toxic_evaluation`

적용 범위: Single toxic component; mixture maximum and four-hole aggregation are separate. Uses theoretical total leak rate without flammable magnitude reduction. HF/H2S/NH3/Cl use gas/vapor exposure assumptions; miscellaneous phases follow Table4.13. Optional printed IDLH screening only supports four refinery toxins. All interpolation domains and HF ambiguity still apply; mitigation may shorten duration below a supported table range and then evaluation is rejected.

## `api581.api.level1.toxic_mixture_consequence`

Largest individual Level 1 toxic consequence area for a mixture

계산 ID: `level1/toxic-mixture-consequence`

출처: Part 3 §4.9.12, §4.9.15(f), eq (3.68); PDF pp500-501

| 입력 | 필수 | 타입 |
|---|---|---|
| `components` | 예 | `list[api581.level1_toxic.ToxicMixtureComponentArea]` |

출력: `personnel_area_m2`, `critical_component_id`, `component_areas_m2`, `component_count`

적용 범위: Takes already calculated individual toxic component areas and returns the largest; it does not add overlapping clouds, recalculate species release rates, or perform dispersion. For four-hole weighting use the separate hole-weighted/Level 2 composition API.

## `api581.api.level1.toxic_hole_summary`

Four-hole GFF-weighted Level 1 toxic consequence

계산 ID: `level1/toxic-hole-summary`

출처: Part 3 §4.9.14-§4.9.15(f), eq (3.68); PDF pp500-501

| 입력 | 필수 | 타입 |
|---|---|---|
| `cases` | 예 | `list[api581.level1_toxic.ToxicHoleCase]` |

출력: `personnel_area_m2`, `total_generic_frequency_per_year`, `by_hole_personnel_area_m2`

적용 범위: Requires one case for each canonical hole. Within each hole the largest individual toxic-component area is used, then areas are weighted by the supplied generic failure frequencies. Detection/DF-adjusted frequencies, dispersion and financial risk are outside this consequence-area API.

## `api581.api.level1.flammable_coefficients`

SI flammable consequence coefficients

계산 ID: `level1/flammable-coefficients`

출처: Part 3 Tables 4.8M, 4.9M; PDF pp522,524

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `release_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `effect` | 예 | `typing.Literal['equipment', 'personnel']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `autoignition` | 예 | `typing.Literal['not_likely', 'likely']` |

출력: `a`, `b`, `magnitude_unit`, `area_unit`

적용 범위: Type0 and Type1 table lookup only; blank cells are unsupported while printed zero coefficients are valid. Coefficients include original event weighting; do not multiply ignition probability again. Type1 areas must use the separate unblended calculation.

## `api581.api.release.detection_reduction`

Detection/isolation reduction factor

계산 ID: `release/detection-reduction`

출처: Part 3 Table 4.6; PDF p519

| 입력 | 필수 | 타입 |
|---|---|---|
| `detection` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation` | 예 | `typing.Literal['A', 'B', 'C']` |

출력: `reduction_fraction`

적용 범위: All nine A/B/C detection-isolation combinations are represented explicitly from Table 4.6; ratings themselves remain qualified inputs.

## `api581.api.release.detection_duration`

Detection/isolation maximum duration

계산 ID: `release/detection-duration`

출처: Part 3 Table 4.7; PDF p520

| 입력 | 필수 | 타입 |
|---|---|---|
| `detection` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation` | 예 | `typing.Literal['A', 'B', 'C']` |
| `hole` | 예 | `typing.Literal['small', 'medium', 'large']` |

출력: `maximum_duration_s`

적용 범위: No rupture-duration entry in this table; returned duration is seconds.

## `api581.api.level1.release_phase`

Level 1 final consequence phase

계산 ID: `level1/release-phase`

출처: Part 3 Table 4.3; PDF p518

| 입력 | 필수 | 타입 |
|---|---|---|
| `stored_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `ambient_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `normal_boiling_point_k` | 예 | `<class 'float'>` |

출력: `release_phase`

적용 범위: Level 1 approximation only; steam/acid overrides must be selected separately. No two-phase flash calculation.

## `api581.api.level1.energy_efficiency`

Instantaneous energy efficiency correction

계산 ID: `level1/energy-efficiency`

출처: Part 3 eq (3.18), Annex 3.B C4A

| 입력 | 필수 | 타입 |
|---|---|---|
| `released_mass_kg` | 예 | `<class 'float'>` |

출력: `energy_efficiency_factor`

적용 범위: Applied to instantaneous-release area only; below 4536 kg the correction is 1.

## `api581.api.level1.blending_factors`

Type 0 release/AIT blending factors

계산 ID: `level1/blending-factors`

출처: Part 3 eqs (3.19)-(3.26), Annex 3.B C5,C6

| 입력 | 필수 | 타입 |
|---|---|---|
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `adjusted_rate_kg_s` | 예 | `<class 'float'>` |
| `instantaneous_coefficients_available` | 예 | `<class 'bool'>` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `autoignition_temperature_k` | 예 | `<class 'float'>` |

출력: `instantaneous_weight`, `autoignition_likely_weight`

적용 범위: Type 0 fluids only. Type 1 correlations already incorporate smoothing.

## `api581.api.level1.flammable_area`

Type 0 per-hole blended flammable consequence

계산 ID: `level1/flammable-area`

출처: Part 3 §4.8.8 eqs (3.29)-(3.58), Tables 4.8M/4.9M

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `release_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `adjusted_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `autoignition_temperature_k` | 예 | `<class 'float'>` |
| `mitigation_fraction` | 예 | `<class 'float'>` |

출력: `equipment_area_m2`, `personnel_area_m2`, `instantaneous_weight`, `autoignition_likely_weight`, `energy_efficiency_factor`

적용 범위: Per-hole flammable consequence only; no toxic/NFNT/financial or hole-frequency weighting. Initial Type 0 set. Caller supplies final phase/AIT/mitigation; LH2 Level 2 behavior is not represented.

## `api581.api.release.controlled_scenario`

Per-hole source, inventory, detection/isolation and release magnitude

계산 ID: `release/controlled-scenario`

출처: Part 3 §§4.3-4.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `source` | 예 | `api581.release.Gas | api581.release.Liquid` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `component_mass_kg` | 예 | `<class 'float'>` |
| `inventory_group_mass_kg` | 예 | `<class 'float'>` |
| `detection` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation` | 예 | `typing.Literal['A', 'B', 'C']` |
| `duration_hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `rupture_maximum_duration_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `theoretical_rate_kg_s`, `available_mass_kg`, `release_type`, `reduction_fraction`, `maximum_duration_s`, `adjusted_rate_kg_s`, `duration_s`, `released_mass_kg`

적용 범위: Single qualified representative hole. Constant ideal-gas/incompressible-liquid source; caller supplies controls and inventory. Rupture duration must be explicit. Adjusted flammable rate is not the toxic source rate.

## `api581.api.level1.release_to_flammable`

Compose source, inventory, controls and per-hole flammable area

계산 ID: `level1/release-to-flammable`

출처: Part 3 §§4.3-4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `source` | 예 | `api581.release.Gas | api581.release.Liquid` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `component_mass_kg` | 예 | `<class 'float'>` |
| `inventory_group_mass_kg` | 예 | `<class 'float'>` |
| `detection` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation` | 예 | `typing.Literal['A', 'B', 'C']` |
| `duration_hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `rupture_maximum_duration_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `fluid` | 예 | `<class 'str'>` |
| `final_release_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `autoignition_temperature_k` | 예 | `<class 'float'>` |
| `mitigation_fraction` | 예 | `<class 'float'>` |

출력: `theoretical_rate_kg_s`, `available_mass_kg`, `release_type`, `reduction_fraction`, `maximum_duration_s`, `adjusted_rate_kg_s`, `duration_s`, `released_mass_kg`, `equipment_area_m2`, `personnel_area_m2`, `instantaneous_weight`, `autoignition_likely_weight`, `energy_efficiency_factor`

적용 범위: Type0 only, single selected hole; caller selects fluid, phase, AIT and mitigation. No toxic/NFNT/cost assessment. Rupture duration must be explicit; Type1 uses release-to-type1-flammable.

## `api581.api.level1.release_to_acid`

Compose controlled release and ACID splash consequence

계산 ID: `level1/release-to-acid`

출처: Part 3 §§4.1.3,4.3-4.7,4.10.3; PDF pp483-484,490,502

| 입력 | 필수 | 타입 |
|---|---|---|
| `source` | 예 | `api581.release.Gas | api581.release.Liquid` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `component_mass_kg` | 예 | `<class 'float'>` |
| `inventory_group_mass_kg` | 예 | `<class 'float'>` |
| `detection` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation` | 예 | `typing.Literal['A', 'B', 'C']` |
| `duration_hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `rupture_maximum_duration_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `differential_pressure_pa` | 예 | `<class 'float'>` |

출력: `theoretical_rate_kg_s`, `available_mass_kg`, `release_type`, `reduction_fraction`, `maximum_duration_s`, `adjusted_rate_kg_s`, `duration_s`, `released_mass_kg`, `personnel_area_m2`, `equipment_area_m2`, `coefficient_g`, `exponent_h`, `representative_fluid`, `release_phase`

적용 범위: ACID representative-fluid route only. The caller must qualify the nonflammable/nontoxic acid-or-caustic selection and the differential pressure. The splash correlation is valid only for the documented 103.4-413.7 kPa range; no toxic, flammable or Level 2 dispersion consequence is inferred.

## `api581.api.level1.release_to_steam`

Compose controlled release and Level 1 steam consequence

계산 ID: `level1/release-to-steam`

출처: Part 3 §§4.3-4.7,4.10.2; PDF pp485-490,501-502

| 입력 | 필수 | 타입 |
|---|---|---|
| `source` | 예 | `api581.release.Gas | api581.release.Liquid` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `component_mass_kg` | 예 | `<class 'float'>` |
| `inventory_group_mass_kg` | 예 | `<class 'float'>` |
| `detection` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation` | 예 | `typing.Literal['A', 'B', 'C']` |
| `duration_hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `rupture_maximum_duration_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `theoretical_rate_kg_s`, `available_mass_kg`, `release_type`, `reduction_fraction`, `maximum_duration_s`, `adjusted_rate_kg_s`, `duration_s`, `released_mass_kg`, `continuous_area_m2`, `instantaneous_area_m2`, `instantaneous_weight`, `personnel_area_m2`, `equipment_area_m2`, `representative_fluid`, `release_phase`

적용 범위: Steam NFNT correlation only. Steam is treated as gas/vapor; the source must be qualified as steam and the returned area is personnel-only with equipment area zero. No condensation, jet dispersion, two-phase flash or Level 2 consequence is inferred.

## `api581.api.level1.release_to_toxic`

Compose controlled release and Level 1 toxic consequence

계산 ID: `level1/release-to-toxic`

출처: Part 3 §§4.3-4.7,4.9; PDF pp485-500

| 입력 | 필수 | 타입 |
|---|---|---|
| `source` | 예 | `api581.release.Gas | api581.release.Liquid` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `component_mass_kg` | 예 | `<class 'float'>` |
| `inventory_group_mass_kg` | 예 | `<class 'float'>` |
| `detection` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation` | 예 | `typing.Literal['A', 'B', 'C']` |
| `duration_hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `rupture_maximum_duration_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `fluid` | 예 | `typing.Literal['hf', 'h2s', 'ammonia', 'chlorine', 'alcl3', 'co', 'hcl', 'nitric_acid', 'no2', 'phosgene', 'tdi', 'ee', 'eo', 'po']` |
| `release_phase` | 예 | `typing.Literal['gas', 'liquid', 'powder']` |
| `toxic_mass_fraction` | 예 | `<class 'float'>` |
| `nonignition_probability` | 예 | `<class 'float'>` |
| `mitigation` | 기본값/선택 | `<class 'api581.level1_toxic.MitigationCredits'>` |
| `concentration_ppm_on_idlh_basis` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `hf_instantaneous_intercept` | 기본값/선택 | `float | None` |
| `intercept_qualification` | 기본값/선택 | `str | None` |

출력: `theoretical_rate_kg_s`, `available_mass_kg`, `release_type`, `reduction_fraction`, `maximum_duration_s`, `adjusted_rate_kg_s`, `duration_s`, `released_mass_kg`, `toxic_rate_kg_s`, `toxic_mass_kg`, `unweighted_personnel_area_m2`, `personnel_area_m2`, `unmitigated_duration_s`, `screening_applied`, `requires_toxic_evaluation`

적용 범위: Uses the controlled source for one representative hole and passes the theoretical rate (not flammable-adjusted rate) to the toxic component calculation. Single toxic component only; mixture maximum, four-hole aggregation, dispersion and Level 2 source partition remain separate.

## `api581.api.level1.consequence_summary`

Four-hole mechanism-weighted final consequence areas

계산 ID: `level1/consequence-summary`

출처: Part 3 eqs (3.27)-(3.28),(3.68),(3.78),(3.81)-(3.84)

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |
| `holes` | 예 | `list[api581.level1_summary.HoleAreas]` |

출력: `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `toxic_personnel_area_m2`, `nfnt_personnel_area_m2`, `equipment_area_m2`, `personnel_area_m2`, `consequence_area_m2`, `generic_frequency_per_year`

적용 범위: Caller supplies complete per-hole mechanism consequences, already event-weighted. GFF table supports non-tank components. Mechanism areas are frequency-weighted before final maximum selection.

## `api581.api.financial.repair_table`

2001 USD component repair cost table

계산 ID: `financial/repair-table`

출처: Part 3 Table 4.15; PDF p532

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |

출력: `cost_by_hole_usd_2001`, `cost_basis_year`, `currency`

적용 범위: Historical 2001 USD, not current prices. COURSE-1-10 normalizes source COURSES-10 label.

## `api581.api.financial.material_factor`

Material repair cost multiplier

계산 ID: `financial/material-factor`

출처: Part 3 Table 4.16; PDF p533

| 입력 | 필수 | 타입 |
|---|---|---|
| `material_id` | 예 | `typing.Literal['carbon_steel', '1.25Cr-0.5Mo', '2.25Cr-1Mo', '5Cr-0.5Mo', '7Cr-0.5Mo', 'clad_304_ss', 'polypropylene_lined', '9Cr-1Mo', '405_ss', '410_ss', '304_ss', 'clad_316_ss', 'cs_saran_lined', 'cs_rubber_lined', '316_ss', 'cs_glass_lined', 'clad_alloy_400', '90_10_CuNi', 'clad_alloy_600', 'cs_teflon_lined', 'clad_nickel', 'alloy_800', '70_30_CuNi', '904L', 'alloy_20', 'alloy_400', 'alloy_600', 'nickel', 'alloy_625', 'titanium', 'alloy_C', 'zirconium', 'alloy_B', 'tantalum']` |

출력: `material_factor`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.financial.outage_table`

Estimated equipment outage table

계산 ID: `financial/outage-table`

출처: Part 3 Table 4.17; PDF p534

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |

출력: `days_by_hole`

적용 범위: NA is returned as null, never zero. Historical estimates require owner review.

## `api581.api.financial.component_repair`

GFF-weighted material-adjusted component repair cost

계산 ID: `financial/component-repair`

출처: Part 3 eq (3.86), Tables 4.15/4.16

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |
| `material_id` | 예 | `typing.Literal['carbon_steel', '1.25Cr-0.5Mo', '2.25Cr-1Mo', '5Cr-0.5Mo', '7Cr-0.5Mo', 'clad_304_ss', 'polypropylene_lined', '9Cr-1Mo', '405_ss', '410_ss', '304_ss', 'clad_316_ss', 'cs_saran_lined', 'cs_rubber_lined', '316_ss', 'cs_glass_lined', 'clad_alloy_400', '90_10_CuNi', 'clad_alloy_600', 'cs_teflon_lined', 'clad_nickel', 'alloy_800', '70_30_CuNi', '904L', 'alloy_20', 'alloy_400', 'alloy_600', 'nickel', 'alloy_625', 'titanium', 'alloy_C', 'zirconium', 'alloy_B', 'tantalum']` |
| `price_factor_since_2001` | 예 | `<class 'float'>` |
| `usd_to_output_currency` | 예 | `<class 'float'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `weighted_repair_cost_usd_2001`, `cost`, `material_factor`, `cost_basis_year`, `currency`

적용 범위: Inflation and currency conversion are explicit caller assumptions, not fetched market data. Non-tank GFF support only.

## `api581.api.financial.component_outage`

GFF-weighted component outage duration

계산 ID: `financial/component-outage`

출처: Part 3 eq (3.88), Table 4.17

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |
| `outage_multiplier` | 예 | `<class 'float'>` |
| `override_days` | 기본값/선택 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |

출력: `component_outage_days`, `effective_days_by_hole`

적용 범위: A nonzero-frequency hole with NA outage requires an explicit owner-supplied override; NA is not silently filled.

## `api581.api.financial.surrounding_outage`

Surrounding equipment repair outage correlation

계산 ID: `financial/surrounding-outage`

출처: Part 3 eq (3.89); PDF p506

| 입력 | 필수 | 타입 |
|---|---|---|
| `surrounding_damage_cost_usd` | 예 | `<class 'float'>` |

출력: `surrounding_outage_days`

적용 범위: USD cost input only; correlation monetary basis must be consistent with the source methodology. Zero damage cost returns the continuous limit 0 days.

## `api581.api.properties.leak_table`

Tabulated SI leak/remediation properties

계산 ID: `properties/leak-table`

출처: Part 3 Table 4.18M; PDF p536

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['C1-C2', 'C3-C5', 'C6-C8', 'C9-C12', 'C13-C16', 'C17-C25', 'C25+', 'Acid', 'H2', 'H2S', 'HF', 'CO', 'DEE', 'HCL', 'Nitric Acid', 'NO2', 'Phosgene', 'TDI', 'Methanol', 'PO', 'Styrene', 'EEA', 'EE', 'EG', 'EO']` |

출력: `molecular_weight_kg_kmol`, `tabulated_liquid_density_kg_m3`, `normal_boiling_point_k`, `evaporated_fraction_24h`

적용 범위: Table liquid density for remediation, not operating gas density or a thermodynamic property solver. Source C3-C5 label is retained and not silently aliased to C3-C4.

## `api581.api.financial.cleanup_eligibility`

Level 1 environmental cleanup screening

계산 ID: `financial/cleanup-eligibility`

출처: Part 3 §4.12.6

| 입력 | 필수 | 타입 |
|---|---|---|
| `release_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `normal_boiling_point_k` | 예 | `<class 'float'>` |
| `autoignition_likely` | 예 | `<class 'bool'>` |

출력: `include_cleanup_cost`

적용 범위: Uses the text's rounded 93 Celsius threshold; source also states 200 Fahrenheit. Screening only; no cost or evaporation-rate model.

## `api581.api.financial.level1_consequence`

Compose five Level 1 financial consequence categories

계산 ID: `financial/level1-consequence`

출처: Part 3 §§4.12.2-4.12.7 eqs (3.85)-(3.94)

| 입력 | 필수 | 타입 |
|---|---|---|
| `repair` | 예 | `<class 'api581.cost_tables.RepairCost'>` |
| `outage` | 예 | `<class 'api581.cost_tables.ComponentOutage'>` |
| `equipment_area_m2` | 예 | `<class 'float'>` |
| `personnel_area_m2` | 예 | `<class 'float'>` |
| `equipment_cost_per_m2` | 예 | `<class 'float'>` |
| `production_cost_per_day` | 예 | `<class 'float'>` |
| `population_density_per_m2` | 예 | `<class 'float'>` |
| `cost_per_injury` | 예 | `<class 'float'>` |
| `weighted_cleanup_volume_m3` | 예 | `<class 'float'>` |
| `cleanup_cost_per_m3` | 예 | `<class 'float'>` |

출력: `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `financial_consequence`, `currency`, `cost_basis_year`

적용 범위: Input areas and remediation volume must already be hole-weighted and screened. All user monetary inputs use repair.currency and repair.cost_basis_year. Surrounding-outage correlation receives equivalent 2001 USD via the explicit price/currency factors.

## `api581.api.damage.scc_severity`

Mechanism-specific SCC severity index

계산 ID: `damage/scc-severity`

출처: Part 2 Tables 6.2,7.2,8.4,9.4,10.3,11.3,12.3,13.3,14.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `mechanism` | 예 | `typing.Literal['caustic', 'amine', 'ssc', 'hic-sohic-h2s', 'acscc', 'pascc', 'clscc', 'hsc-hf', 'hic-sohic-hf']` |
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |

출력: `severity_index`

적용 범위: Caller must complete material/service susceptibility screening before selecting a severity.

## `api581.api.damage.hic_monitoring_factor`

HIC/SOHIC monitoring adjustment factor

계산 ID: `damage/hic-monitoring-factor`

출처: Part 2 Tables 9.5,14.4; PDF pp193,221

| 입력 | 필수 | 타입 |
|---|---|---|
| `monitoring` | 예 | `typing.Literal['none', 'process_variables', 'hydrogen_probes', 'both']` |

출력: `monitoring_factor`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.damage.caustic`

caustic damage factor from qualified susceptibility and inspections

계산 ID: `damage/caustic`

출처: Part 2 §6.6, Table 6.2, eq (2.25), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.amine`

amine damage factor from qualified susceptibility and inspections

계산 ID: `damage/amine`

출처: Part 2 §7.6, Table 7.2, eq (2.26), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.ssc`

ssc damage factor from qualified susceptibility and inspections

계산 ID: `damage/ssc`

출처: Part 2 §8.6, Table 8.4, eq (2.27), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.hic_sohic_h2s`

hic-sohic-h2s damage factor from qualified susceptibility and inspections

계산 ID: `damage/hic-sohic-h2s`

출처: Part 2 §9.6, Table 9.4, eq (2.28), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `monitoring` | 예 | `typing.Literal['none', 'process_variables', 'hydrogen_probes', 'both']` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.acscc`

acscc damage factor from qualified susceptibility and inspections

계산 ID: `damage/acscc`

출처: Part 2 §10.6, Table 10.3, eq (2.29), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.pascc`

pascc damage factor from qualified susceptibility and inspections

계산 ID: `damage/pascc`

출처: Part 2 §11.6, Table 11.3, eq (2.30), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.clscc`

clscc damage factor from qualified susceptibility and inspections

계산 ID: `damage/clscc`

출처: Part 2 §12.6, Table 12.3, eq (2.31), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.hsc_hf`

hsc-hf damage factor from qualified susceptibility and inspections

계산 ID: `damage/hsc-hf`

출처: Part 2 §13.6, Table 13.3, eq (2.32), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.hic_sohic_hf`

hic-sohic-hf damage factor from qualified susceptibility and inspections

계산 ID: `damage/hic-sohic-hf`

출처: Part 2 §14.6, Table 14.3, eq (2.33), §3.4.3 and Table 6.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `monitoring` | 예 | `typing.Literal['none', 'process_variables', 'hydrogen_probes', 'both']` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported.

## `api581.api.damage.hsc_hf_susceptibility`

HSC-HF susceptibility of eligible steel weldments

계산 ID: `damage/hsc-hf-susceptibility`

출처: Part 2 Table 13.2; PDF p215

| 입력 | 필수 | 타입 |
|---|---|---|
| `measured_brinnell_hardness` | 예 | `<class 'float'>` |
| `pwht` | 예 | `<class 'bool'>` |

출력: `susceptibility`

적용 범위: Eligible material and HF exposure must be screened separately. Brinnell must be measured as Brinnell, not converted from microhardness.

## `api581.api.damage.ssc_susceptibility`

SSC hardness/heat-treatment susceptibility

계산 ID: `damage/ssc-susceptibility`

출처: Part 2 Table 8.3; PDF p187

| 입력 | 필수 | 타입 |
|---|---|---|
| `measured_brinnell_hardness` | 예 | `<class 'float'>` |
| `pwht` | 예 | `<class 'bool'>` |
| `environmental_severity` | 예 | `typing.Literal['low', 'moderate', 'high']` |

출력: `susceptibility`

적용 범위: Environmental severity and cyanide-related susceptibility upgrade must be established separately. Table 'Not' is normalized to none.

## `api581.api.damage.hic_hf_susceptibility`

HIC/SOHIC-HF steel/product susceptibility

계산 ID: `damage/hic-hf-susceptibility`

출처: Part 2 Table 14.2; PDF p220

| 입력 | 필수 | 타입 |
|---|---|---|
| `steel_sulfur_weight_percent` | 예 | `<class 'float'>` |
| `product_form` | 예 | `typing.Literal['plate_or_welded', 'seamless_or_extruded_pipe']` |
| `pwht` | 예 | `<class 'bool'>` |

출력: `susceptibility`

적용 범위: Eligible steel with HF exposure only; material/service screening remains separate.

## `api581.api.damage.hic_h2s_susceptibility`

HIC/SOHIC-H2S steel/product susceptibility

계산 ID: `damage/hic-h2s-susceptibility`

출처: Part 2 Table 9.3; PDF p193

| 입력 | 필수 | 타입 |
|---|---|---|
| `steel_sulfur_weight_percent` | 예 | `<class 'float'>` |
| `product_form` | 예 | `typing.Literal['plate_or_welded', 'seamless_or_extruded_pipe']` |
| `pwht` | 예 | `<class 'bool'>` |
| `environmental_severity` | 예 | `typing.Literal['low', 'moderate', 'high']` |

출력: `susceptibility`

적용 범위: Environmental severity, existing-crack rule and cyanide upgrade must be established separately.

## `api581.api.damage.clscc_susceptibility`

CLSCC SI/US temperature/chloride susceptibility

계산 ID: `damage/clscc-susceptibility`

출처: Part 2 Tables 12.2M/12.2; PDF pp210-211

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `temperature_basis` | 기본값/선택 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `ph_over_10` | 예 | `<class 'bool'>` |
| `chloride_band_ppm` | 예 | `typing.Literal['1-10', '11-100', '101-1000', '>1000']` |

출력: `susceptibility`

적용 범위: Eligible material and chloride band selected by caller; no interpolation across concentration gaps. Temperature basis is explicit. For pH>10 at exactly 93 C in the SI table, overlapping source rows require manual resolution.

## `api581.api.damage.wet_h2s_environment`

Wet H2S environmental severity and cyanide flag

계산 ID: `damage/wet-h2s-environment`

출처: Part 2 Tables 8.2,9.2; PDF pp187,193

| 입력 | 필수 | 타입 |
|---|---|---|
| `water_ph` | 예 | `<class 'float'>` |
| `h2s_in_water_ppm` | 예 | `<class 'float'>` |
| `cyanides_present` | 예 | `<class 'bool'>` |

출력: `environmental_severity`, `susceptibility_upgrade_required`

적용 범위: The source pH rows leave gaps and the H2S columns overlap at 1000 ppm; these inputs require manual classification and are rejected. Cyanide flag requires upgrading the subsequent susceptibility, not the environmental-severity row.

## `api581.api.damage.acscc_susceptibility`

ACSCC carbonate/PWHT susceptibility

계산 ID: `damage/acscc-susceptibility`

출처: Part 2 Table 10.2; PDF p199

| 입력 | 필수 | 타입 |
|---|---|---|
| `water_ph_band` | 예 | `typing.Literal['below_7.5', '7.5_to_8', '8_to_9', 'at_least_9']` |
| `carbonate_ppm` | 예 | `<class 'float'>` |
| `pwht` | 예 | `<class 'bool'>` |

출력: `susceptibility`

적용 범위: Caller selects source pH band and establishes eligible material/service. Band endpoint interpretation is not silently inferred from rounded pH readings.

## `api581.api.damage.pascc_susceptibility`

PASCC temperature/material/heat-treatment susceptibility

계산 ID: `damage/pascc-susceptibility`

출처: Part 2 Table 11.2; PDF p205

| 입력 | 필수 | 타입 |
|---|---|---|
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `material_group` | 예 | `typing.Literal['regular_300ss_or_alloy600_800', 'h_grade_300ss', 'l_grade_300ss', '321ss', '347ss_alloy20_625_or_austenitic_overlay']` |
| `heat_treatment` | 예 | `typing.Literal['solution_annealed', 'stabilized_before_welding', 'stabilized_after_welding']` |

출력: `susceptibility`

적용 범위: Eligible material/service must be established separately. Blank heat-treatment cells are unsupported; SI threshold is 427 C.

## `api581.api.damage.external_base_rate`

External corrosion SI base rate

계산 ID: `damage/external-base-rate`

출처: Part 2 Table 15.2M; PDF p231

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `driver` | 예 | `typing.Literal['marine_or_cooling_tower', 'temperate', 'arid_dry', 'severe']` |

출력: `base_corrosion_rate_m_year`

적용 범위: Linear interpolation only within -12..121 C. Severe -8 C cell and adjacent interpolation are disabled due to SI/US mismatch.

## `api581.api.damage.cui_base_rate`

CUI SI base corrosion rate

계산 ID: `damage/cui-base-rate`

출처: Part 2 Table 16.2M; PDF p243

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `driver` | 예 | `typing.Literal['marine_or_cooling_tower', 'temperate', 'arid_dry', 'severe']` |

출력: `base_corrosion_rate_m_year`

적용 범위: Linear interpolation only within -12..176 C; material/service screening separate.

## `api581.api.damage.external_time_weighted_rate`

Time-weighted external/CUI base rate

계산 ID: `damage/external-time-weighted-rate`

출처: Part 2 Tables 15.2M/16.2M note 3

| 입력 | 필수 | 타입 |
|---|---|---|
| `mechanism` | 예 | `typing.Literal['external', 'cui']` |
| `driver` | 예 | `typing.Literal['marine_or_cooling_tower', 'temperate', 'arid_dry', 'severe']` |
| `periods` | 예 | `list[api581.external_corrosion.ExposurePeriod]` |

출력: `base_corrosion_rate_m_year`, `period_rates_m_year`

적용 범위: Weights describe operating-time fractions and must sum to one; all period temperatures must lie within the selected source table.

## `api581.api.damage.external_rate_adjust`

External corrosion design/interface adjustment

계산 ID: `damage/external-rate-adjust`

출처: Part 2 eq (2.34); PDF p224

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `water_retaining_design` | 예 | `<class 'bool'>` |
| `soil_or_water_interface` | 예 | `<class 'bool'>` |

출력: `design_interface_factor`, `corrosion_rate_m_year`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.damage.cui_rate_adjust`

CUI insulation/condition/complexity adjustment

계산 ID: `damage/cui-rate-adjust`

출처: Part 2 eq (2.51), §16.6.3, Table 16.3; PDF pp234-235,244

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `water_retaining_design` | 예 | `<class 'bool'>` |
| `soil_or_water_interface` | 예 | `<class 'bool'>` |
| `insulation` | 예 | `typing.Literal['unknown', 'foamglass', 'pearlite', 'fiberglass', 'mineral_wool', 'calcium_silicate', 'asbestos']` |
| `complexity` | 예 | `typing.Literal['below_average', 'average', 'above_average']` |
| `insulation_condition` | 예 | `typing.Literal['below_average', 'average', 'above_average']` |

출력: `design_interface_factor`, `corrosion_rate_m_year`, `insulation_factor`, `complexity_factor`, `condition_factor`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.damage.coating_exposure`

Coating-adjusted corrosion exposure time

계산 ID: `damage/coating-exposure`

출처: Part 2 eqs (2.36)-(2.42),(2.53)-(2.59); PDF pp224,235

| 입력 | 필수 | 타입 |
|---|---|---|
| `years_since_thickness_reading` | 예 | `<class 'float'>` |
| `coating_age_years` | 예 | `<class 'float'>` |
| `coating_quality` | 예 | `typing.Literal['none_or_poor', 'medium', 'high']` |

출력: `coating_credit_years`, `corrosion_exposure_years`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.damage.external_corrosion`

External corrosion Bayesian damage factor

계산 ID: `damage/external-corrosion`

출처: Part 2 §15.6.3 eqs (2.34)-(2.50)

| 입력 | 필수 | 타입 |
|---|---|---|
| `rate` | 예 | `<class 'api581.external_corrosion.RateAdjustment'>` |
| `coating` | 예 | `<class 'api581.external_corrosion.CoatingExposure'>` |
| `strength` | 예 | `<class 'api581.thinning.StrengthRatio'>` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |

출력: `corrosion_rate_m_year`, `coating_credit_years`, `corrosion_exposure_years`, `wall_loss_fraction`, `strength_ratio`, `weighted_failure_probability`, `damage_factor`, `posterior_probabilities`, `reliability_indices`

적용 범위: Internal-pressure-governed strength path only; eligible material/service, base rate, flow stress and inspection validity supplied. No internal-thinning floor/adjustments applied.

## `api581.api.damage.cui`

Corrosion-under-insulation Bayesian damage factor

계산 ID: `damage/cui`

출처: Part 2 §16.6.3 eqs (2.51)-(2.67)

| 입력 | 필수 | 타입 |
|---|---|---|
| `rate` | 예 | `<class 'api581.external_corrosion.CuiAdjustment'>` |
| `coating` | 예 | `<class 'api581.external_corrosion.CoatingExposure'>` |
| `strength` | 예 | `<class 'api581.thinning.StrengthRatio'>` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |

출력: `corrosion_rate_m_year`, `coating_credit_years`, `corrosion_exposure_years`, `wall_loss_fraction`, `strength_ratio`, `weighted_failure_probability`, `damage_factor`, `posterior_probabilities`, `reliability_indices`

적용 범위: Internal-pressure-governed strength path (2.63) only; the Min/Max discrepancy in source (2.62) is not inferred. Base rate and inspection validity supplied. No internal-thinning floor/adjustments applied. Source STEP 13 references Tables 5.6/5.7, which do not identify prior/conditional probability tables. This implementation explicitly adopts general-thinning Tables 4.5/4.6, consistent with external-corrosion methodology; this interpretation requires independent engineering verification.

## `api581.api.damage.external_clscc_base_susceptibility`

External/CUI CLSCC climate-temperature base susceptibility

계산 ID: `damage/external-clscc-base-susceptibility`

출처: Part 2 Tables 17.2,18.2; PDF pp249,255

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `driver` | 예 | `typing.Literal['marine_or_cooling_tower', 'temperate', 'arid_dry', 'severe']` |
| `mechanism` | 예 | `typing.Literal['external_clscc', 'cui_clscc']` |

출력: `base_susceptibility`

적용 범위: Eligible austenitic material/service required. CUI complexity/condition/chloride adjustments not included. Source rows overlap at 93 C, requiring manual classification.

## `api581.api.damage.external_clscc`

External chloride SCC damage factor

계산 ID: `damage/external-clscc`

출처: Part 2 §17.6.3 eqs (2.68)-(2.76), Table 17.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `coating_age_years` | 예 | `<class 'float'>` |
| `coating_quality` | 예 | `typing.Literal['none_or_poor', 'medium', 'high']` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `coating_credit_years`, `cracking_exposure_years`, `damage_factor`

적용 범위: Qualified susceptibility and inspection age supplied; eligible material/service screening is separate. External severity scale differs from internal CLSCC.

## `api581.api.damage.cui_clscc`

Chloride SCC under insulation damage factor

계산 ID: `damage/cui-clscc`

출처: Part 2 §18.6.3 eqs (2.77)-(2.85), Table 17.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['none', 'low', 'medium', 'high']` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `coating_age_years` | 예 | `<class 'float'>` |
| `coating_quality` | 예 | `typing.Literal['none_or_poor', 'medium', 'high']` |

출력: `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `coating_credit_years`, `cracking_exposure_years`, `damage_factor`

적용 범위: Caller supplies susceptibility AFTER complexity, insulation-condition and chloride adjustments. Eligible material/service screening remains separate.

## `api581.api.damage.fatigue_base`

Piping mechanical fatigue base factor

계산 ID: `damage/fatigue-base`

출처: Part 2 §24.6.3 STEP 1-5, eq (2.92); PDF p289

| 입력 | 필수 | 타입 |
|---|---|---|
| `previous_failure_count` | 예 | `<class 'int'>` |
| `shaking_severity` | 예 | `typing.Literal['minor', 'moderate', 'severe']` |
| `shaking_duration_band` | 예 | `typing.Literal['less_than_2_weeks', '2_to_13_weeks', '13_to_52_weeks']` |
| `cyclic_loading` | 예 | `typing.Literal['reciprocating_machinery', 'prv_chatter', 'high_pressure_drop_valve', 'none']` |

출력: `previous_failure_factor`, `shaking_factor`, `shaking_duration_factor`, `cyclic_loading_factor`, `base_damage_factor`

적용 범위: Piping only; caller selects vibration/duration band. Source gives no explicit duration factor above 52 weeks or unique numeric classification at 13 weeks.

## `api581.api.damage.fatigue_adjustments`

Piping mechanical fatigue adjustment factors

계산 ID: `damage/fatigue-adjustments`

출처: Part 2 §24.6.3 STEP 6, eq (2.93); PDF p290

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrective_action` | 예 | `typing.Literal['complete_engineering_analysis', 'experience_based_modification', 'none']` |
| `total_pipe_fittings` | 예 | `<class 'int'>` |
| `damaged_or_improper_supports` | 예 | `<class 'bool'>` |
| `broken_or_directly_welded_gussets` | 예 | `<class 'bool'>` |
| `branch_design` | 예 | `typing.Literal['threaded_socketweld_saddle_on', 'saddle_in', 'tee_or_weldolet', 'sweepolet']` |
| `any_branch_above_nps_2` | 예 | `<class 'bool'>` |

출력: `corrective_action_factor`, `complexity_factor`, `pipe_condition_factor`, `joint_branch_factor`, `branch_diameter_factor`, `combined_adjustment_factor`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.damage.mechanical_fatigue`

Piping mechanical fatigue damage factor

계산 ID: `damage/mechanical-fatigue`

출처: Part 2 eqs (2.92)-(2.93)

| 입력 | 필수 | 타입 |
|---|---|---|
| `base` | 예 | `<class 'api581.fatigue.FatigueBase'>` |
| `adjustments` | 예 | `<class 'api581.fatigue.FatigueAdjustments'>` |

출력: `previous_failure_factor`, `shaking_factor`, `shaking_duration_factor`, `cyclic_loading_factor`, `base_damage_factor`, `corrective_action_factor`, `complexity_factor`, `pipe_condition_factor`, `joint_branch_factor`, `branch_diameter_factor`, `combined_adjustment_factor`, `damage_factor`

적용 범위: Piping only; qualitative categories supplied by caller. Not a stress-range/cycle-count fatigue life or FFS calculation.

## `api581.api.properties.hydrogen_partial_pressure`

Hydrogen ideal-mixture partial pressure

계산 ID: `properties/hydrogen-partial-pressure`

출처: Part 2 Table 19.1; PDF p259

| 입력 | 필수 | 타입 |
|---|---|---|
| `total_pressure_pa_abs` | 예 | `<class 'float'>` |
| `hydrogen_mole_fraction` | 예 | `<class 'float'>` |

출력: `hydrogen_partial_pressure_pa_abs`

적용 범위: Mole fraction times total absolute pressure; not a fugacity model.

## `api581.api.damage.htha_factor`

HTHA susceptibility damage factor

계산 ID: `damage/htha-factor`

출처: Part 2 Table 19.2; PDF p260

| 입력 | 필수 | 타입 |
|---|---|---|
| `susceptibility` | 예 | `typing.Literal['damage_observed', 'high', 'medium', 'low', 'none']` |

출력: `damage_factor`

적용 범위: Qualified susceptibility supplied; historical exposure and pre-1970 fabrication may require more conservative owner review.

## `api581.api.damage.htha_carbon_screen`

Carbon/C-half-Mo HTHA screening and factor

계산 ID: `damage/htha-carbon-screen`

출처: Part 2 §19.6.3 STEP 1-4; PDF pp258-260

| 입력 | 필수 | 타입 |
|---|---|---|
| `material_group` | 예 | `typing.Literal['carbon_steel', 'c_half_mo']` |
| `exposure_temperature_k` | 예 | `<class 'float'>` |
| `hydrogen_partial_pressure_pa_abs` | 예 | `<class 'float'>` |
| `damage_history` | 예 | `typing.Literal['none', 'observed_not_replaced', 'replaced_in_kind', 'upgraded_material']` |

출력: `susceptibility`, `damage_factor`

적용 범위: Current material must match material_group. Uses printed SI 177 C and 0.345 MPa thresholds. Mixed high/low temperature-pressure cases are not assigned by the printed carbon-steel rules and require engineering review. Cr-Mo/API 941 curve screening is separate.

## `api581.api.damage.brittle_reference_temperature`

Brittle fracture reference temperature

계산 ID: `damage/brittle-reference-temperature`

출처: Part 2 §20.6.3 STEP 3; Table 20.3; PDF p268

| 입력 | 필수 | 타입 |
|---|---|---|
| `material_group` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel']` |
| `minimum_yield_strength_pa` | 예 | `<class 'float'>` |
| `exemption_curve` | 예 | `typing.Literal['A', 'B', 'C', 'D']` |
| `interpolation` | 예 | `typing.Literal['exact', 'linear']` |

출력: `reference_temperature_k`, `table_basis`

적용 범위: Caller qualifies material and assigns ASME exemption curve. Uses the printed US Table 20.3 (ksi, F), explicitly converted to Pa and K; not rounded SI Table 20.3M. Linear interpolation is a caller-selected engineering interpolation; no extrapolation.

## `api581.api.damage.brittle_service_factor`

Brittle fracture service-experience adjustment

계산 ID: `damage/brittle-service-factor`

출처: Part 2 §20.6.3 STEP 6; eq (2.86); PDF pp264-265

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_thickness_m` | 예 | `<class 'float'>` |
| `nominal_uncorroded_thickness_m` | 예 | `<class 'float'>` |
| `equipment_type` | 예 | `typing.Literal['pressure_vessel', 'piping']` |
| `p1_or_p3_steel` | 예 | `<class 'bool'>` |
| `design_temperature_k` | 예 | `<class 'float'>` |
| `construction_code_satisfied` | 예 | `<class 'bool'>` |
| `stable_conditions_no_more_severe_future` | 예 | `<class 'bool'>` |
| `cet_at_mawp_k` | 예 | `<class 'float'>` |
| `cyclic_fatigue_or_vibration_design_service` | 예 | `<class 'bool'>` |
| `environmental_cracking` | 예 | `<class 'bool'>` |
| `shock_chilling` | 예 | `<class 'bool'>` |

출력: `service_experience_factor`, `thin_component_credit`, `service_criteria`

적용 범위: Owner qualifies code compliance, operating history and service exclusions. Thin-component criterion is an independent OR; all eight service criteria are otherwise required. Printed SI thresholds are used.

## `api581.api.damage.brittle_base`

Brittle fracture base damage table

계산 ID: `damage/brittle-base`

출처: Part 2 Tables 20.4M,20.5M; PDF pp270-271

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_thickness_m` | 예 | `<class 'float'>` |
| `cet_minus_reference_k` | 예 | `<class 'float'>` |
| `post_weld_heat_treated` | 예 | `<class 'bool'>` |
| `interpolation` | 예 | `typing.Literal['exact', 'linear']` |

출력: `base_damage_factor`, `table`

적용 범위: Printed SI grid: thickness 6.4-101.6 mm and CET-Tref -56 to 56 K. Linear mode is caller-selected bilinear interpolation of DF, not log DF. No extrapolation or service credit applied here.

## `api581.api.damage.brittle_fracture`

Brittle fracture reference/base/service calculation

계산 ID: `damage/brittle-fracture`

출처: Part 2 §20.6.3; Tables 20.3,20.4M,20.5M; eq (2.86)

| 입력 | 필수 | 타입 |
|---|---|---|
| `reference` | 예 | `<class 'api581.brittle.BrittleReference'>` |
| `service` | 예 | `<class 'api581.brittle.BrittleService'>` |
| `critical_exposure_temperature_k` | 예 | `<class 'float'>` |
| `post_weld_heat_treated` | 예 | `<class 'bool'>` |
| `interpolation` | 예 | `typing.Literal['exact', 'linear']` |

출력: `reference_temperature_k`, `table_basis`, `service_experience_factor`, `thin_component_credit`, `service_criteria`, `base_damage_factor`, `table`, `cet_minus_reference_k`, `damage_factor`

적용 범위: Caller establishes applicability, ASME curve and CET (including credited controls) per API 579. No inspection credit. Uses US reference-temperature table converted to SI plus printed SI base-DF tables. Caller selects interpolation separately for yield and base-DF grids; no extrapolation.

## `api581.api.damage.embrittlement_885f`

885 F embrittlement damage factor

계산 ID: `damage/embrittlement-885f`

출처: Part 2 §22.6.3; Table 22.3; PDF pp279-280

| 입력 | 필수 | 타입 |
|---|---|---|
| `minimum_evaluation_temperature_k` | 예 | `<class 'float'>` |
| `reference_temperature_k` | 기본값/선택 | `<class 'float'>` |
| `interpolation` | 예 | `typing.Literal['exact', 'linear']` |

출력: `reference_temperature_k`, `minimum_minus_reference_k`, `damage_factor`

적용 범위: Qualified susceptible ferritic material and evaluation temperature supplied by caller; no inspection credit. Default reference is printed 28 C (301.15 K), which is not the exact conversion of printed 80 F. Uses printed SI delta-temperature rows. Above +56 K DF=0; at +56 K DF=2. Below -56 K rejected. Linear interpolation is an explicit caller choice.

## `api581.api.damage.sigma_content`

Sigma-phase content category

계산 ID: `damage/sigma-content`

출처: Part 2 Table 23.1; PDF p284

| 입력 | 필수 | 타입 |
|---|---|---|
| `sigma_fraction` | 예 | `<class 'float'>` |

출력: `sigma_category`

적용 범위: Content >1% is tabulated: low >1 to <5%, medium >=5 to <10%, high >=10%. At or below 1% the printed categories are unresolved and rejected; no assumed zero DF.

## `api581.api.damage.sigma_embrittlement`

Sigma-phase embrittlement damage factor

계산 ID: `damage/sigma-embrittlement`

출처: Part 2 §23.6.3; Table 23.3; PDF pp283,285

| 입력 | 필수 | 타입 |
|---|---|---|
| `evaluation_temperature_k` | 예 | `<class 'float'>` |
| `sigma_category` | 예 | `typing.Literal['low', 'medium', 'high']` |
| `interpolation` | 예 | `typing.Literal['exact', 'linear']` |

출력: `damage_factor`, `sigma_category`

적용 범위: Qualified sigmatized austenitic stainless steel and content category supplied. No automatic exposure-to-sigma kinetics model or inspection credit. Printed SI evaluation-temperature grid -46 to 649 C; no extrapolation. Linear interpolation is caller-selected.

## `api581.api.damage.temper_j_factor`

Temper embrittlement composition J factor

계산 ID: `damage/temper-j-factor`

출처: Part 2 §21.2; eq (2.87); PDF p273

| 입력 | 필수 | 타입 |
|---|---|---|
| `silicon_weight_percent` | 예 | `<class 'float'>` |
| `manganese_weight_percent` | 예 | `<class 'float'>` |
| `phosphorus_weight_percent` | 예 | `<class 'float'>` |
| `tin_weight_percent` | 예 | `<class 'float'>` |

출력: `j_factor`

적용 범위: Inputs are numerical weight percentages, not 0-1 fractions. Correlation for 2.25Cr-1Mo/3Cr-1Mo susceptibility; factor alone does not determine DF. Printed eq (2.90) has an unresolved 10^4 exponent; automatic J-to-temperature-shift conversion is not enabled.

## `api581.api.damage.temper_xbar`

Temper embrittlement composition X-bar factor

계산 ID: `damage/temper-xbar`

출처: Part 2 §21.2; eq (2.88); PDF p273

| 입력 | 필수 | 타입 |
|---|---|---|
| `phosphorus_weight_percent` | 예 | `<class 'float'>` |
| `antimony_weight_percent` | 예 | `<class 'float'>` |
| `tin_weight_percent` | 예 | `<class 'float'>` |
| `arsenic_weight_percent` | 예 | `<class 'float'>` |

출력: `xbar_factor`

적용 범위: Inputs are numerical weight percentages, not fractions or ppm. Owner qualifies applicability to 1.25Cr-0.5Mo/1Cr-0.5Mo alloys.

## `api581.api.damage.temper_xbar_shift`

X-bar long-term FATT temperature shift

계산 ID: `damage/temper-xbar-shift`

출처: Part 2 §21.6.3 STEP 4(3); eq (2.91); §21.7; PDF pp274-275

| 입력 | 필수 | 타입 |
|---|---|---|
| `xbar_factor` | 예 | `<class 'float'>` |

출력: `delta_fatt_k`

적용 범위: Equation output is a Celsius temperature difference, hence numerically K, per §21.7. Negative predicted shifts are rejected; no implicit zero clipping. Long-term empirical relation; material and exposure applicability require owner qualification.

## `api581.api.damage.temper_generation_shift`

Fabrication-era conservative FATT shift

계산 ID: `damage/temper-generation-shift`

출처: Part 2 §21.6.3 STEP 4(4); PDF p274

| 입력 | 필수 | 타입 |
|---|---|---|
| `fabrication_year` | 예 | `<class 'int'>` |
| `source_basis` | 예 | `typing.Literal['printed_C', 'printed_F_difference_converted']` |

출력: `generation`, `delta_fatt_k`, `source_basis`

적용 범위: Printed paired C/F shifts are inconsistent as temperature differences. Caller must choose printed_C or printed_F_difference_converted explicitly; this choice is preserved in output. The text says after 1988 and the preceding band ends 1987: year 1988 is rejected. No pre-1965 rule.

## `api581.api.damage.temper_embrittlement`

Low-alloy temper embrittlement damage factor

계산 ID: `damage/temper-embrittlement`

출처: Part 2 §21.6.3 STEP 3-6; Tables 20.3,20.4M,20.5M; PDF pp274-275

| 입력 | 필수 | 타입 |
|---|---|---|
| `reference` | 예 | `<class 'api581.brittle.BrittleReference'>` |
| `minimum_pressurization_temperature_k` | 예 | `<class 'float'>` |
| `delta_fatt_k` | 예 | `<class 'float'>` |
| `component_thickness_m` | 예 | `<class 'float'>` |
| `post_weld_heat_treated` | 예 | `<class 'bool'>` |
| `interpolation` | 예 | `typing.Literal['exact', 'linear']` |

출력: `reference_temperature_k`, `table_basis`, `shifted_reference_temperature_k`, `minimum_minus_shifted_reference_k`, `delta_fatt_k`, `damage_factor`, `table`

적용 범위: Owner qualifies susceptible alloy/exposure and minimum pressurization temperature. Uses supplied measured/qualified delta-FATT; no automatic ambiguous SCE or J-factor shift. No service-experience reduction or inspection credit is specified in §21 STEP 6, and neither is applied. US reference table converted to SI, printed SI base-DF grids; no extrapolation.

## `api581.api.bundle.weibayes_history`

Fixed-shape bundle Weibayes life estimate

계산 ID: `bundle/weibayes-history`

출처: Part 1 §8.3.4.3; eqs (1.62)-(1.63); PDF p100

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `cycles` | 예 | `list[api581.bundle.LifeRecord]` |

출력: `shape`, `characteristic_life_years`, `failure_count`, `record_count`

적용 범위: At least two matched life records and one failure required; failures and right-censored suspensions enter the powered exposure sum. Owner qualifies unchanged design/material/service and externally selected shape. Does not fit shape, perform database matching, goodness-of-fit or Fisher confidence bounds.

## `api581.api.bundle.condition_update`

Add inspection-predicted bundle failure point

계산 ID: `bundle/condition-update`

출처: Part 1 §8.6.4(e); eqs (1.76)-(1.77); PDF pp104-105

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `cycles` | 예 | `list[api581.bundle.LifeRecord]` |
| `predicted_failure_life_years` | 예 | `<class 'float'>` |

출력: `shape`, `characteristic_life_years`, `failure_count`, `record_count`

적용 범위: Adds predicted total life as one additional failure point, including one additional failure in denominator. This is not another right-censored observation. Owner supplies qualified predicted total life; statistical confidence and additional uncertainty are separate.

## `api581.api.bundle.thickness_life`

Inspection-based tube thinning and predicted life

계산 ID: `bundle/thickness-life`

출처: Part 1 §8.6.4(c); eqs (1.71)-(1.74); PDF pp103-104

| 입력 | 필수 | 타입 |
|---|---|---|
| `original_thickness_m` | 예 | `<class 'float'>` |
| `measured_thickness_m` | 예 | `<class 'float'>` |
| `service_duration_years` | 예 | `<class 'float'>` |
| `remaining_wall_failure_fraction` | 예 | `<class 'float'>` |
| `formula_basis` | 예 | `typing.Literal['printed_eq_1_72', 'remaining_wall_threshold']` |

출력: `thinning_rate_m_year`, `predicted_bundle_life_years`, `remaining_life_years`, `remaining_wall_threshold_reached`, `formula_basis`

적용 범위: General corrosion and average tube thickness only. Printed eq (1.72) uses RWT*t_original/rate although RWT is described as remaining wall fraction; a physical threshold extrapolation uses (1-RWT)*t_original/rate. Caller must select basis explicitly. Both agree for the printed 0.5 example. Zero measured loss gives no finite extrapolated life, not a manufactured failure point.

## `api581.api.bundle.estimated_life`

Predicted bundle life from estimated remaining life

계산 ID: `bundle/estimated-life`

출처: Part 1 §8.6.4(d); eq (1.75); PDF p104

| 입력 | 필수 | 타입 |
|---|---|---|
| `service_duration_years` | 예 | `<class 'float'>` |
| `estimated_remaining_life_years` | 예 | `<class 'float'>` |

출력: `predicted_bundle_life_years`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.bundle.life_extension`

Effective bundle age after life-extension action

계산 ID: `bundle/life-extension`

출처: Part 1 §8.6.5; eqs (1.79)-(1.81); PDF p105

| 입력 | 필수 | 타입 |
|---|---|---|
| `age_at_action_years` | 예 | `<class 'float'>` |
| `life_extension_factor` | 예 | `<class 'float'>` |
| `years_since_action` | 기본값/선택 | `<class 'float'>` |

출력: `adjusted_age_at_action_years`, `effective_age_years`, `installation_shift_years`

적용 범위: Owner supplies qualified LEF. Returns effective age rather than imposing a date/day-count convention. Original age is not reset by an ordinary inspection or cleaning; apply only after a qualifying life-extension action.

## `api581.api.bundle.consequence`

Bundle failure or planned replacement financial consequence

계산 ID: `bundle/consequence`

출처: Part 1 §8.4.1; eqs (1.64)-(1.67), (1.88); PDF pp100-101,107

| 입력 | 필수 | 타입 |
|---|---|---|
| `daily_production_margin` | 예 | `<class 'float'>` |
| `production_rate_reduction_fraction` | 예 | `<class 'float'>` |
| `shutdown_days` | 예 | `<class 'float'>` |
| `environmental_cost` | 예 | `<class 'float'>` |
| `replacement_cost` | 예 | `<class 'float'>` |
| `maintenance_cost` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |

출력: `production_loss_cost`, `financial_consequence`, `currency`, `cost_basis_year`

적용 범위: All monetary inputs must share declared currency and price year. Caller explicitly chooses planned or unplanned shutdown duration and environmental cost. No silent historical environmental default or inflation assumption.

## `api581.api.bundle.risk`

Bundle unreliability-weighted consequence

계산 ID: `bundle/risk`

출처: Part 1 §8.5; eq (1.68); PDF p101

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `characteristic_life_years` | 예 | `<class 'float'>` |
| `age_years` | 예 | `<class 'float'>` |
| `financial_consequence` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `cumulative_failure_probability`, `probability_weighted_consequence`, `currency`

적용 범위: Weibull cumulative probability times consequence. Despite source annual-risk terminology, this product is a probability-weighted monetary amount at age, not an instantaneous annual failure-frequency risk. No confidence-bound/inspection-uncertainty shift is inferred.

## `api581.api.bundle.target_age`

Bundle age at owner probability-weighted risk target

계산 ID: `bundle/target-age`

출처: Part 1 §8.6.1; eqs (1.57),(1.69)-(1.70); PDF pp97,102

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `characteristic_life_years` | 예 | `<class 'float'>` |
| `target_probability_weighted_consequence` | 예 | `<class 'float'>` |
| `financial_consequence` | 예 | `<class 'float'>` |

출력: `target_failure_probability`, `target_age_years`, `status`

적용 범위: Uses an explicitly supplied target on the same probability-weighted consequence basis as bundle/risk. Target >= consequence has no finite crossing. Owner must supply any confidence-bound/uncertainty-adjusted Weibull parameters; raw parameters are not automatically treated as 90% LBC.

## `api581.api.bundle.deferral_decision`

Conditional incremental risk and inspection/replacement economics

계산 ID: `bundle/deferral-decision`

출처: Part 1 §8.7.2; eqs (1.82)-(1.84); PDF p106

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `characteristic_life_years` | 예 | `<class 'float'>` |
| `first_turnaround_age_years` | 예 | `<class 'float'>` |
| `second_turnaround_age_years` | 예 | `<class 'float'>` |
| `financial_consequence` | 예 | `<class 'float'>` |
| `inspection_cost` | 예 | `<class 'float'>` |
| `replacement_cost` | 예 | `<class 'float'>` |
| `maintenance_cost` | 예 | `<class 'float'>` |
| `hurdle_rate` | 기본값/선택 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `conditional_failure_probability`, `expected_incremental_risk`, `inspection_hurdle_cost`, `replacement_hurdle_cost`, `inspection_economically_justified`, `replacement_economically_justified`, `currency`

적용 범위: Conditioned on survival to first turnaround; uses survival ratio, not the difference of unconditional CDFs. Source prose reverses action-cost inequality; explicit eqs (1.83)-(1.84) are followed: action cost*(1+ROR) < EIR. Both economic flags may be true; this is not an exclusive inspection plan.

## `api581.api.bundle.replacement_optimization`

Bundle planned-replacement grid cost optimization

계산 ID: `bundle/replacement-optimization`

출처: Part 1 §8.7.4; eqs (1.85)-(1.93); PDF pp107-109

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `characteristic_life_years` | 예 | `<class 'float'>` |
| `unplanned_failure_consequence` | 예 | `<class 'float'>` |
| `planned_replacement_consequence` | 예 | `<class 'float'>` |
| `step_days` | 기본값/선택 | `<class 'float'>` |
| `maximum_replacement_age_years` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |

출력: `optimal_grid_age_years`, `minimum_cost_per_day`, `minimum_at_grid_boundary`, `grid_points`, `samples`, `currency`

적용 범위: Source right-endpoint failure-life integration on uniform grid; days/year=365.24. Global minimum is over supplied finite grid only, not an unbounded certified optimum. Boundary minima are flagged. No confidence bounds, cost inflation or automatic inspection effects. Grid limited to 10000 points.

## `api581.api.bundle.material_factor`

Bundle replacement material cost factor

계산 ID: `bundle/material-factor`

출처: Part 1 Table8.3; PDF pp119-120

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `<class 'str'>` |

출력: `material_factor`

적용 범위: Historical generic bundle factors, not current quotations or the fixed-equipment material factors. Caller may supply a different qualified factor directly to replacement-cost.

## `api581.api.bundle.replacement_cost`

Volume/material-scaled bundle replacement cost

계산 ID: `bundle/replacement-cost`

출처: Part 1 §8.4.1; eq (1.66); PDF p101

| 입력 | 필수 | 타입 |
|---|---|---|
| `shell_inside_diameter_m` | 예 | `<class 'float'>` |
| `tube_length_m` | 예 | `<class 'float'>` |
| `material_factor` | 예 | `<class 'float'>` |
| `reference_bundle_cost_usd` | 기본값/선택 | `<class 'float'>` |
| `price_index_multiplier` | 예 | `<class 'float'>` |
| `output_currency_per_usd` | 예 | `<class 'float'>` |
| `output_currency` | 예 | `<class 'str'>` |
| `output_cost_basis_year` | 예 | `<class 'int'>` |

출력: `bundle_volume_m3`, `reference_basis_cost_usd`, `replacement_cost`, `currency`, `cost_basis_year`

적용 범위: Printed reference volume 3.016 m3 and default reference quote USD22000. Reference quote date is not inferred from edition year; caller supplies qualified price-index multiplier and FX to declared output price year/currency. This is a size/material estimate, not a vendor quote.

## `api581.api.bundle.life_extension_factor`

Suggested bundle life-extension action factor

계산 ID: `bundle/life-extension-factor`

출처: Part 1 Table8.5 Effects of Bundle Life Extension Methods; PDF p121

| 입력 | 필수 | 타입 |
|---|---|---|
| `method` | 예 | `typing.Literal['plug_tubes', 'rotate_180', 'partial_retube', 'total_retube', 'install_spare', 'tube_ferrules']` |
| `ferrules_for_localized_tube_end_damage` | 기본값/선택 | `<class 'bool'>` |

출력: `life_extension_factor`

적용 범위: This is the second table numbered8.5; inspection uncertainty is a different table. Suggested values need owner qualification. Spare factor .5 assumes unknown condition. Ferrules .75 only for localized tube-end erosion/corrosion/impingement protection.

## `api581.api.bundle.categories`

Bundle probability and financial consequence categories

계산 ID: `bundle/categories`

출처: Part 1 Table8.6; PDF p121

| 입력 | 필수 | 타입 |
|---|---|---|
| `cumulative_failure_probability` | 예 | `<class 'float'>` |
| `financial_consequence_usd` | 예 | `<class 'float'>` |
| `consequence_basis` | 예 | `typing.Literal['printed_table_USD_basis']` |

출력: `probability_category`, `consequence_category`

적용 범위: Uses displayed probability and financial-USD thresholds, not inconsistent DF/area footnotes. Caller explicitly declares consequence on printed USD basis; no automatic present-value inflation or FX normalization. Returns categories only; owner risk-color matrix is separate.

## `api581.api.prd.default_weibull`

PRD default Weibull parameters and design modifiers

계산 ID: `prd/default-weibull`

출처: Part 1 Tables 7.5,7.12; §7.2.4(g),§7.3.2(g); PDF pp53,62,83,87

| 입력 | 필수 | 타입 |
|---|---|---|
| `device_type` | 예 | `typing.Literal['conventional', 'balanced_bellows', 'pilot_operated', 'rupture_disk']` |
| `failure_mode` | 예 | `typing.Literal['fail_to_open', 'leak']` |
| `severity` | 예 | `typing.Literal['mild', 'moderate', 'severe']` |
| `closed_system_or_flare` | 기본값/선택 | `<class 'bool'>` |
| `soft_seated` | 기본값/선택 | `<class 'bool'>` |

출력: `shape`, `default_characteristic_life_years`, `design_factor`, `design_adjusted_characteristic_life_years`

적용 범위: Owner selects severity independently for FAIL and LEAK. Uses printed rounded pilot-operated eta (33.7,8.0,3.5), not another division of these entries. Closed-system factor .75 applies only to conventional FAIL; soft-seat factor 1.25 only to conventional/balanced LEAK. Environmental and inspection adjustments are separate.

## `api581.api.prd.environment_factor`

PRD environmental characteristic-life modifier

계산 ID: `prd/environment-factor`

출처: Part 1 Table 7.6; PDF p83

| 입력 | 필수 | 타입 |
|---|---|---|
| `device_type` | 예 | `typing.Literal['conventional', 'balanced_bellows', 'pilot_operated', 'rupture_disk']` |
| `failure_mode` | 예 | `typing.Literal['fail_to_open', 'leak']` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `operating_to_set_pressure_ratio` | 예 | `<class 'float'>` |
| `installed_piping_vibration` | 예 | `<class 'bool'>` |
| `pulsating_or_cyclic_service` | 예 | `<class 'bool'>` |
| `actuations_per_year` | 예 | `<class 'float'>` |
| `history_of_chatter` | 예 | `<class 'bool'>` |
| `qualified_pilot_high_ratio_exception` | 기본값/선택 | `<class 'bool'>` |

출력: `environment_factor`, `individual_factors`

적용 범위: Products of applicable modifiers. LEAK excessive-actuation modifier is not reapplied when operating-ratio modifier applies (Table7.6 note2). Pilot high-ratio exception must be explicitly qualified. Printed strict 200<T<500 F and T>500 F leave exactly 500 F unresolved for LEAK; it is rejected. FAIL does not use temperature/ratio/vibration/cyclic factors.

## `api581.api.prd.set_pressure_factor`

PRD leakage set-pressure probability modifier

계산 ID: `prd/set-pressure-factor`

출처: Part 1 Table 7.7; eq (1.36); PDF pp61,84

| 입력 | 필수 | 타입 |
|---|---|---|
| `device_type` | 예 | `typing.Literal['conventional', 'balanced_bellows', 'pilot_operated', 'rupture_disk']` |
| `operating_to_set_pressure_ratio` | 예 | `<class 'float'>` |

출력: `set_pressure_factor`

적용 범위: Pressure ratio supplied on a consistent pressure basis. Applies to leakage probability after Weibull evaluation, not to eta. Rupture-disk factor=1.

## `api581.api.prd.overpressure_factor`

PRD fail-to-open overpressure modifier

계산 ID: `prd/overpressure-factor`

출처: Part 1 §7.2.4(j); eq (1.31); PDF pp57-58

| 입력 | 필수 | 타입 |
|---|---|---|
| `overpressure_to_set_pressure_ratio` | 예 | `<class 'float'>` |

출력: `overpressure_factor`

적용 범위: Primitive or utility calculation with no additional clause-specific limitation; caller must qualify API 581 applicability, input basis and engineering use.

## `api581.api.prd.demand_rate`

PRD case and total demand rates

계산 ID: `prd/demand-rate`

출처: Part 1 §7.2.3; eqs (1.12)-(1.13); PDF p50

| 입력 | 필수 | 타입 |
|---|---|---|
| `cases` | 예 | `list[api581.prd.DemandCase]` |

출력: `case_demand_rates_per_year`, `total_demand_rate_per_year`

적용 범위: Reduction factor is the residual fraction multiplying initiating frequency, not its reciprocal. Owner qualifies independent demand cases and LOPA credits; defaults/automatic relief-design basis are not inferred.

## `api581.api.prd.inspection_update`

PRD single inspection characteristic-life update

계산 ID: `prd/inspection-update`

출처: Part 1 §7.2.4(i); eqs (1.17)-(1.21); Tables7.8,7.9; PDF pp54-57,84

| 입력 | 필수 | 타입 |
|---|---|---|
| `shape` | 예 | `<class 'float'>` |
| `prior_characteristic_life_years` | 예 | `<class 'float'>` |
| `duration_years` | 예 | `<class 'float'>` |
| `effectiveness` | 예 | `typing.Literal['ineffective', 'fairly', 'usually', 'highly']` |
| `result` | 예 | `typing.Literal['pass', 'fail', 'no_leak', 'leak']` |
| `piping_plugged` | 기본값/선택 | `<class 'bool'>` |

출력: `prior_failure_probability`, `conditional_failure_probability`, `weighted_failure_probability`, `updated_characteristic_life_years`, `update_applied`, `effective_failed_result`

적용 범위: Implements printed eq (1.20), including CF_pass in its second term. Ineffective tests and durations<1 year get no update. Pass/no-leak cannot reduce eta, fail/leak cannot increase eta. Plugged piping overrides pass to fail. Caller sequences records and handles overhaul/as-new date and invalidation after design change. Invalid weighted probability is rejected, not clipped.

## `api581.api.prd.protected_equipment`

Protected equipment overpressure loss-of-containment model

계산 ID: `prd/protected-equipment`

출처: Part 1 §7.2.5; eqs (1.32)-(1.33); PDF p58

| 입력 | 필수 | 타입 |
|---|---|---|
| `generic_frequencies_per_year` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `management_factor` | 예 | `<class 'float'>` |
| `overpressure_to_mawp_ratio` | 예 | `<class 'float'>` |

출력: `normal_failure_frequency_per_year`, `source_model_loc_probability`, `by_hole_loc_probability`

적용 범위: Uses normal damage-adjusted frequency at pressure<=MAWP; above MAWP applies printed exponential and caps source-model probability at1. Source mixes annual-frequency/probability terms; returned source_model_loc_probability follows the published model, not a Poisson conversion. Caller supplies DF at evaluation time and all four GFF holes.

## `api581.api.prd.fail_frequency`

PRD fail-to-open loss-of-containment scenario frequency

계산 ID: `prd/fail-frequency`

출처: Part 1 §7.2.2; eq (1.11); PDF p49

| 입력 | 필수 | 타입 |
|---|---|---|
| `failure_on_demand_probability` | 예 | `<class 'float'>` |
| `demand_rate_per_year` | 예 | `<class 'float'>` |
| `protected_equipment_loc_probability` | 예 | `<class 'float'>` |

출력: `annual_failure_frequency`

적용 범위: One demand case: multiplies scenario-adjusted POFOD, demand rate and protected-equipment LOC model probability. Sum only justified distinct scenarios; dependencies and common-cause effects require owner analysis.

## `api581.api.prd.base_reliability`

PRD default/design/environment/scenario probability

계산 ID: `prd/base-reliability`

출처: Part 1 eqs (1.14)-(1.16),(1.34)-(1.36); Tables7.5-7.7,7.12

| 입력 | 필수 | 타입 |
|---|---|---|
| `defaults` | 예 | `<class 'api581.prd.PrdDefaults'>` |
| `environment` | 예 | `<class 'api581.prd.PrdEnvironment'>` |
| `age_years` | 예 | `<class 'float'>` |
| `overpressure_to_set_pressure_ratio` | 기본값/선택 | `<class 'float'>` |

출력: `shape`, `modified_characteristic_life_years`, `environment_factor`, `scenario_probability_factor`, `unadjusted_cumulative_probability`, `scenario_adjusted_probability`

적용 범위: Uninspected/default reliability path only; no implicit inspection history. Computes cumulative Weibull probability at age and applies Fop for FAIL or Fset for LEAK. LEAK result is not automatically reinterpreted as an instantaneous annual frequency. Caller supplies qualified severity, environmental and pressure inputs.

## `api581.api.prd.leakage_rates`

PRD minor/moderate/combined/stuck-open leakage rates

계산 ID: `prd/leakage-rates`

출처: Part 1 §7.5.2; eqs(1.40)-(1.41); Table7.15; PDF pp66,88

| 입력 | 필수 | 타입 |
|---|---|---|
| `operating_capacity_kg_s` | 예 | `<class 'float'>` |

출력: `minor_rate_kg_s`, `moderate_table_rate_kg_s`, `mild_moderate_equation_rate_kg_s`, `stuck_open_rate_kg_s`

적용 범위: Capacity must be evaluated at normal operating conditions, not silently copied from a relief-condition rating. Eq(1.40) uses 1% for combined mild/moderate; Table7.15 uses 1% minor and 10% moderate. Both are returned explicitly. API520 capacity sizing is not implemented here.

## `api581.api.prd.leakage_duration`

PRD size/discharge leakage duration

계산 ID: `prd/leakage-duration`

출처: Part 1 Table7.14; eq(1.42); PDF pp67,88

| 입력 | 필수 | 타입 |
|---|---|---|
| `inlet_size_nps` | 예 | `<class 'float'>` |
| `discharge` | 예 | `typing.Literal['atmosphere', 'flare', 'closed_system']` |

출력: `mild_moderate_duration_s`, `stuck_open_duration_s`

적용 범위: NPS is a nominal inlet designation, not a measured diameter in metres. Table duration days are converted exactly to seconds (including printed .33 days). Stuck-open duration uses exact30 minutes=1800s, not rounded .021 days.

## `api581.api.prd.inventory_loss_factor`

PRD residual inventory loss factor after recovery

계산 ID: `prd/inventory-loss-factor`

출처: Part 1 §7.5.4; PDF p67

| 입력 | 필수 | 타입 |
|---|---|---|
| `discharge` | 예 | `typing.Literal['atmosphere', 'flare', 'closed_system']` |
| `flare_recovery_installed` | 기본값/선택 | `<class 'bool'>` |

출력: `inventory_loss_factor`

적용 범위: Factor Fr multiplies lost-inventory cost: closed system0, flare with recovery .5, otherwise1. It does not reduce physical leaked mass or environmental/repair/production costs.

## `api581.api.prd.inventory_loss`

PRD leakage inventory mass and financial loss

계산 ID: `prd/inventory-loss`

출처: Part 1 §7.5.5; eqs(1.43)-(1.44); PDF p67

| 입력 | 필수 | 타입 |
|---|---|---|
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `leakage_rate_kg_s` | 예 | `<class 'float'>` |
| `duration_s` | 예 | `<class 'float'>` |
| `fluid_cost_per_kg` | 예 | `<class 'float'>` |
| `inventory_loss_factor` | 예 | `<class 'float'>` |

출력: `leaked_mass_kg`, `inventory_loss_equivalent_mass_kg`, `inventory_loss_cost`, `currency`, `cost_basis_year`

적용 범위: SI mass rate kg/s times seconds replaces source hourly-rate/day factor24. Fluid value must correspond to the protected equipment at the PRD location. Constant supplied operating-capacity leak; no automatic finite inventory/supply limit.

## `api581.api.prd.repair_cost`

PRD reference repair quote adjusted to declared price basis

계산 ID: `prd/repair-cost`

출처: Part 1 §7.5.7; PDF p67

| 입력 | 필수 | 타입 |
|---|---|---|
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `inlet_size_nps` | 예 | `<class 'float'>` |
| `price_index_multiplier` | 예 | `<class 'float'>` |
| `output_currency_per_usd` | 예 | `<class 'float'>` |

출력: `reference_cost_usd`, `repair_cost`, `currency`, `cost_basis_year`

적용 범위: Printed reference USD1000 below NPS6, USD2000 at/above NPS6. Price quote year is not inferred from edition year; explicit owner-qualified price index and FX required. Actual work-order cost is preferred and can be supplied directly to leakage-consequence.

## `api581.api.prd.production_loss`

PRD leakage shutdown production loss

계산 ID: `prd/production-loss`

출처: Part 1 §7.5.8; eqs(1.45)-(1.47); PDF pp67-68

| 입력 | 필수 | 타입 |
|---|---|---|
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `daily_production_margin` | 예 | `<class 'float'>` |
| `shutdown_duration_days` | 예 | `<class 'float'>` |
| `leak_case` | 예 | `typing.Literal['mild_moderate', 'stuck_open']` |
| `mild_leak_tolerated_or_online_repair` | 예 | `<class 'bool'>` |

출력: `production_loss_cost`, `shutdown_loss_applied`, `currency`, `cost_basis_year`

적용 범위: Mild/moderate leak tolerated or isolated/repaired online has zero production loss. Stuck-open case uses shutdown loss per eq(1.47). Caller supplies actual shutdown duration and production margin, including any qualified zero-duration repair.

## `api581.api.prd.leakage_consequence`

PRD two/three-case leakage financial consequence

계산 ID: `prd/leakage-consequence`

출처: Part 1 §7.5.10; eqs(1.39)-(1.50); Tables7.14,7.15; PDF pp66-69,88

| 입력 | 필수 | 타입 |
|---|---|---|
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `operating_capacity_kg_s` | 예 | `<class 'float'>` |
| `inlet_size_nps` | 예 | `<class 'float'>` |
| `discharge` | 예 | `typing.Literal['atmosphere', 'flare', 'closed_system']` |
| `flare_recovery_installed` | 기본값/선택 | `<class 'bool'>` |
| `fluid_cost_per_kg` | 예 | `<class 'float'>` |
| `environmental_cost` | 예 | `<class 'float'>` |
| `repair_cost` | 예 | `<class 'float'>` |
| `daily_production_margin` | 예 | `<class 'float'>` |
| `shutdown_duration_days` | 예 | `<class 'float'>` |
| `mild_leak_tolerated_or_online_repair` | 예 | `<class 'bool'>` |
| `model_basis` | 예 | `typing.Literal['two_case_equations', 'three_case_table_7_15']` |

출력: `financial_consequence`, `case_weights`, `costs_by_case`, `inventory_loss_factor`, `model_basis`, `currency`, `cost_basis_year`

적용 범위: Caller explicitly selects two_case_equations (.9 at1% capacity + .1 stuck at25%) or three_case_table_7_15 (.5 at1%, .4 at10%, .1 at25%) because source rates conflict. Non-stuck cases share Table7.14 duration. Environmental and repair costs are common conditional case costs as printed. All monetary inputs share declared currency/year; no automatic price-year inference or supply/inventory cap.

## `api581.api.prd.multiple_device_pressure`

Multiple PRD area-based protected-equipment pressure adjustment

계산 ID: `prd/multiple-device-pressure`

출처: Part 1 §7.4.4; eqs(1.37)-(1.38); PDF pp64-65

| 입력 | 필수 | 타입 |
|---|---|---|
| `analyzed_orifice_area_m2` | 예 | `<class 'float'>` |
| `total_installed_orifice_area_m2` | 예 | `<class 'float'>` |
| `scenario_pressure_pa_gauge` | 예 | `<class 'float'>` |

출력: `multiple_device_factor`, `protected_equipment_pressure_pa_gauge`, `unreduced_pressure_for_fop_pa_gauge`

적용 범위: Total installed area includes analyzed PRD. Fa=max(.25,sqrt(Aprd/Atotal)). Reduced pressure is used for protected-equipment LOC and consequence calculations only; original scenario pressure must be retained for Fop (PRD POFOD). Source square-root approximation is not an independent parallel-failure probability or a capacity-design verification.

## `api581.api.prd.fail_risk`

PRD fail-to-open case sum and protected-equipment maximum risk

계산 ID: `prd/fail-risk`

출처: Part 1 §7.6.1; eqs(1.51)-(1.52); PDF p69

| 입력 | 필수 | 타입 |
|---|---|---|
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `protected_equipment` | 예 | `list[api581.prd_consequences.ProtectedRisk]` |

출력: `protected_equipment_risks_per_year`, `maximum_fail_risk_per_year`, `governing_equipment_ids`, `currency`, `cost_basis_year`

적용 범위: Within each protected item, sum distinct demand-case frequency*conditional consequence. Then take maximum across protected items as prescribed, not their sum. Caller supplies qualified case frequencies and pressure-dependent COF; currency/year must be common.

## `api581.api.prd.leakage_risk`

PRD leakage consequence weighted by declared probability/frequency basis

계산 ID: `prd/leakage-risk`

출처: Part 1 §7.6.2; eq(1.53); PDF p69

| 입력 | 필수 | 타입 |
|---|---|---|
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `leakage_measure` | 예 | `<class 'float'>` |
| `financial_consequence` | 예 | `<class 'float'>` |
| `measure_basis` | 예 | `typing.Literal['annual_frequency', 'source_cumulative_probability']` |

출력: `leakage_risk_value`, `measure_basis`, `risk_unit`, `currency`, `cost_basis_year`

적용 범위: Source multiplies leakage Weibull cumulative probability by consequence but uses annual-risk terminology. Basis must be explicit: source_cumulative_probability gives monetary probability-weighted consequence; annual_frequency requires an independently qualified annual event frequency. No silent CDF annualization.

## `api581.api.prd.total_risk`

PRD combined risk with explicit dimensional basis

계산 ID: `prd/total-risk`

출처: Part 1 §7.6.3; eq(1.54); PDF p69

| 입력 | 필수 | 타입 |
|---|---|---|
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `fail_risk_per_year` | 예 | `<class 'float'>` |
| `leakage_risk_value` | 예 | `<class 'float'>` |
| `leakage_measure_basis` | 예 | `typing.Literal['annual_frequency', 'source_cumulative_probability']` |

출력: `annual_financial_risk`, `source_total_risk_index`, `leakage_measure_basis`, `currency`, `cost_basis_year`

적용 범위: Annual leakage-frequency basis permits an annual total. Source cumulative-probability basis reproduces printed addition only as source_total_risk_index and leaves annual_financial_risk unset, because summands have inconsistent dimensions. Source index must not be presented as a certified monetary annual rate.

## `api581.api.prd.risk_assessment`

Compose protected-item fail risk and PRD leakage risk

계산 ID: `prd/risk-assessment`

출처: Part 1 §7.6.4; eqs(1.51)-(1.54); PDF pp69-70

| 입력 | 필수 | 타입 |
|---|---|---|
| `currency` | 예 | `<class 'str'>` |
| `cost_basis_year` | 예 | `<class 'int'>` |
| `protected_equipment` | 예 | `list[api581.prd_consequences.ProtectedRisk]` |
| `leakage_measure` | 예 | `<class 'float'>` |
| `leakage_financial_consequence` | 예 | `<class 'float'>` |
| `leakage_measure_basis` | 예 | `typing.Literal['annual_frequency', 'source_cumulative_probability']` |

출력: `protected_equipment_risks_per_year`, `maximum_fail_risk_per_year`, `governing_equipment_ids`, `currency`, `cost_basis_year`, `annual_financial_risk`, `source_total_risk_index`, `leakage_measure_basis`, `leakage_risk_value`, `leakage_risk_unit`

적용 범위: Integration over supplied case frequencies, protected-item conditional consequences and leakage measure/consequence. It does not automatically derive complete relief design or COF. Fail risk takes max across protected items. Cumulative leakage basis yields source index only; annual total requires qualified leakage annual frequency.

## `api581.api.prd.service_age`

PRD as-new service age and valid-history start boundary

계산 ID: `prd/service-age`

출처: Part 1 §7.1.6, §7.2.4(i)(5), §7.7.2-7.7.3; PDF pp48,57,70

| 입력 | 필수 | 타입 |
|---|---|---|
| `installation_date` | 예 | `<class 'datetime.date'>` |
| `evaluation_date` | 예 | `<class 'datetime.date'>` |
| `events` | 기본값/선택 | `list[api581.prd_history.ServiceEvent]` |
| `days_per_year` | 기본값/선택 | `<class 'float'>` |

출력: `effective_age_years`, `elapsed_since_original_installation_years`, `last_age_reset_date`, `last_age_reset_type`, `parameter_history_valid_from_date`, `inspection_update_start_date`, `last_test_date`, `days_per_year`

적용 범위: Overhaul/replacement reset effective age; test alone does not. Replacement/design change invalidate earlier parameter-updating history. Inspection update window starts at later of last as-new reset and parameter-history validity boundary per §7.2.6 STEP6.4. Design change alone does not assert an as-new condition. Dates/age only, not automatic test/eta updating or new-curve qualification. Default365.25-day year is an explicit engineering calendar convention, not a claimed source mandate. Same-day ordered events are allowed.

## `api581.api.level1.type1_flammable_area`

Type1 single-effect flammable consequence area

계산 ID: `level1/type1-flammable-area`

출처: Part 3 §4.1.5(b),§4.8.4,§4.8.8; Tables4.8M,4.9M; PDF pp484,492,522,524

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['Aromatics', 'Styrene', 'CO', 'DEE', 'Methanol', 'PO', 'EEA', 'EE', 'EG', 'EO']` |
| `release_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `effect` | 예 | `typing.Literal['equipment', 'personnel']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `autoignition` | 예 | `typing.Literal['not_likely', 'likely']` |
| `adjusted_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `mitigation_fraction` | 예 | `<class 'float'>` |

출력: `area_m2`, `coefficient_a`, `coefficient_b`, `energy_efficiency_factor`

적용 범위: Ten Type1 flammable fluids. Caller selects phase, release type and AINL/AIL branch; no Type0 IC or AIT blending. Instantaneous energy correction follows STEP8.2 and §4.8.4. Blank cells are rejected, printed zero retained. Equipment/personnel are callable separately when only one source cell exists.

## `api581.api.level1.type1_flammable_consequence`

Type1 equipment and personnel flammable areas

계산 ID: `level1/type1-flammable-consequence`

출처: Part 3 §4.1.5(b),§4.8.8; Tables4.8M,4.9M

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['Aromatics', 'Styrene', 'CO', 'DEE', 'Methanol', 'PO', 'EEA', 'EE', 'EG', 'EO']` |
| `release_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `autoignition` | 예 | `typing.Literal['not_likely', 'likely']` |
| `adjusted_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `mitigation_fraction` | 예 | `<class 'float'>` |

출력: `equipment_area_m2`, `personnel_area_m2`, `energy_efficiency_factor`, `fluid_type`

적용 범위: Unblended Type1 branch selected explicitly by caller. Requires populated equipment and personnel cells; use type1-flammable-area to query just one effect. Energy/mitigation applied once; coefficients already incorporate event probabilities.

## `api581.api.level1.release_to_type1_flammable`

Compose controlled release and Type1 flammable consequence

계산 ID: `level1/release-to-type1-flammable`

출처: Part 3 §§4.3-4.8; §4.1.5(b)

| 입력 | 필수 | 타입 |
|---|---|---|
| `source` | 예 | `api581.release.Gas | api581.release.Liquid` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `component_mass_kg` | 예 | `<class 'float'>` |
| `inventory_group_mass_kg` | 예 | `<class 'float'>` |
| `detection` | 예 | `typing.Literal['A', 'B', 'C']` |
| `isolation` | 예 | `typing.Literal['A', 'B', 'C']` |
| `duration_hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `rupture_maximum_duration_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `fluid` | 예 | `typing.Literal['Aromatics', 'Styrene', 'CO', 'DEE', 'Methanol', 'PO', 'EEA', 'EE', 'EG', 'EO']` |
| `final_release_phase` | 예 | `typing.Literal['gas', 'liquid']` |
| `autoignition` | 예 | `typing.Literal['not_likely', 'likely']` |
| `mitigation_fraction` | 예 | `<class 'float'>` |

출력: `theoretical_rate_kg_s`, `available_mass_kg`, `release_type`, `reduction_fraction`, `maximum_duration_s`, `adjusted_rate_kg_s`, `duration_s`, `released_mass_kg`, `equipment_area_m2`, `personnel_area_m2`, `energy_efficiency_factor`, `fluid_type`

적용 범위: Single qualified hole. Uses gas/liquid source, inventory and detection/isolation duration; Type1 phase/AIT branch is caller-qualified. No Type0 blending. Toxic/financial/other-hole aggregation remain separate composable functions.

## `api581.api.properties.water_partial_pressure`

Water partial pressure for radiation attenuation

계산 ID: `properties/water-partial-pressure`

출처: Part3 eq(3.141), Annex3.B C20/C21; PDF pp552,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `ambient_temperature_k` | 예 | `<class 'float'>` |
| `relative_humidity_fraction` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |

출력: `water_partial_pressure_pa`

적용 범위: Uses printed1.013kPa,5328K and14.4114. RH in this equation is percent; public fraction is multiplied by100. Rejects pressure above declared ambient pressure. Empirical ambient correlation, not a general steam/ice or cryogenic property solver.

## `api581.api.effects.atmospheric_transmissivity`

Water-vapor thermal-radiation transmissivity

계산 ID: `effects/atmospheric-transmissivity`

출처: Part3 eq(3.140), Annex3.B C19; PDF pp552,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `water_partial_pressure_pa` | 예 | `<class 'float'>` |
| `path_length_m` | 예 | `<class 'float'>` |

출력: `transmissivity`, `uncapped_transmissivity`, `dry_air_limit`

적용 범위: Equation exponent-.09 and C19=1.085 with pressure in kPa. Annex dimensional exponent.092 differs; equation exponent followed. Capped at physical maximum1. At zero water pressure uses limiting tau=1 and reports no finite uncapped value.

## `api581.api.effects.pool_mixture_burning_rate`

Mole-weighted liquid-mixture pool burning rate

계산 ID: `effects/pool-mixture-burning-rate`

출처: Part3 eq(3.130); PDF p550

| 입력 | 필수 | 타입 |
|---|---|---|
| `components` | 예 | `list[api581.pool_fire.MixtureComponent]` |

출력: `burning_rate_kg_m2_s`

적용 범위: Source mole-fraction weighting of supplied component burning rates; not a mixture thermodynamic or unignited evaporation model. Fractions must sum to1 and are not silently normalized.

## `api581.api.effects.pool_flame_geometry`

Thomas pool flame length and wind tilt

계산 ID: `effects/pool-flame-geometry`

출처: Part3 eqs(3.135)-(3.137); PDF p551

| 입력 | 필수 | 타입 |
|---|---|---|
| `pool_radius_m` | 예 | `<class 'float'>` |
| `burning_rate_kg_m2_s` | 예 | `<class 'float'>` |
| `air_density_kg_m3` | 예 | `<class 'float'>` |
| `vapor_density_kg_m3` | 예 | `<class 'float'>` |
| `wind_speed_m_s` | 예 | `<class 'float'>` |
| `gravity_m_s2` | 기본값/선택 | `<class 'float'>` |

출력: `nondimensional_wind_speed`, `flame_length_m`, `flame_tilt_rad`, `vertical_flame_height_m`, `downwind_axis_extension_m`

적용 범위: Air density enters Thomas length; vapor density enters nondimensional wind (not interchangeable). Wind must be qualified at source reference height6ft above grade. Printed powers.67,.333,-.21 followed. No automatic wind-height conversion or LH2 validation.

## `api581.api.effects.pool_surface_emissive_power`

Pool flame surface emissive power

계산 ID: `effects/pool-surface-emissive-power`

출처: Part3 eq(3.138); PDF p551

| 입력 | 필수 | 타입 |
|---|---|---|
| `pool_radius_m` | 예 | `<class 'float'>` |
| `flame_length_m` | 예 | `<class 'float'>` |
| `burning_rate_kg_m2_s` | 예 | `<class 'float'>` |
| `heat_of_combustion_j_kg` | 예 | `<class 'float'>` |
| `radiative_fraction` | 기본값/선택 | `<class 'float'>` |

출력: `burning_mass_rate_kg_s`, `radiated_power_w`, `emitting_surface_area_m2`, `surface_emissive_power_w_m2`

적용 범위: Surface emissive power W/m2, not total radiated power W. Uses printed cylindrical side-plus-top area2*pi*R*L+pi*R^2. Uniform emissive surface; no smoke shielding or fuel-specific emissivity model.

## `api581.api.effects.pool_cylinder_view_factor`

Pool cylinder vertical/horizontal/maximum view factors

계산 ID: `effects/pool-cylinder-view-factor`

출처: Part3 eqs(3.142)-(3.149); PDF pp552-553; Independent oblique-cylinder surface integral: docs/POOL_RADIATION_VALIDATION.md

| 입력 | 필수 | 타입 |
|---|---|---|
| `length_radius_ratio` | 예 | `<class 'float'>` |
| `distance_radius_ratio` | 예 | `<class 'float'>` |
| `flame_tilt_rad` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'geometry_checked']` |

출력: `vertical_view_factor`, `horizontal_view_factor`, `maximum_view_factor`, `physical_range`, `equation_basis`

적용 범위: Printed2016 Fv has atan(q), not atan(sqrt(q)), and numerator2Y(1+sin(theta)), not2Y(1+Xsin(theta)). api581_printed reproduces these; geometry_checked makes the two explicit changes verified against independent side-surface integration. Not an authorized standard erratum. Requires Y>1+Xsin(theta), outside downwind flame projection. Ground target in tilt plane; uniform side emission. Physical-range flag must be checked before flux use.

## `api581.api.effects.pool_radiation_flux`

Pool thermal radiation at a specified surface separation

계산 ID: `effects/pool-radiation-flux`

출처: Part3 eqs(3.139)-(3.149); PDF pp552-553

| 입력 | 필수 | 타입 |
|---|---|---|
| `pool_radius_m` | 예 | `<class 'float'>` |
| `flame_length_m` | 예 | `<class 'float'>` |
| `flame_tilt_rad` | 예 | `<class 'float'>` |
| `surface_emissive_power_w_m2` | 예 | `<class 'float'>` |
| `atmosphere` | 예 | `<class 'api581.pool_fire.Atmosphere'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'geometry_checked']` |
| `distance_convention` | 예 | `typing.Literal['printed_surface_ratio', 'surface_to_axis']` |
| `surface_distance_m` | 예 | `<class 'float'>` |

출력: `received_flux_w_m2`, `transmissivity`, `maximum_view_factor`, `view_factor_distance_m`, `equation_basis`, `distance_convention`

적용 범위: Source nomenclature defines xs from flame surface, but printed Y=xs/R conflicts with axis-distance geometry. Caller selects printed_surface_ratio (Y=xs/R) or surface_to_axis (Y=(xs+R)/R). Atmospheric path always uses surface separation. Invalid physical view factors are rejected; no automatic formula fallback.

## `api581.api.effects.pool_fire_distance`

Pool radiation threshold separation and consequence area

계산 ID: `effects/pool-fire-distance`

출처: Part3 §5.8.2.6; eqs(3.150)-(3.151); PDF p553

| 입력 | 필수 | 타입 |
|---|---|---|
| `pool_radius_m` | 예 | `<class 'float'>` |
| `flame_length_m` | 예 | `<class 'float'>` |
| `flame_tilt_rad` | 예 | `<class 'float'>` |
| `surface_emissive_power_w_m2` | 예 | `<class 'float'>` |
| `atmosphere` | 예 | `<class 'api581.pool_fire.Atmosphere'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'geometry_checked']` |
| `distance_convention` | 예 | `typing.Literal['printed_surface_ratio', 'surface_to_axis']` |
| `threshold_w_m2` | 예 | `<class 'float'>` |
| `maximum_surface_distance_m` | 예 | `<class 'float'>` |
| `distance_tolerance_m` | 기본값/선택 | `<class 'float'>` |
| `maximum_iterations` | 기본값/선택 | `<class 'int'>` |

출력: `safe_surface_distance_m`, `consequence_radius_m`, `consequence_area_m2`, `status`, `iterations`, `flux_residual_w_m2`, `minimum_surface_domain_m`, `equation_basis`, `distance_convention`

적용 범위: Assumes decreasing flux outside downwind flame envelope. Solves only within supplied maximum distance; no implicit expansion or far-field substitution. If flux already below limit at domain boundary, returns conservative flame-envelope separation and boundary status, not a claimed threshold crossing. Area always pi*(surface_distance+pool_radius)^2. Printed formula/geometry and distance convention are explicit; no validated LH2 applicability.

## `api581.api.effects.pool_fire_consequence`

Compose burning, pool size, flame and radiation consequence areas

계산 ID: `effects/pool-fire-consequence`

출처: Part3 §5.8.2; eqs(3.128)-(3.151); PDF pp550-553

| 입력 | 필수 | 타입 |
|---|---|---|
| `burning` | 예 | `<class 'api581.effects.PoolBurning'>` |
| `liquid_rate_kg_s` | 예 | `<class 'float'>` |
| `available_liquid_mass_kg` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |
| `pool_depth_m` | 기본값/선택 | `<class 'float'>` |
| `site_maximum_area_m2` | 예 | `<class 'float'>` |
| `air_density_kg_m3` | 예 | `<class 'float'>` |
| `vapor_density_kg_m3` | 예 | `<class 'float'>` |
| `wind_speed_m_s` | 예 | `<class 'float'>` |
| `radiative_fraction` | 기본값/선택 | `<class 'float'>` |
| `atmosphere` | 예 | `<class 'api581.pool_fire.Atmosphere'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'geometry_checked']` |
| `distance_convention` | 예 | `typing.Literal['printed_surface_ratio', 'surface_to_axis']` |
| `maximum_surface_distance_m` | 예 | `<class 'float'>` |
| `personnel_threshold_w_m2` | 기본값/선택 | `<class 'float'>` |
| `equipment_threshold_w_m2` | 기본값/선택 | `<class 'float'>` |

출력: `burning_rate_kg_m2_s`, `burning_area_m2`, `inventory_limited_area_m2`, `pool_area_m2`, `pool_radius_m`, `flame_length_m`, `flame_tilt_rad`, `surface_emissive_power_w_m2`, `personnel_area_m2`, `equipment_area_m2`, `personnel_safe_surface_distance_m`, `equipment_safe_surface_distance_m`, `personnel_status`, `equipment_status`, `equation_basis`, `distance_convention`

적용 범위: Single pool/event only; no ignition/event or hole weighting. Qualified liquid rainout rate/mass supplied; inventory input is liquid mass, not automatic substitution of ambiguous frac_ro in printed eq(3.132). Site limit mandatory. Explicit printed/geometry_checked and distance choices; source-view-factor discrepancies are not silently corrected. Uniform plume model, no smoke/terrain/flame-impingement or LH2-specific validation.

## `api581.api.inspection.effectiveness_category`

API 581 Annex 2.C common inspection effectiveness category metadata

계산 ID: `inspection/effectiveness-category`

출처: Part 2 Annex C §2.C.2-§2.C.2.3; PDF pp443-445

| 입력 | 필수 | 타입 |
|---|---|---|
| `category` | 예 | `typing.Literal['A', 'B', 'C', 'D', 'E']` |
| `owner_user_basis` | 예 | `<class 'str'>` |

출력: `category`, `ordinal`, `label`, `inspection_credit_allowed`, `owner_user_basis`

적용 범위: Returns the common qualitative category metadata only. It does not decide whether a particular NDE method satisfies a mechanism-specific table; use the dedicated inspection effectiveness APIs for that decision. Category E means ineffective or insufficiently evidenced for inspection credit. A-D labels are qualitative and do not by themselves define a numeric damage-factor reduction.

## `api581.api.inspection.thinning_effectiveness`

API 581 Annex 2.C.8 thinning inspection effectiveness category

계산 ID: `inspection/thinning-effectiveness`

출처: Part 2 Annex C §2.C.8.1-§2.C.8.2, Tables 2.C.8.1-2.C.8.2; PDF pp454-455

| 입력 | 필수 | 타입 |
|---|---|---|
| `damage_type` | 예 | `typing.Literal['general', 'local']` |
| `inspection_mode` | 예 | `typing.Literal['intrusive', 'non_intrusive']` |
| `visual_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `spot_thickness_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `advanced_scan_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `profile_radiography_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `follow_up_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `inspection_quality_high` | 기본값/선택 | `<class 'bool'>` |
| `locations_qualified` | 기본값/선택 | `<class 'bool'>` |
| `technique_effective` | 기본값/선택 | `<class 'bool'>` |

출력: `effectiveness_category`, `damage_type`, `inspection_mode`, `qualification_status`, `basis`

적용 범위: Implements the printed general/local thinning percentage examples only. It classifies inspection effectiveness; it does not calculate inspection uncertainty, PoF, damage factor or inspection credit. The caller must qualify inspection quality, CML/location selection and technique effectiveness. A failed qualification returns E rather than manufacturing credit. Thresholds follow the table's percentage bands; ambiguous technique descriptions are not inferred.

## `api581.api.inspection.scc_effectiveness`

API 581 Annex 2.C.9 stress-corrosion-cracking inspection effectiveness category

계산 ID: `inspection/scc-effectiveness`

출처: Part 2 Annex C §2.C.9.1-§2.C.9.9, Tables 2.C.9.1-2.C.9.9; PDF pp456-464

| 입력 | 필수 | 타입 |
|---|---|---|
| `mechanism_family` | 예 | `typing.Literal['weld_scc', 'clscc_pta']` |
| `inspection_mode` | 예 | `typing.Literal['intrusive', 'non_intrusive']` |
| `targeted_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `ultrasonic_scan_percent` | 기본값/선택 | `<class 'float'>` |
| `radiography_percent` | 기본값/선택 | `<class 'float'>` |
| `acoustic_emission_follow_up_percent` | 기본값/선택 | `<class 'float'>` |
| `relevant_indication_follow_up_percent` | 기본값/선택 | `<class 'float'>` |
| `inspection_quality_high` | 기본값/선택 | `<class 'bool'>` |
| `locations_qualified` | 기본값/선택 | `<class 'bool'>` |
| `technique_effective` | 기본값/선택 | `<class 'bool'>` |

출력: `effectiveness_category`, `mechanism_family`, `inspection_mode`, `qualification_status`, `basis`

적용 범위: Implements the common percentage bands in the SCC example tables. It classifies inspection effectiveness only; it does not calculate SCC susceptibility, inspection uncertainty, PoF or damage factor. For CLSCC/PTA the source provides no non-intrusive A-level technique; this API returns E unless a lower category threshold is met. Caller must qualify inspection quality, suspect-area definition and indication follow-up.

## `api581.api.inspection.external_effectiveness`

API 581 Annex 2.C.10 external-damage inspection effectiveness category

계산 ID: `inspection/external-effectiveness`

출처: Part 2 Annex C §2.C.10.1-§2.C.10.2, Tables 2.C.10.1-2.C.10.4; PDF pp463-465

| 입력 | 필수 | 타입 |
|---|---|---|
| `mechanism_family` | 예 | `typing.Literal['external_corrosion', 'external_clscc', 'cui', 'cui_clscc']` |
| `insulation_status` | 기본값/선택 | `typing.Literal['not_applicable', 'removed', 'not_removed']` |
| `visual_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `targeted_ndt_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `insulation_removed_percent` | 기본값/선택 | `<class 'float'>` |
| `follow_up_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `inspection_quality_high` | 기본값/선택 | `<class 'bool'>` |
| `locations_qualified` | 기본값/선택 | `<class 'bool'>` |
| `technique_effective` | 기본값/선택 | `<class 'bool'>` |

출력: `effectiveness_category`, `mechanism_family`, `insulation_status`, `qualification_status`, `basis`

적용 범위: Implements the printed external-corrosion, external CLSCC, CUI and CUI-CLSCC percentage examples. It classifies inspection effectiveness only and does not calculate external damage factor or inspection uncertainty. CUI-CLSCC/non-removed insulation has no source technique for A-D and therefore remains E. Caller must qualify exposed/suspect area definition, inspection quality and follow-up.

## `api581.api.inspection.buried_effectiveness`

API 581 Annex 2.C.7 buried-component inspection effectiveness category

계산 ID: `inspection/buried-effectiveness`

출처: Part 2 Annex C §2.C.7.1-§2.C.7.2, Table 2.C.7.1; PDF pp452-453

| 입력 | 필수 | 타입 |
|---|---|---|
| `inspection_mode` | 예 | `typing.Literal['intrusive', 'non_intrusive']` |
| `coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `state_of_art_internal_technology` | 기본값/선택 | `<class 'bool'>` |
| `selected_internal_technology` | 기본값/선택 | `<class 'bool'>` |
| `statistical_or_extreme_value_analysis` | 기본값/선택 | `<class 'bool'>` |
| `partial_smart_pig_or_specialized_crawler` | 기본값/선택 | `<class 'bool'>` |
| `hydrostatic_test` | 기본값/선택 | `<class 'bool'>` |
| `full_excavation_visual_ndt` | 기본값/선택 | `<class 'bool'>` |
| `external_ndt_crawler` | 기본값/선택 | `<class 'bool'>` |
| `cathodic_protection_managed` | 기본값/선택 | `<class 'bool'>` |
| `close_interval_survey` | 기본값/선택 | `<class 'bool'>` |
| `soil_water_sampling` | 기본값/선택 | `<class 'bool'>` |
| `dcvg_coating_survey` | 기본값/선택 | `<class 'bool'>` |
| `guided_wave_and_corrosion_management` | 기본값/선택 | `<class 'bool'>` |
| `spot_check_exposed_areas` | 기본값/선택 | `<class 'bool'>` |
| `inspection_quality_high` | 기본값/선택 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `effectiveness_category`, `inspection_mode`, `qualification_status`, `basis`

적용 범위: Classifies the example intrusive/non-intrusive evidence bundles in Table 2.C.7.1. It does not infer corrosion rate, cathodic-protection adequacy, soil corrosivity, PoF or damage factor. The caller must qualify the evidence flags and coverage. A missing qualification basis or low inspection quality returns E; partial excavation and non-intrusive evidence are not silently promoted to full coverage.

## `api581.api.inspection.prd_effectiveness`

API 581 Annex 2.C.3 pressure-relief-device inspection effectiveness category

계산 ID: `inspection/prd-effectiveness`

출처: Part 2 Annex C §2.C.3-§2.C.3.1, Table 2.C.3.1; PDF pp445-446

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `typing.Literal['pressure_relief_device', 'rupture_disk']` |
| `as_received_bench_test` | 기본값/선택 | `<class 'bool'>` |
| `leak_pressure_documented` | 기본값/선택 | `<class 'bool'>` |
| `opening_pressure_documented` | 기본값/선택 | `<class 'bool'>` |
| `reseat_pressure_documented` | 기본값/선택 | `<class 'bool'>` |
| `inlet_outlet_examined` | 기본값/선택 | `<class 'bool'>` |
| `cleaned_or_steamed_before_test` | 기본값/선택 | `<class 'bool'>` |
| `detailed_internal_visual` | 기본값/선택 | `<class 'bool'>` |
| `in_situ_actual_process_fluid` | 기본값/선택 | `<class 'bool'>` |
| `removed_and_visually_inspected` | 기본값/선택 | `<class 'bool'>` |
| `in_situ_non_process_fluid` | 기본값/선택 | `<class 'bool'>` |
| `leakage_monitoring` | 기본값/선택 | `<class 'bool'>` |
| `overhaul_without_pop_test` | 기본값/선택 | `<class 'bool'>` |
| `internal_details_documented` | 기본값/선택 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `effectiveness_category`, `component_type`, `qualification_status`, `basis`

적용 범위: Implements the Table 2.C.3.1 evidence examples. It classifies inspection effectiveness only and does not calculate PRD failure frequency, service-age factor, set-pressure factor or leak consequence. Rupture-disk A-level inspection is explicitly unavailable in the source table. Missing qualification basis or incomplete evidence returns E rather than an optimistic category.

## `api581.api.inspection.lining_effectiveness`

API 581 Annex 2.C.6 non-metallic lining inspection effectiveness category

계산 ID: `inspection/lining-effectiveness`

출처: Part 2 Annex C §2.C.6.1-§2.C.6.2, Table 2.C.6.1; PDF pp451-452

| 입력 | 필수 | 타입 |
|---|---|---|
| `inspection_mode` | 예 | `typing.Literal['intrusive', 'non_intrusive']` |
| `visual_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `holiday_test_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `disbonding_test_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `ultrasonic_scan_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `inspection_quality_high` | 기본값/선택 | `<class 'bool'>` |
| `locations_qualified` | 기본값/선택 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `effectiveness_category`, `inspection_mode`, `qualification_status`, `basis`

적용 범위: Implements the example percentage bands for corrosion-resistant non-metallic liners. The source states this inspection effectiveness is not currently used in the lining damage factor calculation; this API does not change that rule. Non-intrusive A-level inspection is explicitly unavailable in the source table. Inspection quality, suspect-area definition and test suitability remain owner-qualified inputs.

## `api581.api.inspection.tube_bundle_uncertainty`

API 581 Annex 2.C.4.1 default tube-bundle inspection uncertainty

계산 ID: `inspection/tube-bundle-uncertainty`

출처: Part 2 Annex C §2.C.4.1.1-§2.C.4.1.3, Table 2.C.4.1; PDF pp446-448

| 입력 | 필수 | 타입 |
|---|---|---|
| `inspection_effectiveness` | 예 | `typing.Literal['A', 'B', 'C', 'D', 'E']` |
| `owner_user_basis` | 예 | `<class 'str'>` |

출력: `inspection_effectiveness`, `uncertainty_percent`, `uncertainty_fraction`, `baseline_no_history_percent`, `owner_user_basis`

적용 범위: Returns the recommended additional-uncertainty percentage only: A=5%, B=10%, C=20%, D=30%, E=50%. It does not shift a Weibull curve or calculate tube-bundle PoF by itself. The source says tube-bundle LoIE tables are owner-user defined; the category and basis remain caller-qualified and must not be inferred from an NDE name alone.

## `api581.api.inspection.ast_effectiveness`

API 581 Annex 2.C.5 atmospheric storage tank inspection effectiveness category

계산 ID: `inspection/ast-effectiveness`

출처: Part 2 Annex C §2.C.5.1-§2.C.5.2, Tables 2.C.5.1-2.C.5.3; PDF pp449-451

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `typing.Literal['shell_internal', 'shell_external', 'tank_bottom']` |
| `inspection_side` | 예 | `typing.Literal['internal', 'external', 'soil_side', 'product_side']` |
| `insulated` | 기본값/선택 | `<class 'bool'>` |
| `visual_coverage_percent` | 기본값/선택 | `<class 'float'>` |
| `internal_video_or_visual` | 기본값/선택 | `<class 'bool'>` |
| `pit_depth_measurement` | 기본값/선택 | `<class 'bool'>` |
| `ut_scan_percent` | 기본값/선택 | `<class 'float'>` |
| `ut_follow_up` | 기본값/선택 | `<class 'bool'>` |
| `insulation_removed_percent` | 기본값/선택 | `<class 'float'>` |
| `pulse_eddy_percent` | 기본값/선택 | `<class 'float'>` |
| `floor_scan_percent` | 기본값/선택 | `<class 'float'>` |
| `vacuum_box_percent` | 기본값/선택 | `<class 'float'>` |
| `sponge_test_percent` | 기본값/선택 | `<class 'float'>` |
| `statistical_floor_analysis` | 기본값/선택 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `inspection_quality_high` | 기본값/선택 | `<class 'bool'>` |

출력: `effectiveness_category`, `component_type`, `inspection_side`, `qualification_status`, `basis`

적용 범위: Implements the example AST shell-internal, shell-external and tank-bottom evidence bands. It does not calculate tank corrosion rate, minimum thickness, PoF or financial consequence. The caller must select the correct side and qualify inspection quality, exposed/suspect area and API 653/NDE interpretation. Inputs from multiple sides are not silently combined into a higher category.

## `api581.api.effects.fireball_mass`

Flammable mass available to a rupture fireball

계산 ID: `effects/fireball-mass`

출처: Part3 eq(3.157); PDF p555

| 입력 | 필수 | 타입 |
|---|---|---|
| `available_mass_kg` | 예 | `<class 'float'>` |
| `flammable_mass_fraction` | 예 | `<class 'float'>` |

출력: `flammable_mass_kg`

적용 범위: Mass fraction of available release inventory, not mole fraction or dispersion cloud mass. Instantaneous rupture applicability must be established by caller.

## `api581.api.effects.fireball_view_factor`

Fireball spherical radiation view factor

계산 ID: `effects/fireball-view-factor`

출처: Part3 eqs(3.159),(3.165)-(3.166); PDF pp555-556

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |
| `distance_m` | 예 | `<class 'float'>` |
| `geometry_basis` | 예 | `typing.Literal['api581_printed', 'elevated_sphere_maximum']` |

출력: `view_factor`, `model_center_distance_m`, `attenuation_path_m`, `geometry_basis`

적용 범위: Explicit basis required: api581_printed follows eqs(3.165)-(3.166), C=.5*hypot(D,xs), F=D^2/(D^2+xs^2), without using H=.75D. elevated_sphere_maximum is a separately identified geometric interpretation: grade receiver at horizontal radius xs, sphere center H=.75D, receiver plane normal facing the center, F=(D/(2*hypot(H,xs)))^2. It is not an authorized erratum.

## `api581.api.effects.fireball_radiation_flux`

Fireball received thermal radiation

계산 ID: `effects/fireball-radiation-flux`

출처: Part3 eqs(3.140),(3.164)-(3.166); PDF pp552,555-556

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |
| `surface_emissive_power_w_m2` | 예 | `<class 'float'>` |
| `atmosphere` | 예 | `<class 'api581.pool_fire.Atmosphere'>` |
| `geometry_basis` | 예 | `typing.Literal['api581_printed', 'elevated_sphere_maximum']` |
| `distance_m` | 예 | `<class 'float'>` |

출력: `view_factor`, `model_center_distance_m`, `attenuation_path_m`, `geometry_basis`, `transmissivity`, `received_flux_w_m2`

적용 범위: Explicit basis required: api581_printed follows eqs(3.165)-(3.166), C=.5*hypot(D,xs), F=D^2/(D^2+xs^2), without using H=.75D. elevated_sphere_maximum is a separately identified geometric interpretation: grade receiver at horizontal radius xs, sphere center H=.75D, receiver plane normal facing the center, F=(D/(2*hypot(H,xs)))^2. It is not an authorized erratum. Printed basis uses nominal xs for atmospheric attenuation. Elevated sphere uses center-to-receiver distance minus radius. Zero printed path uses capped limiting transmissivity1. No flame contact or LH2-specific validation.

## `api581.api.effects.fireball_distance`

Fireball thermal threshold distance and area

계산 ID: `effects/fireball-distance`

출처: Part3 eqs(3.164)-(3.168); PDF pp555-556

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |
| `surface_emissive_power_w_m2` | 예 | `<class 'float'>` |
| `atmosphere` | 예 | `<class 'api581.pool_fire.Atmosphere'>` |
| `geometry_basis` | 예 | `typing.Literal['api581_printed', 'elevated_sphere_maximum']` |
| `threshold_w_m2` | 예 | `<class 'float'>` |
| `maximum_distance_m` | 예 | `<class 'float'>` |
| `distance_tolerance_m` | 기본값/선택 | `<class 'float'>` |
| `maximum_iterations` | 기본값/선택 | `<class 'int'>` |

출력: `safe_distance_m`, `consequence_area_m2`, `status`, `iterations`, `flux_residual_w_m2`, `geometry_basis`

적용 범위: Explicit basis required: api581_printed follows eqs(3.165)-(3.166), C=.5*hypot(D,xs), F=D^2/(D^2+xs^2), without using H=.75D. elevated_sphere_maximum is a separately identified geometric interpretation: grade receiver at horizontal radius xs, sphere center H=.75D, receiver plane normal facing the center, F=(D/(2*hypot(H,xs)))^2. It is not an authorized erratum. Monotone spherical flux solution within caller maximum distance; no automatic bracket expansion. Returns safe upper bracket, with error bounded by distance_tolerance_m. Area=pi*distance^2 per printed equations; elevated-sphere distance is horizontal radius. If origin is below threshold returns zero area and no claimed threshold root.

## `api581.api.effects.fireball_consequence`

Rupture fireball radiation consequence chain

계산 ID: `effects/fireball-consequence`

출처: Part3 eqs(3.157)-(3.168); PDF pp555-556

| 입력 | 필수 | 타입 |
|---|---|---|
| `available_mass_kg` | 예 | `<class 'float'>` |
| `flammable_mass_fraction` | 예 | `<class 'float'>` |
| `heat_of_combustion_j_kg` | 예 | `<class 'float'>` |
| `burst_pressure_pa_abs` | 예 | `<class 'float'>` |
| `atmosphere` | 예 | `<class 'api581.pool_fire.Atmosphere'>` |
| `geometry_basis` | 예 | `typing.Literal['api581_printed', 'elevated_sphere_maximum']` |
| `maximum_distance_m` | 예 | `<class 'float'>` |
| `personnel_threshold_w_m2` | 기본값/선택 | `<class 'float'>` |
| `equipment_threshold_w_m2` | 기본값/선택 | `<class 'float'>` |
| `distance_tolerance_m` | 기본값/선택 | `<class 'float'>` |
| `maximum_iterations` | 기본값/선택 | `<class 'int'>` |

출력: `flammable_mass_kg`, `diameter_m`, `center_height_m`, `duration_s`, `radiative_fraction`, `surface_emissive_power_w_m2`, `personnel_area_m2`, `equipment_area_m2`, `personnel_safe_distance_m`, `equipment_safe_distance_m`, `personnel_status`, `equipment_status`, `geometry_basis`

적용 범위: Explicit basis required: api581_printed follows eqs(3.165)-(3.166), C=.5*hypot(D,xs), F=D^2/(D^2+xs^2), without using H=.75D. elevated_sphere_maximum is a separately identified geometric interpretation: grade receiver at horizontal radius xs, sphere center H=.75D, receiver plane normal facing the center, F=(D/(2*hypot(H,xs)))^2. It is not an authorized erratum. Instantaneous rupture only. Caller qualifies inventory, combustion heat, and burst pressure: normal operating pressure for normal rupture or likely elevated pressure for PRD failure. Pressure correlation giving radiative fraction above1 is rejected. Constant or water-vapor atmospheric model is explicit. No ignition probability weighting, duration-dose injury model, or LH2 validation.

## `api581.api.effects.vce_scaled_distance`

Hopkinson TNT scaled distance

계산 ID: `effects/vce-scaled-distance`

출처: Part3 eq(3.171), Annex3.B C27=1; PDF pp558,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `distance_m` | 예 | `<class 'float'>` |
| `tnt_equivalent_mass_kg` | 예 | `<class 'float'>` |

출력: `scaled_distance_m_kg13`

적용 범위: SI distance m and TNT equivalent mass kg; output units m/kg^(1/3). Scaling alone does not establish blast-curve applicability. Zero TNT mass has no defined scaled distance.

## `api581.api.effects.vce_scaled_overpressure`

Hopkinson-scaled blast overpressure fit

계산 ID: `effects/vce-scaled-overpressure`

출처: Part3 eq(3.170), Annex3.B C26=100; PDF pp558,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `scaled_distance_m_kg13` | 예 | `<class 'float'>` |
| `fit_domain` | 예 | `<class 'api581.blast.BlastFitDomain'>` |

출력: `side_on_overpressure_pa`, `slope_pa_per_scaled_distance`

적용 범위: Printed inverse-log polynomial, not an exponential of the polynomial. C26=100 gives kPa; public pressure is Pa. Source specifies no fit validity interval. Caller must supply bounds and engineering basis; positive pressure and strictly decreasing behavior are checked over that interval. These checks do not establish experimental fit validity or LH2 applicability.

## `api581.api.effects.vce_blast_overpressure`

TNT blast pressure at physical distance

계산 ID: `effects/vce-blast-overpressure`

출처: Part3 eqs(3.170)-(3.171); PDF p558

| 입력 | 필수 | 타입 |
|---|---|---|
| `distance_m` | 예 | `<class 'float'>` |
| `tnt_equivalent_mass_kg` | 예 | `<class 'float'>` |
| `fit_domain` | 예 | `<class 'api581.blast.BlastFitDomain'>` |

출력: `scaled_distance_m_kg13`, `side_on_overpressure_pa`, `slope_pa_per_scaled_distance`

적용 범위: Printed inverse-log polynomial, not an exponential of the polynomial. C26=100 gives kPa; public pressure is Pa. Source specifies no fit validity interval. Caller must supply bounds and engineering basis; positive pressure and strictly decreasing behavior are checked over that interval. These checks do not establish experimental fit validity or LH2 applicability. Side-on gauge overpressure, not reflected pressure or absolute pressure. Point-source TNT equivalence has near-field limitations.

## `api581.api.effects.blast_building_probit`

Blast-induced process-building collapse probit

계산 ID: `effects/blast-building-probit`

출처: Part3 eq(3.172), Annex3.B C28=1000/kPa; PDF pp558,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `side_on_overpressure_pa` | 예 | `<class 'float'>` |

출력: `probit`, `building_collapse_probability`

적용 범위: Probit=-23.8+2.92*ln(overpressure in Pa); probability=Phi(probit-5). Building-collapse mechanism used as a serious-injury proxy, not open-air lung hemorrhage, direct fatality, or a pressure-duration/structural-response model.

## `api581.api.effects.blast_building_pressure_threshold`

Pressure for target building-collapse probability

계산 ID: `effects/blast-building-pressure-threshold`

출처: Part3 eq(3.172) inverse, STEP8.14; PDF pp558,564

| 입력 | 필수 | 타입 |
|---|---|---|
| `building_collapse_probability` | 예 | `<class 'float'>` |

출력: `probit`, `side_on_overpressure_pa`

적용 범위: Target probability must be strictly between0 and1. This is the building-collapse proxy, not a universal personnel injury threshold. Part3 STEP8.14 uses probit5 (50%); standalone inverse also supports explicitly selected alternative targets.

## `api581.api.effects.vce_blast_distance`

TNT blast threshold distance and consequence area

계산 ID: `effects/vce-blast-distance`

출처: Part3 eqs(3.170)-(3.171),(3.173)-(3.174); PDF p558

| 입력 | 필수 | 타입 |
|---|---|---|
| `tnt_equivalent_mass_kg` | 예 | `<class 'float'>` |
| `threshold_overpressure_pa` | 예 | `<class 'float'>` |
| `fit_domain` | 예 | `<class 'api581.blast.BlastFitDomain'>` |
| `distance_tolerance_m` | 기본값/선택 | `<class 'float'>` |
| `maximum_iterations` | 기본값/선택 | `<class 'int'>` |

출력: `safe_distance_m`, `consequence_area_m2`, `scaled_distance_m_kg13`, `status`, `iterations`, `pressure_residual_pa`

적용 범위: Printed inverse-log polynomial, not an exponential of the polynomial. C26=100 gives kPa; public pressure is Pa. Source specifies no fit validity interval. Caller must supply bounds and engineering basis; positive pressure and strictly decreasing behavior are checked over that interval. These checks do not establish experimental fit validity or LH2 applicability. Requires threshold bracket within supplied scaled interval; does not extrapolate to source or beyond bounds. Returns safe upper distance bracket with error bounded by distance tolerance. Zero TNT mass returns no_explosion and zero area. Area=pi*distance^2.

## `api581.api.effects.vce_blast_consequence`

Cloud mass to TNT blast personnel/equipment areas

계산 ID: `effects/vce-blast-consequence`

출처: Part3 §§5.8.5.3-5.8.5.6 eqs(3.169)-(3.174), STEP8.14; PDF pp557-558,564

| 입력 | 필수 | 타입 |
|---|---|---|
| `flammable_cloud_mass_kg` | 예 | `<class 'float'>` |
| `combustion_heat_j_kg` | 예 | `<class 'float'>` |
| `explosion_yield` | 예 | `<class 'float'>` |
| `tnt_heat_j_kg` | 예 | `<class 'float'>` |
| `tnt_heat_source` | 예 | `<class 'str'>` |
| `mass_basis` | 예 | `typing.Literal['between_flammability_limits', 'total_released_flammable']` |
| `yield_engineering_basis` | 예 | `<class 'str'>` |
| `personnel_building_collapse_probability` | 기본값/선택 | `<class 'float'>` |
| `equipment_threshold_overpressure_pa` | 기본값/선택 | `<class 'float'>` |
| `fit_domain` | 예 | `<class 'api581.blast.BlastFitDomain'>` |
| `distance_tolerance_m` | 기본값/선택 | `<class 'float'>` |
| `maximum_iterations` | 기본값/선택 | `<class 'int'>` |

출력: `tnt_equivalent_mass_kg`, `personnel_threshold_overpressure_pa`, `personnel_building_collapse_probability`, `equipment_threshold_overpressure_pa`, `personnel_safe_distance_m`, `equipment_safe_distance_m`, `personnel_area_m2`, `equipment_area_m2`, `personnel_status`, `equipment_status`, `mass_basis`

적용 범위: Printed inverse-log polynomial, not an exponential of the polynomial. C26=100 gives kPa; public pressure is Pa. Source specifies no fit validity interval. Caller must supply bounds and engineering basis; positive pressure and strictly decreasing behavior are checked over that interval. These checks do not establish experimental fit validity or LH2 applicability. Caller supplies cloud mass at ignition or total released flammable mass and a consistent qualified yield. Source recommends yield1 for mass between LFL/UFL; typical total-release yields.03-.19 are not automatically assigned by material. Dispersion/ignition timing not solved here. TNT heat is mandatory because printed4648J/kg conflicts with2000Btu/lb; no silent correction. Personnel target defaults to50% building collapse per Part3 STEP8.14 (probit5), with explicit alternative targets supported. This is not direct lethality. No ignition/event weighting, congestion correction or TNO multi-energy model.

## `api581.api.effects.physical_explosion_tnt`

Gas-vessel Brode energy and TNT equivalent

계산 ID: `effects/physical-explosion-tnt`

출처: Part3 eq(3.192), Annex3.B C29; PDF pp569,648; pressure units PDF578

| 입력 | 필수 | 타입 |
|---|---|---|
| `burst_pressure_pa_abs` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `vapor_volume_m3` | 예 | `<class 'float'>` |
| `heat_capacity_ratio` | 예 | `<class 'float'>` |

출력: `vapor_stored_energy_j`, `tnt_equivalent_mass_kg`

적용 범위: C29=4.303e-4 with source pressures in kPa; Pa inputs therefore use4.303e-7 kg/J. Uses vapor space volume, not total two-phase vessel volume. k>1, absolute burst pressure>=ambient. Returns potential rupture energy, not ignition-dependent combustion energy; no real-gas or vessel fragmentation calculation.

## `api581.api.release.bleve_flashed_amount`

Flashed liquid mass and amount for BLEVE

계산 ID: `release/bleve-flashed-amount`

출처: Part3 STEP10.3(1), nomenclature nv/MW; PDF pp571,576

| 입력 | 필수 | 타입 |
|---|---|---|
| `stored_liquid_mass_kg` | 예 | `<class 'float'>` |
| `liquid_flash_mass_fraction` | 예 | `<class 'float'>` |
| `molecular_weight_kg_kmol` | 예 | `<class 'float'>` |

출력: `flashed_liquid_mass_kg`, `flashed_amount_kmol`

적용 범위: Caller supplies liquid flash mass fraction qualified at atmospheric release; this is not an EOS/isenthalpic flash solver. Amount is kmol (source kg-mol), not mol. Only stored liquid is counted; pre-existing vapor is handled separately.

## `api581.api.effects.bleve_liquid_tnt`

Flashed-liquid BLEVE expansion energy and TNT equivalent

계산 ID: `effects/bleve-liquid-tnt`

출처: Part3 eq(3.195), Annex3.B C30; PDF pp569,648; nv/R units PDF576,578

| 입력 | 필수 | 타입 |
|---|---|---|
| `burst_pressure_pa_abs` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `flashed_amount_kmol` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 예 | `<class 'float'>` |

출력: `liquid_expansion_energy_j`, `tnt_equivalent_mass_kg`

적용 범위: Uses printed C30=9.76e-8 kg/J and R=8314 J/(kmol*K), nv in kmol, storage temperature K, natural log of absolute burst/ambient pressure. Does not infer flash amount from fluid properties. Vapor-space contribution is excluded and must be added separately for two-phase contents. No combustion/fireball energy included.

## `api581.api.effects.physical_explosion_consequence`

Gas-vessel rupture blast consequence

계산 ID: `effects/physical-explosion-consequence`

출처: Part3 eqs(3.192)-(3.194), STEP10.2; PDF pp569-571

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `fit_domain` | 예 | `<class 'api581.blast.BlastFitDomain'>` |
| `personnel_building_collapse_probability` | 기본값/선택 | `<class 'float'>` |
| `equipment_threshold_overpressure_pa` | 기본값/선택 | `<class 'float'>` |
| `distance_tolerance_m` | 기본값/선택 | `<class 'float'>` |
| `maximum_iterations` | 기본값/선택 | `<class 'int'>` |
| `burst_pressure_pa_abs` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `vapor_volume_m3` | 예 | `<class 'float'>` |
| `heat_capacity_ratio` | 예 | `<class 'float'>` |

출력: `vapor_stored_energy_j`, `potential_tnt_equivalent_mass_kg`, `event_tnt_equivalent_mass_kg`, `personnel_threshold_overpressure_pa`, `equipment_threshold_overpressure_pa`, `personnel_building_collapse_probability`, `personnel_safe_distance_m`, `equipment_safe_distance_m`, `personnel_area_m2`, `equipment_area_m2`, `personnel_status`, `equipment_status`, `hole`

적용 범위: Only rupture hole produces blast area; other holes return not_rupture with zero event equivalent and area while retaining potential inventory rupture energy. Personnel default is probit5 (50% building collapse), equipment default34500Pa. Reuses caller-qualified TNT fit domain; no extrapolation, direct lethality, fragmentation or LH2 validation.

## `api581.api.effects.bleve_consequence`

Liquid/two-phase BLEVE blast consequence

계산 ID: `effects/bleve-consequence`

출처: Part3 eqs(3.192),(3.195)-(3.197), STEP10.3; PDF pp569-572

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `fit_domain` | 예 | `<class 'api581.blast.BlastFitDomain'>` |
| `personnel_building_collapse_probability` | 기본값/선택 | `<class 'float'>` |
| `equipment_threshold_overpressure_pa` | 기본값/선택 | `<class 'float'>` |
| `distance_tolerance_m` | 기본값/선택 | `<class 'float'>` |
| `maximum_iterations` | 기본값/선택 | `<class 'int'>` |
| `burst_pressure_pa_abs` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `flashed_amount_kmol` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 예 | `<class 'float'>` |
| `stored_vapor` | 기본값/선택 | `api581.physical_explosion.VaporPortion | None` |

출력: `liquid_expansion_energy_j`, `vapor_stored_energy_j`, `liquid_tnt_equivalent_mass_kg`, `vapor_tnt_equivalent_mass_kg`, `potential_tnt_equivalent_mass_kg`, `event_tnt_equivalent_mass_kg`, `personnel_threshold_overpressure_pa`, `equipment_threshold_overpressure_pa`, `personnel_building_collapse_probability`, `personnel_safe_distance_m`, `equipment_safe_distance_m`, `personnel_area_m2`, `equipment_area_m2`, `personnel_status`, `equipment_status`, `hole`

적용 범위: Sums liquid and pre-existing vapor TNT equivalents using their distinct printed C30/C29 coefficients. Shared absolute burst/ambient pressure; vapor volume must exclude liquid, flashed amount must exclude pre-existing vapor. No automatic EOS, superheat applicability, fireball or combustion calculation. Only rupture produces blast area. Caller-qualified fit domain and building-collapse proxy limits apply; LH2 validation outstanding.

## `api581.api.consequence.level2_nfnt_case`

Level2 NFNT maximum areas and non-ignition weighting

계산 ID: `consequence/level2-nfnt-case`

출처: Part3 eqs(3.198)-(3.199), §5.10.5; PDF p570

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `non_ignition_probability` | 예 | `<class 'float'>` |
| `physical_equipment_area_m2` | 기본값/선택 | `<class 'float'>` |
| `physical_personnel_area_m2` | 기본값/선택 | `<class 'float'>` |
| `bleve_equipment_area_m2` | 기본값/선택 | `<class 'float'>` |
| `bleve_personnel_area_m2` | 기본값/선택 | `<class 'float'>` |
| `steam_chemical_personnel_area_m2` | 기본값/선택 | `<class 'float'>` |

출력: `equipment_area_m2`, `personnel_area_m2`

적용 범위: Inputs are event-conditional unweighted areas. Uses maximum, not sum, then applies non-ignition probability once. Physical/BLEVE areas must be zero for non-rupture holes. Steam/chemical area can be supplied by Level1 NFNT calculation. This does not infer event-tree probabilities.

## `api581.api.consequence.level2_nfnt_summary`

Four-hole Level2 NFNT GFF-weighted final areas

계산 ID: `consequence/level2-nfnt-summary`

출처: Part3 eqs(3.198)-(3.201); PDF p570

| 입력 | 필수 | 타입 |
|---|---|---|
| `cases` | 예 | `list[api581.physical_explosion.NfntFrequencyCase]` |

출력: `equipment_area_m2`, `personnel_area_m2`, `total_generic_frequency_per_year`, `by_hole_equipment_area_m2`, `by_hole_personnel_area_m2`

적용 범위: Requires small,medium,large,rupture once each, including zero-frequency holes. Weights per-case non-ignition-adjusted maximum areas by supplied generic frequencies, not DF-adjusted failure frequencies. No annual risk or financial consequence is computed by this area average.

## `api581.api.properties.toxic_impact_table`

2016 Table4.14 toxic criteria and probit parameters

계산 ID: `properties/toxic-impact-table`

출처: Part3 Table4.14; PDF p531; Annex3.A nomenclature PDF624

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['acrolein', 'acrylonitrile', 'aluminum_trichloride', 'ammonia', 'benzene', 'bromine', 'carbon_monoxide', 'carbon_tetrachloride', 'chlorine', 'ethylene_glycol_monoethyl_ether', 'ethylene_oxide', 'formaldehyde', 'hydrogen_chloride', 'hydrogen_cyanide', 'hydrogen_fluoride', 'hydrogen_sulfide', 'methanol', 'methyl_bromide', 'methyl_isocyanate', 'nitric_acid', 'nitrogen_dioxide', 'phosgene', 'propylene_oxide', 'styrene', 'sulphur_dioxide', 'toluene', 'toluene_diisocyanate']` |

출력: `probit_intercept`, `probit_slope`, `concentration_exponent`, `probit_available`, `probit_concentration_unit`, `probit_duration_unit`, `idlh_ppm`, `aegl3_ppm`, `epa_toxic_endpoint_mg_l`, `erpg3_ppm`

적용 범위: Historical2016 Table4.14 snapshot, not current occupational/emergency exposure guidance. Printed ammonia IDLH10ppm retained. Dashes are unavailable, not zero. Probit concentration ppm and time seconds follow Annex3.A nomenclature; caller must qualify coefficient/species applicability. EPA mg/L is not implicitly converted to ppm.

## `api581.api.effects.toxic_species_probit`

Table4.14 constant-exposure toxic probit

계산 ID: `effects/toxic-species-probit`

출처: Part3 Table4.14, Annex3.A eq(3.A.5); PDF pp531,620,624

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['acrolein', 'acrylonitrile', 'aluminum_trichloride', 'ammonia', 'benzene', 'bromine', 'carbon_monoxide', 'carbon_tetrachloride', 'chlorine', 'ethylene_glycol_monoethyl_ether', 'ethylene_oxide', 'formaldehyde', 'hydrogen_chloride', 'hydrogen_cyanide', 'hydrogen_fluoride', 'hydrogen_sulfide', 'methanol', 'methyl_bromide', 'methyl_isocyanate', 'nitric_acid', 'nitrogen_dioxide', 'phosgene', 'propylene_oxide', 'styrene', 'sulphur_dioxide', 'toluene', 'toluene_diisocyanate']` |
| `concentration_ppm` | 예 | `<class 'float'>` |
| `exposure_duration_s` | 예 | `<class 'float'>` |

출력: `probit`, `fatality_probability`

적용 범위: Historical2016 Table4.14 snapshot, not current occupational/emergency exposure guidance. Printed ammonia IDLH10ppm retained. Dashes are unavailable, not zero. Probit concentration ppm and time seconds follow Annex3.A nomenclature; caller must qualify coefficient/species applicability. EPA mg/L is not implicitly converted to ppm. Pr=A+B*ln(C^N*t); probability=Phi(Pr-5). Constant species concentration, not whole-mixture concentration. Zero exposure gives zero probability with no finite probit. No dispersion, escape or dose-response validation for a particular installation.

## `api581.api.effects.toxic_species_threshold`

Species concentration for target toxic probit probability

계산 ID: `effects/toxic-species-threshold`

출처: Part3 Table4.14, Annex3.A eq(3.A.5) inverse; PDF pp531,620,624

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['acrolein', 'acrylonitrile', 'aluminum_trichloride', 'ammonia', 'benzene', 'bromine', 'carbon_monoxide', 'carbon_tetrachloride', 'chlorine', 'ethylene_glycol_monoethyl_ether', 'ethylene_oxide', 'formaldehyde', 'hydrogen_chloride', 'hydrogen_cyanide', 'hydrogen_fluoride', 'hydrogen_sulfide', 'methanol', 'methyl_bromide', 'methyl_isocyanate', 'nitric_acid', 'nitrogen_dioxide', 'phosgene', 'propylene_oxide', 'styrene', 'sulphur_dioxide', 'toluene', 'toluene_diisocyanate']` |
| `exposure_duration_s` | 예 | `<class 'float'>` |
| `target_fatality_probability` | 기본값/선택 | `<class 'float'>` |

출력: `concentration_ppm`, `probit`, `within_pure_species_limit`

적용 범위: Historical2016 Table4.14 snapshot, not current occupational/emergency exposure guidance. Printed ammonia IDLH10ppm retained. Dashes are unavailable, not zero. Probit concentration ppm and time seconds follow Annex3.A nomenclature; caller must qualify coefficient/species applicability. EPA mg/L is not implicitly converted to ppm. Default50% fatality corresponds to Pr5. Probability must be strictly between0 and1. Reports whether mathematical threshold is within pure-species1e6ppm limit; values above this are not silently capped.

## `api581.api.effects.toxic_dose_profile`

Time-varying species dose and Table4.14 probit

계산 ID: `effects/toxic-dose-profile`

출처: Part3 Annex3.A eq(3.A.5); PDF pp531,620,624

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['acrolein', 'acrylonitrile', 'aluminum_trichloride', 'ammonia', 'benzene', 'bromine', 'carbon_monoxide', 'carbon_tetrachloride', 'chlorine', 'ethylene_glycol_monoethyl_ether', 'ethylene_oxide', 'formaldehyde', 'hydrogen_chloride', 'hydrogen_cyanide', 'hydrogen_fluoride', 'hydrogen_sulfide', 'methanol', 'methyl_bromide', 'methyl_isocyanate', 'nitric_acid', 'nitrogen_dioxide', 'phosgene', 'propylene_oxide', 'styrene', 'sulphur_dioxide', 'toluene', 'toluene_diisocyanate']` |
| `profile` | 예 | `list[api581.toxic_level2.ConcentrationPoint]` |
| `interpolation` | 예 | `typing.Literal['previous', 'linear']` |
| `profile_source` | 예 | `<class 'str'>` |

출력: `probit`, `fatality_probability`, `dose_ppm_power_n_s`, `log_dose`, `dose_representable`, `duration_s`, `equivalent_constant_concentration_ppm`

적용 범위: Historical2016 Table4.14 snapshot, not current occupational/emergency exposure guidance. Printed ammonia IDLH10ppm retained. Dashes are unavailable, not zero. Probit concentration ppm and time seconds follow Annex3.A nomenclature; caller must qualify coefficient/species applicability. EPA mg/L is not implicitly converted to ppm. Explicit extension: replaces constant C^N*t with integral C(t)^N dt. Previous holds each left concentration; final point only closes last interval. Linear integrates concentration power analytically, not a trapezoid of C^N. Not a printed transient API581 equation or an actual slabx run. No tail outside supplied profile and no automatic exposure cap.

## `api581.api.release.level2_toxic_duration`

Level2 toxic release duration bound

계산 ID: `release/level2-toxic-duration`

출처: Part3 eq(3.186), §5.9.3; PDF p566

| 입력 | 필수 | 타입 |
|---|---|---|
| `available_mass_kg` | 예 | `<class 'float'>` |
| `mixture_release_rate_kg_s` | 예 | `<class 'float'>` |
| `detection_maximum_duration_s` | 예 | `<class 'float'>` |

출력: `release_duration_s`, `governing_limit`

적용 범위: Minimum of3600s, full inventory/full mixture rate, detection/isolation duration. Do not divide full inventory by toxic-component rate. Constant-rate source approximation; no transient depressurization. Release duration is not automatically receptor exposure duration.

## `api581.api.consequence.toxic_mixture_limit`

Homogeneous mixture cloud toxic concentration criterion

계산 ID: `consequence/toxic-mixture-limit`

출처: Part3 eqs(3.189)-(3.190); PDF p567

| 입력 | 필수 | 타입 |
|---|---|---|
| `pure_component_limit_ppm` | 예 | `<class 'float'>` |
| `toxic_mole_fraction` | 예 | `<class 'float'>` |

출력: `modified_mixture_limit_ppm`, `component_present`, `attainable_in_mixture`

적용 범위: Divides pure-component ppm criterion by toxic mole fraction, not mass fraction. Applies when dispersion concentration represents entire homogeneous mixture using full release rate. Species-resolved concentration must not be divided again. Zero mole fraction means absent component; no finite modified criterion is returned.

## `api581.api.consequence.level2_toxic_case`

Selected toxic cloud footprints to conditional toxic consequence

계산 ID: `consequence/level2-toxic-case`

출처: Part3 §§5.9.2,5.9.4-5.9.6 eq(3.188); PDF pp565-567

| 입력 | 필수 | 타입 |
|---|---|---|
| `components` | 예 | `list[api581.toxic_level2.ToxicCloudArea]` |
| `non_ignition_probability` | 예 | `<class 'float'>` |

출력: `equipment_area_m2`, `personnel_area_m2`, `unweighted_cloud_area_m2`, `critical_component_id`, `component_cloud_areas_m2`

적용 범위: Caller supplies one chosen criterion and qualified footprint per toxic component. Criteria hierarchy: probit/LC50, then ERPG3/AEGL3/TEEL3, then IDLH/EPA endpoint. Selection within a tier is caller-qualified, not maximum across incomparable exposure criteria. Takes largest component area and applies non-ignition probability once; equipment toxic damage area is0. Does not run dispersion or sum overlapping clouds.

## `api581.api.consequence.level2_toxic_summary`

Four-hole GFF-weighted Level2 toxic consequence

계산 ID: `consequence/level2-toxic-summary`

출처: Part3 eqs(3.188),(3.191); PDF p567

| 입력 | 필수 | 타입 |
|---|---|---|
| `cases` | 예 | `list[api581.toxic_level2.ToxicFrequencyCase]` |

출력: `equipment_area_m2`, `personnel_area_m2`, `total_generic_frequency_per_year`, `by_hole_personnel_area_m2`

적용 범위: Requires all four canonical holes once. Takes component maximum and non-ignition weighting within each hole, then generic-frequency average. No DF-adjusted frequency substitution or financial/individual-risk computation. Cloud footprints and selected exposure criteria remain externally qualified inputs.

## `api581.api.level2.correlated_jet_pool`

One immediate-ignition branch with max(jet,pool) area

계산 ID: `level2/correlated-jet-pool`

출처: Part3 Figure5.3 two-phase continuous immediate branch; PDF p586; eqs(3.176)-(3.177)

| 입력 | 필수 | 타입 |
|---|---|---|
| `probability` | 예 | `<class 'float'>` |
| `jet_equipment_area_m2` | 예 | `<class 'float'>` |
| `jet_personnel_area_m2` | 예 | `<class 'float'>` |
| `pool_equipment_area_m2` | 예 | `<class 'float'>` |
| `pool_personnel_area_m2` | 예 | `<class 'float'>` |
| `consequence_source` | 예 | `<class 'str'>` |

출력: `equipment_area_m2`, `personnel_area_m2`, `maximum_equipment_area_m2`, `maximum_personnel_area_m2`, `governing_equipment`, `governing_personnel`

적용 범위: One branch probability applies to maximum jet/pool area, separately for equipment and personnel. Do not treat jet and pool as two independent terminal probabilities or sum their areas. Source footprints supplied and qualified externally; no geometric union or simultaneous-fire radiation solver.

## `api581.api.level2.flammable_case`

Flammable areas with optional correlated immediate branch

계산 ID: `level2/flammable-case`

출처: Part3 eqs(3.176)-(3.177),Figure5.3; PDF pp559,586

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `outcomes` | 예 | `list[api581.level2_summary.FlammableOutcome]` |
| `non_ignition_probability` | 예 | `<class 'float'>` |
| `event_tree_source` | 예 | `<class 'str'>` |
| `consequence_source` | 예 | `<class 'str'>` |
| `fireball_applicability_basis` | 기본값/선택 | `typing.Literal['rupture_only_text', 'figure53_instantaneous']` |
| `correlated_jet_pool` | 기본값/선택 | `api581.level2_summary.CorrelatedJetPool | None` |

출력: `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `non_ignition_probability`, `terminal_probability_sum`

적용 범위: Requires pool,jet,fireball,VCE,flash outcomes exactly once, including explicit zero branches. Together with optional correlated_jet_pool and non-ignition probabilities they sum to1. Raw areas weighted once. Correlated max(jet,pool) only for continuous leakage; separate jet/pool branches must be zero. Fireball defaults to instantaneous rupture-only text; explicit figure53_instantaneous also permits figure5.3 instantaneous leakage. Caller qualifies tree/area sources.

## `api581.api.level2.final_area`

Final Level2 component/personnel consequence areas

계산 ID: `level2/final-area`

출처: Part3 eqs(3.202)-(3.204); PDF pp572-573

| 입력 | 필수 | 타입 |
|---|---|---|
| `flammable_equipment_area_m2` | 예 | `<class 'float'>` |
| `flammable_personnel_area_m2` | 예 | `<class 'float'>` |
| `toxic_personnel_area_m2` | 예 | `<class 'float'>` |
| `nfnt_equipment_area_m2` | 예 | `<class 'float'>` |
| `nfnt_personnel_area_m2` | 예 | `<class 'float'>` |

출력: `equipment_area_m2`, `personnel_area_m2`, `consequence_area_m2`, `non_ignition_personnel_area_m2`, `governing_non_ignition_personnel_mechanism`

적용 범위: Inputs must already be event- and hole-weighted on a common basis. Equipment=flammable+NFNT; personnel=flammable+max(toxic,NFNT); final=max(equipment,personnel). Safe-event areas are0. Do not replace with Level1 maximum over all mechanisms or apply non-ignition probability twice.

## `api581.api.level2.consequence_summary`

GFF mechanism averages followed by Level2 final selection

계산 ID: `level2/consequence-summary`

출처: Part3 eqs(3.178)-(3.179),(3.191),(3.200)-(3.204); PDF pp560,567,570,572-573

| 입력 | 필수 | 타입 |
|---|---|---|
| `holes` | 예 | `list[api581.level2_summary.MechanismHole]` |

출력: `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `toxic_personnel_area_m2`, `nfnt_equipment_area_m2`, `nfnt_personnel_area_m2`, `generic_frequency_per_year`, `equipment_area_m2`, `personnel_area_m2`, `consequence_area_m2`, `non_ignition_personnel_area_m2`, `governing_non_ignition_personnel_mechanism`

적용 범위: All four holes required. Input mechanism areas already include event/non-ignition probabilities. GFF averages are formed separately before final non-ignition maximum. Averaging per-hole maxima generally gives a different result. No DF-adjusted frequencies as GFF weights.

## `api581.api.level2.scenario_consequence`

One-hole flammable/toxic/NFNT mechanism consequences

계산 ID: `level2/scenario-consequence`

출처: Part3 eqs(3.176)-(3.177),(3.188),(3.198)-(3.199),Figure5.3; PDF pp559,567,570,586

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `outcomes` | 예 | `list[api581.level2_summary.FlammableOutcome]` |
| `non_ignition_probability` | 예 | `<class 'float'>` |
| `event_tree_source` | 예 | `<class 'str'>` |
| `consequence_source` | 예 | `<class 'str'>` |
| `fireball_applicability_basis` | 기본값/선택 | `typing.Literal['rupture_only_text', 'figure53_instantaneous']` |
| `correlated_jet_pool` | 기본값/선택 | `api581.level2_summary.CorrelatedJetPool | None` |
| `toxic_components` | 예 | `list[api581.toxic_level2.ToxicCloudArea]` |
| `toxic_applicability` | 예 | `typing.Literal['evaluated', 'not_applicable']` |
| `toxic_applicability_source` | 예 | `<class 'str'>` |
| `nfnt` | 예 | `<class 'api581.level2_summary.NfntAreas'>` |

출력: `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `non_ignition_probability`, `terminal_probability_sum`, `toxic_personnel_area_m2`, `nfnt_equipment_area_m2`, `nfnt_personnel_area_m2`, `hole`

적용 범위: Supplied terminal probabilities and raw event/footprint areas; no release or dispersion calculation is inferred. One shared non-ignition probability drives toxic and NFNT. Empty toxic list requires explicit not_applicable with basis. Outputs remain separate mechanisms; final selection is after hole weighting.

## `api581.api.level2.scenario_summary`

Four raw event scenarios to final Level2 consequence areas

계산 ID: `level2/scenario-summary`

출처: Part3 §§5.8.7-5.11 eqs(3.176)-(3.204); PDF pp559-573

| 입력 | 필수 | 타입 |
|---|---|---|
| `cases` | 예 | `list[api581.level2_summary.FrequencyScenario]` |

출력: `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `toxic_personnel_area_m2`, `nfnt_equipment_area_m2`, `nfnt_personnel_area_m2`, `generic_frequency_per_year`, `equipment_area_m2`, `personnel_area_m2`, `consequence_area_m2`, `non_ignition_personnel_area_m2`, `governing_non_ignition_personnel_mechanism`

적용 범위: Caller-qualified event probabilities and raw event/dispersion areas for all four holes. Composes conditional mechanisms, separate GFF averages, flammable addition and non-ignition maximum. Does not run thermodynamics, dispersion or applicability inference.

## `api581.api.level2.assessment`

Supplied Level2 event consequences to financial/annual risk

계산 ID: `level2/assessment`

출처: Part3 §§5.8.7-5.12 eqs(3.176)-(3.204); Part1 eqs(1.1),(1.6)-(1.8)

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `<class 'str'>` |
| `management_score` | 예 | `<class 'float'>` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `damage_factor_source` | 예 | `<class 'str'>` |
| `cases` | 예 | `list[api581.level2_summary.ScenarioCase]` |
| `financial` | 예 | `<class 'api581.level2_summary.FinancialBasis'>` |

출력: `integration_scope`, `management_factor`, `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `toxic_personnel_area_m2`, `nfnt_equipment_area_m2`, `nfnt_personnel_area_m2`, `generic_frequency_per_year`, `equipment_area_m2`, `personnel_area_m2`, `consequence_area_m2`, `non_ignition_personnel_area_m2`, `governing_non_ignition_personnel_mechanism`, `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `financial_consequence`, `currency`, `cost_basis_year`, `annual_failure_frequency`, `equipment_area_risk_m2_per_year`, `personnel_area_risk_m2_per_year`, `area_risk_m2_per_year`, `financial_risk_per_year`, `frequency_weighted_equipment_area_m2`, `frequency_weighted_personnel_area_m2`

적용 범위: Explicit integration boundary: owner-qualified terminal probabilities, raw event/dispersion areas, applicability and total DF supplied. Computes GFF/Fms, Level2 area composition, five financial categories and component annual risk. Non-tank GFF only. Common component DF/Fms; no hole-specific DF substitution or automatic future damage model. Repair/outage component types must match assessment. Areas are computed here; cleanup volume/pricing/screening remain supplied. Financial equations reuse §4.12 per §5.12. Not a complete asset-data-to-risk workflow or independent certification.

## `api581.api.properties.pool_surface_interaction`

SI liquid-pool ground interaction properties

계산 ID: `properties/pool-surface-interaction`

출처: Part3 Table5.2M; PDF p582

| 입력 | 필수 | 타입 |
|---|---|---|
| `surface` | 예 | `typing.Literal['concrete', 'soil_average', 'soil_sandy_dry', 'soil_sandy_moist_8pct']` |

출력: `thermal_conductivity_w_m_k`, `thermal_diffusivity_m2_s`, `roughness_factor`

적용 범위: Printed SI table values directly; no exact back-conversion of rounded US table. Historical representative ground properties, not measured site or cryogenic validation. Concrete is source default but public selection is explicit.

## `api581.api.release.pool_evaporation_regime`

Pool boiling/non-boiling temperature classification

계산 ID: `release/pool-evaporation-regime`

출처: Part3 §5.7.4.2-5.7.4.3; PDF p544

| 입력 | 필수 | 타입 |
|---|---|---|
| `bubble_temperature_k` | 예 | `<class 'float'>` |
| `ground_temperature_k` | 예 | `<class 'float'>` |

출력: `regime`

적용 범위: Tb<Tg boiling; Tb>Tg non-boiling. Source gives no equality rule: equal temperatures return boundary_requires_qualification. Bubble temperature and ground temperature are supplied, not calculated with an EOS.

## `api581.api.release.boiling_pool_evaporation`

Printed boiling-pool evaporation correlation

계산 ID: `release/boiling-pool-evaporation`

출처: Part3 eq(3.103), Annex3.B C14=1; PDF pp544,647; Vdot/tp nomenclature PDF579

| 입력 | 필수 | 타입 |
|---|---|---|
| `bubble_temperature_k` | 예 | `<class 'float'>` |
| `ground_temperature_k` | 예 | `<class 'float'>` |
| `latent_heat_j_kg` | 예 | `<class 'float'>` |
| `surface` | 예 | `<class 'api581.evaporation.SurfaceInteraction'>` |
| `gravity_m_s2` | 기본값/선택 | `<class 'float'>` |
| `vapor_volumetric_rate_m3_s` | 예 | `<class 'float'>` |
| `time_to_steady_s` | 예 | `<class 'float'>` |

출력: `evaporation_rate_kg_s`, `latent_heat_rate_w`

적용 범위: Uses pi^1.5, not1.5. Vdot is vapor volume leaving pool surface, not liquid feed volume. Time is time to steady state per source nomenclature; this primitive does not assert an arbitrary transient evolution. No rainout, flash/EOS, inventory, site limit or LH2 validation.

## `api581.api.release.boiling_pool_radius`

Boiling-pool spreading radius at steady-state time

계산 ID: `release/boiling-pool-radius`

출처: Part3 eq(3.104); PDF p544; Vdot/tp nomenclature PDF579

| 입력 | 필수 | 타입 |
|---|---|---|
| `vapor_volumetric_rate_m3_s` | 예 | `<class 'float'>` |
| `time_to_steady_s` | 예 | `<class 'float'>` |
| `gravity_m_s2` | 기본값/선택 | `<class 'float'>` |

출력: `pool_radius_m`, `pool_area_m2`

적용 범위: r=sqrt(2/3)*(8*g*Vdot/pi)^.25*tp^.75. Vdot is vapor leaving the surface. Unconstrained correlation: no bund/terrain/site-area clipping or inventory mass balance.

## `api581.api.release.boiling_pool_steady_source`

Boiling equilibrium vapor source with duration/site support checks

계산 ID: `release/boiling-pool-steady-source`

출처: Part3 eqs(3.103)-(3.104), §5.7.4.2; PDF p544; Vdot definition PDF579

| 입력 | 필수 | 타입 |
|---|---|---|
| `bubble_temperature_k` | 예 | `<class 'float'>` |
| `ground_temperature_k` | 예 | `<class 'float'>` |
| `latent_heat_j_kg` | 예 | `<class 'float'>` |
| `surface` | 예 | `<class 'api581.evaporation.SurfaceInteraction'>` |
| `gravity_m_s2` | 기본값/선택 | `<class 'float'>` |
| `liquid_feed_rate_kg_s` | 예 | `<class 'float'>` |
| `pool_vapor_density_kg_m3` | 예 | `<class 'float'>` |
| `supply_duration_s` | 예 | `<class 'float'>` |
| `maximum_pool_area_m2` | 예 | `<class 'float'>` |

출력: `equilibrium_evaporation_rate_kg_s`, `vapor_volumetric_rate_m3_s`, `time_to_steady_s`, `pool_radius_m`, `pool_area_m2`, `vapor_source_rate_kg_s`, `support_status`

적용 범위: At equilibrium evaporation=liquid feed; Vdot=feed/pool-vapor-density, not feed/liquid-density. Solves tp from eq3.103 then radius from3.104. Usable source returned only if feed persists beyond tp and equilibrium area fits supplied site limit. Failed support is not silently clipped or replaced by feed. No growing-pool transient, finite-inventory depletion, drainage or post-release evaporation solver.

## `api581.api.release.nonboiling_pool_evaporation`

Non-boiling pool wind-driven vapor generation

계산 ID: `release/nonboiling-pool-evaporation`

출처: Part3 eq(3.105), Annex3.B C15; PDF pp544,647; P/R/Ts units PDF578-579

| 입력 | 필수 | 타입 |
|---|---|---|
| `bubble_temperature_k` | 예 | `<class 'float'>` |
| `ground_temperature_k` | 예 | `<class 'float'>` |
| `bubble_pressure_at_ground_pa_abs` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `molecular_weight_kg_kmol` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 예 | `<class 'float'>` |
| `wind_speed_m_s` | 예 | `<class 'float'>` |
| `pool_radius_m` | 예 | `<class 'float'>` |

출력: `evaporation_rate_kg_s`

적용 범위: Follows printed C15=4.685 with Pb,g in kPa and R=8314; Pa public input divided by1000. Denominator uses printed storage Ts, not automatic substitution of ground temperature. Wind exponent.78 and radius exponent1.89. Wind qualified at6ft above grade. Zero wind gives zero correlation rate, not a model of molecular diffusion/quiescent evaporation. No site/inventory clipping or LH2 validation.

## `api581.api.release.nonboiling_pool_steady_source`

Non-boiling equilibrium source radius and site support check

계산 ID: `release/nonboiling-pool-steady-source`

출처: Part3 eq(3.105), §5.7.4.3; PDF p544

| 입력 | 필수 | 타입 |
|---|---|---|
| `bubble_temperature_k` | 예 | `<class 'float'>` |
| `ground_temperature_k` | 예 | `<class 'float'>` |
| `bubble_pressure_at_ground_pa_abs` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `molecular_weight_kg_kmol` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 예 | `<class 'float'>` |
| `wind_speed_m_s` | 예 | `<class 'float'>` |
| `liquid_feed_rate_kg_s` | 예 | `<class 'float'>` |
| `maximum_pool_area_m2` | 예 | `<class 'float'>` |

출력: `equilibrium_evaporation_rate_kg_s`, `pool_radius_m`, `pool_area_m2`, `vapor_source_rate_kg_s`, `support_status`

적용 범위: Solves evaporation=feed for radius. Time to equilibrium is not supplied by this equation and is not invented. Positive feed with zero wind/vapor pressure has no finite equilibrium in this correlation. Site limit failures return no usable source; no arbitrary radius clipping. Requires a separately qualified sustained feed/equilibrium assumption, not a transient pool or mass-balance simulation.

## `api581.api.release.level2_release_phase`

Pressure-based Level2 release-phase screening

계산 ID: `release/level2-release-phase`

출처: Part3 eqs(3.95)-(3.97); PDF p541

| 입력 | 필수 | 타입 |
|---|---|---|
| `storage_pressure_pa_abs` | 예 | `<class 'float'>` |
| `saturation_pressure_at_storage_pa_abs` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |

출력: `release_phase`, `status`

적용 범위: Release phase at opening differs from storage phase and final atmospheric flashed phase. Source inequalities overlap at Psat=Ps and omit equality at Psat=Patm; these boundaries return no selected phase. Ps=Patm returns no_driving_pressure. Saturation pressure is caller-qualified; no supercritical EOS inference.

## `api581.api.release.level2_orifice_rate`

Level2 phase-selected gas/liquid/conservative two-phase source rate

계산 ID: `release/level2-orifice-rate`

출처: Part3 §§5.3.3-5.3.6 eqs(3.95)-(3.97); PDF pp541-542; §4.3 eqs(3.3),(3.6)-(3.7)

| 입력 | 필수 | 타입 |
|---|---|---|
| `storage_pressure_pa_abs` | 예 | `<class 'float'>` |
| `saturation_pressure_at_storage_pa_abs` | 예 | `<class 'float'>` |
| `ambient_pressure_pa_abs` | 기본값/선택 | `<class 'float'>` |
| `diameter_m` | 예 | `<class 'float'>` |
| `gas_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `gas_molecular_weight_kg_kmol` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `gas_heat_capacity_ratio` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `liquid_density_kg_m3` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `gas_discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `liquid_discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `liquid_viscosity_factor` | 기본값/선택 | `<class 'float'>` |
| `qualified_boundary_phase` | 기본값/선택 | `typing.Literal['vapor', 'liquid', 'two_phase'] | None` |
| `boundary_phase_source` | 기본값/선택 | `str | None` |

출력: `mass_rate_kg_s`, `area_m2`, `release_phase`, `rate_method`, `phase_basis`

적용 범위: Two-phase branch uses source-permitted conservative LIQUID approximation, not HEM/Omega or a flashing two-phase flow solver. Vapor uses ideal gas constant upstream model. Boundary phase override requires a nonblank owner basis and cannot contradict a classified phase. No-driving-pressure returns zero without inventing phase. Caller qualifies saturation pressure and properties; no thermodynamic or LH2 validation.

## `api581.api.release.kletz_rainout_fraction`

Kletz rainout mass-fraction correlation

계산 ID: `release/kletz-rainout-fraction`

출처: Part3 eqs(3.98)-(3.99); PDF p543

| 입력 | 필수 | 타입 |
|---|---|---|
| `flash_mass_fraction` | 예 | `<class 'float'>` |

출력: `rainout_mass_fraction`

적용 범위: Rainout=max(0,1-2*flash_fraction). Flash fraction must be supplied by qualified isentropic/isenthalpic atmospheric flash calculation. This correlation does not calculate flash state or verify entrainment composition; no LH2 validation.

## `api581.api.release.rainout_rate_split`

Rainout pool and aerosol-containing jet rates

계산 ID: `release/rainout-rate-split`

출처: Part3 eqs(3.100)-(3.101); PDF p543

| 입력 | 필수 | 타입 |
|---|---|---|
| `adjusted_mass_rate_kg_s` | 예 | `<class 'float'>` |
| `rainout_mass_fraction` | 예 | `<class 'float'>` |

출력: `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`

적용 범위: Pool=adjusted rate*rainout; jet=adjusted rate*(1-rainout). Jet may contain liquid aerosol and must not be labeled pure vapor. Rainout correlation/flash composition supplied separately; no pool evaporation in this split.

## `api581.api.release.jet_liquid_entrainment`

Printed or post-flash-mass-balance aerosol fraction

계산 ID: `release/jet-liquid-entrainment`

출처: Part3 eq(3.102); PDF p543; phase-fraction nomenclature PDF575-576

| 입력 | 필수 | 타입 |
|---|---|---|
| `rainout_mass_fraction` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'post_flash_mass_balance']` |
| `stored_liquid_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `flash_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `post_flash_vapor_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`

적용 범위: api581_printed uses stored_liquid_fraction*flash_fraction/(1-rainout), exactly the printed product. Reports physical_range but does not prove EOS consistency. post_flash_mass_balance uses supplied total post-flash vapor fraction and remaining liquid after rainout, a separately labeled conservation interpretation, not an authorized erratum. Exactly the selected basis fields required. No jet at rainout1 has no defined composition; returns None, not division by zero.

## `api581.api.release.level2_source_partition`

Pool/jet/vapor/aerosol mass and rate partition

계산 ID: `release/level2-source-partition`

출처: Part3 eqs(3.100)-(3.102), STEP7.3-7.6; PDF pp543,545

| 입력 | 필수 | 타입 |
|---|---|---|
| `rainout_mass_fraction` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'post_flash_mass_balance']` |
| `stored_liquid_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `flash_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `post_flash_vapor_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `adjusted_mass_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `rainout_basis_source` | 예 | `<class 'str'>` |
| `flash_property_source` | 예 | `<class 'str'>` |

출력: `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`, `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`, `pool_liquid_mass_kg`, `jet_total_mass_kg`, `jet_liquid_rate_kg_s`, `jet_vapor_rate_kg_s`, `jet_liquid_mass_kg`, `jet_vapor_mass_kg`

적용 범위: Adjusted total rate and released mass must be qualified after detection/isolation and inventory limits. Pool+jet and jet-vapor+jet-liquid conserve mass. Printed composition is explicit and not asserted as EOS closure; nonphysical printed fractions rejected. Rainout and flash properties supplied with source; no pool evaporation, flash/EOS, two-phase hydraulic solver or actual dispersion run.

## `api581.api.release.flammable_phase_rates`

Flammable total/liquid/vapor rates for ignition

계산 ID: `release/flammable-phase-rates`

출처: Part3 eqs(3.106)-(3.108); PDF p546

| 입력 | 필수 | 타입 |
|---|---|---|
| `adjusted_mass_rate_kg_s` | 예 | `<class 'float'>` |
| `flammable_mass_fraction` | 예 | `<class 'float'>` |
| `flash_mass_fraction` | 예 | `<class 'float'>` |

출력: `flammable_rate_kg_s`, `flammable_vapor_rate_kg_s`, `flammable_liquid_rate_kg_s`

적용 범위: Flash fraction supplied by qualified thermodynamics. Phase liquid rate is not pool rainout rate; aerosol/rainout partition is separate. Flammable mass fraction, not mole fraction, multiplies total adjusted rate.

## `api581.api.events.ambient_ignition`

Flash-point/rate ambient ignition correlation

계산 ID: `events/ambient-ignition`

출처: Part3 eqs(3.109)-(3.110),C4B/C5/C12; PDF pp546-547,647

| 입력 | 필수 | 타입 |
|---|---|---|
| `phase` | 예 | `typing.Literal['liquid', 'vapor']` |
| `flammable_rate_kg_s` | 예 | `<class 'float'>` |
| `flash_point_temperature_k` | 예 | `<class 'float'>` |
| `correlation_basis_source` | 예 | `<class 'str'>` |

출력: `ambient_ignition_probability`, `evaluated_rate_kg_s`, `rate_capped`

적용 범위: Printed C12=1.8 converts Kelvin flash point to Rankine; C4B=2.205 converts capped kg/s to lb/s inside natural log. Uses C5=25.2kg/s even though adjacent text also says25.22. Fit range is not certified by accepting source text: requires positive rate exponent and probability<=1, rejects nonphysical extrapolation. Zero rate uses limiting probability0. No LH2 ignition validation.

## `api581.api.events.ait_ignition_maximum`

Ignition probability at autoignition temperature

계산 ID: `events/ait-ignition-maximum`

출처: Part3 eqs(3.111)-(3.112); PDF pp547-548

| 입력 | 필수 | 타입 |
|---|---|---|
| `phase` | 예 | `typing.Literal['liquid', 'vapor']` |
| `molecular_weight_kg_kmol` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `maximum_ignition_probability`

적용 범위: Liquid maximum1; vapor follows printed molecular-weight interpolation with lower floor.7. MW2 gives.9 and MW>=170 gives.7. This is a release ignition probability correlation, not deterministic autoignition physics or a hydrogen certification.

## `api581.api.events.probability_temperature`

Reference-to-AIT probability interpolation

계산 ID: `events/probability-temperature`

출처: Part3 eqs(3.113)-(3.114),(3.116)-(3.117),C16; PDF pp548,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `reference_basis` | 예 | `typing.Literal['api581_printed_c16', 'qualified_reference']` |
| `qualified_reference_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `reference_source` | 예 | `<class 'str'>` |
| `probability_at_reference` | 예 | `<class 'float'>` |
| `probability_at_ait` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 예 | `<class 'float'>` |
| `autoignition_temperature_k` | 예 | `<class 'float'>` |

출력: `probability`, `temperature_weight`, `reference_temperature_k`

적용 범위: Printed C16=30.89K and US70R conflict with ambient-temperature discussion; no silent conversion to70F. Required basis chooses literal C16 or a caller-qualified reference. Ts below reference and AIT<=reference rejected; Ts>=AIT returns AIT limit. AIT probability must be at least reference probability. Qualified reference is not an authorized erratum.

## `api581.api.events.conditional_table`

Table5.3 conditional event probabilities

계산 ID: `events/conditional-table`

출처: Part3 Table5.3; PDF p583

| 입력 | 필수 | 타입 |
|---|---|---|
| `phase` | 예 | `typing.Literal['liquid', 'vapor']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |

출력: `immediate_at_reference`, `immediate_at_ait`, `vce_given_delayed`, `flash_given_delayed`

적용 범위: Historical expert-opinion defaults by phase/release type. Immediate probability at reference, not automatically at current storage temperature. VCE and flash columns are conditional on delayed ignition, not unconditional outcomes.

## `api581.api.events.two_phase_probability`

Explicit-basis liquid/vapor conditional probability mixing

계산 ID: `events/two-phase-probability`

출처: Part3 eqs(3.115),(3.118)-(3.119),(3.122); PDF pp548-549

| 입력 | 필수 | 타입 |
|---|---|---|
| `liquid_probability` | 예 | `<class 'float'>` |
| `vapor_probability` | 예 | `<class 'float'>` |
| `flash_mass_fraction` | 예 | `<class 'float'>` |
| `mixing_basis` | 예 | `typing.Literal['api581_printed_liquid_weight', 'qualified_vapor_weight']` |
| `weighting_source` | 예 | `<class 'str'>` |

출력: `probability`, `mixing_basis`

적용 범위: Printed equations weight LIQUID by flash fraction and VAPOR by its complement, despite flash-as-vapor wording. Literal and separately qualified vapor weighting are explicit alternatives; neither is silently selected or asserted as an erratum. Inputs must be probabilities of the same conditional quantity. No complete two-phase terminal tree or correlated max(jet,pool) consequence representation here.

## `api581.api.events.single_phase_tree`

Single-phase terminal paths from Figures5.3/5.4

계산 ID: `events/single-phase-tree`

출처: Part3 Figures5.3/5.4; PDF pp586-587; conflicting example eq(3.125) PDF549

| 입력 | 필수 | 타입 |
|---|---|---|
| `phase` | 예 | `typing.Literal['liquid', 'vapor']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `case_type` | 예 | `typing.Literal['leakage', 'rupture']` |
| `ignition_probability` | 예 | `<class 'float'>` |
| `immediate_given_ignition` | 예 | `<class 'float'>` |
| `vce_given_delayed` | 예 | `<class 'float'>` |
| `branch_probability_source` | 예 | `<class 'str'>` |

출력: `terminal_probabilities`, `non_ignition_probability`, `probability_sum`, `fireball_applicability_basis`

적용 범위: Follows figure VCE path factor pvcedi, not conflicting printed example1-pvcedi. Figure5.3 labels instantaneous vapor leakage as fireball, although text restricts fireballs to rupture; output explicitly reports figure53_instantaneous applicability when needed. Rupture tree supported only for instantaneous release. Non-ignition is not automatically safe: toxic/NFNT must be evaluated separately.

## `api581.api.events.single_phase_ignition`

Rate/flash-point/temperature to single-phase terminal probabilities

계산 ID: `events/single-phase-ignition`

출처: Part3 eqs(3.109)-(3.117),Table5.3,Figures5.3/5.4; PDF pp547-549,583,586-587

| 입력 | 필수 | 타입 |
|---|---|---|
| `reference_basis` | 예 | `typing.Literal['api581_printed_c16', 'qualified_reference']` |
| `qualified_reference_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `reference_source` | 예 | `<class 'str'>` |
| `phase` | 예 | `typing.Literal['liquid', 'vapor']` |
| `flammable_rate_kg_s` | 예 | `<class 'float'>` |
| `flash_point_temperature_k` | 예 | `<class 'float'>` |
| `correlation_basis_source` | 예 | `<class 'str'>` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `case_type` | 예 | `typing.Literal['leakage', 'rupture']` |
| `molecular_weight_kg_kmol` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `storage_temperature_k` | 예 | `<class 'float'>` |
| `autoignition_temperature_k` | 예 | `<class 'float'>` |

출력: `ambient_ignition_probability`, `evaluated_rate_kg_s`, `rate_capped`, `maximum_ignition_probability`, `terminal_probabilities`, `non_ignition_probability`, `probability_sum`, `fireball_applicability_basis`, `ignition_probability`, `immediate_given_ignition`, `vce_given_delayed`, `flash_given_delayed`, `reference_temperature_k`, `temperature_weight`

적용 범위: Composes supplied phase flammable rate and qualified flash point, printed or qualified temperature reference, AIT maximum and Table5.3. Does not infer release phase, flash properties, two-phase mixture or probability validation from process data. Zero source has zero ignition even above AIT. Figure/text fireball conflict is reported via applicability basis. Continuous rupture and below-reference temperature unsupported.

## `api581.api.events.fireball_given_immediate`

Fireball conditional applicability from text or figure basis

계산 ID: `events/fireball-given-immediate`

출처: Part3 eqs(3.123)-(3.124),Figure5.3; PDF pp549,586

| 입력 | 필수 | 타입 |
|---|---|---|
| `phase` | 예 | `typing.Literal['liquid', 'vapor', 'two_phase']` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `case_type` | 예 | `typing.Literal['leakage', 'rupture']` |
| `applicability_basis` | 예 | `typing.Literal['rupture_only_text', 'figure53_instantaneous']` |

출력: `fireball_given_immediate`

적용 범위: Conditional on immediate ignition. Text basis requires instantaneous rupture of vapor/two-phase; explicit figure53 basis also allows instantaneous leakage. Liquid and continuous cases give0. Correlation does not establish thermal-model applicability or certify leakage fireballs.

## `api581.api.events.two_phase_tree`

Two-phase figure paths including one correlated jet/pool event

계산 ID: `events/two-phase-tree`

출처: Part3 Figures5.3/5.4,eqs(3.123)-(3.126); PDF pp549,586-587

| 입력 | 필수 | 타입 |
|---|---|---|
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `case_type` | 예 | `typing.Literal['leakage', 'rupture']` |
| `qualified_rupture_fireball_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `rupture_fireball_source` | 기본값/선택 | `str | None` |
| `ignition_probability` | 예 | `<class 'float'>` |
| `immediate_given_ignition` | 예 | `<class 'float'>` |
| `vce_given_delayed` | 예 | `<class 'float'>` |
| `branch_probability_source` | 예 | `<class 'str'>` |

출력: `terminal_probabilities`, `non_ignition_probability`, `probability_sum`, `fireball_applicability_basis`, `fireball_given_immediate`, `fireball_probability_basis`

적용 범위: Continuous leakage immediate branch is one jet_pool_max terminal, not independent jet and pool fires. Instantaneous leakage immediate branch is fireball per figure53 despite text conflict. Rupture instantaneous immediate fireball fraction defaults1 per eq3.123; figure54 alternative requires explicit fraction/source, remaining immediate probability goes to pool. Continuous rupture unsupported. Non-ignition still requires toxic/NFNT analysis.

## `api581.api.events.two_phase_ignition`

Phase rates and ignition correlations to two-phase terminal paths

계산 ID: `events/two-phase-ignition`

출처: Part3 eqs(3.106)-(3.124),Table5.3,Figures5.3/5.4; PDF pp546-549,583,586-587

| 입력 | 필수 | 타입 |
|---|---|---|
| `reference_basis` | 예 | `typing.Literal['api581_printed_c16', 'qualified_reference']` |
| `qualified_reference_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `reference_source` | 예 | `<class 'str'>` |
| `release_type` | 예 | `typing.Literal['continuous', 'instantaneous']` |
| `case_type` | 예 | `typing.Literal['leakage', 'rupture']` |
| `qualified_rupture_fireball_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `rupture_fireball_source` | 기본값/선택 | `str | None` |
| `adjusted_mass_rate_kg_s` | 예 | `<class 'float'>` |
| `flammable_mass_fraction` | 예 | `<class 'float'>` |
| `flash_mass_fraction` | 예 | `<class 'float'>` |
| `liquid_flash_point_temperature_k` | 예 | `<class 'float'>` |
| `vapor_flash_point_temperature_k` | 예 | `<class 'float'>` |
| `vapor_molecular_weight_kg_kmol` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 예 | `<class 'float'>` |
| `autoignition_temperature_k` | 예 | `<class 'float'>` |
| `correlation_basis_source` | 예 | `<class 'str'>` |
| `mixing_basis` | 예 | `typing.Literal['api581_printed_liquid_weight', 'qualified_vapor_weight']` |
| `weighting_source` | 예 | `<class 'str'>` |

출력: `terminal_probabilities`, `non_ignition_probability`, `probability_sum`, `fireball_applicability_basis`, `fireball_given_immediate`, `fireball_probability_basis`, `flammable_rate_kg_s`, `flammable_vapor_rate_kg_s`, `flammable_liquid_rate_kg_s`, `ignition_probability`, `immediate_given_ignition`, `vce_given_delayed`, `flash_given_delayed`, `liquid_ignition_probability`, `vapor_ignition_probability`, `liquid_immediate_given_ignition`, `vapor_immediate_given_ignition`, `temperature_weight`, `reference_temperature_k`, `mixing_basis`

적용 범위: Requires strictly mixed atmospheric flash fraction0<f<1; endpoints belong to single-phase model. Composes phase-specific flammable rates, flash points, vapor MW, common qualified AIT/reference, Table5.3 and explicit phase weighting. Printed liquid-weight basis is preserved as source interpretation, not validated physical phase weighting. Zero fuel gives zero ignition. No EOS, two-phase hydraulics, effect footprints or LH2 validation; correlated jet_pool_max must remain one area branch.

## `api581.api.tank.fluid_table`

AST SI representative fluid properties

계산 ID: `tank/fluid-table`

출처: Part3 Table6.1M; PDF p604

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['gasoline', 'light_diesel', 'heavy_diesel', 'fuel_oil', 'crude_oil', 'heavy_fuel_oil', 'heavy_crude_oil']` |

출력: `molecular_weight_kg_kmol`, `liquid_density_kg_m3`, `dynamic_viscosity_pa_s`

적용 범위: Historical representative liquid properties, not an operating-temperature EOS. Printed SI density/viscosity retained. No automatic alias to a Level1 representative fluid or LH2 properties.

## `api581.api.tank.soil_table`

AST SI soil conductivity bounds and porosity

계산 ID: `tank/soil-table`

출처: Part3 Table6.2M; PDF p605

| 입력 | 필수 | 타입 |
|---|---|---|
| `soil` | 예 | `typing.Literal['coarse_sand', 'fine_sand', 'very_fine_sand', 'silt', 'sandy_clay', 'clay', 'concrete_asphalt', 'gravel']` |

출력: `printed_lower_bound_cm_s`, `printed_upper_bound_cm_s`, `porosity`

적용 범위: Printed lower/upper labels are reversed for most rows; fields preserve printed labels and values without sorting. Eq3.207 arithmetic mean is symmetric. Raw conductivity units cm/s, not m/day. Representative soil values need site qualification.

## `api581.api.tank.soil_water_conductivity`

Mean water hydraulic conductivity in m/day

계산 ID: `tank/soil-water-conductivity`

출처: Part3 eq(3.207),Annex3.B C31; PDF pp593,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `printed_lower_bound_cm_s` | 예 | `<class 'float'>` |
| `printed_upper_bound_cm_s` | 예 | `<class 'float'>` |

출력: `water_hydraulic_conductivity_m_day`

적용 범위: Uses arithmetic mean, not geometric mean: C31=864 converts cm/s to m/day. Accepts reversed printed bound ordering without relabeling it.

## `api581.api.tank.fluid_conductivity`

Product hydraulic conductivity from water reference

계산 ID: `tank/fluid-conductivity`

출처: Part3 eq(3.205); PDF p592

| 입력 | 필수 | 타입 |
|---|---|---|
| `water_hydraulic_conductivity_m_day` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |
| `dynamic_viscosity_pa_s` | 예 | `<class 'float'>` |
| `water_density_kg_m3` | 예 | `<class 'float'>` |
| `water_dynamic_viscosity_pa_s` | 예 | `<class 'float'>` |

출력: `product_hydraulic_conductivity_m_day`

적용 범위: Water density/viscosity must be supplied at qualified reference conditions. Product/water density ratio and inverse viscosity ratio applied; no hidden standard-water defaults or temperature correction.

## `api581.api.tank.seepage_velocity`

AST product seepage velocity through soil

계산 ID: `tank/seepage-velocity`

출처: Part3 eq(3.206); PDF p592

| 입력 | 필수 | 타입 |
|---|---|---|
| `product_hydraulic_conductivity_m_day` | 예 | `<class 'float'>` |
| `porosity` | 예 | `<class 'float'>` |

출력: `seepage_velocity_m_day`

적용 범위: Conductivity divided by strictly positive porosity. Representative porous-medium approximation; no groundwater plume or capillary/unsaturated transport solver.

## `api581.api.tank.bottom_hole_count`

AST bottom small-hole count from diameter

계산 ID: `tank/bottom-hole-count`

출처: Part3 Table6.5,Annex3.B C36; PDF pp607,649

| 입력 | 필수 | 타입 |
|---|---|---|
| `tank_diameter_m` | 예 | `<class 'float'>` |

출력: `small_hole_count`, `medium_hole_count`, `large_hole_count`, `outside_tabulated_diameter_range`

적용 범위: max(1,nint((D/30.5)^2)) with positive half-up nearest-integer rounding, not Python bankers rounding. Medium/large counts0. Formula evaluated outside tabulated30.5-91.4m range is flagged; no extrapolation validity claimed.

## `api581.api.tank.bottom_inventory`

Full cylindrical AST bottom inventory

계산 ID: `tank/bottom-inventory`

출처: Part3 eqs(3.219)-(3.221); PDF p596

| 입력 | 필수 | 타입 |
|---|---|---|
| `tank_diameter_m` | 예 | `<class 'float'>` |
| `fill_height_m` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |

출력: `available_volume_m3`, `available_volume_bbl`, `available_mass_kg`

적용 범위: Vertical cylindrical tank, full contents above bottom. Printed C13=6.29bbl/m3 retained. No roof volume, dished geometry or connected inventory.

## `api581.api.tank.shell_course_inventory`

Inventory and head above AST shell-course lower edge

계산 ID: `tank/shell-course-inventory`

출처: Part3 eqs(3.214)-(3.218); PDF pp595-596

| 입력 | 필수 | 타입 |
|---|---|---|
| `tank_diameter_m` | 예 | `<class 'float'>` |
| `fill_height_m` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |
| `course_index` | 예 | `<class 'int'>` |
| `course_height_m` | 예 | `<class 'float'>` |

출력: `available_volume_m3`, `available_volume_bbl`, `available_mass_kg`, `course_bottom_elevation_m`, `available_liquid_head_m`, `course_wet`

적용 범위: Leak located at course lower edge, equal course heights, index starts1. Above-fill courses return physical dry head/inventory0 instead of negative fluid. This dry-course handling is explicit geometry interpretation. Printed C13=6.29 retained.

## `api581.api.tank.shell_flow`

Constant-head AST shell-course liquid discharge

계산 ID: `tank/shell-flow`

출처: Part3 eq(3.209),Annex3.B C32; PDF pp593-594,648

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole_diameter_m` | 예 | `<class 'float'>` |
| `liquid_head_m` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `gravity_m_s2` | 기본값/선택 | `<class 'float'>` |

출력: `native_rate_bbl_day`, `volume_rate_m3_s`, `mass_rate_kg_s`, `hole_area_m2`

적용 범위: Printed C32=.543 with orifice area mm2, g/head in SI, native result bbl/day. Converts result to m3/s with C13=6.29; rounded constants differ slightly from exact Torricelli units. Cd constrained to source fully-turbulent.60-.65 range, default.61. Constant head, not tank drainage transient or detection/isolation reduction.

## `api581.api.tank.bottom_flow`

AST bottom Bernoulli/Giraud/transition discharge

계산 ID: `tank/bottom-flow`

출처: Part3 eqs(3.210)-(3.212),Annex3.B C33-C40; PDF pp594,649

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole_diameter_m` | 예 | `<class 'float'>` |
| `liquid_height_m` | 예 | `<class 'float'>` |
| `product_hydraulic_conductivity_m_day` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |
| `number_of_holes` | 예 | `<class 'int'>` |
| `has_release_prevention_barrier` | 예 | `<class 'bool'>` |
| `transition_hole_basis` | 예 | `typing.Literal['api581_printed', 'per_hole_scaled']` |
| `soil_contact_factor` | 기본값/선택 | `<class 'float'>` |
| `gravity_m_s2` | 기본값/선택 | `<class 'float'>` |

출력: `native_rate_bbl_day`, `volume_rate_m3_s`, `mass_rate_kg_s`, `per_hole_native_rate_bbl_day`, `equation`, `liquid_head_used_m`, `lower_conductivity_threshold_m_day`, `upper_conductivity_threshold_m_day`, `applied_hole_multiplier`, `transition_hole_basis`

적용 범위: Native units d mm, head m, Kh m/day, result bbl/day. Printed C37 SI/US regime thresholds disagree under conversion; SI threshold used literally, no cross-unit regime equivalence claimed. Eq3.210/211 multiply number of holes; printed3.212 omits it. Required api581_printed preserves omission; per_hole_scaled is explicit alternative, not authorized erratum. RPB substitutes head.0762m when liquid exists; empty tank remains zero. Soil-contact factor.21-1.15. Small-hole constant-head soil leak model, not rupture inventory or groundwater transport.

## `api581.api.tank.shell_detection_time`

AST shell leak detection-time criterion

계산 ID: `tank/shell-detection-time`

출처: Part3 §6.7.2 STEP7.2,eq(3.223); PDF pp596-597

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole_diameter_m` | 예 | `<class 'float'>` |
| `diameter_boundary_basis` | 예 | `typing.Literal['printed_3_17_mm', 'inch_0_125']` |

출력: `detection_time_days`, `diameter_boundary_m`

적용 범위: Source prints3.17mm paired with.125inch=3.175mm; required basis preserves selection. Diameter at/below selected boundary7days, above1day. AST does not apply generic detection/isolation reduction factors.

## `api581.api.tank.bottom_detection_time`

AST bottom leak detection-time criterion

계산 ID: `tank/bottom-detection-time`

출처: Part3 §6.7.3 STEP7.2; PDF p597

| 입력 | 필수 | 타입 |
|---|---|---|
| `foundation` | 예 | `typing.Literal['concrete_asphalt', 'other']` |
| `has_release_prevention_barrier` | 예 | `<class 'bool'>` |
| `overlap_basis` | 기본값/선택 | `typing.Literal['foundation_priority', 'barrier_priority'] | None` |

출력: `detection_time_days`, `selected_basis`

적용 범위: Concrete/asphalt7days, RPB30days, otherwise360days. Conditions overlap if concrete/asphalt AND RPB: explicit priority required instead of inventing precedence. This is source detection time, not a generic isolation-system factor.

## `api581.api.tank.release_volume`

Inventory-limited AST leakage or full-volume rupture

계산 ID: `tank/release-volume`

출처: Part3 eqs(3.223)-(3.230),§6.5; PDF pp596-598

| 입력 | 필수 | 타입 |
|---|---|---|
| `release_case` | 예 | `typing.Literal['leak', 'rupture']` |
| `native_rate_bbl_day` | 예 | `<class 'float'>` |
| `available_volume_m3` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |
| `detection_time_days` | 예 | `<class 'float'>` |

출력: `release_duration_days`, `released_volume_bbl`, `released_volume_m3`, `released_mass_kg`, `printed_mass_index`, `release_type`

적용 범위: Leak volume is min(rate*min(inventory/rate,detection time),inventory); rupture uses all available volume without invented duration. Source AST release type remains continuous. Eq3.225/227 print mass=Bbl without density/conversion; printed_mass_index preserves that number separately. released_mass_kg uses(volume m3*density) from3.218/221, an explicit dimensional interpretation, not an authorized erratum. C13=6.29 retained.

## `api581.api.tank.environment_cost_table`

AST estimated environmental costs in source USD/bbl

계산 ID: `tank/environment-cost-table`

출처: Part3 Table6.6; PDF p608

| 입력 | 필수 | 타입 |
|---|---|---|
| `sensitivity` | 예 | `typing.Literal['low', 'medium', 'high']` |

출력: `cost_by_location_usd_per_bbl`

적용 범위: Historical source estimates, not current prices. Source supplies no explicit price year for Table6.6; no 2001 assumption is inferred from repair Table4.15. End user must qualify applicability and escalation.

## `api581.api.tank.surface_spill_partition`

Sequential AST surface spill allocation

계산 ID: `tank/surface-spill-partition`

출처: Part3 eqs(3.232)-(3.235),(3.238)-(3.241); PDF pp599-600

| 입력 | 필수 | 타입 |
|---|---|---|
| `released_volume_bbl` | 예 | `<class 'float'>` |
| `fraction_leaving_dike` | 예 | `<class 'float'>` |
| `fraction_on_site` | 예 | `<class 'float'>` |
| `fraction_off_site` | 예 | `<class 'float'>` |

출력: `in_dike_bbl`, `surface_on_site_bbl`, `surface_off_site_bbl`, `surface_water_bbl`

적용 범위: Fractions are conditional: on-site applies to volume leaving dike; off-site applies to what remains after on-site. Use fractions0..1, not percentage numbers0..100. No dike capacity or surface transport simulation.

## `api581.api.tank.groundwater_arrival`

AST seepage travel time to groundwater

계산 ID: `tank/groundwater-arrival`

출처: Part3 eq(3.244); PDF p601

| 입력 | 필수 | 타입 |
|---|---|---|
| `distance_to_groundwater_m` | 예 | `<class 'float'>` |
| `seepage_velocity_m_day` | 예 | `<class 'float'>` |

출력: `arrival_time_days`, `arrival_status`

적용 범위: Zero distance means already at groundwater; positive distance with zero velocity returns null arrival time, not infinity. No plume, retardation or groundwater migration model.

## `api581.api.tank.subsurface_spill_partition`

AST bottom leakage allocation to groundwater and subsoil

계산 ID: `tank/subsurface-spill-partition`

출처: Part3 eqs(3.245)-(3.247); PDF p601

| 입력 | 필수 | 타입 |
|---|---|---|
| `leaked_volume_bbl` | 예 | `<class 'float'>` |
| `detection_time_days` | 예 | `<class 'float'>` |
| `groundwater_arrival_time_days` | 예 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `groundwater_bbl`, `subsoil_bbl`, `groundwater_fraction`

적용 범위: Printed detection time is the denominator, even if inventory depletion limits actual leak duration. This is not a transient transport solution. Null arrival means no finite arrival. Positive detection time required; zero-volume leakage returns zero in both compartments.

## `api581.api.tank.shell_environment_cost`

GFF-weighted AST shell environmental consequence

계산 ID: `tank/shell-environment-cost`

출처: Part3 eqs(3.208),(3.231)-(3.243); PDF pp593,599-600

| 입력 | 필수 | 타입 |
|---|---|---|
| `generic_frequency_by_hole_per_year` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `cost_by_location_per_bbl` | 예 | `dict[typing.Literal['in_dike', 'surface_on_site', 'surface_off_site', 'subsoil', 'groundwater', 'surface_water'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `currency` | 예 | `<class 'str'>` |
| `cost_basis` | 예 | `<class 'str'>` |
| `fraction_leaving_dike` | 예 | `<class 'float'>` |
| `fraction_on_site` | 예 | `<class 'float'>` |
| `fraction_off_site` | 예 | `<class 'float'>` |
| `released_volume_by_hole_bbl` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |

출력: `leak_environment_cost`, `rupture_environment_cost`, `environment_cost`, `currency`, `cost_basis`, `weighted_leak_volume_bbl`, `weighted_rupture_volume_bbl`, `weighted_leak_surface_volumes_bbl`, `weighted_rupture_surface_volumes_bbl`

적용 범위: Caller supplies qualified per-hole GFF; total is their sum (eq3.208), including rupture in leak denominator. No ambiguous printed tank-total lookup. Frequencies are normalized once; no ignition probability applied. Costs are per bbl in one declared currency and caller-declared cost basis. No implicit escalation, FX conversion or current-price claim. Table6.6 values require owner qualification.

## `api581.api.tank.bottom_environment_cost`

GFF-weighted AST bottom environmental consequence

계산 ID: `tank/bottom-environment-cost`

출처: Part3 eqs(3.238)-(3.249); PDF pp600-601

| 입력 | 필수 | 타입 |
|---|---|---|
| `generic_frequency_by_hole_per_year` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `cost_by_location_per_bbl` | 예 | `dict[typing.Literal['in_dike', 'surface_on_site', 'surface_off_site', 'subsoil', 'groundwater', 'surface_water'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `currency` | 예 | `<class 'str'>` |
| `cost_basis` | 예 | `<class 'str'>` |
| `fraction_leaving_dike` | 예 | `<class 'float'>` |
| `fraction_on_site` | 예 | `<class 'float'>` |
| `fraction_off_site` | 예 | `<class 'float'>` |
| `leaked_volume_by_hole_bbl` | 예 | `dict[typing.Literal['small', 'medium', 'large'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `total_tank_volume_bbl` | 예 | `<class 'float'>` |
| `detection_time_days` | 예 | `<class 'float'>` |
| `groundwater_arrival_time_days` | 예 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `leak_environment_cost`, `rupture_environment_cost`, `environment_cost`, `currency`, `cost_basis`, `weighted_groundwater_volume_bbl`, `weighted_subsoil_volume_bbl`, `weighted_rupture_volume_bbl`, `weighted_rupture_surface_volumes_bbl`

적용 범위: Caller supplies qualified per-hole GFF; total is their sum (eq3.208), including rupture in leak denominator. No ambiguous printed tank-total lookup. Frequencies are normalized once; no ignition probability applied. Costs are per bbl in one declared currency and caller-declared cost basis. No implicit escalation, FX conversion or current-price claim. Table6.6 values require owner qualification. Bottom leaks enter subsoil/groundwater; rupture releases total tank inventory to four surface locations. Printed detection-time partition retained despite inventory-limited release duration. Surrounding-equipment and injury costs are not applicable to bottom assessment; this API returns environmental cost only.

## `api581.api.tank.bottom_repair_cost`

AST bottom repair with rupture-only diameter scaling

계산 ID: `tank/bottom-repair-cost`

출처: Part3 eq(3.250),Tables4.15/4.16,Annex3.B C36; PDF pp532-533,601,649

| 입력 | 필수 | 타입 |
|---|---|---|
| `generic_frequency_by_hole_per_year` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `tank_diameter_m` | 예 | `<class 'float'>` |
| `repair_cost_by_hole` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `material_factor` | 예 | `<class 'float'>` |
| `currency` | 예 | `<class 'str'>` |
| `cost_basis` | 예 | `<class 'str'>` |

출력: `component_repair_cost`, `currency`, `cost_basis`

적용 범위: Caller supplies all four repair costs and qualified GFF. Only rupture cost scales by (D/30.5m)^2; small/medium/large repair costs do not. Historical financial/repair-table returns USD2001; caller must explicitly qualify escalation/currency and retain consistent cost basis.

## `api581.api.tank.generic_frequency`

AST generic frequencies with explicit equation-summed total

계산 ID: `tank/generic-frequency`

출처: Part2 Table3.1; Part3 eq(3.208); PDF pp147,593

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_type` | 예 | `typing.Literal['TANKBOTTOM', 'COURSE-1-10']` |

출력: `by_hole_per_year`, `total_per_year`, `printed_total_per_year`, `sum_minus_printed_per_year`, `total_basis`

적용 범위: Uses the sum of four hole frequencies authorized by eq3.208. Printed tank totals differ and are returned separately; this is not an authorized correction of Table3.1. COURSE-1-10 is one shell-course component, not the whole tank or ten multiplied courses.

## `api581.api.tank.component_outage`

AST GFF-weighted component outage duration

계산 ID: `tank/component-outage`

출처: Part3 eq(3.88),Table4.17,§6.12; PDF pp506,534,599-601

| 입력 | 필수 | 타입 |
|---|---|---|
| `generic_frequency_by_hole_per_year` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `component_type` | 예 | `typing.Literal['TANKBOTTOM', 'COURSE-1-10']` |
| `outage_multiplier` | 예 | `<class 'float'>` |
| `override_days` | 기본값/선택 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |

출력: `component_outage_days`, `effective_days_by_hole`

적용 범위: All four qualified per-hole GFF are supplied by caller and normalized by their sum. Source NA is not zero: nonzero-frequency NA requires owner override. Zero-frequency NA contributes zero. No automatic diameter correction of outage duration.

## `api581.api.tank.bottom_financial_consequence`

Compose AST bottom repair, production and environmental consequence

계산 ID: `tank/bottom-financial-consequence`

출처: Part3 §6.12.3,eqs(3.88),(3.90),(3.243)-(3.250); PDF pp506,600-601

| 입력 | 필수 | 타입 |
|---|---|---|
| `repair` | 예 | `<class 'api581.tank_financial.TankRepairBasis'>` |
| `outage_multiplier` | 예 | `<class 'float'>` |
| `override_outage_days` | 기본값/선택 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `production_cost_per_day` | 예 | `<class 'float'>` |
| `generic_frequency_source` | 예 | `<class 'str'>` |
| `generic_frequency_by_hole_per_year` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `cost_by_location_per_bbl` | 예 | `dict[typing.Literal['in_dike', 'surface_on_site', 'surface_off_site', 'subsoil', 'groundwater', 'surface_water'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `currency` | 예 | `<class 'str'>` |
| `cost_basis` | 예 | `<class 'str'>` |
| `fraction_leaving_dike` | 예 | `<class 'float'>` |
| `fraction_on_site` | 예 | `<class 'float'>` |
| `fraction_off_site` | 예 | `<class 'float'>` |
| `leaked_volume_by_hole_bbl` | 예 | `dict[typing.Literal['small', 'medium', 'large'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `total_tank_volume_bbl` | 예 | `<class 'float'>` |
| `detection_time_days` | 예 | `<class 'float'>` |
| `groundwater_arrival_time_days` | 예 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `tank_diameter_m` | 예 | `<class 'float'>` |

출력: `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `leak_environment_cost`, `rupture_environment_cost`, `financial_consequence`, `currency`, `cost_basis_year`, `cost_basis`

적용 범위: Per-hole GFF, release volumes and qualified environmental costs are supplied inputs. Environment, production, surrounding-equipment and injury unit costs must use the declared currency and repair.cost_basis_year; cost_basis records the common valuation. Table6.6 has no stated price year and must be qualified explicitly before combining with escalated USD2001 repair costs. Component-only consequence. Damage applicability, release hydraulics, consequence areas and monetary qualification are not inferred. Per-hole frequencies normalize once including rupture. No additional ignition weighting or automatic whole-tank course summation. Bottom surrounding-equipment and injury costs are not applicable per §6.12.3 and returned zero. Rupture repair alone scales by diameter squared. Groundwater uses printed detection time, not inventory depletion time.

## `api581.api.tank.shell_financial_consequence`

Compose five AST shell-course financial consequence categories

계산 ID: `tank/shell-financial-consequence`

출처: Part3 §6.12.2,eqs(3.85)-(3.91),(3.231)-(3.243); PDF pp505-506,599-600

| 입력 | 필수 | 타입 |
|---|---|---|
| `repair` | 예 | `<class 'api581.tank_financial.TankRepairBasis'>` |
| `outage_multiplier` | 예 | `<class 'float'>` |
| `override_outage_days` | 기본값/선택 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `production_cost_per_day` | 예 | `<class 'float'>` |
| `generic_frequency_source` | 예 | `<class 'str'>` |
| `generic_frequency_by_hole_per_year` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `cost_by_location_per_bbl` | 예 | `dict[typing.Literal['in_dike', 'surface_on_site', 'surface_off_site', 'subsoil', 'groundwater', 'surface_water'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `currency` | 예 | `<class 'str'>` |
| `cost_basis` | 예 | `<class 'str'>` |
| `fraction_leaving_dike` | 예 | `<class 'float'>` |
| `fraction_on_site` | 예 | `<class 'float'>` |
| `fraction_off_site` | 예 | `<class 'float'>` |
| `released_volume_by_hole_bbl` | 예 | `dict[typing.Literal['small', 'medium', 'large', 'rupture'], typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])]]` |
| `equipment_area_m2` | 예 | `<class 'float'>` |
| `personnel_area_m2` | 예 | `<class 'float'>` |
| `equipment_cost_per_m2` | 예 | `<class 'float'>` |
| `population_density_per_m2` | 예 | `<class 'float'>` |
| `cost_per_injury` | 예 | `<class 'float'>` |

출력: `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `leak_environment_cost`, `rupture_environment_cost`, `financial_consequence`, `currency`, `cost_basis_year`, `cost_basis`

적용 범위: Per-hole GFF, release volumes and qualified environmental costs are supplied inputs. Environment, production, surrounding-equipment and injury unit costs must use the declared currency and repair.cost_basis_year; cost_basis records the common valuation. Table6.6 has no stated price year and must be qualified explicitly before combining with escalated USD2001 repair costs. Component-only consequence. Damage applicability, release hydraulics, consequence areas and monetary qualification are not inferred. Per-hole frequencies normalize once including rupture. No additional ignition weighting or automatic whole-tank course summation. Areas must already be GFF-weighted from a qualified AST flammable/toxic assessment. No automatic AST NFNT area is inferred. Surrounding-outage correlation uses equivalent USD2001 via explicit escalation/FX factors; damage area is not converted again.

## `api581.api.tank.bottom_risk_assessment`

AST bottom financial consequence and annual risk

계산 ID: `tank/bottom-risk-assessment`

출처: Part1 eqs(1.1),(1.8); Part2 eqs(2.9)-(2.10); Part3 §6.12.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `management_score` | 예 | `<class 'float'>` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `damage_factor_source` | 예 | `<class 'str'>` |
| `financial` | 예 | `<class 'api581.tank_financial.BottomFinancial'>` |

출력: `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `leak_environment_cost`, `rupture_environment_cost`, `financial_consequence`, `currency`, `cost_basis_year`, `cost_basis`, `generic_frequency_per_year`, `management_factor`, `annual_failure_frequency`, `financial_risk_per_year`, `annual_frequency_by_hole`, `integration_scope`

적용 범위: Per-hole GFF, release volumes and qualified environmental costs are supplied inputs. Environment, production, surrounding-equipment and injury unit costs must use the declared currency and repair.cost_basis_year; cost_basis records the common valuation. Table6.6 has no stated price year and must be qualified explicitly before combining with escalated USD2001 repair costs. Component-only consequence. Damage applicability, release hydraulics, consequence areas and monetary qualification are not inferred. Per-hole frequencies normalize once including rupture. No additional ignition weighting or automatic whole-tank course summation. Uniform supplied DF and Fms apply to all four holes of one component. Annual financial risk is sum(GFF)*DF*Fms*already-GFF-weighted financial consequence. This composition does not calculate damage applicability, dynamic release, whole-tank common-cause risk or individual/societal risk. Bottom assessment returns financial risk only; no unsupported zero-valued physical consequence area is implied. Surrounding-equipment and injury costs are not applicable; rupture-only repair diameter scaling and printed detection-time groundwater partition retained.

## `api581.api.tank.shell_risk_assessment`

AST shell-course financial and area risks

계산 ID: `tank/shell-risk-assessment`

출처: Part1 eqs(1.1),(1.6)-(1.8); Part2 eqs(2.9)-(2.10); Part3 §6.12.2

| 입력 | 필수 | 타입 |
|---|---|---|
| `management_score` | 예 | `<class 'float'>` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `damage_factor_source` | 예 | `<class 'str'>` |
| `financial` | 예 | `<class 'api581.tank_financial.ShellFinancial'>` |

출력: `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `leak_environment_cost`, `rupture_environment_cost`, `financial_consequence`, `currency`, `cost_basis_year`, `cost_basis`, `generic_frequency_per_year`, `management_factor`, `annual_failure_frequency`, `financial_risk_per_year`, `annual_frequency_by_hole`, `integration_scope`, `equipment_area_risk_m2_per_year`, `personnel_area_risk_m2_per_year`

적용 범위: Per-hole GFF, release volumes and qualified environmental costs are supplied inputs. Environment, production, surrounding-equipment and injury unit costs must use the declared currency and repair.cost_basis_year; cost_basis records the common valuation. Table6.6 has no stated price year and must be qualified explicitly before combining with escalated USD2001 repair costs. Component-only consequence. Damage applicability, release hydraulics, consequence areas and monetary qualification are not inferred. Per-hole frequencies normalize once including rupture. No additional ignition weighting or automatic whole-tank course summation. Uniform supplied DF and Fms apply to all four holes of one component. Annual financial risk is sum(GFF)*DF*Fms*already-GFF-weighted financial consequence. This composition does not calculate damage applicability, dynamic release, whole-tank common-cause risk or individual/societal risk. Equipment/personnel area risks use externally qualified GFF-weighted AST areas. No automatic AST NFNT, course summation or whole-tank spatial overlap resolution.

## `api581.api.tank.shell_hole_sizes`

AST shell-course representative hole diameters and areas

계산 ID: `tank/shell-hole-sizes`

출처: Part3 Tables6.3/6.3M; PDF p606

| 입력 | 필수 | 타입 |
|---|---|---|
| `tank_diameter_m` | 예 | `<class 'float'>` |

출력: `diameter_by_hole_m`, `area_by_hole_m2`

적용 범위: Small3.175mm, medium6.35mm, large50.8mm, rupture=tank diameter/4. This selects representative holes, not measured-hole classification. Rupture diameter is a source convention, not validation of tank-diameter/4 orifice hydraulics.

## `api581.api.tank.bottom_hole_sizes`

AST bottom representative hole diameters and areas

계산 ID: `tank/bottom-hole-sizes`

출처: Part3 Tables6.4/6.4M; PDF pp606-607

| 입력 | 필수 | 타입 |
|---|---|---|
| `tank_diameter_m` | 예 | `<class 'float'>` |
| `has_release_prevention_barrier` | 예 | `<class 'bool'>` |

출력: `diameter_by_hole_m`, `area_by_hole_m2`

적용 범위: Small3.175mm with RPB or12.7mm without, medium/large zero, rupture=tank diameter/4. Printed SI Table6.4M rupture row shows only Yes; US Table6.4 explicitly covers Yes/No under shared tank-diameter/4 formula. No-RPB rupture follows that US row converted to SI, not an authorized SI erratum. No rupture flow/hole count inferred from Table6.5.

## `api581.api.tank.shell_source_assessment`

Compose AST shell holes, head, inventory, rates and released quantities

계산 ID: `tank/shell-source-assessment`

출처: Part3 §§6.1-6.7,Tables6.1M/6.3M,eqs(3.208)-(3.209),(3.214)-(3.227); PDF pp592-597,604,606

| 입력 | 필수 | 타입 |
|---|---|---|
| `tank_diameter_m` | 예 | `<class 'float'>` |
| `fill_height_m` | 예 | `<class 'float'>` |
| `course_index` | 예 | `<class 'int'>` |
| `course_height_m` | 예 | `<class 'float'>` |
| `fluid` | 예 | `typing.Literal['gasoline', 'light_diesel', 'heavy_diesel', 'fuel_oil', 'crude_oil', 'heavy_fuel_oil', 'heavy_crude_oil']` |
| `diameter_boundary_basis` | 예 | `typing.Literal['printed_3_17_mm', 'inch_0_125']` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `gravity_m_s2` | 기본값/선택 | `<class 'float'>` |

출력: `diameter_by_hole_m`, `area_by_hole_m2`, `available_volume_m3`, `available_volume_bbl`, `available_mass_kg`, `generic_frequency_by_hole_per_year`, `generic_total_per_year`, `printed_generic_total_per_year`, `generic_total_basis`, `native_rate_by_hole_bbl_day`, `mass_rate_by_hole_kg_s`, `detection_time_by_hole_days`, `release_duration_by_hole_days`, `released_volume_by_hole_bbl`, `released_volume_by_hole_m3`, `released_mass_by_hole_kg`, `release_type`, `liquid_density_kg_m3`, `course_bottom_elevation_m`, `available_liquid_head_m`, `course_wet`, `source_scope`

적용 범위: Uses representative Table6.1M liquid properties, constant head and C13=6.29bbl/m3. No operating-temperature EOS, connected inventory or transient drainage. Source mass=Bbl printing is not used as kg: mass is volume*density, the explicitly qualified dimensional interpretation. Table3.1 hole frequencies use eq3.208 summed total, with printed total returned separately. One component only; no whole-tank course summation, area consequences or damage applicability inferred. AST release type remains continuous. No generic detection/isolation reduction factors. Equal-height courses; source at course lower edge. Above-fill courses use physical dry inventory/head0. Shell3.17mm vs3.175mm detection ambiguity requires explicit boundary basis. Eq3.209 evaluated for all four representative holes as STEP3.3 specifies; nominal rupture rate is a printed constant-head convention, not validated catastrophic-rupture hydraulics. Rupture uses full above-course inventory with null duration/detection; no invented rupture duration.

## `api581.api.tank.bottom_source_assessment`

Compose AST soil, holes, inventory, seepage and released quantities

계산 ID: `tank/bottom-source-assessment`

출처: Part3 §§6.1-6.7,Tables6.1M/6.2M/6.4/6.4M/6.5,eqs(3.205)-(3.212),(3.219)-(3.230); PDF pp592-598,604-607

| 입력 | 필수 | 타입 |
|---|---|---|
| `tank_diameter_m` | 예 | `<class 'float'>` |
| `fill_height_m` | 예 | `<class 'float'>` |
| `fluid` | 예 | `typing.Literal['gasoline', 'light_diesel', 'heavy_diesel', 'fuel_oil', 'crude_oil', 'heavy_fuel_oil', 'heavy_crude_oil']` |
| `soil` | 예 | `typing.Literal['coarse_sand', 'fine_sand', 'very_fine_sand', 'silt', 'sandy_clay', 'clay', 'concrete_asphalt', 'gravel']` |
| `water_density_kg_m3` | 예 | `<class 'float'>` |
| `water_dynamic_viscosity_pa_s` | 예 | `<class 'float'>` |
| `foundation` | 예 | `typing.Literal['concrete_asphalt', 'other']` |
| `has_release_prevention_barrier` | 예 | `<class 'bool'>` |
| `detection_overlap_basis` | 기본값/선택 | `typing.Literal['foundation_priority', 'barrier_priority'] | None` |
| `transition_hole_basis` | 예 | `typing.Literal['api581_printed', 'per_hole_scaled']` |
| `soil_contact_factor` | 기본값/선택 | `<class 'float'>` |
| `gravity_m_s2` | 기본값/선택 | `<class 'float'>` |

출력: `diameter_by_hole_m`, `area_by_hole_m2`, `available_volume_m3`, `available_volume_bbl`, `available_mass_kg`, `generic_frequency_by_hole_per_year`, `generic_total_per_year`, `printed_generic_total_per_year`, `generic_total_basis`, `native_rate_by_hole_bbl_day`, `mass_rate_by_hole_kg_s`, `detection_time_by_hole_days`, `release_duration_by_hole_days`, `released_volume_by_hole_bbl`, `released_volume_by_hole_m3`, `released_mass_by_hole_kg`, `release_type`, `liquid_density_kg_m3`, `small_hole_count`, `medium_hole_count`, `large_hole_count`, `outside_tabulated_diameter_range`, `product_hydraulic_conductivity_m_day`, `seepage_velocity_m_day`, `bottom_flow_equation`, `applied_small_hole_multiplier`, `detection_time_days`, `detection_selected_basis`, `source_scope`

적용 범위: Uses representative Table6.1M liquid properties, constant head and C13=6.29bbl/m3. No operating-temperature EOS, connected inventory or transient drainage. Source mass=Bbl printing is not used as kg: mass is volume*density, the explicitly qualified dimensional interpretation. Table3.1 hole frequencies use eq3.208 summed total, with printed total returned separately. One component only; no whole-tank course summation, area consequences or damage applicability inferred. AST release type remains continuous. No generic detection/isolation reduction factors. Soil arithmetic mean preserves reversed printed bounds; explicit water reference properties required. RPB small-hole head.0762m when filled; empty tank zero. SI C37 threshold retained despite SI/US mismatch. Transition count omission requires explicit printed vs per-hole-scaled basis. No-RPB rupture diameter follows complete US Table6.4 row; SI rupture row is incomplete. Medium/large holes have zero count/flow. Table6.5 gives no rupture count, so rupture flow and duration are null; rupture volume is whole inventory per eq3.230. Bottom detection with concrete/asphalt AND RPB requires explicit priority. Count outside30.5-91.4m is flagged, not qualified by this composition.

## `api581.api.tank.bottom_integrated_assessment`

AST bottom geometry and soil through source, financial consequence and annual risk

계산 ID: `tank/bottom-integrated-assessment`

출처: Part3 §§6.1-6.7,Tables6.1M/6.2M/6.4/6.4M/6.5,eqs(3.205)-(3.212),(3.219)-(3.230); PDF pp592-598,604-607; Part3 eq(3.244); PDF p601; Part1 eqs(1.1),(1.8); Part2 eqs(2.9)-(2.10); Part3 §6.12.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `management_score` | 예 | `<class 'float'>` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `damage_factor_source` | 예 | `<class 'str'>` |
| `source` | 예 | `<class 'api581.tank_source.BottomSource'>` |
| `distance_to_groundwater_m` | 예 | `<class 'float'>` |
| `economics` | 예 | `<class 'api581.tank_integrated.BottomEconomics'>` |

출력: `diameter_by_hole_m`, `area_by_hole_m2`, `available_volume_m3`, `available_volume_bbl`, `available_mass_kg`, `generic_frequency_by_hole_per_year`, `generic_total_per_year`, `printed_generic_total_per_year`, `generic_total_basis`, `native_rate_by_hole_bbl_day`, `mass_rate_by_hole_kg_s`, `detection_time_by_hole_days`, `release_duration_by_hole_days`, `released_volume_by_hole_bbl`, `released_volume_by_hole_m3`, `released_mass_by_hole_kg`, `release_type`, `liquid_density_kg_m3`, `small_hole_count`, `medium_hole_count`, `large_hole_count`, `outside_tabulated_diameter_range`, `product_hydraulic_conductivity_m_day`, `seepage_velocity_m_day`, `bottom_flow_equation`, `applied_small_hole_multiplier`, `detection_time_days`, `detection_selected_basis`, `source_scope`, `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `leak_environment_cost`, `rupture_environment_cost`, `financial_consequence`, `currency`, `cost_basis_year`, `cost_basis`, `generic_frequency_per_year`, `management_factor`, `annual_failure_frequency`, `financial_risk_per_year`, `annual_frequency_by_hole`, `integration_scope`, `groundwater_arrival_time_days`

적용 범위: Uses representative Table6.1M liquid properties, constant head and C13=6.29bbl/m3. No operating-temperature EOS, connected inventory or transient drainage. Source mass=Bbl printing is not used as kg: mass is volume*density, the explicitly qualified dimensional interpretation. Table3.1 hole frequencies use eq3.208 summed total, with printed total returned separately. One component only; no whole-tank course summation, area consequences or damage applicability inferred. AST release type remains continuous. No generic detection/isolation reduction factors. Soil arithmetic mean preserves reversed printed bounds; explicit water reference properties required. RPB small-hole head.0762m when filled; empty tank zero. SI C37 threshold retained despite SI/US mismatch. Transition count omission requires explicit printed vs per-hole-scaled basis. No-RPB rupture diameter follows complete US Table6.4 row; SI rupture row is incomplete. Medium/large holes have zero count/flow. Table6.5 gives no rupture count, so rupture flow and duration are null; rupture volume is whole inventory per eq3.230. Bottom detection with concrete/asphalt AND RPB requires explicit priority. Count outside30.5-91.4m is flagged, not qualified by this composition. Per-hole GFF, release volumes and qualified environmental costs are supplied inputs. Environment, production, surrounding-equipment and injury unit costs must use the declared currency and repair.cost_basis_year; cost_basis records the common valuation. Table6.6 has no stated price year and must be qualified explicitly before combining with escalated USD2001 repair costs. Component-only consequence. Damage applicability, release hydraulics, consequence areas and monetary qualification are not inferred. Per-hole frequencies normalize once including rupture. No additional ignition weighting or automatic whole-tank course summation. Uniform supplied DF and Fms apply to all four holes of one component. Annual financial risk is sum(GFF)*DF*Fms*already-GFF-weighted financial consequence. This composition does not calculate damage applicability, dynamic release, whole-tank common-cause risk or individual/societal risk. Bottom assessment returns financial risk only; no unsupported zero-valued physical consequence area is implied. Surrounding-equipment and injury costs are not applicable; rupture-only repair diameter scaling and printed detection-time groundwater partition retained. Computes source inventory/rates/volumes, summed table GFF and seepage arrival from the same geometry/soil request. DF applicability and monetary qualification are external supplied assumptions. Single bottom only; no shell, whole-tank common-cause or digital-twin sensor assimilation inferred.

## `api581.api.tank.diked_pool_consequence`

AST pool radiation with explicit dike-area interpretation

계산 ID: `tank/diked-pool-consequence`

출처: Part3 §6.7.2; PDF p596; Part3 §5.8.2; eqs(3.128)-(3.151); PDF pp550-553

| 입력 | 필수 | 타입 |
|---|---|---|
| `burning` | 예 | `<class 'api581.effects.PoolBurning'>` |
| `liquid_rate_kg_s` | 예 | `<class 'float'>` |
| `available_liquid_mass_kg` | 예 | `<class 'float'>` |
| `liquid_density_kg_m3` | 예 | `<class 'float'>` |
| `pool_depth_m` | 기본값/선택 | `<class 'float'>` |
| `site_maximum_area_m2` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `air_density_kg_m3` | 예 | `<class 'float'>` |
| `vapor_density_kg_m3` | 예 | `<class 'float'>` |
| `wind_speed_m_s` | 예 | `<class 'float'>` |
| `radiative_fraction` | 기본값/선택 | `<class 'float'>` |
| `atmosphere` | 예 | `<class 'api581.pool_fire.Atmosphere'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'geometry_checked']` |
| `distance_convention` | 예 | `typing.Literal['printed_surface_ratio', 'surface_to_axis']` |
| `maximum_surface_distance_m` | 예 | `<class 'float'>` |
| `personnel_threshold_w_m2` | 기본값/선택 | `<class 'float'>` |
| `equipment_threshold_w_m2` | 기본값/선택 | `<class 'float'>` |
| `dike_area_m2` | 예 | `<class 'float'>` |
| `dike_limit_basis` | 예 | `typing.Literal['burning_pool_area', 'burning_and_consequence_area']` |

출력: `burning_rate_kg_m2_s`, `burning_area_m2`, `inventory_limited_area_m2`, `pool_area_m2`, `pool_radius_m`, `flame_length_m`, `flame_tilt_rad`, `surface_emissive_power_w_m2`, `personnel_area_m2`, `equipment_area_m2`, `personnel_status`, `equipment_status`, `equation_basis`, `distance_convention`, `unclipped_personnel_safe_surface_distance_m`, `unclipped_equipment_safe_surface_distance_m`, `unclipped_equipment_area_m2`, `unclipped_personnel_area_m2`, `effective_pool_area_limit_m2`, `dike_area_m2`, `equipment_area_clipped`, `personnel_area_clipped`, `dike_limit_basis`

적용 범위: Single pool/event only; no ignition/event or hole weighting. Qualified liquid rainout rate/mass supplied; inventory input is liquid mass, not automatic substitution of ambiguous frac_ro in printed eq(3.132). Site limit mandatory. Explicit printed/geometry_checked and distance choices; source-view-factor discrepancies are not silently corrected. Uniform plume model, no smoke/terrain/flame-impingement or LH2-specific validation. Source says pool fire area must not exceed dike area without distinguishing burning pool from radiation consequence. Required burning_pool_area caps physical pool before radiation; burning_and_consequence_area additionally clips reported consequence areas numerically. Neither is an authorized erratum. Raw radiation areas and threshold separations remain separately labeled; numerical clipping is not a spatial dike intersection. No ignition/hole weighting.

## `api581.api.tank.shell_level2_case`

AST continuous shell event-weighted flammable and toxic areas

계산 ID: `tank/shell-level2-case`

출처: Part3 §§6.5,6.7.2,6.8-6.11; PDF pp596,598; Part3 eqs(3.176)-(3.177),(3.188)

| 입력 | 필수 | 타입 |
|---|---|---|
| `hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `release_type` | 기본값/선택 | `typing.Literal['continuous']` |
| `outcomes` | 예 | `list[api581.level2_summary.FlammableOutcome]` |
| `non_ignition_probability` | 예 | `<class 'float'>` |
| `event_tree_source` | 예 | `<class 'str'>` |
| `consequence_source` | 예 | `<class 'str'>` |
| `fireball_applicability_basis` | 기본값/선택 | `typing.Literal['rupture_only_text', 'figure53_instantaneous']` |
| `correlated_jet_pool` | 기본값/선택 | `api581.level2_summary.CorrelatedJetPool | None` |
| `toxic_components` | 예 | `list[api581.toxic_level2.ToxicCloudArea]` |
| `toxic_applicability` | 예 | `typing.Literal['evaluated', 'not_applicable']` |
| `toxic_applicability_source` | 예 | `<class 'str'>` |
| `dike_area_m2` | 예 | `<class 'float'>` |
| `burning_pool_area_m2` | 예 | `<class 'float'>` |
| `pool_dike_limit_basis` | 예 | `typing.Literal['burning_pool_area', 'burning_and_consequence_area']` |

출력: `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `non_ignition_probability`, `terminal_probability_sum`, `toxic_personnel_area_m2`, `nfnt_status`

적용 범위: AST shell release type is continuous, including rupture. Raw event probabilities and flammable/toxic footprints are externally qualified. All five canonical flammable events required; inapplicable fireball branch zero. Shared non-ignition probability weights toxic once; empty toxic components require explicit not-applicable basis. NFNT is not determined for AST per §6.10 and is absent from the request. Pool burning area must fit dike; explicit dike interpretation and raw footprint provenance are required. Burning area0 requires zero pool radiation footprint; no circular radiation area is silently clipped after weighting.

## `api581.api.tank.shell_level2_summary`

AST four-hole GFF-weighted flammable plus toxic final areas

계산 ID: `tank/shell-level2-summary`

출처: Part3 §§6.10-6.11,eqs(3.178)-(3.179),(3.191),(3.202)-(3.204); PDF pp560,567,572-573,598

| 입력 | 필수 | 타입 |
|---|---|---|
| `cases` | 예 | `list[api581.tank_shell.ShellCase]` |

출력: `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `toxic_personnel_area_m2`, `equipment_area_m2`, `personnel_area_m2`, `consequence_area_m2`, `generic_frequency_per_year`, `by_hole_flammable_equipment_area_m2`, `by_hole_flammable_personnel_area_m2`, `by_hole_toxic_personnel_area_m2`, `nfnt_status`

적용 범위: AST shell release type is continuous, including rupture. Raw event probabilities and flammable/toxic footprints are externally qualified. All five canonical flammable events required; inapplicable fireball branch zero. Shared non-ignition probability weights toxic once; empty toxic components require explicit not-applicable basis. NFNT is not determined for AST per §6.10 and is absent from the request. Pool burning area must fit dike; explicit dike interpretation and raw footprint provenance are required. Burning area0 requires zero pool radiation footprint; no circular radiation area is silently clipped after weighting. Exactly four canonical holes on one common dike basis. Uses COURSE-1-10 Table3.1 frequencies with eq3.208 total. Mechanism GFF averages precede final equipment=flammable and personnel=flammable+toxic; this is Level2 additive composition with NFNT absent, not Level1 maximum selection. No DF in GFF averaging.

## `api581.api.tank.shell_integrated_assessment`

AST shell source, supplied event footprints, financial consequence and annual risk

계산 ID: `tank/shell-integrated-assessment`

출처: Part3 §§6.1-6.7,Tables6.1M/6.3M,eqs(3.208)-(3.209),(3.214)-(3.227); PDF pp592-597,604,606; Part3 §§6.10-6.11,eqs(3.178)-(3.179),(3.191),(3.202)-(3.204); PDF pp560,567,572-573,598; Part1 eqs(1.1),(1.6)-(1.8); Part2 eqs(2.9)-(2.10); Part3 §6.12.2

| 입력 | 필수 | 타입 |
|---|---|---|
| `management_score` | 예 | `<class 'float'>` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `damage_factor_source` | 예 | `<class 'str'>` |
| `source` | 예 | `<class 'api581.tank_source.ShellSource'>` |
| `cases` | 예 | `list[api581.tank_shell.ShellCase]` |
| `economics` | 예 | `<class 'api581.tank_shell.ShellEconomics'>` |

출력: `diameter_by_hole_m`, `area_by_hole_m2`, `available_volume_m3`, `available_volume_bbl`, `available_mass_kg`, `generic_frequency_by_hole_per_year`, `generic_total_per_year`, `printed_generic_total_per_year`, `generic_total_basis`, `native_rate_by_hole_bbl_day`, `mass_rate_by_hole_kg_s`, `detection_time_by_hole_days`, `release_duration_by_hole_days`, `released_volume_by_hole_bbl`, `released_volume_by_hole_m3`, `released_mass_by_hole_kg`, `release_type`, `liquid_density_kg_m3`, `course_bottom_elevation_m`, `available_liquid_head_m`, `course_wet`, `source_scope`, `flammable_equipment_area_m2`, `flammable_personnel_area_m2`, `toxic_personnel_area_m2`, `equipment_area_m2`, `personnel_area_m2`, `consequence_area_m2`, `generic_frequency_per_year`, `by_hole_flammable_equipment_area_m2`, `by_hole_flammable_personnel_area_m2`, `by_hole_toxic_personnel_area_m2`, `nfnt_status`, `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `leak_environment_cost`, `rupture_environment_cost`, `financial_consequence`, `currency`, `cost_basis_year`, `cost_basis`, `management_factor`, `annual_failure_frequency`, `financial_risk_per_year`, `annual_frequency_by_hole`, `integration_scope`, `equipment_area_risk_m2_per_year`, `personnel_area_risk_m2_per_year`

적용 범위: Uses representative Table6.1M liquid properties, constant head and C13=6.29bbl/m3. No operating-temperature EOS, connected inventory or transient drainage. Source mass=Bbl printing is not used as kg: mass is volume*density, the explicitly qualified dimensional interpretation. Table3.1 hole frequencies use eq3.208 summed total, with printed total returned separately. One component only; no whole-tank course summation, area consequences or damage applicability inferred. AST release type remains continuous. No generic detection/isolation reduction factors. Equal-height courses; source at course lower edge. Above-fill courses use physical dry inventory/head0. Shell3.17mm vs3.175mm detection ambiguity requires explicit boundary basis. Eq3.209 evaluated for all four representative holes as STEP3.3 specifies; nominal rupture rate is a printed constant-head convention, not validated catastrophic-rupture hydraulics. Rupture uses full above-course inventory with null duration/detection; no invented rupture duration. AST shell release type is continuous, including rupture. Raw event probabilities and flammable/toxic footprints are externally qualified. All five canonical flammable events required; inapplicable fireball branch zero. Shared non-ignition probability weights toxic once; empty toxic components require explicit not-applicable basis. NFNT is not determined for AST per §6.10 and is absent from the request. Pool burning area must fit dike; explicit dike interpretation and raw footprint provenance are required. Burning area0 requires zero pool radiation footprint; no circular radiation area is silently clipped after weighting. Exactly four canonical holes on one common dike basis. Uses COURSE-1-10 Table3.1 frequencies with eq3.208 total. Mechanism GFF averages precede final equipment=flammable and personnel=flammable+toxic; this is Level2 additive composition with NFNT absent, not Level1 maximum selection. No DF in GFF averaging. Per-hole GFF, release volumes and qualified environmental costs are supplied inputs. Environment, production, surrounding-equipment and injury unit costs must use the declared currency and repair.cost_basis_year; cost_basis records the common valuation. Table6.6 has no stated price year and must be qualified explicitly before combining with escalated USD2001 repair costs. Component-only consequence. Damage applicability, release hydraulics, consequence areas and monetary qualification are not inferred. Per-hole frequencies normalize once including rupture. No additional ignition weighting or automatic whole-tank course summation. Uniform supplied DF and Fms apply to all four holes of one component. Annual financial risk is sum(GFF)*DF*Fms*already-GFF-weighted financial consequence. This composition does not calculate damage applicability, dynamic release, whole-tank common-cause risk or individual/societal risk. Equipment/personnel area risks use externally qualified GFF-weighted AST areas. No automatic AST NFNT, course summation or whole-tank spatial overlap resolution. Computes source/GFF/environment from one geometry request and inserts event/GFF-weighted AST areas into financial risk. Footprints and event probabilities remain external and must be qualified for this computed source. Does not infer dispersion, EOS, source-to-footprint consistency or whole-tank spatial overlap. Dry source requires zero flammable/toxic footprints for every hole.

## `api581.api.dispersion.native_engine_capabilities`

Inspect optional SLABx engine capabilities

계산 ID: `dispersion/native-engine-capabilities`

출처: Native adapter deployment contract; tested mappings SLABx1.0.8 and SLABx-LH2 0.2.0

| 입력 | 필수 | 타입 |
|---|---|---|
| `requested_engines` | 기본값/선택 | `list[typing.Literal['slabx', 'slabx-lh2']]` |

출력: `requested_engines`, `required_versions`, `installed_versions`, `engine_status`, `module_import_status`, `worker_isolation`, `supported_operations`, `probe_scope`

적용 범위: Deployment probe only; it performs no dispersion calculation and does not validate a native engine scientifically. Missing or mismatched packages are reported as status values rather than silently replaced. Available operations are the adapter's supported constant pool/jet boundaries, not a claim that every source domain is implemented.

## `api581.api.dispersion.native_pool_centreline`

Run native SLABx/SLABx-LH2 constant vapor pool in an isolated process

계산 ID: `dispersion/native-pool-centreline`

출처: Part3 §§5.8.5-5.8.6,5.9: external dispersion boundary; SLABx1.0.8 core.source.EvaporatingPool/core.plume.run_dispersion/post.concentration.concentration_field; SLABx-LH2 0.2.0 water_ice.with_sublimation/plume_width_coupling/diagnostics.premise_summary

| 입력 | 필수 | 타입 |
|---|---|---|
| `engine` | 예 | `typing.Literal['slabx', 'slabx-lh2']` |
| `substance` | 예 | `<class 'api581.slabx_adapter.NativeSubstance'>` |
| `atmosphere` | 예 | `<class 'api581.slabx_adapter.NativeAtmosphere'>` |
| `receptor_height_m` | 예 | `<class 'float'>` |
| `averaging_time_s` | 예 | `<class 'float'>` |
| `plume_distance_limit_m` | 예 | `<class 'float'>` |
| `puff_time_limit_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `puff_steps` | 기본값/선택 | `<class 'int'>` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `threshold_source` | 예 | `<class 'str'>` |
| `source_qualification` | 예 | `<class 'str'>` |
| `meander_closure` | 예 | `typing.Literal['ermak', 'sigma_theta']` |
| `lh2_plume_width_coupling` | 예 | `<class 'bool'>` |
| `timeout_s` | 기본값/선택 | `<class 'float'>` |
| `vapor_source_rate_kg_s` | 예 | `<class 'float'>` |
| `source_area_m2` | 예 | `<class 'float'>` |
| `release_duration_s` | 예 | `<class 'float'>` |

출력: `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `effective_source_half_width_m`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`

적용 범위: Optional native packages required: tested mapping slabx1.0.8 and slabx-lh2 0.2.0. Each run uses a fresh Python subprocess so LH2 module-global corrections cannot alter host calculations. No silent alternate engine/version or fallback model. Only constant finite-duration ground-level pure-vapor evaporating pool at normal boiling temperature and101325Pa. Required rate is evaporated vapor, not liquid feed/orifice rate. Caller qualifies physical source, material properties, threshold, wind/stability and averaging. No automatic conversion from draft SourcePoint profiles, jets, droplets, mixtures, growing pools or source-ledger transitions. Native x_max limits the plume grid, not the final puff extent. plume_distance_limit_m maps exactly to that parameter; puff_time_limit_s maps to native t_max, or null preserves native automatic puff duration. Actual grid extent is reported. Threshold censoring uses the final returned native grid, not an assumed x_max cutoff. Returns time-averaged native centreline volume fractions and native endpoint interpolation, not a 2D contour area or flammable cloud mass. Last-node exceedance is boundary-censored, not a solved separation distance. No distance-to-circle area substitution. No LH2 safety factor is applied. LH2 premise violation makes threshold_distance_m null while native_threshold_distance_m and centreline remain diagnostics. A passing premise check is not experimental/site validation. Baseline slabx applicability remains not_evaluated. External package versions/source fingerprints accompany result; API581 software-test status is not native model certification.

## `api581.api.dispersion.native_pool_footprint`

Native SLABx/SLABx-LH2 planar concentration threshold footprint

계산 ID: `dispersion/native-pool-footprint`

출처: Part3 §§5.8.5-5.8.6,5.9: external dispersion footprint boundary; SLABx1.0.8 post.concentration.ConcentrationField.at_y

| 입력 | 필수 | 타입 |
|---|---|---|
| `engine` | 예 | `typing.Literal['slabx', 'slabx-lh2']` |
| `substance` | 예 | `<class 'api581.slabx_adapter.NativeSubstance'>` |
| `atmosphere` | 예 | `<class 'api581.slabx_adapter.NativeAtmosphere'>` |
| `receptor_height_m` | 예 | `<class 'float'>` |
| `averaging_time_s` | 예 | `<class 'float'>` |
| `plume_distance_limit_m` | 예 | `<class 'float'>` |
| `puff_time_limit_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `puff_steps` | 기본값/선택 | `<class 'int'>` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `threshold_source` | 예 | `<class 'str'>` |
| `source_qualification` | 예 | `<class 'str'>` |
| `meander_closure` | 예 | `typing.Literal['ermak', 'sigma_theta']` |
| `lh2_plume_width_coupling` | 예 | `<class 'bool'>` |
| `timeout_s` | 기본값/선택 | `<class 'float'>` |
| `vapor_source_rate_kg_s` | 예 | `<class 'float'>` |
| `source_area_m2` | 예 | `<class 'float'>` |
| `release_duration_s` | 예 | `<class 'float'>` |
| `crosswind_half_span_m` | 예 | `<class 'float'>` |
| `crosswind_points_per_side` | 기본값/선택 | `<class 'int'>` |

출력: `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `effective_source_half_width_m`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`, `crosswind_distance_m`, `volume_fraction_by_crosswind_then_downwind`

적용 범위: Same explicitly qualified finite ground-level vapor pool, package versions, property/atmosphere constraints and process isolation as native-pool-centreline. Uses native at_y on a symmetric crosswind grid at one receptor height/averaging time. No conversion from centreline distance to circular area. Area integrates a piecewise-linear triangular concentration interpolant on the native downwind grid and user crosswind grid. Not an exact continuous contour; supplied resolution and span require convergence checks. Plume x_max is not the final puff extent. Returned field includes negative/upwind positions, and source expansion remains native. Any threshold exceedance at a sampled grid edge or LH2 premise violation sets threshold_area_m2 to null. sampled_exceedance_area_m2 and native field remain diagnostics. No boundary truncation reported as a resolved footprint, no LH2 safety factor, mass integration or individual/societal-risk inference. Baseline native applicability remains not_evaluated.

## `api581.api.dispersion.native_pool_flash_fire`

Native LFL footprint through API581 flash-fire consequence

계산 ID: `dispersion/native-pool-flash-fire`

출처: Part3 §§5.8.6,4.8.2.3; Native ConcentrationField.at_y plus sampled triangular threshold area

| 입력 | 필수 | 타입 |
|---|---|---|
| `engine` | 예 | `typing.Literal['slabx', 'slabx-lh2']` |
| `substance` | 예 | `<class 'api581.slabx_adapter.NativeSubstance'>` |
| `atmosphere` | 예 | `<class 'api581.slabx_adapter.NativeAtmosphere'>` |
| `receptor_height_m` | 예 | `typing.Literal[0.0]` |
| `averaging_time_s` | 예 | `<class 'float'>` |
| `plume_distance_limit_m` | 예 | `<class 'float'>` |
| `puff_time_limit_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `puff_steps` | 기본값/선택 | `<class 'int'>` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `threshold_source` | 예 | `<class 'str'>` |
| `source_qualification` | 예 | `<class 'str'>` |
| `meander_closure` | 예 | `typing.Literal['ermak', 'sigma_theta']` |
| `lh2_plume_width_coupling` | 예 | `<class 'bool'>` |
| `timeout_s` | 기본값/선택 | `<class 'float'>` |
| `vapor_source_rate_kg_s` | 예 | `<class 'float'>` |
| `source_area_m2` | 예 | `<class 'float'>` |
| `release_duration_s` | 예 | `<class 'float'>` |
| `crosswind_half_span_m` | 예 | `<class 'float'>` |
| `crosswind_points_per_side` | 기본값/선택 | `<class 'int'>` |
| `criterion_role` | 예 | `typing.Literal['qualified_lfl']` |

출력: `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `effective_source_half_width_m`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`, `crosswind_distance_m`, `volume_fraction_by_crosswind_then_downwind`, `personnel_area_m2`, `equipment_area_m2`, `criterion_role`

적용 범위: Same explicitly qualified finite ground-level vapor pool, package versions, property/atmosphere constraints and process isolation as native-pool-centreline. Uses native at_y on a symmetric crosswind grid at one receptor height/averaging time. No conversion from centreline distance to circular area. Area integrates a piecewise-linear triangular concentration interpolant on the native downwind grid and user crosswind grid. Not an exact continuous contour; supplied resolution and span require convergence checks. Plume x_max is not the final puff extent. Returned field includes negative/upwind positions, and source expansion remains native. Any threshold exceedance at a sampled grid edge or LH2 premise violation sets threshold_area_m2 to null. sampled_exceedance_area_m2 and native field remain diagnostics. No boundary truncation reported as a resolved footprint, no LH2 safety factor, mass integration or individual/societal-risk inference. Baseline native applicability remains not_evaluated. Ground-level receptor height0 required by §5.8.6. Caller must declare threshold as a qualified fluid-specific LFL using criterion_role=qualified_lfl. A declaration does not validate thermodynamics, exposure averaging or field applicability. Censored/premise-violating footprints fail explicitly instead of becoming zero or valid fire consequence. Not-reached yields zero only on the supplied sampled interpolant. Personnel area=LFL footprint; equipment=.25*footprint. No ignition/event/GFF weighting.

## `api581.api.dispersion.native_jet_centreline`

Native horizontal/vertical jet centreline dispersion

계산 ID: `dispersion/native-jet-centreline`

출처: Part3 §§5.3,5.7,5.8.5-5.8.6,5.9 external dispersion source boundary; SLABx1.0.8 core.source.HorizontalJet/core.vertical_jet.VerticalJet

| 입력 | 필수 | 타입 |
|---|---|---|
| `engine` | 예 | `typing.Literal['slabx', 'slabx-lh2']` |
| `substance` | 예 | `<class 'api581.slabx_adapter.NativeSubstance'>` |
| `atmosphere` | 예 | `<class 'api581.slabx_adapter.NativeAtmosphere'>` |
| `receptor_height_m` | 예 | `<class 'float'>` |
| `averaging_time_s` | 예 | `<class 'float'>` |
| `plume_distance_limit_m` | 예 | `<class 'float'>` |
| `puff_time_limit_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `puff_steps` | 기본값/선택 | `<class 'int'>` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `threshold_source` | 예 | `<class 'str'>` |
| `source_qualification` | 예 | `<class 'str'>` |
| `meander_closure` | 예 | `typing.Literal['ermak', 'sigma_theta']` |
| `lh2_plume_width_coupling` | 예 | `<class 'bool'>` |
| `timeout_s` | 기본값/선택 | `<class 'float'>` |
| `orientation` | 예 | `typing.Literal['horizontal_downwind', 'vertical_up']` |
| `jet_exit_area_m2` | 예 | `<class 'float'>` |
| `release_height_m` | 예 | `<class 'float'>` |
| `source_temperature_k` | 예 | `<class 'float'>` |
| `temperature_basis` | 예 | `typing.Literal['require_consistent', 'allow_native_clamp']` |
| `mass_source_rate_kg_s` | 예 | `<class 'float'>` |
| `release_duration_s` | 예 | `<class 'float'>` |
| `jet_liquid_mass_fraction` | 예 | `<class 'float'>` |

출력: `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `orientation`, `jet_exit_area_m2`, `geometric_exit_half_width_m`, `native_exit_velocity_m_s`, `requested_source_temperature_k`, `used_source_temperature_k`, `source_temperature_clamped`, `native_jet_liquid_mass_fraction`, `native_initial_downwind_distance_m`, `native_near_field_status`

적용 범위: Actual slabx1.0.8 HorizontalJet or VerticalJet at constant finite rate/duration, optional slabx-lh2 0.2.0 water/plume-width corrections in an isolated process. Direction is downwind horizontal or upward vertical only. No arbitrary yaw/downward/impinging jet, mixture carrier, physical-transition ledger or underexpanded-jet solver. Input total pure-material vapor+droplet mass rate, effective atmospheric exit area, source temperature and liquid MASS fraction, not gas volume fraction. Native velocity derives from q/(rho*A); this API does not substitute a vessel choked-orifice area for a qualified expanded area. Source liquid fraction must be below1. Equilibrium droplets use native default closures; kinetic evaporation/rainout flags are not implicitly enabled. Temperature basis is explicit: native clamps vapor below boiling to boiling and all droplet sources to boiling. require_consistent rejects a conflicting input; allow_native_clamp reports requested and used temperature. No EOS/flash reconciliation inferred.101325Pa ambient and supplied constant properties only. Vertical buoyant-source rise is delegated to the installed SLABx VerticalJet implementation and returned as native diagnostics. The adapter does not substitute a separate plume model or apply an empirical safety factor. LH2 premise diagnostics still gate distance/area; passing them does not validate near-field jets or field applicability. Native source/handoff may begin at x=1m or beyond the vertical rise. Full upstream/near-field extent is not reconstructed. A footprint touching first/last or lateral grid edge is censored, and threshold_area_m2 remains null. No source-boundary extrapolation or circle-area substitution. x_max limits plume, not full puff extent.

## `api581.api.dispersion.native_jet_footprint`

Native horizontal/vertical jet sampled threshold footprint

계산 ID: `dispersion/native-jet-footprint`

출처: Part3 §§5.8.6,5.9 external spatial footprint boundary; SLABx1.0.8 ConcentrationField.at_y

| 입력 | 필수 | 타입 |
|---|---|---|
| `engine` | 예 | `typing.Literal['slabx', 'slabx-lh2']` |
| `substance` | 예 | `<class 'api581.slabx_adapter.NativeSubstance'>` |
| `atmosphere` | 예 | `<class 'api581.slabx_adapter.NativeAtmosphere'>` |
| `receptor_height_m` | 예 | `<class 'float'>` |
| `averaging_time_s` | 예 | `<class 'float'>` |
| `plume_distance_limit_m` | 예 | `<class 'float'>` |
| `puff_time_limit_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `puff_steps` | 기본값/선택 | `<class 'int'>` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `threshold_source` | 예 | `<class 'str'>` |
| `source_qualification` | 예 | `<class 'str'>` |
| `meander_closure` | 예 | `typing.Literal['ermak', 'sigma_theta']` |
| `lh2_plume_width_coupling` | 예 | `<class 'bool'>` |
| `timeout_s` | 기본값/선택 | `<class 'float'>` |
| `orientation` | 예 | `typing.Literal['horizontal_downwind', 'vertical_up']` |
| `jet_exit_area_m2` | 예 | `<class 'float'>` |
| `release_height_m` | 예 | `<class 'float'>` |
| `source_temperature_k` | 예 | `<class 'float'>` |
| `temperature_basis` | 예 | `typing.Literal['require_consistent', 'allow_native_clamp']` |
| `mass_source_rate_kg_s` | 예 | `<class 'float'>` |
| `release_duration_s` | 예 | `<class 'float'>` |
| `jet_liquid_mass_fraction` | 예 | `<class 'float'>` |
| `crosswind_half_span_m` | 예 | `<class 'float'>` |
| `crosswind_points_per_side` | 기본값/선택 | `<class 'int'>` |

출력: `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `orientation`, `jet_exit_area_m2`, `geometric_exit_half_width_m`, `native_exit_velocity_m_s`, `requested_source_temperature_k`, `used_source_temperature_k`, `source_temperature_clamped`, `native_jet_liquid_mass_fraction`, `native_initial_downwind_distance_m`, `native_near_field_status`, `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`, `crosswind_distance_m`, `volume_fraction_by_crosswind_then_downwind`

적용 범위: Actual slabx1.0.8 HorizontalJet or VerticalJet at constant finite rate/duration, optional slabx-lh2 0.2.0 water/plume-width corrections in an isolated process. Direction is downwind horizontal or upward vertical only. No arbitrary yaw/downward/impinging jet, mixture carrier, physical-transition ledger or underexpanded-jet solver. Input total pure-material vapor+droplet mass rate, effective atmospheric exit area, source temperature and liquid MASS fraction, not gas volume fraction. Native velocity derives from q/(rho*A); this API does not substitute a vessel choked-orifice area for a qualified expanded area. Source liquid fraction must be below1. Equilibrium droplets use native default closures; kinetic evaporation/rainout flags are not implicitly enabled. Temperature basis is explicit: native clamps vapor below boiling to boiling and all droplet sources to boiling. require_consistent rejects a conflicting input; allow_native_clamp reports requested and used temperature. No EOS/flash reconciliation inferred.101325Pa ambient and supplied constant properties only. Vertical buoyant-source rise is delegated to the installed SLABx VerticalJet implementation and returned as native diagnostics. The adapter does not substitute a separate plume model or apply an empirical safety factor. LH2 premise diagnostics still gate distance/area; passing them does not validate near-field jets or field applicability. Native source/handoff may begin at x=1m or beyond the vertical rise. Full upstream/near-field extent is not reconstructed. A footprint touching first/last or lateral grid edge is censored, and threshold_area_m2 remains null. No source-boundary extrapolation or circle-area substitution. x_max limits plume, not full puff extent. Planar area uses the same explicit main-diagonal triangular interpolant as threshold-grid-area. Native x grid and user symmetric y grid require resolution checks. Raw field and within-grid diagnostic area remain available when censored/premise-violating; no valid full footprint is claimed.

## `api581.api.dispersion.threshold_grid_area`

Planar concentration exceedance area on a sampled triangulated grid

계산 ID: `dispersion/threshold-grid-area`

출처: Part3 §§5.8.5-5.8.6,5.9: external spatial concentration footprint boundary

| 입력 | 필수 | 타입 |
|---|---|---|
| `downwind_coordinates_m` | 예 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), AllowInfNan(allow_inf_nan=False)])]]` |
| `crosswind_coordinates_m` | 예 | `list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), AllowInfNan(allow_inf_nan=False)])]]` |
| `volume_fraction_by_crosswind_then_downwind` | 예 | `list[list[typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])]]]` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `sampling_basis` | 예 | `<class 'str'>` |

출력: `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`

적용 범위: Numerical postprocessing, not a printed API581 correlation. Each rectangular cell is split along lower-left to upper-right diagonal; concentration is linear on each triangle and the threshold polygon is clipped exactly on that interpolant. Results depend on supplied sampling, not an exact continuous-model contour. Field is at one common receptor height/time-averaging/source basis. No circular area from centreline distance, vertical cloud mass or multi-weather/event union. Any edge reaching threshold censors the footprint: threshold_area_m2 is null; sampled_exceedance_area_m2 remains the within-grid diagnostic. Below-threshold nodes do not rule out unresolved subgrid peaks; caller must establish resolution/convergence.

## `api581.api.dispersion.partitioned_jet_centreline`

API581 source partition through native jet centreline

계산 ID: `dispersion/partitioned-jet-centreline`

출처: Part3 eqs(3.100)-(3.102), STEP7.3-7.6; PDF pp543,545; Part3 §§5.3,5.7,5.8.5-5.8.6,5.9 external dispersion source boundary; SLABx1.0.8 core.source.HorizontalJet/core.vertical_jet.VerticalJet

| 입력 | 필수 | 타입 |
|---|---|---|
| `partition` | 예 | `<class 'api581.source_partition.SourcePartition'>` |
| `jet` | 예 | `<class 'api581.slabx_adapter.NativeJetGeometry'>` |

출력: `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `orientation`, `jet_exit_area_m2`, `geometric_exit_half_width_m`, `native_exit_velocity_m_s`, `requested_source_temperature_k`, `used_source_temperature_k`, `source_temperature_clamped`, `native_jet_liquid_mass_fraction`, `native_initial_downwind_distance_m`, `native_near_field_status`, `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`, `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`, `pool_liquid_mass_kg`, `jet_total_mass_kg`, `jet_liquid_rate_kg_s`, `jet_vapor_rate_kg_s`, `jet_liquid_mass_kg`, `jet_vapor_mass_kg`, `release_duration_s`, `integration_scope`

적용 범위: Source-partition stage only: Adjusted total rate and released mass must be qualified after detection/isolation and inventory limits. Pool+jet and jet-vapor+jet-liquid conserve mass. Printed composition is explicit and not asserted as EOS closure; nonphysical printed fractions rejected. Rainout and flash properties supplied with source; no pool evaporation, flash/EOS, two-phase hydraulic solver or actual dispersion run. Actual slabx1.0.8 HorizontalJet or VerticalJet at constant finite rate/duration, optional slabx-lh2 0.2.0 water/plume-width corrections in an isolated process. Direction is downwind horizontal or upward vertical only. No arbitrary yaw/downward/impinging jet, mixture carrier, physical-transition ledger or underexpanded-jet solver. Input total pure-material vapor+droplet mass rate, effective atmospheric exit area, source temperature and liquid MASS fraction, not gas volume fraction. Native velocity derives from q/(rho*A); this API does not substitute a vessel choked-orifice area for a qualified expanded area. Source liquid fraction must be below1. Equilibrium droplets use native default closures; kinetic evaporation/rainout flags are not implicitly enabled. Temperature basis is explicit: native clamps vapor below boiling to boiling and all droplet sources to boiling. require_consistent rejects a conflicting input; allow_native_clamp reports requested and used temperature. No EOS/flash reconciliation inferred.101325Pa ambient and supplied constant properties only. Vertical buoyant-source rise is delegated to the installed SLABx VerticalJet implementation and returned as native diagnostics. The adapter does not substitute a separate plume model or apply an empirical safety factor. LH2 premise diagnostics still gate distance/area; passing them does not validate near-field jets or field applicability. Native source/handoff may begin at x=1m or beyond the vertical rise. Full upstream/near-field extent is not reconstructed. A footprint touching first/last or lateral grid edge is censored, and threshold_area_m2 remains null. No source-boundary extrapolation or circle-area substitution. x_max limits plume, not full puff extent. Native q is partition jet-total vapor+droplet rate; liquid MASS fraction is partition entrained-liquid fraction. Duration is jet mass/rate from same partition. No independent duplicate source rate/composition/duration accepted. Pool rainout remains a separate source, not added to native jet. Empty/zero-duration jet and pure-liquid jet fail explicitly. Caller still qualifies effective atmospheric exit area, temperature, flash/rainout data and native source applicability.

## `api581.api.dispersion.partitioned_jet_footprint`

API581 source partition through native planar jet footprint

계산 ID: `dispersion/partitioned-jet-footprint`

출처: Part3 eqs(3.100)-(3.102), STEP7.3-7.6; PDF pp543,545; Part3 §§5.8.6,5.9 external spatial footprint boundary; SLABx1.0.8 ConcentrationField.at_y

| 입력 | 필수 | 타입 |
|---|---|---|
| `partition` | 예 | `<class 'api581.source_partition.SourcePartition'>` |
| `jet` | 예 | `<class 'api581.jet_handoff.JetFootprintGeometry'>` |

출력: `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `orientation`, `jet_exit_area_m2`, `geometric_exit_half_width_m`, `native_exit_velocity_m_s`, `requested_source_temperature_k`, `used_source_temperature_k`, `source_temperature_clamped`, `native_jet_liquid_mass_fraction`, `native_initial_downwind_distance_m`, `native_near_field_status`, `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`, `crosswind_distance_m`, `volume_fraction_by_crosswind_then_downwind`, `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`, `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`, `pool_liquid_mass_kg`, `jet_total_mass_kg`, `jet_liquid_rate_kg_s`, `jet_vapor_rate_kg_s`, `jet_liquid_mass_kg`, `jet_vapor_mass_kg`, `release_duration_s`, `integration_scope`

적용 범위: Source-partition stage only: Adjusted total rate and released mass must be qualified after detection/isolation and inventory limits. Pool+jet and jet-vapor+jet-liquid conserve mass. Printed composition is explicit and not asserted as EOS closure; nonphysical printed fractions rejected. Rainout and flash properties supplied with source; no pool evaporation, flash/EOS, two-phase hydraulic solver or actual dispersion run. Actual slabx1.0.8 HorizontalJet or VerticalJet at constant finite rate/duration, optional slabx-lh2 0.2.0 water/plume-width corrections in an isolated process. Direction is downwind horizontal or upward vertical only. No arbitrary yaw/downward/impinging jet, mixture carrier, physical-transition ledger or underexpanded-jet solver. Input total pure-material vapor+droplet mass rate, effective atmospheric exit area, source temperature and liquid MASS fraction, not gas volume fraction. Native velocity derives from q/(rho*A); this API does not substitute a vessel choked-orifice area for a qualified expanded area. Source liquid fraction must be below1. Equilibrium droplets use native default closures; kinetic evaporation/rainout flags are not implicitly enabled. Temperature basis is explicit: native clamps vapor below boiling to boiling and all droplet sources to boiling. require_consistent rejects a conflicting input; allow_native_clamp reports requested and used temperature. No EOS/flash reconciliation inferred.101325Pa ambient and supplied constant properties only. Vertical buoyant-source rise is delegated to the installed SLABx VerticalJet implementation and returned as native diagnostics. The adapter does not substitute a separate plume model or apply an empirical safety factor. LH2 premise diagnostics still gate distance/area; passing them does not validate near-field jets or field applicability. Native source/handoff may begin at x=1m or beyond the vertical rise. Full upstream/near-field extent is not reconstructed. A footprint touching first/last or lateral grid edge is censored, and threshold_area_m2 remains null. No source-boundary extrapolation or circle-area substitution. x_max limits plume, not full puff extent. Native q is partition jet-total vapor+droplet rate; liquid MASS fraction is partition entrained-liquid fraction. Duration is jet mass/rate from same partition. No independent duplicate source rate/composition/duration accepted. Pool rainout remains a separate source, not added to native jet. Empty/zero-duration jet and pure-liquid jet fail explicitly. Caller still qualifies effective atmospheric exit area, temperature, flash/rainout data and native source applicability. Area is sampled-grid triangular interpolation and needs spatial convergence. Source/handoff-edge concentration, outer-grid exceedance or LH2 premise violation censors usable area; diagnostic field/area preserved. No missing near-field completion or source-face extrapolation.

## `api581.api.consequence.select_toxic_criterion`

Select duration-matched toxic criterion by API581 priority

계산 ID: `consequence/select-toxic-criterion`

출처: Part3 §5.9.2,Table4.14,eqs(3.189)-(3.190); PDF pp531,565-567

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid_id` | 예 | `<class 'str'>` |
| `exposure_duration_s` | 예 | `<class 'float'>` |
| `use_printed_table` | 기본값/선택 | `<class 'bool'>` |
| `additional_candidates` | 기본값/선택 | `list[api581.toxic_criteria.CriterionCandidate]` |
| `excluded_candidate_ids` | 기본값/선택 | `dict[str, str]` |
| `selected_criterion_id` | 기본값/선택 | `str | None` |
| `toxic_mole_fraction` | 기본값/선택 | `<class 'float'>` |
| `candidate_availability_basis` | 예 | `<class 'str'>` |

출력: `fluid_id`, `selected_criterion_id`, `selected_kind`, `priority_tier`, `pure_component_limit_ppm`, `modified_mixture_limit_ppm`, `threshold_volume_fraction`, `component_present`, `attainable_in_mixture`, `exposure_duration_s`, `criterion_source`, `eligible_candidate_ids`, `excluded_candidate_ids`, `unavailable_candidate_reasons`

적용 범위: Historical2016 Table4.14 snapshot, not current occupational/emergency exposure guidance. Printed ammonia IDLH10ppm retained. Dashes are unavailable, not zero. Probit concentration ppm and time seconds follow Annex3.A nomenclature; caller must qualify coefficient/species applicability. EPA mg/L is not implicitly converted to ppm. Only provided candidates and the enabled historical table snapshot are considered, not an external literature/current-limit search. Caller declares candidate availability/applicability; named exclusions require a nonblank basis. Printed probit uses50% fatality and supplied exposure seconds. Same-priority ties require explicit selection, not minimum/maximum of incomparable limits. Exposure durations match exactly. Printed IDLH uses1800s, ERPG3600s, AEGL600/1800/3600 only where available. LC50/TEEL/EPA ppm must be owner-qualified candidates; EPA mg/L is not silently converted. A lower-priority selection cannot override an eligible higher-priority candidate without explicit exclusion. Mixture threshold divides pure-component ppm by toxic MOLE fraction once. Zero fraction means absent component; mathematically above1e6ppm is unattainable, not capped. Returned threshold is a criterion, not a field exposure duration or validated damage footprint.

## `api581.api.dispersion.native_pool_toxic_consequence`

Historical toxic criterion through native pure-pool footprint and conditional toxic consequence

계산 ID: `dispersion/native-pool-toxic-consequence`

출처: Part3 §§5.9.2-5.9.6,eqs(3.186)-(3.189); PDF pp565-567; SLABx1.0.8 native time-averaged planar field

| 입력 | 필수 | 타입 |
|---|---|---|
| `criterion` | 예 | `<class 'api581.toxic_criteria.ToxicCriterion'>` |
| `source` | 예 | `<class 'api581.native_toxic.ToxicPoolSource'>` |
| `non_ignition_probability` | 예 | `<class 'float'>` |
| `exposure_model_basis` | 예 | `typing.Literal['constant_exposure_equivalent_native_time_average']` |

출력: `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `effective_source_half_width_m`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`, `crosswind_distance_m`, `volume_fraction_by_crosswind_then_downwind`, `fluid_id`, `selected_criterion_id`, `selected_kind`, `priority_tier`, `pure_component_limit_ppm`, `modified_mixture_limit_ppm`, `threshold_volume_fraction`, `component_present`, `attainable_in_mixture`, `exposure_duration_s`, `criterion_source`, `eligible_candidate_ids`, `excluded_candidate_ids`, `unavailable_candidate_reasons`, `equipment_area_m2`, `personnel_area_m2`, `unweighted_cloud_area_m2`, `critical_component_id`, `component_cloud_areas_m2`, `release_duration_s`, `release_duration_governing_limit`, `exposure_model_basis`

적용 범위: Historical2016 Table4.14 snapshot, not current occupational/emergency exposure guidance. Printed ammonia IDLH10ppm retained. Dashes are unavailable, not zero. Probit concentration ppm and time seconds follow Annex3.A nomenclature; caller must qualify coefficient/species applicability. EPA mg/L is not implicitly converted to ppm. Only provided candidates and the enabled historical table snapshot are considered, not an external literature/current-limit search. Caller declares candidate availability/applicability; named exclusions require a nonblank basis. Printed probit uses50% fatality and supplied exposure seconds. Same-priority ties require explicit selection, not minimum/maximum of incomparable limits. Exposure durations match exactly. Printed IDLH uses1800s, ERPG3600s, AEGL600/1800/3600 only where available. LC50/TEEL/EPA ppm must be owner-qualified candidates; EPA mg/L is not silently converted. A lower-priority selection cannot override an eligible higher-priority candidate without explicit exclusion. Mixture threshold divides pure-component ppm by toxic MOLE fraction once. Zero fraction means absent component; mathematically above1e6ppm is unattainable, not capped. Returned threshold is a criterion, not a field exposure duration or validated damage footprint. Pure species only: selected fluid_id must equal native substance.fluid_id and toxic mole fraction must be1. Mixture criteria remain callable independently but mixture thermodynamics/species-resolved source mapping is not inferred. Uses native slabx1.0.8 ground-level constant vapor pool with explicit properties/atmosphere/spatial grid; no automatic LH2 toxicity or asphyxiation model. Eq3.186 bounds source duration by3600s,inventory/rate,detection duration. Selected exposure window must not exceed this source duration; native averaging equals that exposure. Short pulses fail explicitly, not zero consequence. Constant-exposure-equivalent TWA is a declared engineering screening assumption: nonlinear probit dose from C(t) is not generally equal to dose from average C. Native cloud passage does not prove time-above-threshold at every receptor. Ground-level receptor height0 is required by §5.9.6. Censored/premise-invalid spatial footprints fail before toxic consequence. Valid sampled area is multiplied by non-ignition probability exactly once, with toxic equipment area0 per eq3.188. No mixture maximum, additional event/GFF weighting or actual exposure-history/dose integration beyond this single pure component. Historical criteria are not current exposure advice or model/site certification.

## `api581.api.damage.soil_base_rate_table`

Soil base corrosion-rate reference profiles

계산 ID: `damage/soil-base-rate-table`

출처: Part2 Annex2.B §12.4.2,Table2.B.12.2; PDF pp417,420

| 입력 | 필수 | 타입 |
|---|---|---|
| `condition_profile` | 예 | `typing.Literal['dry_inland_sand', 'variable_industrial_silt', 'saturated_coastal_clay']` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_mpy']` |

출력: `corrosion_rate_m_year`, `printed_si_rate_mm_year`, `printed_us_rate_mpy`, `selected_unit_basis`, `condition_description`

적용 범위: Three full soil/contaminant/particle/moisture profiles, not automatic classification by soil name alone. Measured comparable rates take precedence under source guidance. Mixed conditions require qualified owner base rate, no invented interpolation. Printed SI.03/.13/.25mm/y differ from exact1/5/10mpy conversion; selected basis explicit.

## `api581.api.damage.soil_resistivity_factor`

Optional soil resistivity adjustment factor

계산 ID: `damage/soil-resistivity-factor`

출처: Part2 Annex2.B §12.4.3,Table2.B.12.3; PDF pp417-418,420

| 입력 | 필수 | 타입 |
|---|---|---|
| `soil_resistivity_ohm_m` | 예 | `<class 'float'>` |
| `shared_boundary_basis` | 기본값/선택 | `typing.Literal['lower_resistivity_interval', 'higher_resistivity_interval'] | None` |

출력: `resistivity_factor`, `source_row`

적용 범위: Public resistivity ohm m; source ohm cm=100*ohm m. Shared1000/2000ohm cm endpoints require explicit lower/higher interval selection.500 belongs500-1000,10000 belongs2000-10000. No inferred continuous resistivity interpolation. Omit adjustment when already incorporated in base rate to avoid double counting.

## `api581.api.damage.soil_temperature_factor`

Buried equipment soil-corrosion temperature factor

계산 ID: `damage/soil-temperature-factor`

출처: Part2 Annex2.B §12.4.4,Table2.B.12.4; PDF pp418,420

| 입력 | 필수 | 타입 |
|---|---|---|
| `equipment_temperature_k` | 예 | `<class 'float'>` |
| `threshold_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `temperature_factor`, `lower_boundary_k`, `upper_boundary_k`, `threshold_basis`

적용 범위: SI uses49/104C; US uses120/220F converted exactly to K. Paired boundaries differ, so basis required. Middle interval includes both endpoints; outer factors1, middle2. This table lookup does not qualify cryogenic/high-temperature buried service or frozen-soil chemistry.

## `api581.api.damage.soil_cp_factor`

Soil corrosion cathodic-protection effectiveness factor

계산 ID: `damage/soil-cp-factor`

출처: Part2 Annex2.B §12.4.5,Table2.B.12.5; PDF pp418,421

| 입력 | 필수 | 타입 |
|---|---|---|
| `protection_category` | 예 | `typing.Literal['unprotected_adjacent_cp_stray_current', 'no_cp', 'not_annual_or_partly_noncompliant', 'annual_on_potential_entire_structure', 'annual_polarized_or_instant_off_entire_structure']` |

출력: `cathodic_protection_factor`

적용 범위: Owner classifies actual coverage, annual testing,2016 NACE-reference compliance and adjacent-CP stray-current risk. No-CP1 differs from unprotected/untested with adjacent-CP stray current10. Factor.05 requires full-structure annual polarized/instant-off criteria; not automatic interpretation of one potential reading. Large/dynamic stray currents require specialist analysis under source scope.

## `api581.api.damage.soil_coating_factor`

Product of independent soil-coating effectiveness factors

계산 ID: `damage/soil-coating-factor`

출처: Part2 Annex2.B §12.4.6,eq(2.B.22),Table2.B.12.6; PDF pp419,421

| 입력 | 필수 | 타입 |
|---|---|---|
| `coating_type` | 예 | `typing.Literal['bare', 'fusion_bonded_epoxy', 'liquid_epoxy', 'asphalt_enamel', 'asphalt_mastic', 'coal_tar_enamel', 'extruded_pe_mastic_or_rubber', 'mill_pe_tape_mastic', 'field_pe_tape_mastic', 'three_layer_pe_pp']` |
| `coating_age_years` | 예 | `<class 'float'>` |
| `rated_temperature_occasionally_exceeded` | 예 | `<class 'bool'>` |
| `maintenance_rare_or_none` | 예 | `<class 'bool'>` |

출력: `coating_effectiveness_factor`, `base_factor`, `age_factor`, `temperature_abuse_factor`, `maintenance_factor`, `calculation_basis`, `printed_example_discrepancy_applies`, `printed_example_reported_factor`

적용 범위: Factors apply independently; age multiplier only for age>20years, nonapplicable multipliers1. Bare factor1. Applies even without CP. Source worked mill-PE example prints1.5*1.2*3*1.5=13.5, but table-factor product is8.1; calculation follows factor multiplication, reports printed example separately and does not assert an authorized erratum.

## `api581.api.damage.soil_rate_equation`

Soil corrosion multiplicative rate equation

계산 ID: `damage/soil-rate-equation`

출처: Part2 Annex2.B eq(2.B.21); PDF p417

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `resistivity_factor` | 예 | `<class 'float'>` |
| `temperature_factor` | 예 | `<class 'float'>` |
| `cathodic_protection_factor` | 예 | `<class 'float'>` |
| `coating_effectiveness_factor` | 예 | `<class 'float'>` |

출력: `corrosion_rate_m_year`

적용 범위: CR=CRB*FSR*FT*FCP*FCE. Qualified factors supplied; no automatic material/service selection. Does not clamp to minimum corrosion rate or infer coating as zero-corrosion protection.

## `api581.api.damage.soil_corrosion_rate`

Compose qualified soil-side corrosion base rate and table factors

계산 ID: `damage/soil-corrosion-rate`

출처: Part2 Annex2.B Tables2.B.1.1/1.2,§12,eq(2.B.21); PDF pp322-323,417-421

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel']` |
| `in_contact_with_soil` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `base_rate_source` | 예 | `<class 'str'>` |
| `resistivity_application` | 예 | `typing.Literal['apply', 'already_in_base', 'omitted_by_qualification']` |
| `resistivity` | 기본값/선택 | `api581.soil_corrosion.SoilResistivity | None` |
| `resistivity_omission_basis` | 기본값/선택 | `str | None` |
| `temperature` | 예 | `<class 'api581.soil_corrosion.SoilTemperature'>` |
| `cathodic_protection` | 예 | `<class 'api581.soil_corrosion.SoilCathodicProtection'>` |
| `coating` | 예 | `<class 'api581.soil_corrosion.SoilCoating'>` |

출력: `corrosion_rate_m_year`, `resistivity_factor`, `temperature_factor`, `cathodic_protection_factor`, `coating_effectiveness_factor`, `base_corrosion_rate_m_year`, `thinning_type`, `resistivity_application`, `coating_calculation_basis`, `coating_example_discrepancy_applies`

적용 범위: Annex2.B screening requires carbon steel in soil contact. Owner qualifies buried-service applicability, actual soil/base rate and current/coating condition. Uses Table2.B.1.2 local thinning classification; not atmospheric/CUI corrosion, AST floor automatic model, MIC/stray-current detailed analysis or arbitrary cryogenic service. Optional resistivity factor must be explicitly applied or omitted with basis, including when already incorporated in base rate. No duplicate soil-resistivity weighting. Source SI/US rate/temperature rounding, resistivity shared endpoints and coating example8.1vs13.5 remain explicit. Coating uses table product, not erroneous worked arithmetic. Base-rate reference conditions must be qualified before reapplying CP,coating or temperature effects. Already-adjusted measured net rates can feed the existing thinning kernel directly; this composition does not infer which effects a measured rate already contains.

## `api581.api.damage.soil_thinning_assessment`

Soil corrosion rate through unclad non-AST thinning DF

계산 ID: `damage/soil-thinning-assessment`

출처: Part2 Annex2.B §12; Part2 §4.5.7 eqs(2.13),(2.18)-(2.23)

| 입력 | 필수 | 타입 |
|---|---|---|
| `soil` | 예 | `<class 'api581.soil_corrosion.SoilRate'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `<class 'api581.thinning.StrengthRatio'>` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `online_monitoring_factor` | 예 | `<class 'float'>` |
| `assessment_scope` | 예 | `typing.Literal['unclad_internal_pressure_governed_non_ast']` |

출력: `corrosion_rate_m_year`, `resistivity_factor`, `temperature_factor`, `cathodic_protection_factor`, `coating_effectiveness_factor`, `base_corrosion_rate_m_year`, `thinning_type`, `resistivity_application`, `coating_calculation_basis`, `coating_example_discrepancy_applies`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `assessment_scope`

적용 범위: Annex2.B screening requires carbon steel in soil contact. Owner qualifies buried-service applicability, actual soil/base rate and current/coating condition. Uses Table2.B.1.2 local thinning classification; not atmospheric/CUI corrosion, AST floor automatic model, MIC/stray-current detailed analysis or arbitrary cryogenic service. Optional resistivity factor must be explicitly applied or omitted with basis, including when already incorporated in base rate. No duplicate soil-resistivity weighting. Source SI/US rate/temperature rounding, resistivity shared endpoints and coating example8.1vs13.5 remain explicit. Coating uses table product, not erroneous worked arithmetic. Base-rate reference conditions must be qualified before reapplying CP,coating or temperature effects. Already-adjusted measured net rates can feed the existing thinning kernel directly; this composition does not infer which effects a measured rate already contains. Single soil-side mechanism for qualified unclad non-AST internal-pressure-governed component and one constant-rate interval. No automatic history integration across coating-age20,CP or temperature changes. Same starting thickness from strength input feeds wall loss. Uses existing Bayesian thinning kernel and supplied monitoring factor. Injection/deadleg factors1 for this soil-only path. No AST floor, structural/external-pressure, cladding or automatic inspection-effectiveness determination. Result is not total all-mechanism DF or inspection acceptance.

## `api581.api.tank.bottom_base_corrosion_rate`

AST floor reference base corrosion rate

계산 ID: `tank/bottom-base-corrosion-rate`

출처: Part2 Annex2.B §14.3.1-14.3.2,Tables2.B.14.3,14.10; PDF pp430-435

| 입력 | 필수 | 타입 |
|---|---|---|
| `side` | 예 | `typing.Literal['soil', 'product']` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_mpy']` |

출력: `base_corrosion_rate_m_year`, `printed_si_rate_mm_year`, `printed_us_rate_mpy`, `side`, `unit_basis`

적용 범위: Fallback rates only; comparable inspection-derived base rates take precedence. Rounded SI and US pairs differ. Soil reference: moderate resistivity, continuous asphalt/concrete, good drainage, no functioning CP, single bottom, below24C. Product reference: no required coating, below24C, no coil, no regular water draws. Not a measured net rate.

## `api581.api.tank.bottom_soil_rate_equation`

AST floor soil-side corrosion rate equation

계산 ID: `tank/bottom-soil-rate-equation`

출처: Part2 Annex2.B §14.2.1,eq(2.B.37); PDF p430

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `resistivity_factor` | 예 | `<class 'float'>` |
| `pad_factor` | 예 | `<class 'float'>` |
| `drainage_factor` | 예 | `<class 'float'>` |
| `cathodic_protection_factor` | 예 | `<class 'float'>` |
| `bottom_type_factor` | 예 | `<class 'float'>` |
| `temperature_factor` | 예 | `<class 'float'>` |

출력: `soil_corrosion_rate_m_year`

적용 범위: Independent equation kernel only. Factors and reference base rate are supplied and must be qualified from §14.3 tables or comparable inspection data. No soil classification, factor selection, AST applicability or measured-rate correction is inferred.

## `api581.api.tank.bottom_product_rate_equation`

AST floor product-side corrosion rate equation

계산 ID: `tank/bottom-product-rate-equation`

출처: Part2 Annex2.B §14.2.2,eq(2.B.38); PDF p430

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `product_condition_factor` | 예 | `<class 'float'>` |
| `temperature_factor` | 예 | `<class 'float'>` |
| `steam_coil_factor` | 예 | `<class 'float'>` |
| `water_draw_factor` | 예 | `<class 'float'>` |

출력: `product_corrosion_rate_m_year`

적용 범위: Independent equation kernel only. Factors and reference base rate are supplied and must be qualified from §14.3 tables or comparable inspection data. No product wetness, temperature, coil or water-draw classification is inferred.

## `api581.api.tank.bottom_soil_resistivity_factor`

AST floor native-soil resistivity factor

계산 ID: `tank/bottom-soil-resistivity-factor`

출처: Part2 Annex2.B §14.3.1(a),Table2.B.14.4; PDF pp430,433

| 입력 | 필수 | 타입 |
|---|---|---|
| `release_prevention_barrier` | 예 | `<class 'bool'>` |
| `soil_resistivity_ohm_m` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `shared_boundary_basis` | 기본값/선택 | `typing.Literal['lower_resistivity_interval', 'higher_resistivity_interval'] | None` |

출력: `resistivity_factor`, `selection_reason`

적용 범위: RPB or unknown resistivity uses1 by source instruction. Public ohm m; source ohm cm=100*ohm m. Shared1000/2000ohm cm endpoints require explicit interval basis. High-resistivity factor is.66 for AST, not the buried-pipe.60 factor.

## `api581.api.tank.bottom_pad_factor`

AST floor foundation pad factor

계산 ID: `tank/bottom-pad-factor`

출처: Part2 Annex2.B Table2.B.14.5; PDF p434

| 입력 | 필수 | 타입 |
|---|---|---|
| `pad_type` | 예 | `typing.Literal['soil_high_salt', 'crushed_limestone', 'native_soil', 'construction_grade_sand', 'continuous_asphalt', 'continuous_concrete', 'oil_sand', 'high_resistivity_low_chloride_sand']` |

출력: `pad_factor`

적용 범위: Owner qualifies actual pad category; no interpolation or automatic soil classification.

## `api581.api.tank.bottom_drainage_factor`

AST floor drainage factor

계산 ID: `tank/bottom-drainage-factor`

출처: Part2 Annex2.B §14.3.1(c),Table2.B.14.6; PDF pp430,434

| 입력 | 필수 | 타입 |
|---|---|---|
| `drainage_category` | 예 | `typing.Literal['one_third_frequently_underwater', 'storm_water_collects', 'no_storm_water_collects']` |

출력: `drainage_factor`

적용 범위: Owner selects category: table says one-third frequently underwater; prose describes more than one-third circumference underwater for extended periods. No invented numeric exposure classifier.

## `api581.api.tank.bottom_cp_factor`

AST floor cathodic protection factor with inspection credit gate

계산 ID: `tank/bottom-cp-factor`

출처: Part2 Annex2.B §14.3.1(d),Table2.B.14.7; PDF pp431,434

| 입력 | 필수 | 타입 |
|---|---|---|
| `protection_category` | 예 | `typing.Literal['none', 'present_not_per_api651', 'present_per_api651']` |
| `effectiveness_verified_by_high_level_inspection` | 예 | `<class 'bool'>` |
| `verification_basis` | 기본값/선택 | `str | None` |

출력: `nominal_table_factor`, `cathodic_protection_factor`, `credit_applied`

적용 범위: Table nominal factors1/.66/.33; text allows no credit without High Level inspection verifying effective CP under referenced NACE RP0169 or equivalent. Owner supplies verification basis. Historical references do not establish current compliance.

## `api581.api.tank.bottom_type_factor`

AST floor construction factor

계산 ID: `tank/bottom-type-factor`

출처: Part2 Annex2.B Table2.B.14.8; PDF p434

| 입력 | 필수 | 타입 |
|---|---|---|
| `bottom_type` | 예 | `typing.Literal['rpb_not_per_api650', 'rpb_per_api650', 'single_bottom']` |

출력: `bottom_type_factor`

적용 범위: RPB classification is supplied by the owner; qualified RPB and single bottom both have factor1.

## `api581.api.tank.bottom_temperature_factor`

AST floor soil and product temperature factor

계산 ID: `tank/bottom-temperature-factor`

출처: Part2 Annex2.B Tables2.B.14.9,14.12; PDF p435

| 입력 | 필수 | 타입 |
|---|---|---|
| `highest_operating_temperature_k` | 예 | `<class 'float'>` |
| `threshold_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `temperature_factor`, `source_row`, `threshold_basis`

적용 범위: Both tables have identical five bands. Printed SI24/66/93/121C differ from US75/150/200/250F converted to K; basis required. Above highest threshold source factor returns1; not a qualification of high-temperature or cryogenic service.

## `api581.api.tank.bottom_product_condition_factor`

AST floor product wetness factor

계산 ID: `tank/bottom-product-condition-factor`

출처: Part2 Annex2.B §14.3.2(a),Table2.B.14.11; PDF pp431,435

| 입력 | 필수 | 타입 |
|---|---|---|
| `product_condition` | 예 | `typing.Literal['wet', 'dry']` |

출력: `product_condition_factor`

적용 범위: Wet means significant bottom sediment and water; owner qualifies actual condition.

## `api581.api.tank.bottom_steam_coil_factor`

AST floor steam coil factor

계산 ID: `tank/bottom-steam-coil-factor`

출처: Part2 Annex2.B Table2.B.14.13; PDF p436

| 입력 | 필수 | 타입 |
|---|---|---|
| `steam_coil_present` | 예 | `<class 'bool'>` |

출력: `steam_coil_factor`

적용 범위: Presence multiplier only; no detailed steam-leak thermal model.

## `api581.api.tank.bottom_water_draw_factor`

AST floor qualified regular water draw factor

계산 ID: `tank/bottom-water-draw-factor`

출처: Part2 Annex2.B §14.3.2(d),Table2.B.14.14; PDF pp431,436

| 입력 | 필수 | 타입 |
|---|---|---|
| `water_draw_practice` | 예 | `typing.Literal['none_or_not_regular', 'weekly', 'after_every_receipt']` |

출력: `water_draw_factor`

적용 범위: Credit.7 requires weekly draws or draws after every receipt; merely having a drain earns no credit.

## `api581.api.tank.bottom_corrosion_rate_combine`

AST floor two-sided corrosion-rate combination

계산 ID: `tank/bottom-corrosion-rate-combine`

출처: Part2 Annex2.B §14.3.3; PDF p431

| 입력 | 필수 | 타입 |
|---|---|---|
| `soil_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `product_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `product_distribution` | 예 | `typing.Literal['general', 'local']` |
| `minimum_rate_policy` | 예 | `typing.Literal['apply_2_mpy_recommendation', 'qualified_no_floor']` |
| `no_floor_qualification_basis` | 기본값/선택 | `str | None` |

출력: `raw_combined_rate_m_year`, `combined_corrosion_rate_m_year`, `recommended_minimum_rate_m_year`, `minimum_applied`, `combination_rule`

적용 범위: Soil corrosion is local. General product corrosion adds both rates; local product corrosion uses maximum. Source recommends minimum2mpy=.0000508m/year. Explicit qualified bypass retains raw value. General/local selection follows section14.3.3; summary Table2.B.1.2 lists AST product as local. No AST damage factor computed here.

## `api581.api.tank.bottom_corrosion_assessment`

AST floor soil and product corrosion assessment

계산 ID: `tank/bottom-corrosion-assessment`

출처: Part2 Annex2.B §14.3,eqs(2.B.37-38),Tables2.B.14.4-14; PDF pp430-436

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel']` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `soil_base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `product_base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `soil_base_rate_source` | 예 | `<class 'str'>` |
| `product_base_rate_source` | 예 | `<class 'str'>` |
| `bottom_type` | 예 | `typing.Literal['rpb_not_per_api650', 'rpb_per_api650', 'single_bottom']` |
| `soil_resistivity_ohm_m` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `shared_boundary_basis` | 기본값/선택 | `typing.Literal['lower_resistivity_interval', 'higher_resistivity_interval'] | None` |
| `pad` | 예 | `<class 'api581.tank_corrosion.BottomPad'>` |
| `drainage` | 예 | `<class 'api581.tank_corrosion.BottomDrainage'>` |
| `cathodic_protection` | 예 | `<class 'api581.tank_corrosion.BottomCP'>` |
| `temperature` | 예 | `<class 'api581.tank_corrosion.BottomTemperature'>` |
| `product_condition` | 예 | `<class 'api581.tank_corrosion.BottomProductCondition'>` |
| `steam_coil` | 예 | `<class 'api581.tank_corrosion.BottomSteamCoil'>` |
| `water_draw` | 예 | `<class 'api581.tank_corrosion.BottomWaterDraw'>` |
| `product_distribution` | 예 | `typing.Literal['general', 'local']` |
| `minimum_rate_policy` | 예 | `typing.Literal['apply_2_mpy_recommendation', 'qualified_no_floor']` |
| `no_floor_qualification_basis` | 기본값/선택 | `str | None` |

출력: `raw_combined_rate_m_year`, `combined_corrosion_rate_m_year`, `recommended_minimum_rate_m_year`, `minimum_applied`, `combination_rule`, `soil_corrosion_rate_m_year`, `product_corrosion_rate_m_year`, `resistivity_factor`, `pad_factor`, `drainage_factor`, `cathodic_protection_factor`, `bottom_type_factor`, `temperature_factor`, `product_condition_factor`, `steam_coil_factor`, `water_draw_factor`, `cp_credit_applied`

적용 범위: Carbon-steel AST floor only. Explicit comparable base rates and provenance required; measured net rates must not be multiplied again without qualification. RPB soil-resistivity override derives from bottom type. Single highest operating temperature drives both source temperature factors. CP inspection gate enforced. No coating credit, remaining life, AST thinning damage factor or complete asset risk calculation.

## `api581.api.tank.bottom_minimum_thickness`

AST floor minimum thickness for thinning calculation

계산 ID: `tank/bottom-minimum-thickness`

출처: Part2 §4.5.7 STEP5(3)-(4); PDF p153

| 입력 | 필수 | 타입 |
|---|---|---|
| `release_prevention_barrier` | 예 | `<class 'bool'>` |
| `thickness_basis` | 예 | `typing.Literal['api581_2016_default', 'documented_owner_method']` |
| `owner_minimum_thickness_m` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `owner_method_basis` | 기본값/선택 | `str | None` |

출력: `minimum_thickness_m`, `thickness_basis`

적용 범위: Historical 2016 source defaults0.1in without RPB and0.05in with RPB converted exactly to SI. Owner documented alternate method permitted. Not current API653 acceptance, design-code compliance or FFS verification.

## `api581.api.tank.bottom_wall_parameter`

AST floor remaining thickness and Art parameter

계산 ID: `tank/bottom-wall-parameter`

출처: Part2 §4.5.7 STEP6(1),eq(2.12); PDF p153

| 입력 | 필수 | 타입 |
|---|---|---|
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `minimum_thickness_m` | 예 | `<class 'float'>` |
| `corrosion_allowance_m` | 예 | `<class 'float'>` |

출력: `art_parameter`, `predicted_remaining_thickness_m`, `predicted_wall_loss_m`, `reference_thickness_m`, `at_or_below_minimum_thickness`, `predicted_penetration`

적용 범위: Art=max(1-(starting_thickness-rate*elapsed)/(minimum_thickness+corrosion_allowance),0). This is not non-AST fractional wall loss. Starting thickness and elapsed time must refer to same qualified baseline. Negative predicted remaining thickness is returned diagnostically; no clamp to hide penetration. Art>1 is outside the damage table and rejected by subsequent lookup.

## `api581.api.tank.bottom_inspection_selection`

Select one AST floor inspection credit

계산 ID: `tank/bottom-inspection-selection`

출처: Part2 §§4.5.5-4.5.6,Table4.7; PDF pp151-152,163

| 입력 | 필수 | 타입 |
|---|---|---|
| `eligible_inspection_grades` | 예 | `list[typing.Literal['a', 'b', 'c', 'd', 'e']]` |
| `eligibility_basis` | 예 | `<class 'str'>` |

출력: `selected_inspection_grade`, `credited_inspection_count`, `eligible_inspection_count`

적용 범위: Only best effectiveness of eligible inspections is credited, never stacked or Bayesian-upgraded. Empty list/E gives no credit. Caller qualifies actual inspection effectiveness under Annex2.C.5 and inclusion in baseline-to-assessment period; furnished-to-measured baseline reset does not preserve earlier inspection credit automatically.

## `api581.api.tank.bottom_thinning_base`

AST floor tabulated base thinning damage factor

계산 ID: `tank/bottom-thinning-base`

출처: Part2 §4.5.7 STEP13,Table4.7; PDF pp155,163

| 입력 | 필수 | 타입 |
|---|---|---|
| `art_parameter` | 예 | `<class 'float'>` |
| `inspection_grade` | 예 | `typing.Literal['a', 'b', 'c', 'd', 'e']` |
| `lookup_policy` | 예 | `typing.Literal['exact_rows_only', 'linear_between_rows', 'conservative_upper_row']` |

출력: `base_damage_factor`, `lower_art_row`, `upper_art_row`, `interpolation_weight`, `lookup_policy`

적용 범위: Uses all21x5 printed cells. STEP13 calls it Table4.8, but actual AST table is4.7; actual4.8 is online monitoring. Table covers0<=Art<=1. No extrapolation or terminal-row saturation for Art>1. Between-row handling is explicit owner numerical policy: linear, upper-row conservative, or exact-only; source gives no explicit interpolation instruction. Inspection columns assume at most one credited inspection.

## `api581.api.tank.bottom_thinning_adjustment_factors`

AST floor construction maintenance and settlement factors

계산 ID: `tank/bottom-thinning-adjustment-factors`

출처: Part2 §4.5.7 STEP15(4)-(6); PDF p156

| 입력 | 필수 | 타입 |
|---|---|---|
| `construction` | 예 | `typing.Literal['welded', 'riveted']` |
| `maintained_per_api653` | 예 | `<class 'bool'>` |
| `settlement_category` | 예 | `typing.Literal['exceeds_api653', 'meets_api653', 'never_evaluated', 'concrete_no_settlement']` |

출력: `welded_construction_factor`, `maintenance_factor`, `settlement_factor`

적용 범위: Owner qualifies actual construction, historical API653 maintenance and settlement category. Factors are not a structural settlement assessment. Online monitoring for AST-bottom corrosion uses other-mechanism table value1 in integrated APIs; no invented monitoring credit.

## `api581.api.tank.bottom_thinning_assessment`

AST floor dedicated thinning damage assessment

계산 ID: `tank/bottom-thinning-assessment`

출처: Part2 §4.5.7,eqs(2.12),(2.23),Tables4.7-4.8; PDF pp152-156,163-164

| 입력 | 필수 | 타입 |
|---|---|---|
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `baseline_basis` | 예 | `<class 'str'>` |
| `corrosion_allowance_m` | 예 | `<class 'float'>` |
| `minimum_thickness` | 예 | `<class 'api581.tank_thinning.BottomMinimumThickness'>` |
| `inspections` | 예 | `<class 'api581.tank_thinning.BottomInspectionSelection'>` |
| `lookup_policy` | 예 | `typing.Literal['exact_rows_only', 'linear_between_rows', 'conservative_upper_row']` |
| `adjustments` | 예 | `<class 'api581.tank_thinning.BottomAdjustments'>` |
| `corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `corrosion_rate_basis` | 예 | `<class 'str'>` |

출력: `minimum_thickness_m`, `thickness_basis`, `art_parameter`, `predicted_remaining_thickness_m`, `predicted_wall_loss_m`, `reference_thickness_m`, `at_or_below_minimum_thickness`, `predicted_penetration`, `selected_inspection_grade`, `credited_inspection_count`, `eligible_inspection_count`, `base_damage_factor`, `lower_art_row`, `upper_art_row`, `interpolation_weight`, `lookup_policy`, `welded_construction_factor`, `maintenance_factor`, `settlement_factor`, `thinning_damage_factor`, `online_monitoring_factor`

적용 범위: Carbon-steel unlined AST bottom with qualified supplied net corrosion rate. Uses dedicated table, not pressure strength-ratio/Bayesian non-AST equations. One inspection credit. Injection/deadleg factors1 as non-piping; monitoring1 for other-corrosion-mechanism row. No automatic baseline reset, coating/lining credit, variable corrosion history or all-mechanism DF. Minimum-thickness flag is diagnostic, not acceptance/FFS.

## `api581.api.tank.bottom_corrosion_thinning_assessment`

AST floor two-sided corrosion through thinning damage

계산 ID: `tank/bottom-corrosion-thinning-assessment`

출처: Part2 Annex2.B §14.3,eqs(2.B.37-38),Tables2.B.14.4-14; PDF pp430-436; Part2 §4.5.7,eqs(2.12),(2.23),Tables4.7-4.8; PDF pp152-156,163-164

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.tank_corrosion.BottomCorrosion'>` |
| `thinning` | 예 | `<class 'api581.tank_thinning.BottomThinningBasis'>` |

출력: `raw_combined_rate_m_year`, `combined_corrosion_rate_m_year`, `recommended_minimum_rate_m_year`, `minimum_applied`, `combination_rule`, `soil_corrosion_rate_m_year`, `product_corrosion_rate_m_year`, `resistivity_factor`, `pad_factor`, `drainage_factor`, `cathodic_protection_factor`, `bottom_type_factor`, `temperature_factor`, `product_condition_factor`, `steam_coil_factor`, `water_draw_factor`, `cp_credit_applied`, `minimum_thickness_m`, `thickness_basis`, `art_parameter`, `predicted_remaining_thickness_m`, `predicted_wall_loss_m`, `reference_thickness_m`, `at_or_below_minimum_thickness`, `predicted_penetration`, `selected_inspection_grade`, `credited_inspection_count`, `eligible_inspection_count`, `base_damage_factor`, `lower_art_row`, `upper_art_row`, `interpolation_weight`, `lookup_policy`, `welded_construction_factor`, `maintenance_factor`, `settlement_factor`, `thinning_damage_factor`, `online_monitoring_factor`

적용 범위: Carbon-steel unlined AST floor only. Comparable baseline corrosion rates and provenance required; do not multiply already-corrected measured net rates again. RPB resistivity override and CP inspection gate enforced. Temperature and minimum-rate policies remain explicit. Carbon-steel unlined AST bottom with qualified supplied net corrosion rate. Uses dedicated table, not pressure strength-ratio/Bayesian non-AST equations. One inspection credit. Injection/deadleg factors1 as non-piping; monitoring1 for other-corrosion-mechanism row. No automatic baseline reset, coating/lining credit, variable corrosion history or all-mechanism DF. Minimum-thickness flag is diagnostic, not acceptance/FFS. Same combined product/soil rate drives Art; same RPB status must drive corrosion and default minimum thickness. No second external-corrosion DF added for the same soil-side loss.

## `api581.api.tank.bottom_corrosion_risk_assessment`

AST floor corrosion through source consequence and annual financial risk

계산 ID: `tank/bottom-corrosion-risk-assessment`

출처: Part2 Annex2.B §14.3,eqs(2.B.37-38),Tables2.B.14.4-14; PDF pp430-436; Part2 §4.5.7,eqs(2.12),(2.23),Tables4.7-4.8; PDF pp152-156,163-164; Part3 §§6.1-6.7,Tables6.1M/6.2M/6.4/6.4M/6.5,eqs(3.205)-(3.212),(3.219)-(3.230); PDF pp592-598,604-607; Part3 eq(3.244); PDF p601; Part1 eqs(1.1),(1.8); Part2 eqs(2.9)-(2.10); Part3 §6.12.3

| 입력 | 필수 | 타입 |
|---|---|---|
| `damage` | 예 | `<class 'api581.tank_thinning.BottomCorrosionThinning'>` |
| `source` | 예 | `<class 'api581.tank_source.BottomSource'>` |
| `distance_to_groundwater_m` | 예 | `<class 'float'>` |
| `economics` | 예 | `<class 'api581.tank_integrated.BottomEconomics'>` |
| `management_score` | 예 | `<class 'float'>` |
| `damage_scope` | 예 | `typing.Literal['qualified_thinning_only']` |
| `other_mechanisms_exclusion_basis` | 예 | `<class 'str'>` |

출력: `raw_combined_rate_m_year`, `combined_corrosion_rate_m_year`, `recommended_minimum_rate_m_year`, `minimum_applied`, `combination_rule`, `soil_corrosion_rate_m_year`, `product_corrosion_rate_m_year`, `resistivity_factor`, `pad_factor`, `drainage_factor`, `cathodic_protection_factor`, `bottom_type_factor`, `temperature_factor`, `product_condition_factor`, `steam_coil_factor`, `water_draw_factor`, `cp_credit_applied`, `minimum_thickness_m`, `thickness_basis`, `art_parameter`, `predicted_remaining_thickness_m`, `predicted_wall_loss_m`, `reference_thickness_m`, `at_or_below_minimum_thickness`, `predicted_penetration`, `selected_inspection_grade`, `credited_inspection_count`, `eligible_inspection_count`, `base_damage_factor`, `lower_art_row`, `upper_art_row`, `interpolation_weight`, `lookup_policy`, `welded_construction_factor`, `maintenance_factor`, `settlement_factor`, `thinning_damage_factor`, `online_monitoring_factor`, `diameter_by_hole_m`, `area_by_hole_m2`, `available_volume_m3`, `available_volume_bbl`, `available_mass_kg`, `generic_frequency_by_hole_per_year`, `generic_total_per_year`, `printed_generic_total_per_year`, `generic_total_basis`, `native_rate_by_hole_bbl_day`, `mass_rate_by_hole_kg_s`, `detection_time_by_hole_days`, `release_duration_by_hole_days`, `released_volume_by_hole_bbl`, `released_volume_by_hole_m3`, `released_mass_by_hole_kg`, `release_type`, `liquid_density_kg_m3`, `small_hole_count`, `medium_hole_count`, `large_hole_count`, `outside_tabulated_diameter_range`, `product_hydraulic_conductivity_m_day`, `seepage_velocity_m_day`, `bottom_flow_equation`, `applied_small_hole_multiplier`, `detection_time_days`, `detection_selected_basis`, `source_scope`, `component_repair_cost`, `surrounding_equipment_cost`, `business_interruption_cost`, `injury_cost`, `environmental_cost`, `component_outage_days`, `surrounding_outage_days`, `surrounding_cost_reference_usd_2001`, `leak_environment_cost`, `rupture_environment_cost`, `financial_consequence`, `currency`, `cost_basis_year`, `cost_basis`, `generic_frequency_per_year`, `management_factor`, `annual_failure_frequency`, `financial_risk_per_year`, `annual_frequency_by_hole`, `integration_scope`, `groundwater_arrival_time_days`, `total_damage_factor`

적용 범위: Carbon-steel unlined AST floor only. Comparable baseline corrosion rates and provenance required; do not multiply already-corrected measured net rates again. RPB resistivity override and CP inspection gate enforced. Temperature and minimum-rate policies remain explicit. Carbon-steel unlined AST bottom with qualified supplied net corrosion rate. Uses dedicated table, not pressure strength-ratio/Bayesian non-AST equations. One inspection credit. Injection/deadleg factors1 as non-piping; monitoring1 for other-corrosion-mechanism row. No automatic baseline reset, coating/lining credit, variable corrosion history or all-mechanism DF. Minimum-thickness flag is diagnostic, not acceptance/FFS. Same combined product/soil rate drives Art; same RPB status must drive corrosion and default minimum thickness. No second external-corrosion DF added for the same soil-side loss. Uses representative Table6.1M liquid properties, constant head and C13=6.29bbl/m3. No operating-temperature EOS, connected inventory or transient drainage. Source mass=Bbl printing is not used as kg: mass is volume*density, the explicitly qualified dimensional interpretation. Table3.1 hole frequencies use eq3.208 summed total, with printed total returned separately. One component only; no whole-tank course summation, area consequences or damage applicability inferred. AST release type remains continuous. No generic detection/isolation reduction factors. Soil arithmetic mean preserves reversed printed bounds; explicit water reference properties required. RPB small-hole head.0762m when filled; empty tank zero. SI C37 threshold retained despite SI/US mismatch. Transition count omission requires explicit printed vs per-hole-scaled basis. No-RPB rupture diameter follows complete US Table6.4 row; SI rupture row is incomplete. Medium/large holes have zero count/flow. Table6.5 gives no rupture count, so rupture flow and duration are null; rupture volume is whole inventory per eq3.230. Bottom detection with concrete/asphalt AND RPB requires explicit priority. Count outside30.5-91.4m is flagged, not qualified by this composition. Per-hole GFF, release volumes and qualified environmental costs are supplied inputs. Environment, production, surrounding-equipment and injury unit costs must use the declared currency and repair.cost_basis_year; cost_basis records the common valuation. Table6.6 has no stated price year and must be qualified explicitly before combining with escalated USD2001 repair costs. Component-only consequence. Damage applicability, release hydraulics, consequence areas and monetary qualification are not inferred. Per-hole frequencies normalize once including rupture. No additional ignition weighting or automatic whole-tank course summation. Bottom surrounding-equipment and injury costs are not applicable per §6.12.3 and returned zero. Rupture repair alone scales by diameter squared. Groundwater uses printed detection time, not inventory depletion time. This composition derives DF internally for explicit qualified thinning-only scope; other applicable mechanisms must be excluded with owner basis. Uniform computed DF and Fms apply to all four holes. Annual financial risk=sum(GFF)*DF*Fms*already-GFF-weighted consequence. Single bottom, not all-mechanism or whole-tank risk. Corrosion, thickness and source RPB status must agree.

## `api581.api.damage.cladding_remaining_life`

Cladding or weld overlay depletion time from thickness baseline

계산 ID: `damage/cladding-remaining-life`

출처: Part2 §4.5.7 STEP4,eq(2.11); PDF p152

| 입력 | 필수 | 타입 |
|---|---|---|
| `starting_total_thickness_m` | 예 | `<class 'float'>` |
| `original_base_material_thickness_m` | 예 | `<class 'float'>` |
| `cladding_corrosion_rate_m_year` | 예 | `<class 'float'>` |

출력: `remaining_cladding_at_baseline_m`, `cladding_depletion_age_years`, `cladding_baseline_state`

적용 범위: Remaining cladding=max(starting total thickness-original base thickness,0); depletion age divides this by cladding corrosion rate. Base reference thickness is owner-qualified, not auto-inferred from a measured total. No coating/lining equivalence. Zero-rate extension: intact noncorroding cladding has null depletion age, already-depleted cladding has age0; no numeric infinity or division by zero.

## `api581.api.damage.thinning_clad_wall_loss`

Sequential cladding and base-material fractional wall loss

계산 ID: `damage/thinning-clad-wall-loss`

출처: Part2 §4.5.7 STEP6(2)-(4),eqs(2.13)-(2.15); PDF pp152-153

| 입력 | 필수 | 타입 |
|---|---|---|
| `starting_total_thickness_m` | 예 | `<class 'float'>` |
| `original_base_material_thickness_m` | 예 | `<class 'float'>` |
| `cladding_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |

출력: `remaining_cladding_at_baseline_m`, `cladding_depletion_age_years`, `cladding_baseline_state`, `wall_loss_fraction`, `cladding_wall_loss_m`, `base_material_wall_loss_m`, `base_material_exposure_years`, `predicted_remaining_thickness_m`, `predicted_penetration`, `wall_loss_branch`

적용 범위: Cladding/overlay is assumed to corrode before base material, as source procedure states. Before depletion: cladding rate*elapsed. At/after depletion: cladding rate*depletion age+base rate*(elapsed-depletion age). Already depleted uses base-only eq2.13. Divide by starting TOTAL thickness. Constant rates from same qualified baseline; no simultaneous backside/external corrosion, debonding, coating life or variable process history. Noncorroding intact cladding uses explicit zero-rate analytic extension. Predicted penetration is diagnostic, not FFS acceptance.

## `api581.api.damage.thinning_design_strength_ratio`

Thinning strength ratio from required and structural thickness

계산 ID: `damage/thinning-design-strength-ratio`

출처: Part2 §4.5.7 STEP5,STEP8,eq(2.17); PDF pp152-154

| 입력 | 필수 | 타입 |
|---|---|---|
| `allowable_stress_pa` | 예 | `<class 'float'>` |
| `weld_efficiency` | 예 | `<class 'float'>` |
| `flow_stress_pa` | 예 | `<class 'float'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `minimum_required_thickness_m` | 예 | `<class 'float'>` |
| `minimum_structural_thickness_m` | 예 | `<class 'float'>` |
| `design_thickness_basis` | 예 | `<class 'str'>` |

출력: `strength_ratio`, `governing_minimum_thickness_m`, `governing_thickness_source`

적용 범위: SR=(allowable stress*weld efficiency/flow stress)*max(code minimum,structural minimum)/starting thickness. Owner supplies qualified code/design thickness including governing internal/external pressure and structural loads. This API does not calculate those code minima or certify buckling strength. Zero explicitly denotes a non-governing term; both minima cannot be zero. Flow stress, allowable stress and efficiency must have consistent design-temperature/material basis; no automatic cladding structural-strength credit.

## `api581.api.damage.thinning_clad`

Compose clad non-AST thinning with selected strength-ratio method

계산 ID: `damage/thinning-clad`

출처: Part2 §4.5.7,eqs(2.11),(2.13)-(2.23); PDF pp152-156

| 입력 | 필수 | 타입 |
|---|---|---|
| `assessment_scope` | 예 | `typing.Literal['non_ast_pressure_vessel_sequential_cladding']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `wall` | 예 | `<class 'api581.clad_thinning.CladWall'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `injection_point_factor` | 예 | `<class 'float'>` |
| `deadleg_factor` | 예 | `<class 'float'>` |
| `online_monitoring_factor` | 예 | `<class 'float'>` |

출력: `remaining_cladding_at_baseline_m`, `cladding_depletion_age_years`, `cladding_baseline_state`, `wall_loss_fraction`, `cladding_wall_loss_m`, `base_material_wall_loss_m`, `base_material_exposure_years`, `predicted_remaining_thickness_m`, `predicted_penetration`, `wall_loss_branch`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `strength_ratio`, `strength_method`

적용 범위: Explicit non-AST pressure-vessel sequential-cladding scope; owner qualifies baseline, reference base thickness, corrosion rates, inspection eligibility, monitoring and applicability. Select internal-hoop-pressure eq2.18 only when governing; structural/external-pressure cases require qualified code-minimum eq2.17. Same total starting thickness must drive wall-loss and strength equations. Standard three damage states and conservative default COVs are reused. AST welded/maintenance/settlement factors1; not AST-bottom table, lining protection, simultaneous corrosion or all-mechanism DF. Grade counts must be eligible since same baseline. Zero-rate intact cladding extension is explicit in branch output.

## `api581.api.damage.thinning_unclad_design`

Compose unclad thinning with code and structural minimum strength ratio

계산 ID: `damage/thinning-unclad-design`

출처: Part2 §4.5.7,eqs(2.13),(2.17),(2.19)-(2.23); PDF pp153-156

| 입력 | 필수 | 타입 |
|---|---|---|
| `assessment_scope` | 예 | `typing.Literal['non_ast_unclad_design_thickness_governed']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `wall` | 예 | `<class 'api581.thinning.WallLoss'>` |
| `strength` | 예 | `<class 'api581.clad_thinning.DesignStrengthRatio'>` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `injection_point_factor` | 예 | `<class 'float'>` |
| `deadleg_factor` | 예 | `<class 'float'>` |
| `online_monitoring_factor` | 예 | `<class 'float'>` |

출력: `wall_loss_fraction`, `strength_ratio`, `governing_minimum_thickness_m`, `governing_thickness_source`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`

적용 범위: Non-AST unclad component with owner-qualified governing code/structural minima. Eq2.17 replaces internal-hoop-only eq2.18; source code minima and load applicability are external inputs, not computed FFS. Starting thickness must agree. No AST construction factors, cladding/lining credit, automatic corrosion-rate selection or all-mechanism DF. Inspection counts and monitoring factors require same baseline and applicable mechanism qualification.

## `api581.api.damage.thinning_monitoring_row`

Select thinning online-monitoring table row

계산 ID: `damage/thinning-monitoring-row`

출처: Part2 Table4.8; PDF p164

| 입력 | 필수 | 타입 |
|---|---|---|
| `mechanism` | 예 | `typing.Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_acid', 'hydrofluoric_acid', 'sour_water', 'amine', 'other']` |
| `velocity_m_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `sulfuric_material_group` | 기본값/선택 | `typing.Literal['carbon_steel', 'stainless_steel', 'higher_alloy'] | None` |
| `amine_velocity_regime` | 기본값/선택 | `typing.Literal['low', 'high'] | None` |
| `amine_regime_basis` | 기본값/선택 | `str | None` |

출력: `monitoring_row`, `velocity_threshold_m_s`

적용 범위: Sulfuric acid low/high thresholds3/5/7ft/s for CS/SS/higher alloys, sour water20ft/s; public m/s with exact.3048 conversion. Threshold equality is low. Amine low/high numeric threshold is not supplied by this table: owner regime and basis required. Mechanism applicability and actual material classification are external qualifications. Printed sulfuric-acid label appends H2S/H2; this API follows named sulfuric-acid row, preserves issue in documentation and does not assert official erratum.

## `api581.api.damage.thinning_monitoring_table_factor`

Thinning online-monitoring table cell and explicit joint exception

계산 ID: `damage/thinning-monitoring-table-factor`

출처: Part2 Table4.8; PDF p164

| 입력 | 필수 | 타입 |
|---|---|---|
| `monitoring_row` | 예 | `typing.Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']` |
| `monitoring_method` | 예 | `typing.Literal['key_process_variables', 'electrical_resistance_probes', 'corrosion_coupons']` |
| `key_variables_with_probes` | 기본값/선택 | `<class 'bool'>` |

출력: `table_monitoring_factor`

적용 범위: Table row factors in column order key variables/ER probes/coupons. HCl and high-velocity sulfuric key-variable factor rises10 to20 only in conjunction with probes. This independent cell lookup does not establish a qualified organized monitoring plan; use thinning-online-monitoring-factor for credit gate. Other methods require specialist judgment, not guessed table equivalence.

## `api581.api.damage.thinning_online_monitoring_factor`

Qualified thinning monitoring credit without stacking

계산 ID: `damage/thinning-online-monitoring-factor`

출처: Part2 §4.5.7 STEP15(1),Table4.8 notes1-3; PDF pp155,164

| 입력 | 필수 | 타입 |
|---|---|---|
| `row` | 예 | `<class 'api581.thinning_conditions.MonitoringRow'>` |
| `methods` | 예 | `list[typing.Literal['key_process_variables', 'electrical_resistance_probes', 'corrosion_coupons']]` |
| `organized_monitoring_plan` | 예 | `<class 'bool'>` |
| `qualification_basis` | 기본값/선택 | `str | None` |
| `key_variables_probe_conjunction_confirmed` | 기본값/선택 | `<class 'bool'>` |
| `experience_factor` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `experience_factor_basis` | 기본값/선택 | `str | None` |

출력: `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`

적용 범위: No organized plan means applied factor1 regardless of installed methods. Qualified plan must recognize mechanism, appropriate variables and specialist intervals. Choose maximum applicable method factor, never sum/product. Joint20 needs both key variables and ER probes plus confirmed conjunction. Table estimates may be replaced by owner-experience positive factor with basis under note1; replacement is entire applied factor, not a stacked bonus. No methods and no override gives1. Other monitoring methods require qualified experience basis; no automatic sensor-data efficacy classification.

## `api581.api.damage.thinning_injection_point_factor`

Thinning injection or corrosive mix point adjustment

계산 ID: `damage/thinning-injection-point-factor`

출처: Part2 §4.5.7 STEP15(2); PDF p156

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_scope` | 예 | `typing.Literal['piping', 'non_piping']` |
| `injection_or_mix_point_present` | 예 | `<class 'bool'>` |
| `highly_effective_targeted_inspection` | 예 | `<class 'bool'>` |
| `inspection_basis` | 기본값/선택 | `str | None` |

출력: `injection_point_factor`

적용 범위: Piping with injection/mix point factor3, reduced1 only by highly effective targeted inspection per source API570 reference. Owner classifies actual mix corrosion: flashing liquid/vapor mixing, water-bearing streams or mixed temperature below combined dew point. Generic inspection does not earn automatic credit. Non-piping factor1.

## `api581.api.damage.thinning_deadleg_factor`

Thinning intermittent-service or stagnant deadleg adjustment

계산 ID: `damage/thinning-deadleg-factor`

출처: Part2 §4.5.7 STEP15(3); PDF p156

| 입력 | 필수 | 타입 |
|---|---|---|
| `component_scope` | 예 | `typing.Literal['piping', 'non_piping']` |
| `deadleg_present` | 예 | `<class 'bool'>` |
| `highly_effective_targeted_inspection` | 예 | `<class 'bool'>` |
| `inspection_basis` | 기본값/선택 | `str | None` |

출력: `deadleg_factor`

적용 범위: Piping deadleg factor3, reduced1 only by highly effective inspection specifically addressing localized deadleg corrosion. Owner classifies intermittent/no-significant-flow service; no automatic velocity threshold. Non-piping factor1.

## `api581.api.damage.thinning_conditional_adjustment`

Apply qualified non-AST thinning adjustment conditions

계산 ID: `damage/thinning-conditional-adjustment`

출처: Part2 §4.5.7 STEP15,eq(2.23),Table4.8; PDF pp155-156,164

| 입력 | 필수 | 타입 |
|---|---|---|
| `assessment_scope` | 예 | `typing.Literal['non_ast']` |
| `base_damage_factor` | 예 | `<class 'float'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |

출력: `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `base_damage_factor`, `thinning_damage_factor`

적용 범위: Non-AST conditions only: AST construction, maintenance and settlement factors1. FinalDF=max(baseDF*injection*deadleg/monitoring,.1). Monitoring uses maximum qualified method or documented experience replacement; no duplicate monitoring factors. No automatic corrosion/inspection applicability screening.

## `api581.api.damage.thinning_unclad_qualified`

Unclad non-AST thinning with condition-derived adjustment factors

계산 ID: `damage/thinning-unclad-qualified`

출처: Part2 §4.5.7,eqs(2.13),(2.17)-(2.23),Table4.8; PDF pp153-156,164

| 입력 | 필수 | 타입 |
|---|---|---|
| `assessment_scope` | 예 | `typing.Literal['non_ast_unclad']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `wall` | 예 | `<class 'api581.thinning.WallLoss'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |

출력: `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`

적용 범위: Qualified non-AST unclad component; shared wall/strength baseline required. Governing strength method explicit; code minima and load applicability remain supplied. Conditions derive piping/monitoring adjustments rather than accepting duplicate numeric factors. Table row classification is not corrosion-mechanism applicability screening or inspection validation. No all-mechanism DF or AST corrections.

## `api581.api.damage.thinning_clad_qualified`

Clad pressure-vessel thinning with condition-derived monitoring adjustment

계산 ID: `damage/thinning-clad-qualified`

출처: Part2 §4.5.7,eqs(2.11),(2.13)-(2.23),Table4.8; PDF pp152-156,164

| 입력 | 필수 | 타입 |
|---|---|---|
| `assessment_scope` | 예 | `typing.Literal['non_ast_pressure_vessel_sequential_cladding']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `wall` | 예 | `<class 'api581.clad_thinning.CladWall'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |

출력: `remaining_cladding_at_baseline_m`, `cladding_depletion_age_years`, `cladding_baseline_state`, `wall_loss_fraction`, `cladding_wall_loss_m`, `base_material_wall_loss_m`, `base_material_exposure_years`, `predicted_remaining_thickness_m`, `predicted_penetration`, `wall_loss_branch`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `strength_ratio`, `strength_method`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`

적용 범위: Non-AST pressure vessel with sequential-cladding scope, owner-qualified corrosion rates and baseline. Injection/deadleg conditions must both be non-piping. Shared monitoring classification drives one applied factor. Reuses clad zero-rate extension and both strength methods; no coating/lining, simultaneous backside corrosion, code-minimum calculation or all-mechanism DF.

## `api581.api.damage.lining_effective_age`

Lining age from installation or qualified A/B inspection

계산 ID: `damage/lining-effective-age`

출처: Part2 §§5.5.2-5.5.3 STEP1,Table5.3,Figure5.1; PDF pp166,168,171

| 입력 | 필수 | 타입 |
|---|---|---|
| `lining_family` | 예 | `typing.Literal['inorganic', 'organic']` |
| `installed_on` | 예 | `<class 'datetime.date'>` |
| `evaluated_on` | 예 | `<class 'datetime.date'>` |
| `inspections` | 기본값/선택 | `list[api581.lining.LiningInspection]` |
| `age_basis_policy` | 예 | `typing.Literal['step1_installation_or_last_ab', 'figure51_organic_service_only']` |
| `year_length_days` | 예 | `typing.Literal[365, 365.25]` |

출력: `effective_age_years`, `elapsed_service_years`, `age_baseline_date`, `age_baseline_source`, `reset_inspection_id`, `qualified_ab_inspection_count`, `age_basis_policy`

적용 범위: STEP1 permits installation or last A/B inspection baseline; organic table/figure also say years in service. Explicit policy chooses STEP1 reset or organic service-only interpretation, not an asserted erratum. No inspection-count/Bayesian credit. Owner qualifies A/B reset applicability under Annex2.C.6; C/D/E cannot reset. Date-only deterministic elapsed days divided by explicit365 or365.25; no inferred current clock, time zone or service downtime subtraction.

## `api581.api.damage.lining_base_factor`

Inorganic and organic lining base damage factor tables

계산 ID: `damage/lining-base-factor`

출처: Part2 Tables5.4-5.5; PDF pp169-170

| 입력 | 필수 | 타입 |
|---|---|---|
| `lining_type` | 예 | `typing.Literal['strip_lined_resistant_alloy', 'castable_refractory', 'castable_refractory_severe', 'glass_lined', 'acid_brick', 'fiberglass', 'organic_low_quality', 'organic_medium_quality', 'organic_high_quality']` |
| `age_years` | 예 | `<class 'float'>` |
| `lookup_policy` | 예 | `typing.Literal['exact_rows_only', 'linear_between_rows', 'conservative_upper_row']` |
| `first_year_policy` | 예 | `typing.Literal['reject_below_first_year', 'qualified_first_year_value']` |
| `first_year_qualification_basis` | 기본값/선택 | `str | None` |

출력: `base_damage_factor`, `lower_age_row_years`, `upper_age_row_years`, `age_interpolation_weight`, `first_year_value_used`, `source_table`

적용 범위: All225 cells:6 inorganic/3 organic columns over1..25years. Fiberglass follows source Table5.4 grouping without inferring chemical classification. Organic quality includes stated application/reinforcement thickness, not material name alone. No >25year extrapolation even if selected column plateaus. Between-year numerical policy explicit; source gives no interpolation instruction. Below1year requires rejection or qualified first-year-value policy, never silently zero damage or invented age0 row.

## `api581.api.damage.lining_condition_factor`

Qualitative lining condition factor

계산 ID: `damage/lining-condition-factor`

출처: Part2 Table5.6; PDF p171

| 입력 | 필수 | 타입 |
|---|---|---|
| `condition` | 예 | `typing.Literal['good', 'average', 'poor']` |

출력: `condition_factor`

적용 범위: Owner classifies good: like new/no attack/no repairs; average: no excessive attack with successful good-quality local repairs; poor: prior failures/imminent failure conditions or unsuccessful/poor repairs. No automatic classification from a single damage flag or image.

## `api581.api.damage.lining_monitoring_factor`

Lining early-detection monitoring credit

계산 ID: `damage/lining-monitoring-factor`

출처: Part2 §5.5.3 STEP3(2); PDF p167

| 입력 | 필수 | 타입 |
|---|---|---|
| `monitoring_used` | 예 | `<class 'bool'>` |
| `known_effective_for_lining_deterioration` | 예 | `<class 'bool'>` |
| `effectiveness_basis` | 기본값/선택 | `str | None` |

출력: `monitoring_factor`

적용 범위: Factor.1 only when monitoring is used and known effective for detecting lining deterioration early enough for orderly shutdown; otherwise1. Owner supplies effectiveness basis. Merely installed sensors do not prove efficacy. Unlike thinning FOM, lining factor multiplies DF, not divides; no stacked methods.

## `api581.api.damage.lining_governing_thinning`

Minimum of base-material thinning and lining damage factors

계산 ID: `damage/lining-governing-thinning`

출처: Part2 §5.5.1 and eq(2.2); PDF pp142,166

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_material_thinning_damage_factor` | 예 | `<class 'float'>` |
| `lining_damage_factor` | 예 | `<class 'float'>` |

출력: `governing_thinning_damage_factor`, `governing_source`

적용 범위: Compares lining DF to base-material thinning DF as source instructs. Not total DF: other applicable damage mechanisms require separate combination. No automatic zero/thinning applicability assumption or additional.1 floor on lining DF.

## `api581.api.damage.lining_assessment`

Compose lining age base factor condition monitoring and governing thinning

계산 ID: `damage/lining-assessment`

출처: Part2 §§5.1-5.5,eq(2.24),Tables5.4-5.6,Figure5.1; PDF pp166-171

| 입력 | 필수 | 타입 |
|---|---|---|
| `lining_type` | 예 | `typing.Literal['strip_lined_resistant_alloy', 'castable_refractory', 'castable_refractory_severe', 'glass_lined', 'acid_brick', 'fiberglass', 'organic_low_quality', 'organic_medium_quality', 'organic_high_quality']` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `organic_compatible_with_environment` | 기본값/선택 | `bool | None` |
| `organic_within_design_temperature_including_steamout` | 기본값/선택 | `bool | None` |
| `organic_properly_applied_and_cured` | 기본값/선택 | `bool | None` |
| `age` | 예 | `<class 'api581.lining.LiningAge'>` |
| `lookup_policy` | 예 | `typing.Literal['exact_rows_only', 'linear_between_rows', 'conservative_upper_row']` |
| `first_year_policy` | 예 | `typing.Literal['reject_below_first_year', 'qualified_first_year_value']` |
| `first_year_qualification_basis` | 기본값/선택 | `str | None` |
| `condition` | 예 | `<class 'api581.lining.LiningCondition'>` |
| `monitoring` | 예 | `<class 'api581.lining.LiningMonitoring'>` |
| `base_material_thinning_damage_factor` | 예 | `<class 'float'>` |
| `base_material_thinning_basis` | 예 | `<class 'str'>` |

출력: `effective_age_years`, `elapsed_service_years`, `age_baseline_date`, `age_baseline_source`, `reset_inspection_id`, `qualified_ab_inspection_count`, `age_basis_policy`, `base_damage_factor`, `lower_age_row_years`, `upper_age_row_years`, `age_interpolation_weight`, `first_year_value_used`, `source_table`, `condition_factor`, `monitoring_factor`, `lining_damage_factor`, `governing_thinning_damage_factor`, `governing_source`, `base_material_thinning_damage_factor`

적용 범위: Compatible protective lining must be owner-qualified. Organic compatibility, temperature including steamout and proper application/curing must all be affirmed; false/unknown rejects source-assumption credit. Date history only resets per explicit source-interpretation policy and qualified A/B inspection. No automatic inspection-method classification or actual lining degradation-rate model. Base tables1..25years; interpolation/first-year policies explicit. LiningDF=base*condition*monitoring, then governing thinning=min(base-metal thinningDF,liningDF), not sum or product of both DFs. No.1 floor or automatic all-mechanism DF. Cladding/overlay sequential wall-loss calculations are distinct.

## `api581.api.damage.cooling_water_rate_factors`

Cooling-water qualitative corrosion-rate factor flags

계산 ID: `damage/cooling-water-rate-factors`

출처: Part2 Annex2.B §11.1.6; PDF pp398-399

| 입력 | 필수 | 타입 |
|---|---|---|
| `process_temperature_k` | 예 | `<class 'float'>` |
| `impurities_in_makeup_water` | 기본값/선택 | `<class 'bool'>` |
| `deposits_present` | 기본값/선택 | `<class 'bool'>` |
| `corrosion_products_present` | 기본값/선택 | `<class 'bool'>` |
| `biomass_present` | 기본값/선택 | `<class 'bool'>` |
| `hydrocarbon_process_leak` | 기본값/선택 | `<class 'bool'>` |
| `low_flow_or_stagnant_area` | 기본값/선택 | `<class 'bool'>` |

출력: `scale_potential`, `deposit_risk`, `biological_or_mic_risk`, `underdeposit_risk`, `factor_flags`

적용 범위: Qualitative screening only: the source describes impurities, scale, deposits, biomass and low-flow effects but supplies no universal multipliers. Scale potential is flagged when process temperature exceeds60C. No flag is converted into a corrosion rate, damage factor or treatment credit; owner qualification remains required.

## `api581.api.damage.cooling_water_ph_coefficients`

Cooling water saturation-pH coefficient table

계산 ID: `damage/cooling-water-ph-coefficients`

출처: Part2 Table2.B.11.3; PDF p408

| 입력 | 필수 | 타입 |
|---|---|---|
| `total_dissolved_solids_mg_l` | 예 | `<class 'float'>` |
| `water_temperature_k` | 예 | `<class 'float'>` |
| `temperature_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `calcium_hardness_mg_caco3_l` | 예 | `<class 'float'>` |
| `methyl_orange_alkalinity_mg_caco3_l` | 예 | `<class 'float'>` |
| `lookup_policy` | 예 | `typing.Literal['exact_rows_only', 'linear_between_rows', 'maximum_bracketing_value']` |
| `c4_source_policy` | 예 | `typing.Literal['reject_ambiguous_cells', 'qualified_printed_literal']` |
| `c4_literal_basis` | 기본값/선택 | `str | None` |

출력: `c1`, `c2`, `c3`, `c4`, `c4_printed_literal_used`

적용 범위: C1 TDS50..400=.1,>400..1000=.2. C2 uses explicit printed C/F temperature grid; pairs rounded inconsistently. C3/C4 rows20/31 have no printed factors: exact use or interpolation crossing those rows rejected. C4 first two factors print10.5/12.5, unlike following1.2..3: reject those cells/adjacent interpolation unless qualified printed-literal policy and basis chosen. No inferred1.0/1.1 repair. Interpolation/maximum bracketing is explicit numerical policy, not a source mandate.

## `api581.api.damage.cooling_water_stability_indices`

Langelier and Ryznar cooling-water indices

계산 ID: `damage/cooling-water-stability-indices`

출처: Part2 eqs(2.B.9)-(2.B.10); PDF p402

| 입력 | 필수 | 타입 |
|---|---|---|
| `actual_ph` | 예 | `<class 'float'>` |
| `saturation_ph` | 예 | `<class 'float'>` |

출력: `langelier_saturation_index`, `ryznar_stability_index`

적용 범위: LSI=pHa-pHs; RSI=2*pHs-pHa. Index alone is not quantitative corrosion rate or water-treatment effectiveness. Main cooling model assumes pH6.5..9.5; this independent index arithmetic does not screen that applicability.

## `api581.api.damage.cooling_water_saturation_ph`

Cooling water saturation pH from four coefficients

계산 ID: `damage/cooling-water-saturation-ph`

출처: Part2 eq(2.B.11); PDF p403

| 입력 | 필수 | 타입 |
|---|---|---|
| `c1` | 예 | `<class 'float'>` |
| `c2` | 예 | `<class 'float'>` |
| `c3` | 예 | `<class 'float'>` |
| `c4` | 예 | `<class 'float'>` |

출력: `saturation_ph`

적용 범위: pHs=(9.3+C1+C2)-(C3+C4). Coefficients supplied or obtained from separate table API. Signed raw pHs retained diagnostically; no clamp of anomalous literal C4 results into a physical range. Main freshwater model requires qualified pHs0..14.

## `api581.api.damage.cooling_water_base_rate`

Cooling water chloride and scaling base corrosion rate

계산 ID: `damage/cooling-water-base-rate`

출처: Part2 §11.3.1.2,Tables2.B.11.4/11.4M; PDF pp402-403,409

| 입력 | 필수 | 타입 |
|---|---|---|
| `chloride_ppm` | 예 | `<class 'float'>` |
| `ryznar_stability_index` | 예 | `<class 'float'>` |
| `velocity_m_s` | 예 | `<class 'float'>` |
| `condition_interpretation` | 예 | `typing.Literal['body_rsi6_velocity2_44', 'us_header_rsi6_velocity8ft']` |
| `rate_unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_rows_only', 'linear_between_rows', 'maximum_bracketing_value']` |

출력: `base_corrosion_rate_m_year`, `base_column`, `base_velocity_threshold_m_s`

적용 범위: SI table both headers repeat RSI<=1.8 and velocity<=2.4; unusable for automatic column choice. Explicit interpretation follows detailed-body RSI6/2.44m/s or US header RSI6/8ft/s; no official SI erratum asserted. High column if RSI>6 OR velocity>threshold, otherwise scaling low column. Printed SI rates and exact US-mpy conversion differ. Chloride5..10000ppm only, explicit interpolation policy; maximum bracketing stays conservative on declining high-chloride rows. Not automatic seawater/freshwater classification.

## `api581.api.damage.cooling_water_temperature_factor`

Cooling water open or closed system temperature factor

계산 ID: `damage/cooling-water-temperature-factor`

출처: Part2 eq(2.B.12),Table2.B.11.5; PDF pp403,410

| 입력 | 필수 | 타입 |
|---|---|---|
| `metal_temperature_k` | 예 | `<class 'float'>` |
| `system` | 예 | `typing.Literal['open', 'closed']` |
| `temperature_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `argument_policy` | 예 | `typing.Literal['table_operating_temperature', 'text_delta_from_reference']` |
| `duplicate_row_policy` | 예 | `typing.Literal['reject_unresolved_row', 'qualified_ignore_misordered_row']` |
| `duplicate_row_basis` | 기본값/선택 | `str | None` |
| `lookup_policy` | 예 | `typing.Literal['exact_rows_only', 'linear_between_rows', 'maximum_bracketing_value']` |

출력: `temperature_factor`, `temperature_table_argument`, `misordered_row_ignored`

적용 범위: Text says use deltaT from24C/75F, table labels operating temperature. Explicit argument policy selects interpretation. Source penultimate row repeats41C/105F with factors4.3/2.5 after93C/200F; no invented96C/205F fix. Default rejects repeated node/adjacent interpolation and upper gap crossing misordered row. Qualified ignore policy omits row explicitly, with owner basis; remaining printed rows interpolate by selected policy. No table-range extrapolation; temperature basis is rounded SI or converted US grid.

## `api581.api.damage.cooling_water_velocity_factor`

Cooling water velocity adjustment equation

계산 ID: `damage/cooling-water-velocity-factor`

출처: Part2 eqs(2.B.13)-(2.B.18),Table2.B.11.6; PDF pp403-404,411

| 입력 | 필수 | 타입 |
|---|---|---|
| `velocity_m_s` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `velocity_factor`

적용 범위: Printed SI uses boundaries.914/2.44m/s and slopes1.64/.82; US3/8ft/s and slopes.50/.25. Explicit basis preserves rounding difference. Public velocitym/s, qualified source application up to6.1m/s(20ft/s rounded), no extrapolation beyond. Equation evaluated directly, not interpolated rounded table values.

## `api581.api.damage.cooling_water_rate_equation`

Cooling water base rate with temperature and velocity factors

계산 ID: `damage/cooling-water-rate-equation`

출처: Part2 eq(2.B.8); PDF p402

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `temperature_factor` | 예 | `<class 'float'>` |
| `velocity_factor` | 예 | `<class 'float'>` |

출력: `corrosion_rate_m_year`

적용 범위: Constant qualified carbon-steel cooling-water factors only; this equation does not screen treatment, MIC, deposits or material applicability.

## `api581.api.damage.cooling_water_seawater_rate`

Once-through seawater carbon-steel corrosion correlation

계산 ID: `damage/cooling-water-seawater-rate`

출처: Part2 §11.3.2.3,eqs(2.B.19)-(2.B.20); PDF p405

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel']` |
| `velocity_m_s` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `applicability_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`

적용 범위: Correlation reference about21C and dissolved oxygen6-8ppm; owner qualifies seawater, untreated carbon steel, oxygen/temperature and absence of deposit/MIC exceptions. Public velocitym/s, limit6.1m/s source cooling assumption; erosion-corrosion above about12.2m/s is outside. SI polynomialmm/y and US polynomialmpy are separately rounded and selectable. No temperature/oxygen/treatment correction invented.

## `api581.api.damage.cooling_water_coupon_pitting_rate`

Qualified cooling-water coupon general to pitting estimate

계산 ID: `damage/cooling-water-coupon-pitting-rate`

출처: Part2 §11.1.10(c),Table2.B.11.1; PDF pp401,407

| 입력 | 필수 | 타입 |
|---|---|---|
| `coupon_general_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `pitting_multiplier` | 예 | `<class 'float'>` |
| `representativeness_basis` | 예 | `<class 'str'>` |

출력: `pitting_corrosion_rate_m_year`

적용 범위: Source prefers representative measured coupon rates over model; rule-of-thumb pitting5-10 times weight-loss general rate. Explicit multiplier and representativeness basis required. Flowing coupon may miss deposits/stagnant/MIC attack; no implied qualification of those cases or universal pitting multiplier.

## `api581.api.damage.cooling_water_fresh_assessment`

Untreated freshwater cooling corrosion with qualified supplied saturation pH

계산 ID: `damage/cooling-water-fresh-assessment`

출처: Part2 §11.1.10,§11.3.1-11.3.2.2,eqs(2.B.8)-(2.B.18); PDF pp401-404,409-410

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel']` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `actual_ph` | 예 | `<class 'float'>` |
| `saturation_ph` | 예 | `<class 'float'>` |
| `saturation_ph_basis` | 예 | `<class 'str'>` |
| `chloride_ppm` | 예 | `<class 'float'>` |
| `velocity_m_s` | 예 | `<class 'float'>` |
| `system` | 예 | `typing.Literal['open_recirculating', 'closed_recirculating', 'once_through_fresh']` |
| `effective_microbiological_control` | 예 | `<class 'bool'>` |
| `no_deposits_or_local_low_flow` | 예 | `<class 'bool'>` |
| `no_corrosion_inhibitor_model_credit` | 예 | `typing.Literal[True]` |
| `condition_interpretation` | 예 | `typing.Literal['body_rsi6_velocity2_44', 'us_header_rsi6_velocity8ft']` |
| `rate_unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `velocity_equation_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `temperature` | 예 | `<class 'api581.cooling_water.CoolingTemperature'>` |
| `chloride_lookup_policy` | 예 | `typing.Literal['exact_rows_only', 'linear_between_rows', 'maximum_bracketing_value']` |

출력: `langelier_saturation_index`, `ryznar_stability_index`, `base_corrosion_rate_m_year`, `base_column`, `base_velocity_threshold_m_s`, `temperature_factor`, `temperature_table_argument`, `misordered_row_ignored`, `velocity_factor`, `corrosion_rate_m_year`

적용 범위: Carbon-steel representative rate; qualified supplied pHs can bypass unresolved coefficient table cells without inventing corrections. Measured representative rates preferred. Assumes pH6.5..9.5, effective MIC control and no deposits/local low flow; no inhibitor credit in this model path. Once-through fresh requires chloride<1000ppm; exactly1000 is unclassified by source strict inequalities and rejected. Temperature table and actual system must agree, once-through fresh uses open factors. Return rate is not automatically general/pitting classified; detailed body says pitting dominates, Annex2.B Table1.2 lists general at specified velocity. No5-10 coupon multiplier automatically applied to modeled rate.

## `api581.api.damage.cooling_water_thinning_assessment`

Freshwater cooling rate through qualified non-AST thinning DF

계산 ID: `damage/cooling-water-thinning-assessment`

출처: Part2 Annex2.B §11; Part2 §4.5.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `cooling` | 예 | `<class 'api581.cooling_water.CoolingFresh'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `thinning_type` | 예 | `typing.Literal['general', 'local']` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `langelier_saturation_index`, `ryznar_stability_index`, `base_corrosion_rate_m_year`, `base_column`, `base_velocity_threshold_m_s`, `temperature_factor`, `temperature_table_argument`, `misordered_row_ignored`, `velocity_factor`, `corrosion_rate_m_year`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `thinning_type`

적용 범위: Unclad non-AST component only. Same representative cooling model rate drives loss and either strength method; conditions derive monitoring/piping adjustments. Owner must qualify general/local thinning and actual inspection coverage despite source body/summary classification difference. No automatic pit multiplier on modeled rate; coupon-pitting estimate is a separate API. No treatment-credit path, MIC/deposit modeling, all-mechanism DF, heat-exchanger bundle rupture model or AST use.

## `api581.api.damage.cooling_water_system_type`

Cooling-water system type and operating premise

계산 ID: `damage/cooling-water-system-type`

출처: Part2 Annex2.B §§11.1.2-11.1.5; PDF pp397-398

| 입력 | 필수 | 타입 |
|---|---|---|
| `system` | 예 | `typing.Literal['once_through', 'closed_recirculated', 'open_recirculated']` |
| `water_source` | 예 | `typing.Literal['fresh', 'seawater', 'brackish', 'unknown']` |
| `reuses_heated_water` | 예 | `<class 'bool'>` |
| `continual_makeup_required` | 예 | `<class 'bool'>` |
| `blowdown_or_evaporation_loss` | 예 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `system`, `water_source`, `requires_continual_makeup`, `has_evaporation_or_blowdown_loss`, `classification_basis`

적용 범위: System classification contract only. Once-through, closed-recirculated and open-recirculated definitions are validated from supplied operating facts; water treatment, corrosion rate, material suitability and source chemistry are not inferred.

## `api581.api.damage.cooling_water_treatment_bounds`

Qualified treated cooling-water strict corrosion bounds

계산 ID: `damage/cooling-water-treatment-bounds`

출처: Part2 §11.1.10,§11.3.2.2,Figure2.B.11.1; PDF pp401,404,414

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel']` |
| `system` | 예 | `typing.Literal['open_recirculating', 'closed_recirculating', 'once_through_fresh']` |
| `qualified_effective_treatment_program` | 예 | `<class 'bool'>` |
| `actual_ph` | 예 | `<class 'float'>` |
| `effective_microbiological_control` | 예 | `<class 'bool'>` |
| `no_deposits_or_local_low_flow` | 예 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `once_through_interpretation` | 기본값/선택 | `typing.Literal['body_untreated_only', 'qualified_figure_treatment'] | None` |

출력: `general_upper_bound_m_year`, `pitting_upper_bound_m_year`, `source_rate_relation`

적용 범위: Figure treated branch gives general<3mpy and pitting<15mpy, not exact measured rates. Bounds converted exactly to m/year and returned with strict-less relation. Qualified effective treatment, MIC control, no deposits/local low flow and pH6.5..9.5 required. Figure allows once-through fresh to enter treatment branch but detailed body assumes no chemical treatment except biocide: explicit qualified-figure interpretation required for treated once-through. No automatic program-efficacy or alloy-degradation assessment.

## `api581.api.damage.cooling_water_other_material_estimate`

Cooling-water non-carbon/low-alloy nominal figure estimate

계산 ID: `damage/cooling-water-other-material-estimate`

출처: Part2 §11.1.10-11.1.11,Figure2.B.11.1; PDF pp401,414

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['other_material']` |
| `qualified_for_resistant_material_nominal_estimate` | 예 | `<class 'bool'>` |
| `other_degradation_assessed` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |

출력: `nominal_corrosion_rate_m_year`

적용 범위: Figure non-carbon/non-low-alloy branch estimates.5mpy=.0000127m/year. This is not treated closed-system rate. Detailed text has no quantitative SCC/pitting/dealloying model for other alloys; explicit owner qualification and separate assessment of other degradation required. No automatic assertion stainless/copper/titanium or any nonmetal is immune, and no selection of this estimate solely from material name.

## `api581.api.damage.cooling_water_measured_rate`

Qualified representative measured cooling-water rate

계산 ID: `damage/cooling-water-measured-rate`

출처: Part2 §11.1.10(c),Figure2.B.11.1; PDF pp401,414

| 입력 | 필수 | 타입 |
|---|---|---|
| `measurement` | 예 | `<class 'api581.cooling_selection.CoolingMeasurement'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |

출력: `corrosion_rate_m_year`, `selection_source`

적용 범위: Representative component/coupon measurements take priority over model. General/local component rate must match assessment. General weight-loss coupon used for local assessment requires explicit5-10 multiplier; already-local component measurements must never be multiplied again. Coupon coverage of deposits/stagnant/MIC areas is not inferred. Zero measured rate remains a valid explicit input, not treated as missing.

## `api581.api.damage.cooling_water_rate_selection`

Select measured treated freshwater seawater or other-material cooling rate

계산 ID: `damage/cooling-water-rate-selection`

출처: Part2 §11.1.10,§11.3,Figure2.B.11.1; PDF pp401-405,414

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel', 'other_material']` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `selection_basis` | 예 | `<class 'str'>` |
| `measurement` | 기본값/선택 | `api581.cooling_selection.CoolingMeasurement | None` |
| `fallback` | 기본값/선택 | `api581.cooling_selection.FreshChoice | api581.cooling_selection.SeawaterChoice | api581.cooling_selection.TreatmentChoice | api581.cooling_selection.OtherChoice | None` |

출력: `corrosion_rate_m_year`, `selection_source`, `assessment_distribution`, `source_strict_upper_bound_m_year`, `selected_rate_is_screening_bound`, `fallback_ignored_due_to_measurement`

적용 범위: Qualified measured rate always selected before fallback; malformed/unrepresentative measurement errors instead of silently switching to model. Supplied fallback input structure is validated, but fallback calculation/assumption gates are not executed when measurement selected. Without measurement, explicit fallback required; no material/water/treatment guess. Model general/local representativeness must be owner-qualified. Treated strict bound is either an explicitly labeled conservative screening rate at the bound or an owner rate strictly below it, not automatic exact prediction. Main quantitative fresh/seawater models remain carbon-steel-only; other-material nominal path needs separate qualification. No all-mechanism/whole-component immunity conclusion.

## `api581.api.damage.cooling_water_selected_thinning`

Selected cooling-water measured or model rate through non-AST thinning DF

계산 ID: `damage/cooling-water-selected-thinning`

출처: Part2 Annex2.B §11,Figure2.B.11.1; Part2 §4.5.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `selection` | 예 | `<class 'api581.cooling_selection.CoolingRateSelection'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `selection_source`, `assessment_distribution`, `source_strict_upper_bound_m_year`, `selected_rate_is_screening_bound`, `fallback_ignored_due_to_measurement`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`

적용 범위: Same selected measured/model/bound rate drives unclad non-AST thinning; general/local classification and inspection coverage are qualified inputs. Retains screening-bound flag through final DF, never presents it as a measured rate. No second pitting multiplier, treatment credit or duplicated monitoring adjustment. Either strength-ratio method supported with same thickness baseline. Other-material nominal rate does not exclude SCC/pitting/dealloying DFs; apply other applicable mechanisms separately. No AST, cladding, bundle or all-mechanism/whole-system risk assessment.

## `api581.api.damage.co2_relative_humidity`

CO2-service source relative-humidity approximation

계산 ID: `damage/co2-relative-humidity`

출처: Part2 eq(2.B.24); PDF pp423-424

| 입력 | 필수 | 타입 |
|---|---|---|
| `water_mass_fraction` | 예 | `<class 'float'>` |
| `total_pressure_pa_abs` | 예 | `<class 'float'>` |
| `water_saturation_pressure_pa_abs` | 예 | `<class 'float'>` |

출력: `water_dry_gas_mass_ratio`, `relative_humidity_fraction`, `supersaturated`, `saturated`

적용 범위: x=water mass fraction/(1-water mass fraction); RH=x*P/Psat/(.622+x). Source uses air-based MW ratio.622 while discussing natural gas; preserve literal approximation, not an EOS or general natural-gas dew-point calculation. RH may exceed1, not clamped. Strictly greater than1 indicates source condensation condition; equality reported saturated, not automatically free liquid water.

## `api581.api.damage.co2_dew_point`

Approximate source dew point for water-containing gas

계산 ID: `damage/co2-dew-point`

출처: Part2 eq(2.B.25),Table2.B.13.1; PDF pp424,427

| 입력 | 필수 | 타입 |
|---|---|---|
| `water_mass_fraction` | 예 | `<class 'float'>` |
| `total_pressure_pa_abs` | 예 | `<class 'float'>` |

출력: `dew_point_temperature_k`

적용 범위: log10(Td_F)=2.0866+.2088*log10(water mass fraction)+.2242*log10(P_psia). Source water0..30wt%; zero has undefined logarithm and is rejected, not a fabricated dew point. ReturnsK; guidance should not be assumed accurate within±10F. No automatic dry-service screening from this approximate value.

## `api581.api.damage.co2_temperature_ph_factor`

CO2 corrosion temperature-pH table function

계산 ID: `damage/co2-temperature-ph-factor`

출처: Part2 Tables2.B.13.2/13.2M; PDF p428

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `ph` | 예 | `<class 'float'>` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'bilinear']` |
| `jump_policy` | 예 | `typing.Literal['reject_cross_80_90', 'qualified_linear_across_jump']` |
| `jump_qualification_basis` | 기본값/선택 | `str | None` |

출력: `temperature_ph_factor`, `sharp_temperature_interval_interpolated`

적용 범위: All98 cells,20..150C andpH3.5..6.5; exact or explicitly selected bilinear interpolation. Detailed source scope says temperatures above140C not considered: standalone table includes150C printed row, integrated model rejects>140C. Sharp80..90C change is not silently smoothed: interpolation across that interval requires explicit qualified policy/basis. No clamped/extrapolated pH or temperature; table function is not corrosion rate alone.

## `api581.api.damage.co2_ph_estimate`

Carbonic-acid RBI pH approximation by water case

계산 ID: `damage/co2-ph-estimate`

출처: Part2 eqs(2.B.27)-(2.B.29); PDF p424

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `co2_partial_pressure_pa_abs` | 예 | `<class 'float'>` |
| `water_case` | 예 | `typing.Literal['condensate', 'ferrous_saturated', 'salinity_46_g_l']` |
| `approximation_basis` | 예 | `<class 'str'>` |

출력: `estimated_ph`

적용 범위: Uses temperatureF and CO2 partial pressurepsi as printed; publicK/Pa converted first. Supplied known pH preferred. Owner qualifies simple water/Fe++/saline case, negligible bicarbonate buffering and salinity limitations. Source saline case says46g/L but following paragraph cautions>45g/L: no automatic resolution or general electrolyte equilibrium model. PositiveF required for logarithm; result not forced into lookup range.

## `api581.api.damage.co2_fugacity`

CO2 fugacity and coefficient from partial pressure

계산 ID: `damage/co2-fugacity`

출처: Part2 eqs(2.B.30)-(2.B.32); PDF p425

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `co2_partial_pressure_pa_abs` | 예 | `<class 'float'>` |
| `temperature_denominator_basis` | 예 | `typing.Literal['printed_celsius_plus_273', 'kelvin_exact']` |

출력: `fugacity_pa`, `fugacity_coefficient`

적용 범위: Literal log10(f_bar)=log10(p_bar)+min(250,p_bar)*(.0031-1.4/(T_C+273)). PublicPa/K; explicit printed273 versus exactK denominator basis, no hidden273.15 repair. Primitive evaluates printed250bar exponent cap; integrated model separately limits partial pressure4MPa perTable13.1. Not a general-mixture EOS, total-pressure substitution or phase-equilibrium calculation.

## `api581.api.damage.co2_reynolds`

Mixture Reynolds number for CO2 flow correlation

계산 ID: `damage/co2-reynolds`

출처: Part2 eq(2.B.35); PDF p425

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |
| `mixture_density_kg_m3` | 예 | `<class 'float'>` |
| `mixture_velocity_m_s` | 예 | `<class 'float'>` |
| `mixture_viscosity_pa_s` | 예 | `<class 'float'>` |

출력: `reynolds_number`

적용 범위: D*rho*velocity/viscosity, all SI. Mixture properties externally qualified; no two-phase holdup/viscosity/density or gas-in-oil solubility model inferred.

## `api581.api.damage.co2_friction_factor`

Source turbulent mixture friction factor

계산 ID: `damage/co2-friction-factor`

출처: Part2 eq(2.B.34); PDF p425

| 입력 | 필수 | 타입 |
|---|---|---|
| `reynolds_number` | 예 | `<class 'float'>` |
| `relative_roughness` | 예 | `<class 'float'>` |

출력: `friction_factor`

적용 범위: f=.001375*[1+(20000*relative_roughness+1e6/Re)^.33]. Printed.33 exponent retained, not1/3. Valid only Re>2300; no laminar/transitional fallback or automatic Darcy/Fanning conversion.

## `api581.api.damage.co2_shear_stress`

CO2 mixture wall shear stress

계산 ID: `damage/co2-shear-stress`

출처: Part2 eq(2.B.33); PDF p425

| 입력 | 필수 | 타입 |
|---|---|---|
| `friction_factor` | 예 | `<class 'float'>` |
| `mixture_density_kg_m3` | 예 | `<class 'float'>` |
| `mixture_velocity_m_s` | 예 | `<class 'float'>` |

출력: `shear_stress_pa`

적용 범위: RawS=f*rho*velocity^2/2; no hidden factor conversion. Separate corrosion base-rate API caps applied shear150Pa, preserves requested shear separately. Not CFD or two-phase property prediction.

## `api581.api.damage.co2_base_rate`

CO2 carbonic-acid base corrosion equation

계산 ID: `damage/co2-base-rate`

출처: Part2 eq(2.B.26),§13.3.6; PDF pp424-425

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_ph_factor` | 예 | `<class 'float'>` |
| `fugacity_pa` | 예 | `<class 'float'>` |
| `shear_stress_pa` | 예 | `<class 'float'>` |

출력: `base_corrosion_rate_m_year`, `applied_shear_stress_pa`, `shear_cap_applied`

적용 범위: CR_mm/y=f(T,pH)*f_bar^.62*(min(S,150)/19)^(.146+.0324*f_bar), literal exponent uses fugacity itself, not log(fugacity). PublicPa/m-year conversions explicit. Applied shear capped150Pa. Zero shear yields literal equation zero; this is not proof stagnant wet steel is safe or outside-mechanism corrosion absent. Positive numeric under/overflow rejected. No automatic applicability or pH-table screening in this primitive.

## `api581.api.damage.co2_glycol_factor`

CO2 glycol reduction with explicit composition basis

계산 ID: `damage/co2-glycol-factor`

출처: Part2 eq(2.B.36),Table2.B.13.1; PDF pp426-427

| 입력 | 필수 | 타입 |
|---|---|---|
| `composition_percent` | 예 | `<class 'float'>` |
| `composition_basis` | 예 | `typing.Literal['equation_g_percent', 'table_water_weight_percent']` |

출력: `glycol_factor`, `glycol_floor_applied`

적용 범위: Equation definesG glycol percent while data table requests water weight percent of glycol/water mix. Explicit basis either uses literalG orG=100-water%; no inference of arbitrary glycol-to-water mass ratio. Factor=max(.008,((100-G)/100)^1.6), algebraically equivalent to printed base10 logs. G100 uses continuous limiting value with source.008 floor, not log0. Absent glycol isG0,factor1.

## `api581.api.damage.co2_rate_adjustment`

Apply minimum of glycol and independently qualified inhibitor factors

계산 ID: `damage/co2-rate-adjustment`

출처: Part2 eq(2.B.23),§13.3.7; PDF pp423,426

| 입력 | 필수 | 타입 |
|---|---|---|
| `glycol` | 기본값/선택 | `api581.co2_corrosion.CO2Glycol | None` |
| `inhibitor_factor` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `inhibitor_effectiveness_basis` | 기본값/선택 | `str | None` |
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |

출력: `glycol_factor`, `inhibitor_factor`, `applied_reduction_factor`, `corrosion_rate_m_year`

적용 범위: FinalCR=baseCR*min(Fglycol,Finhibitor), never product or additive credit. No glycol/inhibitor defaults factor1. Any supplied inhibitor factor requires independently determined effectiveness basis, including explicitly supplied1. Factor0 is retained if independently qualified; glycol.008 floor does not impose an invented floor on the inhibitor. This calculation does not validate real inhibitor deployment or uptime.

## `api581.api.damage.co2_corrosion_assessment`

Qualified free-water CO2 corrosion from pH fugacity flow and reductions

계산 ID: `damage/co2-corrosion-assessment`

출처: Part2 Annex2.B §13,eqs(2.B.23)-(2.B.36),Table2.B.13.1; PDF pp423-429

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel']` |
| `temperature_k` | 예 | `<class 'float'>` |
| `co2_partial_pressure_pa_abs` | 예 | `<class 'float'>` |
| `free_liquid_water_present` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `wet_model` | 기본값/선택 | `api581.co2_corrosion.CO2WetModel | None` |

출력: `glycol_factor`, `inhibitor_factor`, `applied_reduction_factor`, `corrosion_rate_m_year`, `base_corrosion_rate_m_year`, `calculation_branch`, `model_ph`, `temperature_ph_factor`, `fugacity_pa`, `requested_shear_stress_pa`, `applied_shear_stress_pa`, `shear_cap_applied`, `sharp_temperature_interval_interpolated`

적용 범위: Carbon/low-alloy steel only, integrated wet model20..140C and CO2 partial pressure<=4MPa; table150C remains standalone only. No free liquid water or CO2 gives CO2-specific rate0, not zero total corrosion/damage. Free-water and upstream simple crude/water/natural-gas wetting applicability are externally qualified; oil-water<20%/velocity>1m/s figure screen and approximate dew point are not automatically used to assert dry metal. pH and shear supplied or estimated with explicit bases; no two-phase EOS, buffering/salinity chemistry, inhibition efficacy or material immunity inferred. Positive wet case uses same pressure/temperature through all primitives; table interpolation and273 denominator explicit. Standalone RH/dew-point approximations do not substitute for free-water evidence.

## `api581.api.damage.co2_thinning_assessment`

CO2 corrosion through qualified non-AST unclad thinning DF

계산 ID: `damage/co2-thinning-assessment`

출처: Part2 Annex2.B §13; Part2 §4.5.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.co2_corrosion.CO2Assessment'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `glycol_factor`, `inhibitor_factor`, `applied_reduction_factor`, `corrosion_rate_m_year`, `base_corrosion_rate_m_year`, `calculation_branch`, `model_ph`, `temperature_ph_factor`, `fugacity_pa`, `requested_shear_stress_pa`, `applied_shear_stress_pa`, `shear_cap_applied`, `sharp_temperature_interval_interpolated`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`

적용 범위: Same CO2 rate drives constant-baseline unclad non-AST wall loss and either strength method. Owner qualifies localized/general inspection coverage, free-water/material/mixture scope and conditions. Zero CO2 rate does not force DF0: baseline strength, uncertainty and.1 thinning floor remain. No AST, cladding, total all-mechanism DF, FFS or automatic moisture/material/wetting/inhibitor qualification.

## `api581.api.properties.co2_partial_pressure`

CO2 partial pressure from absolute total pressure and mole fraction

계산 ID: `properties/co2-partial-pressure`

출처: Part2 Table2.B.13.1; PDF p427

| 입력 | 필수 | 타입 |
|---|---|---|
| `total_pressure_pa_abs` | 예 | `<class 'float'>` |
| `co2_mole_fraction` | 예 | `<class 'float'>` |

출력: `co2_partial_pressure_pa_abs`

적용 범위: pCO2=mole fraction*absolute total pressure. Input is fraction0..1, not mole percent or gauge pressure. No fugacity/EOS calculation or clamping to4MPa integrated model limit. Pure input conversion does not establish free-water or material applicability.

## `api581.api.damage.co2_reynolds_mass_flow`

CO2 mixture Reynolds number from mass flow and area

계산 ID: `damage/co2-reynolds-mass-flow`

출처: Part2 eq(2.B.35); PDF p425

| 입력 | 필수 | 타입 |
|---|---|---|
| `diameter_m` | 예 | `<class 'float'>` |
| `cross_sectional_area_m2` | 예 | `<class 'float'>` |
| `mass_flow_kg_s` | 예 | `<class 'float'>` |
| `mixture_viscosity_pa_s` | 예 | `<class 'float'>` |

출력: `mass_flux_kg_m2_s`, `reynolds_number`

적용 범위: Re=mass_flow*diameter/(area*viscosity); mass flux=mass_flow/area. Source wording calls dottedm mass flux although printed formula divides byarea; API names dimensional quantities explicitly rather than dividing an already-area-normalized flux again. Area/hydraulic diameter and effective viscosity externally qualified; no mixture-property model or laminar correlation.

## `api581.api.damage.co2_material_screen`

CO2 figure chromium or table material screening

계산 ID: `damage/co2-material-screen`

출처: Part2 Figure2.B.13.1,Table2.B.13.1; PDF pp427,429

| 입력 | 필수 | 타입 |
|---|---|---|
| `material_category` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel', 'stainless_steel', 'copper_alloy', 'other']` |
| `interpretation` | 예 | `typing.Literal['figure_13cr_ferrous', 'table_resistant_alloys']` |
| `chromium_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `material_screen_decision`, `source_material_resistance_assumed`

적용 범위: Figure screens carbon steel orCr<13%; equality13% is source-assumed resistant. Chromium threshold applied only to qualified ferrous categories, not copper with nominalCr0. Table interpretation lists stainless/copper assumed resistant and carbon/low-alloy evaluated. Other material remains not_covered, never automatic zero. Explicit interpretation preserves differences between named-alloy table and elemental figure. Source-assumed resistance is CO2-specific, not immunity to other corrosion/SCC or a verified material-performance conclusion.

## `api581.api.damage.co2_hydrocarbon_wetting_screen`

CO2 low-water high-velocity hydrocarbon figure screen

계산 ID: `damage/co2-hydrocarbon-wetting-screen`

출처: Part2 Figure2.B.13.1,Table2.B.13.1; PDF pp427,429

| 입력 | 필수 | 타입 |
|---|---|---|
| `liquid_hydrocarbons_present` | 예 | `<class 'bool'>` |
| `water_cut_policy` | 기본값/선택 | `typing.Literal['explicit_qualified_percent', 'source_default_30_percent'] | None` |
| `water_content_percent` | 기본값/선택 | `float | None` |
| `water_content_basis` | 기본값/선택 | `str | None` |
| `mixture_velocity_m_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `wetting_screen_decision`, `water_content_percent_used`, `source_water_default_used`

적용 범위: LiquidHC AND water<20% AND velocity>1m/s gives source figure exemption. Equality20%/1m/s proceeds to moisture/water check. Percentage basis is not identified precisely in figure: explicit qualified water-cut percent/basis required; do not substitute gas water mass fraction or glycol composition. Missing liquid-system water cut can use explicit source default30%, which never grants exemption. NoHC proceeds to moisture check. This is a qualified legacy figure rule, not proof metal is oil-wet under actual multiphase flow.

## `api581.api.damage.co2_moisture_screen`

CO2 free-water or dew-point screening with explicit uncertainty

계산 ID: `damage/co2-moisture-screen`

출처: Part2 §13.3.2,Table2.B.13.1,Figure2.B.13.1; PDF pp423-424,427,429

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `evidence` | 예 | `typing.Literal['qualified_dew_point', 'qualified_free_water_present', 'qualified_no_free_water', 'source_missing_moisture_assume_wet']` |
| `dew_point_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `dew_point_uncertainty_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `equality_policy` | 기본값/선택 | `typing.Literal['figure_strict_less', 'indeterminate_at_saturation'] | None` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `free_water_screen_state`, `free_water_assumed_from_missing_data`

적용 범위: Known free-water presence/absence can be supplied with basis. Missing gas moisture can explicitly assume wet per table, flagged as source assumption. Qualified dew point requires owner uncertainty and equality policy: outside uncertainty interval classify; inside interval indeterminate. At zero uncertainty and equalT, figure_strict_less uses absent, alternative leaves indeterminate. Approximate eq2.B.25 is not assumed accurate within±10F: no automatic zero-uncertainty adoption of its output. Free-water states concern CO2 only, not all corrosion.

## `api581.api.damage.co2_screened_assessment`

CO2 material hydrocarbon moisture screening through corrosion model

계산 ID: `damage/co2-screened-assessment`

출처: Part2 Annex2.B §13,Figure2.B.13.1,Table2.B.13.1; PDF pp423-429

| 입력 | 필수 | 타입 |
|---|---|---|
| `temperature_k` | 예 | `<class 'float'>` |
| `pressure` | 예 | `<class 'api581.co2_screening.CO2PartialPressure'>` |
| `material` | 예 | `<class 'api581.co2_screening.CO2MaterialScreen'>` |
| `hydrocarbon_wetting` | 기본값/선택 | `api581.co2_screening.CO2HydrocarbonWetting | None` |
| `moisture` | 기본값/선택 | `api581.co2_screening.CO2MoistureScreen | None` |
| `wet_model` | 기본값/선택 | `api581.co2_corrosion.CO2WetModel | None` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `glycol_factor`, `inhibitor_factor`, `applied_reduction_factor`, `corrosion_rate_m_year`, `base_corrosion_rate_m_year`, `model_ph`, `temperature_ph_factor`, `fugacity_pa`, `requested_shear_stress_pa`, `applied_shear_stress_pa`, `shear_cap_applied`, `sharp_temperature_interval_interpolated`, `co2_partial_pressure_pa_abs`, `material_screen_decision`, `source_material_resistance_assumed`, `wetting_screen_decision`, `water_content_percent_used`, `source_water_default_used`, `free_water_screen_state`, `free_water_assumed_from_missing_data`, `screened_calculation_branch`

적용 범위: Explicit 2016 material/HC-water-velocity/dew-point policies, source defaults and qualified wet model; no autonomous metallurgy or actual wetting/EOS judgment. Source resistance/exemption yields CO2-specific0 with flags, not measured immunity or zero total DF. Indeterminate moisture errors rather than asserts dry. Unused downstream inputs on screened branches rejected; no hidden model fallback. Low-Cr stainless figure evaluation is not silently reclassified low-alloy: current quantitative model supports only named carbon/low-alloy steel. Same pressure/temperature/known velocity drives screens and wet kernel. Explicit free-water evidence or source wet assumption supersedes approximate dew-point generation.

## `api581.api.damage.co2_screened_thinning`

Screened CO2 rate through non-AST unclad thinning DF

계산 ID: `damage/co2-screened-thinning`

출처: Part2 Annex2.B §13,Figure2.B.13.1; Part2 §4.5.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.co2_screening.CO2ScreenedAssessment'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `glycol_factor`, `inhibitor_factor`, `applied_reduction_factor`, `corrosion_rate_m_year`, `base_corrosion_rate_m_year`, `model_ph`, `temperature_ph_factor`, `fugacity_pa`, `requested_shear_stress_pa`, `applied_shear_stress_pa`, `shear_cap_applied`, `sharp_temperature_interval_interpolated`, `co2_partial_pressure_pa_abs`, `material_screen_decision`, `source_material_resistance_assumed`, `wetting_screen_decision`, `water_content_percent_used`, `source_water_default_used`, `free_water_screen_state`, `free_water_assumed_from_missing_data`, `screened_calculation_branch`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`

적용 범위: Unclad non-AST component and owner-qualified strength/inspection baseline. Retains material/HC exemption, moisture uncertainty/default flags and source-specific rate through DF. Zero CO2 rate is not total DF0 or omission of other mechanisms. No independent confirmation of legacy material/wetting rules, oil-water phase distribution, chromium chemistry, actual moisture or field conditions.

## `api581.api.damage.oxidation_screen`

High-temperature oxidation temperature and oxygen screening

계산 ID: `damage/oxidation-screen`

출처: Part2 Annex2.B Table1.1,§9.1; PDF pp322,389

| 입력 | 필수 | 타입 |
|---|---|---|
| `maximum_metal_temperature_k` | 예 | `<class 'float'>` |
| `oxygen_present` | 예 | `<class 'bool'>` |
| `threshold_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `screen_temperature_threshold_k`, `temperature_screen_met`, `evaluate_high_temperature_oxidation`

적용 범위: Annex screen requires metal temperature>=482C(900F) AND oxygen present. Printed SI482C differs from exact900F conversion: basis explicit. Screening out does not assert rate0 or no other damage; description says onset approximately482C forCS and higher for alloys. Maximum METAL temperature controls, including furnace tube metal, not bulk gas/fluid temperature.

## `api581.api.damage.oxidation_table_row`

Full oxidation table row with explicit unavailable cells

계산 ID: `damage/oxidation-table-row`

출처: Part2 Tables2.B.9.2/9.2M/9.3/9.3M; PDF pp390-391

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'cr_1_25', 'cr_2_25', 'cr_5', 'cr_7', 'cr_9', 'cr_12', 'ss_304', 'ss_309', 'ss_310_hk', 'alloy_800h_hp']` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `temperature_nodes_k`, `corrosion_rates_m_year`, `native_rates`, `native_rate_unit`, `source_table_ids`

적용 범위: 11 named material rows,24 temperature columns,SI andUS. Combined source material labels310SS/HK and800H/HP preserved as grouped categories, not arbitrary alloy equivalence. Rounded SI temperatures/rates differ from exact US conversions. Printed dashes returnedNone, never0 or material failure-temperature certification. No continuous interpolation in chromium composition.

## `api581.api.damage.oxidation_rate`

Material and maximum-metal-temperature oxidation rate

계산 ID: `damage/oxidation-rate`

출처: Part2 §9.3,Tables2.B.9.2-9.3M; PDF pp389-391

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'cr_1_25', 'cr_2_25', 'cr_5', 'cr_7', 'cr_9', 'cr_12', 'ss_304', 'ss_309', 'ss_310_hk', 'alloy_800h_hp']` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `maximum_metal_temperature_k` | 예 | `<class 'float'>` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'linear_between_nodes', 'upper_temperature_node']` |
| `below_table_policy` | 예 | `typing.Literal['reject_below_table', 'qualified_first_node_value']` |
| `first_node_qualification_basis` | 기본값/선택 | `str | None` |

출력: `corrosion_rate_m_year`, `lower_temperature_node_k`, `upper_temperature_node_k`, `interpolation_weight`, `rate_calculation_basis`, `first_node_value_used`

적용 범위: No source interpolation rule: exact,linear or upper-temperature-node numerical policy must be selected. No high-temperature extrapolation or interpolation touching unavailable dash. Below first printed node496C/925F is rejected or explicitly qualified first-node estimate; source screening begins482C/900F, does not supply this gap's rate. First-node policy not a zero/ambient-corrosion assumption. Adjacent tables are joined only where both bordering cells exist. Primitive lookup does not itself qualify oxygen or actual metal-temperature identification.

## `api581.api.damage.oxidation_assessment`

Screened qualified maximum-metal-temperature oxidation estimate

계산 ID: `damage/oxidation-assessment`

출처: Part2 Annex2.B Table1.1,§9,Tables2.B.9.2-9.3M; PDF pp322,389-391

| 입력 | 필수 | 타입 |
|---|---|---|
| `oxidation` | 예 | `<class 'api581.oxidation.OxidationRate'>` |
| `oxygen_present` | 예 | `<class 'bool'>` |
| `screening_threshold_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `applicability_basis` | 예 | `<class 'str'>` |

출력: `screen_temperature_threshold_k`, `temperature_screen_met`, `evaluate_high_temperature_oxidation`, `corrosion_rate_m_year`, `lower_temperature_node_k`, `upper_temperature_node_k`, `interpolation_weight`, `rate_calculation_basis`, `first_node_value_used`, `thinning_type`

적용 범위: Owner qualifies named material, oxygen and actual maximum exposed metal temperature. Screen-out rejects quantitative estimate instead of reporting invented rate0. One assessed surface/exposure; no implicit second-side loss or duplicate atmospheric/CUI corrosion DF. Source calls oxidation general thinning. Does not evaluate creep, thermal fatigue, oxide spallation cycling, carburization/sulfidation, metallurgy, service suitability or total damage.

## `api581.api.damage.oxidation_thinning_assessment`

Oxidation rate through qualified non-AST unclad thinning DF

계산 ID: `damage/oxidation-thinning-assessment`

출처: Part2 Annex2.B §9; Part2 §4.5.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.oxidation.OxidationAssessment'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `screen_temperature_threshold_k`, `temperature_screen_met`, `evaluate_high_temperature_oxidation`, `corrosion_rate_m_year`, `lower_temperature_node_k`, `upper_temperature_node_k`, `interpolation_weight`, `rate_calculation_basis`, `first_node_value_used`, `thinning_type`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`

적용 범위: Same qualified oxidation rate drives single constant-baseline unclad non-AST thinning. Strength/allowable stress/flow stress/minimum thickness must be qualified at governing design temperature; no room-temperature strength assumption. Monitoring row must be other, table factor1; qualified experience replacement remains available underTable4.8 note1. Liquid-corrosion rows cannot supply borrowed credits. Inspection eligibility needs owner qualification for oxidation. No AST/cladding, automatic creep/high-temperature code evaluation, FFS or all-mechanism DF.

## `api581.api.damage.acid_sour_water_route`

Acid sour water free-water pH and chloride route

계산 ID: `damage/acid-sour-water-route`

출처: Part2 Annex2.B Table1.1,§10.1-10.3,Figure10.1; PDF pp322,392-393,396

| 입력 | 필수 | 타입 |
|---|---|---|
| `free_water_present` | 예 | `<class 'bool'>` |
| `ph` | 기본값/선택 | `float | None` |
| `chlorides_present` | 기본값/선택 | `bool | None` |
| `chloride_concentration_ppm` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `chloride_policy` | 기본값/선택 | `typing.Literal['figure_any_presence_routes_hcl', 'qualified_below_50ppm'] | None` |
| `chloride_qualification_basis` | 기본값/선택 | `str | None` |
| `neutral_ph_policy` | 기본값/선택 | `typing.Literal['detailed_body_inclusive', 'unclassified_at_neutral'] | None` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_route`

적용 범위: No free water gives source-specific dry branch. Detailed pH<4.5 routesHCl,>7 routes alkaline sour water, otherwise acid sour. Overview sayspH<7: exact7 can follow explicit detailed-body inclusion or remain unclassified, not guessed. Figure any chloride presence routesHCl, while Annex screen permits<50ppm and body assumes insignificant chloride: qualified-below50ppm policy requires concentration and basis. Route result does not execute another mechanism or assert zero total damage; use lowest separated-water-phase pH, not unqualified bulk average.

## `api581.api.damage.acid_sour_water_base_rate`

Acid sour water pH and temperature base corrosion rate

계산 ID: `damage/acid-sour-water-base-rate`

출처: Part2 Tables2.B.10.2/10.2M; PDF pp394-395

| 입력 | 필수 | 타입 |
|---|---|---|
| `ph` | 예 | `<class 'float'>` |
| `maximum_water_temperature_k` | 예 | `<class 'float'>` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'bilinear', 'maximum_bracketing_value']` |
| `ph_edge_policy` | 예 | `typing.Literal['reject_unprinted_ph', 'qualified_nearest_edge_row']` |
| `ph_edge_qualification_basis` | 기본값/선택 | `str | None` |

출력: `base_corrosion_rate_m_year`, `ph_for_lookup`, `ph_edge_row_used`

적용 범위: 20SI and20US cells; pH4.75..6.75,SI38/52/79/93C orUS100/125/175/200F. Explicit basis preserves rounded temperatures/rates. Detailed scope4.5..7 extends beyond table: missing pH edge bands reject or use qualified nearest-edge row, flagged, never silent clamping. Temperature never extrapolated. Between-node handling exact/bilinear/max-bracketing explicit numerical policy, not source instruction. Lowest separated aqueous-phase pH and maximum water temperature, including local heating, must be qualified.

## `api581.api.damage.acid_sour_water_oxygen_factor`

Acid sour water oxygen adjustment factor

계산 ID: `damage/acid-sour-water-oxygen-factor`

출처: Part2 Table2.B.10.3; PDF p395

| 입력 | 필수 | 타입 |
|---|---|---|
| `oxygen_content_ppb` | 예 | `<class 'float'>` |

출력: `oxygen_factor`, `high_oxygen_localized_review`

적용 범위: Table oxygen<=50ppb factor1,>50ppb factor2. Detailed scope says normal<50ppb; equality follows explicit table. High oxygen can introduce localized/pitting attack: factor2 is source general-rate correction, not a separate pitting prediction or wetH2S cracking assessment.

## `api581.api.damage.acid_sour_water_velocity_factor`

Acid sour water piecewise velocity factor

계산 ID: `damage/acid-sour-water-velocity-factor`

출처: Part2 eqs(2.B.2)-(2.B.7); PDF p393

| 입력 | 필수 | 타입 |
|---|---|---|
| `velocity_m_s` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `velocity_factor`, `high_velocity_localized_review`

적용 범위: SI: below1.83m/s factor1,1.83..6.10 inclusive .82*v-.5,above6.10 factor5. US: below6ft/s1,6..20 inclusive .25*v-.5,above20 factor5. Publicm/s, explicit basis; equality and discontinuity at high threshold retained, not smoothed. High velocity requires localized-attack review; factor5 is not erosion/CFD or cracking model.

## `api581.api.damage.acid_sour_water_rate_equation`

Acid sour water base rate times oxygen and velocity

계산 ID: `damage/acid-sour-water-rate-equation`

출처: Part2 Annex2.B §10.3 eq(2.B.1); PDF p393

| 입력 | 필수 | 타입 |
|---|---|---|
| `base_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `oxygen_factor` | 예 | `<class 'float'>` |
| `velocity_factor` | 예 | `<class 'float'>` |

출력: `corrosion_rate_m_year`

적용 범위: CR=CRpH*FO*FV. Context-specific duplicate equation number is Annex2.B §10, not other source equations2.B.1. Applicability, water/pH/chloride and material qualification are separate.

## `api581.api.damage.acid_sour_water_other_material_rate`

Acid sour water suitable-other-material source estimate

계산 ID: `damage/acid-sour-water-other-material-rate`

출처: Part2 §10.1.2(c),Figure10.1; PDF pp392,396

| 입력 | 필수 | 타입 |
|---|---|---|
| `service_suitability_qualified` | 예 | `<class 'bool'>` |
| `other_degradation_assessed` | 예 | `<class 'bool'>` |
| `rate_policy` | 예 | `typing.Literal['body_upper_bound_screening', 'figure_nominal_2mpy']` |
| `body_unit_basis` | 기본값/선택 | `typing.Literal['printed_si', 'printed_us_converted'] | None` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `selected_rate_is_screening_bound`

적용 범위: Body assumes suitable other material corrosion will not exceed.05mm/y(2mpy); figure assignsCR=2mpy. Explicit choice returns body upper-bound screening or figure nominal point. Rounded bodySI.00005m/y differs from exact2mpy=.0000508. Requires actual suitability and other-degradation assessment; no alloy-name immunity to wetH2S cracking/ClSCC/dealloying. No oxygen/velocity correction automatically applied to separate other-material branch.

## `api581.api.damage.acid_sour_water_assessment`

Acid sour water routed material and corrected corrosion estimate

계산 ID: `damage/acid-sour-water-assessment`

출처: Part2 Annex2.B §10,Tables10.1-10.3,Figure10.1; PDF pp392-396

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.acid_sour_water.AcidSourRoute'>` |
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel', 'other_material']` |
| `total_alloy_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `primary_h2s_and_insignificant_other_corrosives_qualified` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `carbon_model` | 기본값/선택 | `api581.acid_sour_water.AcidSourCarbon | None` |
| `other_material_model` | 기본값/선택 | `api581.acid_sour_water.AcidSourOtherMaterial | None` |

출력: `corrosion_route`, `corrosion_rate_m_year`, `base_corrosion_rate_m_year`, `ph_for_lookup`, `ph_edge_row_used`, `oxygen_factor`, `velocity_factor`, `localized_attack_review_required`, `selected_rate_is_screening_bound`, `default_thinning_type`

적용 범위: Free-water/pH/chloride routing first. HCl/alkaline/neutral-unclassified routes error rather than fake zero or silently calculate acid-sour rate. Dry branch0 is acid-sour-specific only, with null uncomputed factors. Wet acid branch requires primaryH2S and insignificant ammonia/CO2/cyanides/other-corrosive qualification; no actual mixed-chemistry model. Body quantitativeCS scope versus tablelow-alloy<=6% preserved through explicit low-alloy fraction. Other material requires qualified separate fallback policy. High oxygen/velocity flags localized-attack review; no automatic pit multiplier or wetH2S crackingDF. General thinning source classification is not proof localized attack absent.

## `api581.api.damage.acid_sour_water_thinning_assessment`

Acid sour water rate through qualified non-AST thinning DF

계산 ID: `damage/acid-sour-water-thinning-assessment`

출처: Part2 Annex2.B §10; Part2 §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.acid_sour_water.AcidSourAssessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `localized_attack_review_basis` | 기본값/선택 | `str | None` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_route`, `corrosion_rate_m_year`, `base_corrosion_rate_m_year`, `ph_for_lookup`, `ph_edge_row_used`, `oxygen_factor`, `velocity_factor`, `localized_attack_review_required`, `selected_rate_is_screening_bound`, `default_thinning_type`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Unclad non-AST component; same selected rate and thickness drive loss/strength. General source classification versus owner general/local inspection coverage explicit. High oxygen/velocity requires additional localized-attack review basis; no unsupported pit multiplier. Uses sour-water monitoring row with same measured velocity, never unrelatedHCl credit; monitoring source threshold20ft/s differs from acid-sour velocity correction6ft/s threshold. Other-material nominal estimate does not exclude other DFs. No all-mechanism DF, wetH2S cracking, AST, cladding, code/FFS or actual chemistry qualification.

## `api581.api.properties.h2s_partial_pressure`

H2S partial pressure from absolute pressure and mole fraction

계산 ID: `properties/h2s-partial-pressure`

출처: Part2 Table2.B.7.1; PDF p379

| 입력 | 필수 | 타입 |
|---|---|---|
| `total_pressure_pa_abs` | 예 | `<class 'float'>` |
| `h2s_mole_fraction` | 예 | `<class 'float'>` |

출력: `h2s_partial_pressure_pa_abs`

적용 범위: Public mole fraction0..1, not printed mole-percent number multiplied without/100. AbsolutePa, not gauge. Product only; no gas-liquid equilibrium, dissolvedH2S or fugacity calculation.

## `api581.api.damage.alkaline_sour_water_nh4hs_estimate`

Source NH4HS analytical approximation with disputed branch gate

계산 ID: `damage/alkaline-sour-water-nh4hs-estimate`

출처: Part2 Table2.B.7.1; PDF p379

| 입력 | 필수 | 타입 |
|---|---|---|
| `h2s_mass_fraction` | 예 | `<class 'float'>` |
| `nh3_mass_fraction` | 예 | `<class 'float'>` |
| `analytical_basis` | 예 | `<class 'str'>` |
| `excess_h2s_policy` | 예 | `typing.Literal['reject_disputed_branch', 'qualified_printed_literal']` |
| `excess_h2s_qualification_basis` | 기본값/선택 | `str | None` |
| `equality_policy` | 예 | `typing.Literal['reject_unassigned_equality', 'qualified_lower_branch', 'qualified_upper_branch']` |
| `equality_qualification_basis` | 기본값/선택 | `str | None` |

출력: `estimated_nh4hs_mass_fraction`, `concentration_estimate_branch`, `estimated_fraction_exceeds_one`

적용 범위: Source prefers ionic process model. Printed ifH2S<2*NH3:NH4HS=1.5*H2S; ifH2S>2*NH3:NH4HS=3*H2S, notNH3. Excess branch rejected unless qualified literal use; no undocumented ammonia-limited repair. Equality unassigned, requires explicit qualified lower/upper selection or error. Public mass fractions, same condensed-water analytical basis, H2S+NH3<=1. Literal estimate can exceed1; raw value/flag retained, not clipped or claimed mass-balanced chemistry. Integrated table rejects out-of-range concentration.

## `api581.api.damage.alkaline_sour_water_velocity_selection`

Select vapor or liquid velocity for NH4HS table

계산 ID: `damage/alkaline-sour-water-velocity-selection`

출처: Part2 Table2.B.7.1; PDF p379

| 입력 | 필수 | 타입 |
|---|---|---|
| `phase_regime` | 예 | `typing.Literal['two_phase', 'liquid_full']` |
| `vapor_velocity_m_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `liquid_velocity_m_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `selected_velocity_m_s`, `selected_velocity_phase`

적용 범위: Two-phase system uses vapor-phase velocity, liquid-full system uses liquid velocity. Bulk/mixture velocity is not substituted. Two-phase liquid velocity may be supplied as contextual input but is not selected. Vapor input in liquid-full case rejected. No phase fractions, holdup, slip velocity or wall-shear calculation inferred.

## `api581.api.damage.alkaline_sour_water_base_rate`

NH4HS and phase-velocity baseline carbon-steel corrosion rate

계산 ID: `damage/alkaline-sour-water-base-rate`

출처: Part2 Tables2.B.7.2/7.2M; PDF pp379-380

| 입력 | 필수 | 타입 |
|---|---|---|
| `nh4hs_mass_fraction` | 예 | `<class 'float'>` |
| `selected_velocity_m_s` | 예 | `<class 'float'>` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'bilinear', 'maximum_bracketing_value']` |

출력: `baseline_corrosion_rate_m_year`

적용 범위: 20cells per unit basis:NH4HS2/5/10/15wt%,SI3.05/4.57/6.10/7.62/9.14m/s,US10/15/20/25/30ft/s. Public fractions/m/s/m-year; rounded SI rates/grid versus exactUS conversions explicit. Exact/bilinear/max-bracketing numerical policy required; no concentration or velocity extrapolation/edge defaults. Baseline before pressure correction, not independently modeled temperature/hydrocarbon effects.

## `api581.api.damage.alkaline_sour_water_pressure_adjustment`

NH4HS sour-water H2S partial-pressure correction

계산 ID: `damage/alkaline-sour-water-pressure-adjustment`

출처: Part2 Tables2.B.7.2/7.2M notes1-2; PDF pp379-380

| 입력 | 필수 | 타입 |
|---|---|---|
| `baseline_corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `h2s_partial_pressure_pa_abs` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `corrosion_rate_m_year`, `unclamped_pressure_factor`, `pressure_correction_factor`, `negative_pressure_factor_clamped`, `pressure_correction_branch`

적용 범위: US factor=1+(p_psia-50)/25 below50, /40 above;SI=1+(p_kPa-345)/173 below345,/276 above. At reference both expressions return1. Finalrate=max(baseline*factor,0). Public absolutePa; rounded pressure thresholds/slopes differ, basis explicit. Negative factor/low-pressure zero clamp flagged, not actual immunity to sour-water/wetH2S damage. No extrapolation range is specified by source pressure notes; owner qualifies actual pressure applicability.

## `api581.api.damage.alkaline_sour_water_assessment`

Qualified alkaline NH4HS carbon-steel corrosion assessment

계산 ID: `damage/alkaline-sour-water-assessment`

출처: Part2 Annex2.B §7,Tables7.1-7.2M; Table1.2; PDF pp323,378-381

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel']` |
| `free_water_present` | 예 | `<class 'bool'>` |
| `ph` | 기본값/선택 | `float | None` |
| `h2s_ammonia_service_qualified` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `wet_model` | 기본값/선택 | `api581.alkaline_sour_water.AlkalineWet | None` |

출력: `corrosion_rate_m_year`, `baseline_corrosion_rate_m_year`, `nh4hs_mass_fraction_used`, `concentration_source`, `selected_velocity_m_s`, `selected_velocity_phase`, `unclamped_pressure_factor`, `pressure_correction_factor`, `negative_pressure_factor_clamped`, `pressure_correction_branch`, `source_thinning_type`, `calculation_branch`

적용 범위: Carbon-steel free-water/H2S/NH3 service above neutralpH only; wet concentration preferably supplied from qualified ionic model/analysis. Disputed source approximations retain gates. Phase-specific velocity selected once; pressure correction applied to same baseline. Source table general/local classification uses<=6.1m/s or<=20ft/s as explicit threshold basis. Temperature/HC-water ratio effects are secondary but no quantitative correction supplied; not invented. Dry0 is NH4HS-specific, not zero all-mechanismDF. Low-pressure source clamp0 not validated absence of damage. No wetH2S cracking, material-alloy extension or process equilibrium inferred.

## `api581.api.damage.alkaline_sour_water_thinning_assessment`

NH4HS corrosion through qualified non-AST unclad thinning DF

계산 ID: `damage/alkaline-sour-water-thinning-assessment`

출처: Part2 Annex2.B §7,Table1.2; Part2 §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.alkaline_sour_water.AlkalineAssessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `distribution_qualification_basis` | 예 | `<class 'str'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `baseline_corrosion_rate_m_year`, `nh4hs_mass_fraction_used`, `concentration_source`, `selected_velocity_m_s`, `selected_velocity_phase`, `unclamped_pressure_factor`, `pressure_correction_factor`, `negative_pressure_factor_clamped`, `pressure_correction_branch`, `source_thinning_type`, `calculation_branch`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Same selected phase velocity and rate drive sour-water monitoring and wall loss. Explicit source general/local classification retained separately from owner-qualified inspection/distribution; no automatic coverage validation. Source pressure-clamp0 does not force DF0: strength/uncertainty/floor remain. Non-AST unclad only; no ammonia/wetH2S cracking, material extension, two-phase EOS, all-mechanismDF or code/FFS.

## `api581.api.damage.hcl_ph_from_chloride`

Dilute HCl pH estimate from printed chloride concentration bands

계산 ID: `damage/hcl-ph-from-chloride`

출처: Part2 Table2.B.2.2; PDF p325

| 입력 | 필수 | 타입 |
|---|---|---|
| `chloride_mass_fraction` | 예 | `<class 'float'>` |
| `no_alkaline_agents_qualified` | 예 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `estimated_ph`, `chloride_band_lower_wppm`, `chloride_band_upper_wppm`, `chloride_band_upper_inclusive`

적용 범위: Mass fraction converted to wppm. Assumes no ammonia, neutralizing amines or caustic: explicit qualification required. Literal bands contain continuous gaps, e.g.2..3 and35..36ppm; gaps and>12000ppm rejected without rounding or band extension. This is table approximation for separated acid phase, not acid equilibrium, HCl wt% or measured pH.

## `api581.api.damage.hcl_chloride_interval_from_ph`

Printed chloride interval corresponding to a tabulated HCl pH

계산 ID: `damage/hcl-chloride-interval-from-ph`

출처: Part2 Table2.B.2.2,Figure2.B.2.1; PDF pp325,330

| 입력 | 필수 | 타입 |
|---|---|---|
| `ph` | 예 | `<class 'float'>` |
| `no_alkaline_agents_qualified` | 예 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `chloride_band_lower_wppm`, `chloride_band_upper_wppm`, `chloride_band_upper_inclusive`

적용 범위: Inverse table is an interval, not unique concentration. Only printed pH values0.5,1,...5 allowed; no log-law, midpoint or invented interpolation. Requires no alkaline agents. High-alloy use must explicitly select/qualify concentration inside interval and rate-table range; lower-pH/high-chloride assumptions cannot be inferred from unrelated aqueous chemistry.

## `api581.api.damage.hcl_ph_rate`

HCl carbon-steel and 304/316/321/347 pH-temperature rate tables

계산 ID: `damage/hcl-ph-rate`

출처: Part2 Tables2.B.2.3/2.3M,2.4/2.4M; PDF pp326-327

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'ss_304', 'ss_316', 'ss_321', 'ss_347']` |
| `ph` | 예 | `<class 'float'>` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'bilinear', 'maximum_bracketing_value']` |

출력: `corrosion_rate_m_year`, `source_999_corner_used`, `localized_pitting_already_included`, `source_table_id`

적용 범위: 14pH x4temperature x2materials x2unit tables,224physical cells. Named four stainless grades share source table; other300 grades/low-alloy not inferred. Stainless values already10x general for localized pitting: do not multiply10 again or divide to claim qualified general rate. Printed999mpy/25.37mm/y retained literally and flagged for any contributing cell; not infinity, missing or immunity. Explicit interpolation policy only; no extrapolation. Unit tables preserve rounding. SCC/crevice corrosion not calculated.

## `api581.api.damage.hcl_alloy_rate`

HCl high-alloy chloride-temperature and oxidant rate tables

계산 ID: `damage/hcl-alloy-rate`

출처: Part2 Tables2.B.2.5/2.5M,2.6/2.6M; PDF pp328-329

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['alloy_825', 'alloy_20', 'alloy_625', 'alloy_c276', 'alloy_b2', 'alloy_400']` |
| `chloride_mass_fraction` | 예 | `<class 'float'>` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `oxidants_present` | 기본값/선택 | `bool | None` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'bilinear', 'maximum_bracketing_value']` |

출력: `corrosion_rate_m_year`, `source_999_corner_used`, `localized_pitting_already_included`, `source_table_id`

적용 범위: Chloride-ion mass fraction .005/.0075/.01 (0.5/0.75/1wt%), not HCl acid fraction.825/20 share table;625/C276 distinct. B2/400 require explicit oxidant state; supplied oxidant field on other table rejected as unused. All168physical SI/US high-alloy cells preserved, including400 no-oxidant1wt%,100F=19mpy. No universal4x oxidant multiplier. Source999 literal/rounding retained and flagged. No extrapolation or oxidant interpolation; heat-treatment, salt deposits and actual process qualification external.

## `api581.api.damage.hcl_assessment`

Qualified dilute HCl chemistry material and corrosion-rate assessment

계산 ID: `damage/hcl-assessment`

출처: Part2 Annex2.B §2,Tables2.1-2.6M,Figure2.1; Table1.2; PDF pp323-330

| 입력 | 필수 | 타입 |
|---|---|---|
| `free_water_present` | 예 | `<class 'bool'>` |
| `dilute_hcl_service_qualified` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `wet_model` | 기본값/선택 | `api581.hydrochloric_acid.HClPHWet | api581.hydrochloric_acid.HClAlloyWet | None` |

출력: `corrosion_rate_m_year`, `source_999_corner_used`, `localized_pitting_already_included`, `source_table_id`, `ph_used`, `chloride_mass_fraction_used`, `chemistry_method`, `source_thinning_type`, `calculation_branch`

적용 범위: Only qualified dilute free-water HCl service and listed materials. Supplied separated acid-phase pH preferred; chloride-derived pH gated on no alkaline agents. Inverse pH route returns band and requires explicitly selected qualified chloride inside it; no unique inverse inferred. Maximum local temperature and material/heat-treatment applicability qualified externally. Source class local, stainless pitting already included. Dry0 HCl-specific, diagnosticsNone; not total damage. No shock-condensation/salt deposition dynamics, SCC or concentrated acid extrapolation.

## `api581.api.damage.hcl_thinning_assessment`

Dilute HCl rate through qualified non-AST unclad thinning DF

계산 ID: `damage/hcl-thinning-assessment`

출처: Part2 Annex2.B §2,Table1.2; §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.hydrochloric_acid.HClAssessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `distribution_qualification_basis` | 예 | `<class 'str'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `source_999_corner_used`, `localized_pitting_already_included`, `source_table_id`, `ph_used`, `chloride_mass_fraction_used`, `chemistry_method`, `source_thinning_type`, `calculation_branch`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Same HCl rate drives wall loss with HCl monitoring row and explicit inspection/distribution qualification. Source local class retained apart from owner assessment distribution. Stainless pitting factor already in table, never added again. Dry0 not DF0; general thinning uncertainty/floor still applies. Non-AST unclad only; no crack/crevice/SCC/FFS or automatic all-mechanism risk.

## `api581.api.damage.sour_water_assessment`

Route qualified sour water to acid or alkaline quantitative model

계산 ID: `damage/sour-water-assessment`

출처: Part2 Annex2.B §§2,7,10,Figures2.1,10.1; PDF pp324-330,378-381,392-396

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.acid_sour_water.AcidSourRoute'>` |
| `acid_model` | 기본값/선택 | `api581.acid_sour_water.AcidSourAssessment | None` |
| `alkaline_model` | 기본값/선택 | `api581.alkaline_sour_water.AlkalineAssessment | None` |
| `hcl_model` | 기본값/선택 | `api581.hydrochloric_acid.HClAssessment | None` |
| `hcl_shared_phase_qualification_basis` | 기본값/선택 | `str | None` |

출력: `corrosion_route`, `corrosion_rate_m_year`, `selected_model_base_rate_m_year`, `selected_rate_is_screening_bound`, `localized_attack_review_required`

적용 범위: Reuses explicit free-water/pH/chloride policies. Executes only matching supplied acid/alkaline/HCl model, never sums them. Acid child screening must match entire shared request; alkaline child must have same free-water/pH. HCl child requires shared separated-phase qualification and matching available pH/chloride; screeningroute alone does not establish dilute HCl applicability. Neutral-unclassified errors, never zero. Returns common selected-rate fields; independent APIs retain detailed diagnostics including HCl999-cell flags. Dry0 source-specific; no all-mechanismDF or immunity statement.

## `api581.api.damage.hf_concentration_selection`

HF table concentration with explicit above81wt% extension policy

계산 ID: `damage/hf-concentration-selection`

출처: Part2 Annex2.B §6.1,Tables6.2-6.3M; PDF pp374,376-377

| 입력 | 필수 | 타입 |
|---|---|---|
| `hf_mass_fraction` | 예 | `<class 'float'>` |
| `concentrated_extension_policy` | 예 | `typing.Literal['reject_above_81wt_percent', 'qualified_81wt_percent_node']` |
| `concentrated_extension_qualification_basis` | 기본값/선택 | `str | None` |

출력: `hf_mass_fraction_for_lookup`, `concentrated_81_node_extension_used`

적용 범위: HF-in-water mass fraction, not water mass fraction. Source body says>=80wt% equivalent to anhydrous but tables distinguish80/81wt% and stop81. Values>81 default reject; qualified81-node extension requires owner basis and flag, never silent extrapolation or81>= label. Below1wt% rejected.80..81 handled by explicit table interpolation policy. No-free-water is not HF immunity: anhydrous acid remains in scope.

## `api581.api.damage.hf_carbon_velocity_band`

HF carbon-steel low/high velocity band

계산 ID: `damage/hf-carbon-velocity-band`

출처: Part2 Tables2.B.6.2/6.2M; PDF p376

| 입력 | 필수 | 타입 |
|---|---|---|
| `velocity_m_s` | 예 | `<class 'float'>` |
| `velocity_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `velocity_band`, `velocity_threshold_m_s`

적용 범위: PrintedSI threshold3.05m/s versus10ft/s=3.048m/s explicitly selected. Low strictly below; equality high. No continuous velocity interpolation or generic erosion/film-stripping rate. This rate-table threshold differs from other mechanisms and is not a universal process limit.

## `api581.api.damage.hf_carbon_rate`

HF carbon-steel concentration temperature velocity residual rate table

계산 ID: `damage/hf-carbon-rate`

출처: Part2 Tables2.B.6.2/6.2M; PDF p376

| 입력 | 필수 | 타입 |
|---|---|---|
| `velocity_m_s` | 예 | `<class 'float'>` |
| `velocity_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `hf_mass_fraction` | 예 | `<class 'float'>` |
| `concentrated_extension_policy` | 예 | `typing.Literal['reject_above_81wt_percent', 'qualified_81wt_percent_node']` |
| `concentrated_extension_qualification_basis` | 기본값/선택 | `str | None` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `residual_category` | 기본값/선택 | `typing.Literal['low', 'high'] | None` |
| `residual_qualification_basis` | 기본값/선택 | `str | None` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'bilinear', 'maximum_bracketing_value']` |

출력: `hf_mass_fraction_for_lookup`, `concentrated_81_node_extension_used`, `velocity_band`, `velocity_threshold_m_s`, `corrosion_rate_m_year`, `source_999_corner_used`, `residual_column_used`, `source_table_id`

적용 범위: 252SI/US cells at7temperatures x2velocity x9columns. Concentrations1,2,5,6,63,64,80,81wt%;81haslow/high residual. Any lookup using81corner needs qualified residual classification; source supplies no numeric Cu/Ni/Cr cutoff, none inferred. Residual fields outside81-corner region rejected as unused. All999mpy/25.37mm/y literal with flag. Source SI/US rounding explicit, no temperature extrapolation. Initial high corrosion before protective fluoride scale, galvanic coupling and disturbed scale not quantified by table. Figure6.1 swapped table numbers resolved by actual table titles, not treated as official erratum.

## `api581.api.damage.hf_alloy400_rate`

HF Alloy400 concentration temperature aeration rate table

계산 ID: `damage/hf-alloy400-rate`

출처: Part2 Tables2.B.6.3/6.3M,Table6.1; PDF pp375,377

| 입력 | 필수 | 타입 |
|---|---|---|
| `hf_mass_fraction` | 예 | `<class 'float'>` |
| `concentrated_extension_policy` | 예 | `typing.Literal['reject_above_81wt_percent', 'qualified_81wt_percent_node']` |
| `concentrated_extension_qualification_basis` | 기본값/선택 | `str | None` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `aerated_or_oxidants_present` | 예 | `<class 'bool'>` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'bilinear', 'maximum_bracketing_value']` |

출력: `hf_mass_fraction_for_lookup`, `concentrated_81_node_extension_used`, `corrosion_rate_m_year`, `source_999_corner_used`, `source_table_id`

적용 범위: 128SI/US cells at4temperatures x2aeration x8HF concentrations. Explicit aeration/oxidants bool, no dissolved-oxygen cutoff supplied or inferred. No blanket aeration multiplier or velocity correction. Actual material and applicable solution conditions external. No extrapolation except flagged qualified above81 extension. Figure6.1 swapped table references resolved using actual Alloy400 table title.

## `api581.api.damage.hf_assessment`

Qualified HF exposure material and source-classification corrosion assessment

계산 ID: `damage/hf-assessment`

출처: Part2 Annex2.B §6,Tables6.1-6.3M,Figure6.1,Table1.2; PDF pp323,374-378

| 입력 | 필수 | 타입 |
|---|---|---|
| `hf_exposure_present` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `rate_model` | 기본값/선택 | `api581.hydrofluoric_acid.HFCarbonService | api581.hydrofluoric_acid.HFAlloy400Service | api581.hydrofluoric_acid.HFPublishedRate | None` |
| `galvanic_coupling_present` | 기본값/선택 | `bool | None` |
| `thinning_classification_policy` | 기본값/선택 | `typing.Literal['overview_local', 'detailed_general_without_galvanic'] | None` |
| `classification_qualification_basis` | 기본값/선택 | `str | None` |

출력: `corrosion_rate_m_year`, `source_table_id`, `rate_source`, `source_999_corner_used`, `hf_mass_fraction_for_lookup`, `concentrated_81_node_extension_used`, `velocity_band`, `velocity_threshold_m_s`, `residual_column_used`, `source_thinning_type`, `calculation_branch`

적용 범위: HF exposure, not free-water presence controls branch: no free water cannot imply zero because anhydrous HF corrodes. No-HF0 source-specific only. CS table requires stable established fluoride scale/material-residual qualification; table paths reject galvanic coupling whose acceleration is unquantified. Other materials/conditions may use explicit published rate with provenance and applicability qualification per source figure, not an API581 table prediction. Source overviewLocal versus detailedGeneral absent galvanic conflict requires explicit policy/basis; general policy disallowed with galvanic coupling. No HSC/HIC/blistering, SCC, film growth or transient dilution model.

## `api581.api.damage.hf_thinning_assessment`

Qualified HF rate through non-AST unclad thinning DF

계산 ID: `damage/hf-thinning-assessment`

출처: Part2 Annex2.B §6,Table1.2; §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.hydrofluoric_acid.HFAssessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `distribution_qualification_basis` | 예 | `<class 'str'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `source_table_id`, `rate_source`, `source_999_corner_used`, `hf_mass_fraction_for_lookup`, `concentrated_81_node_extension_used`, `velocity_band`, `velocity_threshold_m_s`, `residual_column_used`, `source_thinning_type`, `calculation_branch`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Same selected HF rate drives wall loss and qualified HF monitoring row. Source class conflict policy and owner-qualified actual distribution retained separately. No-HF0 not DF0, uncertainty/floor remain. Non-AST unclad only; no added residual/aeration multipliers, no automatic cracking/totalDF/FFS acceptance. Published rate retains supplied provenance in input snapshot, not relabeled API581 table data.

## `api581.api.damage.amine_acid_gas_loading`

Combined H2S and CO2 loading per mole of active amine

계산 ID: `damage/amine-acid-gas-loading`

출처: Part2 Annex2.B §8.1,Table8.1; PDF pp382-383

| 입력 | 필수 | 타입 |
|---|---|---|
| `h2s_amount_mol` | 예 | `<class 'float'>` |
| `co2_amount_mol` | 예 | `<class 'float'>` |
| `active_amine_amount_mol` | 예 | `<class 'float'>` |
| `common_sample_basis` | 예 | `<class 'str'>` |

출력: `acid_gas_loading_mol_mol`

적용 범위: Both acid gases on same representative sample basis divided by active, not total or degraded amine. No HSAS-to-active-amine subtraction, equilibrium or rich/lean process-state inference. Zero acid-gas loading valid; denominator strictly positive. Owner process analysis/qualification required.

## `api581.api.damage.amine_loading_selection`

Amine lean/rich source loading rows and explicit gap selection

계산 ID: `damage/amine-loading-selection`

출처: Part2 Tables2.B.8.2-8.3M; PDF pp384-387

| 입력 | 필수 | 타입 |
|---|---|---|
| `acid_gas_loading_mol_mol` | 예 | `<class 'float'>` |
| `loading_gap_policy` | 예 | `typing.Literal['reject_unassigned_0p10_to_0p15', 'qualified_lean_row', 'qualified_first_rich_row']` |
| `loading_gap_qualification_basis` | 기본값/선택 | `str | None` |

출력: `lower_loading_row_index`, `upper_loading_row_index`, `loading_interpolation_weight`, `table_loading_regime`, `loading_gap_mapping_used`

적용 범위: Carbon tables have lean<0.1 and rich nodes0.15..0.7.0.1<=loading<0.15 is unassigned, default rejected; owner-qualified nearest lean/first-rich mapping flagged, never interpolation across incompatible velocity thresholds. Rich nodes may be numerically bracketed; rate lookup separately selects interpolation. Loading>0.7 rejected. Returned row indices0lean,1..7rich are table coordinates, not process rich/lean designation.

## `api581.api.damage.amine_contaminant_row`

Select amine HSAS or MDEA organic-acid contamination row

계산 ID: `damage/amine-contaminant-row`

출처: Part2 Table2.B.8.1,Tables8.2-8.3M; PDF pp383-387

| 입력 | 필수 | 타입 |
|---|---|---|
| `amine_type` | 예 | `typing.Literal['mea', 'dea', 'mdea']` |
| `contaminant_mass_fraction` | 예 | `<class 'float'>` |
| `mdea_scale_policy` | 예 | `typing.Literal['not_mdea', 'qualified_basic_data_organic_ppm_bands', 'qualified_printed_wt_percent_nodes']` |
| `mdea_scale_qualification_basis` | 기본값/선택 | `str | None` |
| `four_percent_boundary_policy` | 기본값/선택 | `typing.Literal['basic_data_middle_band', 'printed_four_percent_high_row'] | None` |
| `four_percent_qualification_basis` | 기본값/선택 | `str | None` |

출력: `contaminant_row`, `printed_hsas_row_mass_fraction`

적용 범위: MEA/DEA basic-data<=2wt%,2..4,>4 maplow/middle/high table rows2/3/4. Exact4 conflicts with printed high-row4: explicit middle/high policy/basis required. MDEA basic-data organic-acid<500,500..4000,>4000wppm differs from tableHSAS0.5/2.25/4wt%; explicit qualified basic-data band mapping or literal exactwt%node policy required. Never treat500ppm as0.5wt%. No hidden HSAS composition or active-amine correction. No interpolation between contaminant categories.

## `api581.api.damage.amine_strength_factor`

Carbon-steel amine concentration multiplier

계산 ID: `damage/amine-strength-factor`

출처: Part2 Table2.B.8.4; PDF p388

| 입력 | 필수 | 타입 |
|---|---|---|
| `amine_type` | 예 | `typing.Literal['mea', 'dea', 'mdea']` |
| `amine_mass_fraction` | 예 | `<class 'float'>` |

출력: `amine_strength_factor`

적용 범위: MEA<=20wt%:1,21..25:1.5,>25:2;DEA<=30:1,31..40:1.2,>40:1.5;MDEA<=50:1 only. Continuous20..21 and30..31 gaps rejected, no rounding/interpolation. MDEA>50 not supplied. Positive active process solution concentration required. Carbon-table factor, not extra stainless multiplier or concentration derating credit.

## `api581.api.damage.amine_carbon_base_rate`

Carbon-steel amine loading temperature contamination velocity tables

계산 ID: `damage/amine-carbon-base-rate`

출처: Part2 Tables2.B.8.2-8.3M; PDF pp384-387

| 입력 | 필수 | 타입 |
|---|---|---|
| `table_family` | 예 | `typing.Literal['mea_dea', 'mdea']` |
| `loading` | 예 | `<class 'api581.amine_corrosion.AmineLoadingSelection'>` |
| `contaminant_row` | 예 | `typing.Literal['low', 'middle', 'high']` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `velocity_m_s` | 예 | `<class 'float'>` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'linear_loading_temperature', 'maximum_bracketing_value']` |

출력: `lower_loading_row_index`, `upper_loading_row_index`, `loading_interpolation_weight`, `table_loading_regime`, `loading_gap_mapping_used`, `base_corrosion_rate_m_year`, `velocity_band`, `velocity_threshold_m_s`, `source_table_id`

적용 범위: 1152physical source cells:2families x2units x8loading rows x3contamination rows x6temperatures x2velocity. Base rates before strength factor. Lean velocity low<=6.1m/s or20ft/s,rich<=1.5m/s or5ft/s; equality low, no velocity interpolation. Rich loading/temperature interpolation explicit, not across lean gap. Contaminant row is source table coordinate; process classification independent API. Unit differences preserved, temperature outside table rejected. No local evaporation/metal-temperature prediction, film transient or automatic amineSCC.

## `api581.api.damage.amine_stainless_rate`

Type300 stainless amine loading corrosion table

계산 ID: `damage/amine-stainless-rate`

출처: Part2 Table2.B.8.5,§8.3,Figure8.1; PDF pp382,388-389

| 입력 | 필수 | 타입 |
|---|---|---|
| `acid_gas_loading_mol_mol` | 예 | `<class 'float'>` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'linear_loading_temperature', 'maximum_bracketing_value']` |
| `low_loading_policy` | 예 | `typing.Literal['reject_below_0p1', 'qualified_first_row']` |
| `low_loading_qualification_basis` | 기본값/선택 | `str | None` |
| `normal_service_conditions_qualified` | 예 | `<class 'bool'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `low_loading_first_row_used`, `source_table_id`

적용 범위: 8loading x2unit cells,temperature<=149C or300F explicitly selected. Below0.1loading not printed: reject or qualified first-row screening value flagged, not guaranteed bound. No loading>0.7 or high-temperature extrapolation. Normal service qualification required: source says extreme concentration/temperature/degradation can cause up to200x, not fixed multiplier or guaranteed upper bound. No carbon strength factor on stainless and no inferred HSAS/velocity modifier. Source figure Type300 scope; not all chromium/nickel/copper alloys.

## `api581.api.damage.amine_corrosion_assessment`

Qualified amine chemistry and material corrosion assessment

계산 ID: `damage/amine-corrosion-assessment`

출처: Part2 Annex2.B §8,Tables8.1-8.5,Figure8.1,Table1.2; PDF pp323,382-389

| 입력 | 필수 | 타입 |
|---|---|---|
| `amine_service_present` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `rate_model` | 기본값/선택 | `api581.amine_corrosion.AmineCarbonService | api581.amine_corrosion.AmineStainlessService | None` |

출력: `corrosion_rate_m_year`, `base_corrosion_rate_m_year`, `amine_strength_factor`, `contaminant_row`, `printed_hsas_row_mass_fraction`, `table_loading_regime`, `loading_gap_mapping_used`, `velocity_band`, `velocity_threshold_m_s`, `low_loading_first_row_used`, `source_table_id`, `source_thinning_type`, `calculation_branch`

적용 범위: MEA/DEA/MDEA chemical gas-treating amines only; no physical solvent/DIPA extension. Same amine in strength/contaminants required. CS table and qualified figurelow-alloy branch use base*strength once;Type300 stainless uses normal-service table without carbon multiplier. CS classification explicitly qualified to rate-table velocity columns: overviewstrict boundaries/body6.01vs6.1/1.52vs1.5 differ; equality follows rate-table low, not unqualified universal limit. Stainless source type not inferred without velocity:None. No-service0 specific, not totalDF0. Maximum local metal temperature/amine concentration, active loading and contaminant applicability external; no amineSCC.

## `api581.api.damage.amine_thinning_assessment`

Amine rate through qualified non-AST unclad thinning DF

계산 ID: `damage/amine-thinning-assessment`

출처: Part2 Annex2.B §8,Table1.2; §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.amine_corrosion.AmineAssessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `distribution_qualification_basis` | 예 | `<class 'str'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `base_corrosion_rate_m_year`, `amine_strength_factor`, `contaminant_row`, `printed_hsas_row_mass_fraction`, `table_loading_regime`, `loading_gap_mapping_used`, `velocity_band`, `velocity_threshold_m_s`, `low_loading_first_row_used`, `source_table_id`, `source_thinning_type`, `calculation_branch`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Same final base*strength rate drives wall loss; amine monitoring row must match table velocity band when carbon model supplies one. Monitoring regime basis and actual inspection distribution qualified explicitly. Stainless has no rate-table velocity classification; owner monitoring regime remains separately qualified. No-amine0 does not bypass generalDF floor/uncertainty. Non-AST unclad only; no amineSCC, process equilibrium, code/FFS or all-mechanism risk inference.

## `api581.api.damage.sulfuric_table_axes`

Sulfuric material table concentration temperature and velocity axes

계산 ID: `damage/sulfuric-table-axes`

출처: Part2 Tables2.B.5.2-5.7M; PDF pp365-372

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'ss_304', 'ss_316', 'alloy_20', 'alloy_c276', 'alloy_b2']` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `carbon_si_velocity_policy` | 기본값/선택 | `typing.Literal['reject_ambiguous_header', 'qualified_printed_m_s', 'qualified_us_ft_s_header']` |
| `carbon_si_velocity_qualification_basis` | 기본값/선택 | `str | None` |

출력: `acid_mass_fraction_nodes`, `temperature_nodes_k`, `velocity_nodes_m_s`, `source_table_id`, `carbon_si_velocity_interpretation`

적용 범위: Six named materials only. CS SI header saysm/s but repeats US numericft/s headings0,1,2,3,4.5,6.5,8.5,11.5,12: default reject, qualified literalSI or US-header interpretation explicit. SI/US temperature axes retained literally, includingAlloy20 SI70C versus US163.5F. No automatic temperature/unit repair, extrapolation or cross-material substitution. Axes alone do not establish table applicability.

## `api581.api.damage.sulfuric_table_rate`

Sulfuric concentration temperature velocity material corrosion table

계산 ID: `damage/sulfuric-table-rate`

출처: Part2 Annex2.B §5,Tables5.2-5.7M,Figure5.1; PDF pp363-373

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'ss_304', 'ss_316', 'alloy_20', 'alloy_c276', 'alloy_b2']` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `carbon_si_velocity_policy` | 기본값/선택 | `typing.Literal['reject_ambiguous_header', 'qualified_printed_m_s', 'qualified_us_ft_s_header']` |
| `carbon_si_velocity_qualification_basis` | 기본값/선택 | `str | None` |
| `acid_mass_fraction` | 예 | `<class 'float'>` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `velocity_m_s` | 예 | `<class 'float'>` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'trilinear', 'maximum_bracketing_value']` |
| `oxidants_present` | 기본값/선택 | `bool | None` |
| `disputed_304_cell_policy` | 기본값/선택 | `typing.Literal['reject_disputed_cell', 'qualified_printed_literal']` |
| `disputed_304_qualification_basis` | 기본값/선택 | `str | None` |

출력: `corrosion_rate_m_year`, `source_table_id`, `carbon_si_velocity_interpretation`, `source_999_corner_used`, `disputed_304_cell_used`, `source_localized_enhancement_already_included`

적용 범위: 1776physical SI/US cells. Rates are source maximum estimates, not certified universal bounds. CS turbulent localized enhancement already included, no added3x multiplier or automatic20..50% actual-rate discount. Literal999mpy/25.37mm/y flagged, not infinity/missing.30475wt%,middleT,highestv prints99mpy/2.51mm/y amid999: default reject exact cell/any bracketing corner; qualified printed literal requires basis and flag, no invented999 correction. B2 requires explicit no-oxidant state; oxidizingB2 rejected to source specialist route. Other tables reject unused oxidant input, no oxidant improvement credit. Trilinear/max-corner are explicit numerical policies, not original interpolation instruction; nonmonotonic concentration cannot be replaced by global monotonic rule.

## `api581.api.damage.sulfuric_thinning_classification`

Sulfuric source general/local thinning velocity classification

계산 ID: `damage/sulfuric-thinning-classification`

출처: Part2 Table2.B.1.2,Annex2.B §5.1; PDF pp323,363

| 입력 | 필수 | 타입 |
|---|---|---|
| `material_group` | 예 | `typing.Literal['carbon_steel', 'stainless_steel', 'higher_alloy']` |
| `velocity_m_s` | 예 | `<class 'float'>` |
| `threshold_basis` | 예 | `typing.Literal['overview_printed_si', 'overview_us_converted', 'detailed_carbon_body_si']` |
| `equality_policy` | 예 | `typing.Literal['reject_ambiguous_boundary', 'qualified_general', 'qualified_local']` |
| `equality_qualification_basis` | 기본값/선택 | `str | None` |

출력: `source_thinning_type`, `thinning_velocity_threshold_m_s`, `thinning_velocity_boundary_resolved`

적용 범위: Overview SI thresholdsCS.61/SS1.22/higher1.83m/s versus2/4/6ft/s; detailed CS bodyapprox.91m/s. Explicit basis preserves differences. Overview CS/SS equality overlaps; general equality resolution requires qualified policy, never guessed. Distinct from online-monitoring Table4.8 thresholds3/5/7ft/s and table velocity nodes; do not force all classifications equal. Actual distribution and inspection coverage external.

## `api581.api.damage.sulfuric_corrosion_assessment`

Qualified sulfuric material rate and thinning classification assessment

계산 ID: `damage/sulfuric-corrosion-assessment`

출처: Part2 Annex2.B §5,Tables5.1-5.7M,Figure5.1,Table1.2; PDF pp323,363-373

| 입력 | 필수 | 타입 |
|---|---|---|
| `sulfuric_service_present` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `rate_model` | 기본값/선택 | `api581.sulfuric_acid.SulfuricTableService | api581.sulfuric_acid.SulfuricSpecialistRate | None` |
| `classification` | 기본값/선택 | `api581.sulfuric_acid.SulfuricThinningClassification | None` |

출력: `corrosion_rate_m_year`, `source_table_id`, `carbon_si_velocity_interpretation`, `source_999_corner_used`, `disputed_304_cell_used`, `source_localized_enhancement_already_included`, `source_thinning_type`, `thinning_velocity_threshold_m_s`, `thinning_velocity_boundary_resolved`, `rate_source`, `calculation_branch`

적용 범위: Same velocity/material group must drive supplied classification and selected rate. Table conditions including concentration,maximum local/nozzle conditions,passivity and impurity applicability owner-qualified. No-service0 is sulfuric-specific, not based on free-water absence;100wt% sulfuric table remains valid. OxidizingB2 uses explicit qualified specialist rate/provenance, not fictitious oxidant multiplier or source table prediction. Specialist route may cover other qualified material/conditions. Source maximum estimates retained without extra3x or automatic actual-rate discount. General/local thresholds and online-monitoring thresholds intentionally distinct; no all-mechanismDF/FFS or corrosion equilibrium inferred.

## `api581.api.damage.sulfuric_thinning_assessment`

Qualified sulfuric corrosion through non-AST unclad thinning DF

계산 ID: `damage/sulfuric-thinning-assessment`

출처: Part2 Annex2.B §5,Table1.2; §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.sulfuric_acid.SulfuricAssessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `distribution_qualification_basis` | 예 | `<class 'str'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `source_table_id`, `carbon_si_velocity_interpretation`, `source_999_corner_used`, `disputed_304_cell_used`, `source_localized_enhancement_already_included`, `source_thinning_type`, `thinning_velocity_threshold_m_s`, `thinning_velocity_boundary_resolved`, `rate_source`, `calculation_branch`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Same final rate drives wall loss; same physical velocity/material group must be used for sulfuric monitoring and source classification, but their threshold values differ. Source general/local and actual owner-qualified inspection distribution retained separately. No extra localized3x multiplication or rate discount. No-service0 not DF0; uncertainty/floor retained. Non-AST unclad only, no source condition certification,all-mechanismDF or code/FFS acceptance.

## `api581.api.damage.h2sh2_table_axes`

High-temperature H2S/H2 material and table axes

계산 ID: `damage/h2sh2-table-axes`

출처: Part2 Tables2.B.4.2-4.7M; PDF pp354-362

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'cr1_0p2mo', 'cr1_0p5mo', 'cr1p25_0p5mo', 'cr2p25_1mo', 'cr3_1mo', 'cr5_0p5mo', 'cr7', 'cr9_1mo', 'cr12', 'ss_304', 'ss_304l', 'ss_316', 'ss_316l', 'ss_321', 'ss_347']` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `h2s_mole_fraction_nodes`, `temperature_nodes_k`, `table_group`, `hydrocarbon_curve_required`, `source_table_id`

적용 범위: Six source material groups,16named materials. Public vapor H2S mole fraction, not molepercent/massfraction/partial pressure.0.002mole%=0.00002fraction=20ppmv. SI218..524C and US425..975F nodes retain source rounding. Stream type required onlyCS/lowCr groups, excluded for12Cr and named stainless. Axes not process qualification; no unlisted alloy interpolation.

## `api581.api.damage.h2sh2_table_rate`

High-temperature H2S/H2 concentration-temperature corrosion rate

계산 ID: `damage/h2sh2-table-rate`

출처: Part2 Annex2.B §4.1-4.3,Tables4.2-4.7M,Figure4.1; PDF pp353-363

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'cr1_0p2mo', 'cr1_0p5mo', 'cr1p25_0p5mo', 'cr2p25_1mo', 'cr3_1mo', 'cr5_0p5mo', 'cr7', 'cr9_1mo', 'cr12', 'ss_304', 'ss_304l', 'ss_316', 'ss_316l', 'ss_321', 'ss_347']` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `h2s_mole_fraction` | 예 | `<class 'float'>` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `stream_case` | 기본값/선택 | `typing.Literal['naphtha', 'gas_oil', 'hydrocarbon_free'] | None` |
| `hydrocarbon_free_curve` | 기본값/선택 | `typing.Literal['naphtha', 'gas_oil'] | None` |
| `hydrocarbon_free_qualification_basis` | 기본값/선택 | `str | None` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'bilinear', 'maximum_bracketing_value']` |

출력: `corrosion_rate_m_year`, `source_table_id`, `selected_hydrocarbon_curve`, `hydrocarbon_free_curve_selection_used`, `source_thinning_type`

적용 범위: 1920physical SI/US cells. Naphtha/gas-oil curves categorical, no fluid blending. Typical boiling430F distinction requires process classification, not automatic maximum-temperature comparison. Hydrocarbon-free source says same correlations adequate despite possible50% greater rates: explicit qualified choice of source curve, no added1.5multiplier.12Cr/stainless tables have no hydrocarbon branch:unused stream fields rejected. Positive H2S below20ppmv or above1mole% and temperatures outside printed table rejected, never zero/cap. Approx204C onset is not first table218C: gap not extrapolated. Bilinear uses linear concentration, not inferred log correlation; explicit numerical policy. No HTHA,wetH2S cracking,catalyst chemistry or automatic material certification.

## `api581.api.damage.h2sh2_corrosion_assessment`

Qualified high-temperature H2S/H2 corrosion assessment

계산 ID: `damage/h2sh2-corrosion-assessment`

출처: Part2 Annex2.B §4,Table1.2; PDF pp323,353-363

| 입력 | 필수 | 타입 |
|---|---|---|
| `h2s_h2_service_present` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `service_model` | 기본값/선택 | `api581.h2sh2_corrosion.H2SH2Service | None` |

출력: `corrosion_rate_m_year`, `source_table_id`, `selected_hydrocarbon_curve`, `hydrocarbon_free_curve_selection_used`, `source_thinning_type`, `calculation_branch`

적용 범위: Requires actual high-temperature hydrogen-sulfidation environment and material/stream qualification; sulfur and hydrogen alone do not establish catalytic conversion. Same source rate applies with no extra50% vapor correction. No-service0 is mechanism-specific with absent diagnostics, not all-mechanismDF0 or temperature-based immunity. Actual maximum process temperature and vapor composition external; low-temperature gap,traceH2S or unlisted material not filled by unrelated wet-sour/oxidation model. General source thinning does not validate inspection distribution.

## `api581.api.damage.h2sh2_thinning_assessment`

High-temperature H2S/H2 rate through qualified unclad thinning DF

계산 ID: `damage/h2sh2-thinning-assessment`

출처: Part2 Annex2.B §4,Table1.2; §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.h2sh2_corrosion.H2SH2Assessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `distribution_qualification_basis` | 예 | `<class 'str'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `source_table_id`, `selected_hydrocarbon_curve`, `hydrocarbon_free_curve_selection_used`, `source_thinning_type`, `calculation_branch`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Same computed rate drives wall loss and dedicated high-temperatureH2S/H2 monitoring row, not amine/wet-sour row. Actual distribution/inspection coverage separately qualified. No-service0 retains generalDF floor/uncertainty. Non-AST unclad only; no wetH2S/HTHA or other mechanism aggregation,code/FFS acceptance or added vapor multiplier.

## `api581.api.damage.sulfidic_material_selection`

Sulfidic/naphthenic material and316 molybdenum source group

계산 ID: `damage/sulfidic-material-selection`

출처: Part2 Table2.B.3.1,Tables3.2-3.10M; PDF pp333-351

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'cr1_0p2mo', 'cr1_0p5mo', 'cr1p25_0p5mo', 'cr2p25_1mo', 'cr3_1mo', 'cr5_0p5mo', 'cr7_1mo', 'cr9_1mo', 'cr12', 'austenitic_without_mo', 'ss_304', 'ss_304l', 'ss_321', 'ss_347', 'ss_316', 'ss_316l', 'ss_316h', 'ss_317']` |
| `molybdenum_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |

출력: `table_group`, `unknown_molybdenum_low_assumed`

적용 범위: Named alloys only, no continuousCr interpolation.316/316L/316H withMo>=2.5wt% use high-Mo group, below use low; unknownMo assumes<2.5wt% per source and flags assumption.317source high-Mo group;Mo input only used for316family and rejected elsewhere. Austenitic-withoutMo includes304/304L/321/347. Actual composition/material suitability remains owner-qualified.

## `api581.api.damage.sulfidic_table_axes`

Sulfidic/naphthenic sulfur TAN and temperature-bin axes

계산 ID: `damage/sulfidic-table-axes`

출처: Part2 Tables2.B.3.2-3.10M; PDF pp334-351

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'cr1_0p2mo', 'cr1_0p5mo', 'cr1p25_0p5mo', 'cr2p25_1mo', 'cr3_1mo', 'cr5_0p5mo', 'cr7_1mo', 'cr9_1mo', 'cr12', 'austenitic_without_mo', 'ss_304', 'ss_304l', 'ss_321', 'ss_347', 'ss_316', 'ss_316l', 'ss_316h', 'ss_317']` |
| `molybdenum_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |

출력: `table_group`, `unknown_molybdenum_low_assumed`, `sulfur_mass_fraction_nodes`, `tan_nodes_mg_koh_g`, `lower_temperature_bin_upper_k`, `interior_temperature_nodes_k`, `upper_temperature_bin_lower_exclusive_k`, `source_table_id`

적용 범위: Material-specific sulfur andTAN grids, not common axes. CS sulfur0.6wt% versus5Cr0.75wt% and most others0.8wt% preserved. Lower temperature column<=232C/450F is interval, upper>399C/750F interval; neither invented finite node. Interior six temperature nodes exposed separately. Interpolation near first bin needs explicit threshold-anchor qualification. SI/US rates/temperatures retain rounding.

## `api581.api.damage.sulfidic_table_rate`

Sulfidic/naphthenic sulfur TAN temperature base rate

계산 ID: `damage/sulfidic-table-rate`

출처: Part2 Annex2.B §3.3,Tables3.2-3.10M; PDF pp332-351

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'cr1_0p2mo', 'cr1_0p5mo', 'cr1p25_0p5mo', 'cr2p25_1mo', 'cr3_1mo', 'cr5_0p5mo', 'cr7_1mo', 'cr9_1mo', 'cr12', 'austenitic_without_mo', 'ss_304', 'ss_304l', 'ss_321', 'ss_347', 'ss_316', 'ss_316l', 'ss_316h', 'ss_317']` |
| `molybdenum_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `sulfur_mass_fraction` | 예 | `<class 'float'>` |
| `tan_mg_koh_g` | 예 | `<class 'float'>` |
| `maximum_temperature_k` | 예 | `<class 'float'>` |
| `lookup_policy` | 예 | `typing.Literal['exact_nodes_only', 'trilinear', 'maximum_bracketing_value']` |
| `temperature_edge_policy` | 예 | `typing.Literal['reject_edge_bins_and_first_gap', 'qualified_source_bins_and_threshold_anchor']` |
| `temperature_edge_qualification_basis` | 기본값/선택 | `str | None` |
| `low_tan_policy` | 예 | `typing.Literal['reject_below_first_tan', 'qualified_first_tan_row']` |
| `low_tan_qualification_basis` | 기본값/선택 | `str | None` |

출력: `base_corrosion_rate_m_year`, `source_table_id`, `table_group`, `unknown_molybdenum_low_assumed`, `source_temperature_bin_used`, `first_temperature_threshold_anchor_used`, `below_first_tan_row_used`

적용 범위: 3840physical SI/US cells before velocity correction. Low/high temperature bins require qualified applicability and flag;232..260C/450..500F first-gap interpolation additionally uses qualified lower-bin threshold anchor, not invented source point. No interpolation from750F into open-ended>750bin; exact750 is interior last node, immediatelyabove uses upper bin. FirstTAN rows are literal nodes, not<=:below-first requires owner-qualified first-row extension/flag;above-last and sulfur outside table rejected. Concentration/TAN nonmonotonicities retained, including12Cr rate declines: no smoothing. Explicit trilinear/max-corner policy, not validated physical correlation. Naphthenic-influenced values only order-of-magnitude per source. No automatic gas-only acidity suppression or unknown-sulfur default.

## `api581.api.damage.sulfidic_velocity_factor`

Sulfidic/naphthenic high-velocity factor with100ft/s boundary policy

계산 ID: `damage/sulfidic-velocity-factor`

출처: Part2 Annex2.B §3.3,Figure3.1; PDF pp332,352

| 입력 | 필수 | 타입 |
|---|---|---|
| `velocity_m_s` | 예 | `<class 'float'>` |
| `boundary_interpretation` | 예 | `typing.Literal['body_strictly_above_100ft_s', 'figure_at_or_above_100ft_s']` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `velocity_factor`, `velocity_boundary_conflict_encountered`

적용 범위: Factor5 above30.48m/s(100ft/s),1below. Body saysstrictly> while figure< test sends equality to5: explicit interpretation/basis determines exact boundary and conflict flag. No continuous velocity interpolation,hydraulic phase-velocity calculation or repeated5x in composition. Maximum nozzle/stream velocity applicability external.

## `api581.api.damage.sulfidic_thinning_classification`

Sulfidic/naphthenic TAN general/local source classification

계산 ID: `damage/sulfidic-thinning-classification`

출처: Part2 Table2.B.1.2; PDF p323

| 입력 | 필수 | 타입 |
|---|---|---|
| `tan_mg_koh_g` | 예 | `<class 'float'>` |

출력: `source_thinning_type`

적용 범위: TAN<=0.5mgKOH/g general,>0.5local. Actual liquid-phaseTAN required,not whole-crude average or acid fraction. Classification does not establish mechanism presence or actual pit/inspection distribution; no velocity boundary from another table substituted.

## `api581.api.damage.sulfidic_corrosion_assessment`

Qualified high-temperature sulfidic/naphthenic corrosion assessment

계산 ID: `damage/sulfidic-corrosion-assessment`

출처: Part2 Annex2.B §3,Tables3.1-3.10M,Figure3.1,Table1.2; PDF pp323,331-352

| 입력 | 필수 | 타입 |
|---|---|---|
| `sulfidic_service_present` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |
| `service_model` | 기본값/선택 | `api581.sulfidic_corrosion.SulfidicService | None` |

출력: `base_corrosion_rate_m_year`, `source_table_id`, `table_group`, `unknown_molybdenum_low_assumed`, `source_temperature_bin_used`, `first_temperature_threshold_anchor_used`, `below_first_tan_row_used`, `velocity_factor`, `velocity_boundary_conflict_encountered`, `source_thinning_type`, `corrosion_rate_m_year`, `calculation_branch`

적용 범위: Same table rate*velocity factor once. Source hydrogen-free sulfidation and actual liquid-phaseTAN/material/process qualification required; highTAN>0.5 gas-only rejected,naphthenic attack needs liquid. Explicit working high-temperature scope>=204C or400F;below rejected,not immunity/zero. Above399C table upper bin retained with qualification,not automatic naphthenic decomposition discount. Source lowTAN first-row/Mo assumptions and edge flags retained. No-service0 specific,not totalDF0. No catalyticH2S/H2 substitution,phase equilibrium,McConomy curve digitization beyond printed tables or model certification.

## `api581.api.damage.sulfidic_thinning_assessment`

Sulfidic/naphthenic rate through qualified unclad thinning DF

계산 ID: `damage/sulfidic-thinning-assessment`

출처: Part2 Annex2.B §3,Table1.2; §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.sulfidic_corrosion.SulfidicAssessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `distribution_qualification_basis` | 예 | `<class 'str'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `base_corrosion_rate_m_year`, `source_table_id`, `table_group`, `unknown_molybdenum_low_assumed`, `source_temperature_bin_used`, `first_temperature_threshold_anchor_used`, `below_first_tan_row_used`, `velocity_factor`, `velocity_boundary_conflict_encountered`, `source_thinning_type`, `corrosion_rate_m_year`, `calculation_branch`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Same base*velocity-corrected rate drives wall loss once,dedicated high-temperature sulfidic/naphthenic monitoring row required. Actual distribution/inspection coverage owner-qualified independently of sourceTAN classification. Non-AST unclad only,no additional5x or unrelated H2S/H2 model. No-service0 retains generalDF floor/uncertainty;no all-mechanismDF,code/FFS acceptance or source-condition certification.

## `api581.api.properties.pure_fluid_flash`

Qualified pure-fluid isentropic or isenthalpic flash

계산 ID: `properties/pure-fluid-flash`

출처: Part3 §5.1.3,STEP1.3; PDF pp539-541

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `storage_pressure_pa_abs` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `storage_vapor_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `final_pressure_pa_abs` | 예 | `<class 'float'>` |
| `method` | 예 | `typing.Literal['isentropic', 'isenthalpic']` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `flashed_temperature_k`, `vapor_mass_fraction`, `flashed_phase`, `bulk_density_kg_m3`, `conserved_property`, `conserved_value_si`, `engine_version`, `storage_phase`, `storage_vapor_mass_fraction`, `vapor_mass_fraction_change`, `storage_temperature_k`, `storage_state_basis`

적용 범위: Optional CoolProp8.0.0 required. Pure-fluid HEOS expansion only; no mixtures,arbitrary backend strings,supercritical final pressure or equilibrium chemistry. Isentropic source preference and acceptable isenthalpic alternative explicitly selected. Returns final equilibrium vapor mass fraction,not incremental vaporized fraction or API581 rainout. Single-phase Q=-1 is not a physical quality: phase identifies0/1 vapor fraction. Storage uses exactly one of PT (unambiguous single phase) or pressure/equilibrium mass quality (triple-point to subcritical coexistence). Saturated PT ambiguities and invalid EOS states fail explicitly. Signed quality change includes condensation and is not rainout. Pure-propane reference verified; no independent fluid-wide/LH2 validation or hydraulic two-phase flow calculation. Final pressure supplied explicitly; atmospheric applicability owner-qualified.

## `api581.api.release.pure_liquid_flash_partition`

Pure-liquid flash with explicit pool/jet composition basis

계산 ID: `release/pure-liquid-flash-partition`

출처: Part3 §§5.7.1-5.7.3 eqs(3.98)-(3.102); PDF p543

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `storage_pressure_pa_abs` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `storage_vapor_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `final_pressure_pa_abs` | 예 | `<class 'float'>` |
| `method` | 예 | `typing.Literal['isentropic', 'isenthalpic']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `adjusted_mass_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'post_flash_mass_balance']` |
| `atmospheric_partition_basis` | 예 | `<class 'str'>` |

출력: `flashed_temperature_k`, `vapor_mass_fraction`, `flashed_phase`, `bulk_density_kg_m3`, `conserved_property`, `conserved_value_si`, `engine_version`, `storage_phase`, `storage_vapor_mass_fraction`, `vapor_mass_fraction_change`, `storage_temperature_k`, `storage_state_basis`, `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`, `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`, `pool_liquid_mass_kg`, `jet_total_mass_kg`, `jet_liquid_rate_kg_s`, `jet_vapor_rate_kg_s`, `jet_liquid_mass_kg`, `jet_vapor_mass_kg`, `rainout_mass_fraction`

적용 범위: Optional CoolProp8.0.0; only unambiguous initially liquid pure fluid. Final pressure and atmospheric applicability must be qualified. Kletz rainout correlation is used, not experimentally validated for every fluid. Printed entrainment and conservation interpretation remain explicitly distinct; no silent erratum. Input mass/rate already detection/isolation/inventory adjusted. No hydraulic rate calculation, pool evaporation, mixtures or LH2 validation.

## `api581.api.properties.pure_fluid_saturation_pressure`

Pure-fluid bubble/dew and saturated properties at pressure

계산 ID: `properties/pure-fluid-saturation-pressure`

출처: Part3 §5.1.3-5.1.4 STEP1.4; §5.7.4.2; PDF pp540-541,544

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `pressure_pa_abs` | 예 | `<class 'float'>` |

출력: `saturation_pressure_pa_abs`, `bubble_temperature_k`, `dew_temperature_k`, `liquid_density_kg_m3`, `vapor_density_kg_m3`, `liquid_specific_heat_j_kg_k`, `vapor_specific_heat_j_kg_k`, `latent_heat_j_kg`, `molecular_weight_kg_kmol`, `engine_version`

적용 범위: Optional CoolProp8.0.0 HEOS pure fluids only. Triple-point to subcritical equilibrium saturation; no metastable, solid, pseudopure or mixture states. Saturated liquid cp/densities and latent heat are evaluated on the coexistence curve, not at storage or arbitrary flash temperature. Pure-fluid bubble/dew temperatures coincide. No heat of combustion, flammability, transient evaporation or fluid-wide/LH2 validation. Caller qualifies EOS and physical applicability.

## `api581.api.properties.pure_fluid_saturation_temperature`

Pure-fluid vapor pressure and saturated properties at temperature

계산 ID: `properties/pure-fluid-saturation-temperature`

출처: Part3 §5.7.4.3 eq(3.105); PDF p544

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `temperature_k` | 예 | `<class 'float'>` |

출력: `saturation_pressure_pa_abs`, `bubble_temperature_k`, `dew_temperature_k`, `liquid_density_kg_m3`, `vapor_density_kg_m3`, `liquid_specific_heat_j_kg_k`, `vapor_specific_heat_j_kg_k`, `latent_heat_j_kg`, `molecular_weight_kg_kmol`, `engine_version`

적용 범위: Optional CoolProp8.0.0 HEOS pure fluids only. Triple-point to subcritical equilibrium saturation; no metastable, solid, pseudopure or mixture states. Saturated liquid cp/densities and latent heat are evaluated on the coexistence curve, not at storage or arbitrary flash temperature. Pure-fluid bubble/dew temperatures coincide. No heat of combustion, flammability, transient evaporation or fluid-wide/LH2 validation. Caller qualifies EOS and physical applicability.

## `api581.api.dispersion.flashed_boiling_pool_centreline`

Pure-liquid flash through steady boiling-pool native centreline

계산 ID: `dispersion/flashed-boiling-pool-centreline`

출처: Part3 §§5.1.3,5.7.2-5.7.4,5.8.5-5.8.6; PDF pp539-544; external SLABx dispersion

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `storage_pressure_pa_abs` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `storage_vapor_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `final_pressure_pa_abs` | 예 | `<class 'float'>` |
| `method` | 예 | `typing.Literal['isentropic', 'isenthalpic']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `adjusted_mass_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'post_flash_mass_balance']` |
| `atmospheric_partition_basis` | 예 | `<class 'str'>` |
| `ground_temperature_k` | 예 | `<class 'float'>` |
| `surface` | 예 | `<class 'api581.evaporation.SurfaceInteraction'>` |
| `maximum_pool_area_m2` | 예 | `<class 'float'>` |
| `engine` | 예 | `typing.Literal['slabx', 'slabx-lh2']` |
| `atmosphere` | 예 | `<class 'api581.slabx_adapter.NativeAtmosphere'>` |
| `receptor_height_m` | 예 | `<class 'float'>` |
| `averaging_time_s` | 예 | `<class 'float'>` |
| `plume_distance_limit_m` | 예 | `<class 'float'>` |
| `puff_time_limit_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `puff_steps` | 기본값/선택 | `<class 'int'>` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `threshold_source` | 예 | `<class 'str'>` |
| `meander_closure` | 예 | `typing.Literal['ermak', 'sigma_theta']` |
| `lh2_plume_width_coupling` | 예 | `<class 'bool'>` |
| `native_property_basis` | 예 | `<class 'str'>` |
| `timeout_s` | 기본값/선택 | `<class 'float'>` |

출력: `flashed_temperature_k`, `vapor_mass_fraction`, `flashed_phase`, `bulk_density_kg_m3`, `conserved_property`, `conserved_value_si`, `engine_version`, `storage_phase`, `storage_vapor_mass_fraction`, `vapor_mass_fraction_change`, `storage_temperature_k`, `storage_state_basis`, `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`, `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`, `pool_liquid_mass_kg`, `jet_total_mass_kg`, `jet_liquid_rate_kg_s`, `jet_vapor_rate_kg_s`, `jet_liquid_mass_kg`, `jet_vapor_mass_kg`, `rainout_mass_fraction`, `saturation_pressure_pa_abs`, `bubble_temperature_k`, `dew_temperature_k`, `liquid_density_kg_m3`, `vapor_density_kg_m3`, `liquid_specific_heat_j_kg_k`, `vapor_specific_heat_j_kg_k`, `latent_heat_j_kg`, `molecular_weight_kg_kmol`, `equilibrium_evaporation_rate_kg_s`, `vapor_volumetric_rate_m3_s`, `time_to_steady_s`, `pool_radius_m`, `pool_area_m2`, `vapor_source_rate_kg_s`, `support_status`, `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `effective_source_half_width_m`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `steady_window_start_s`, `steady_window_duration_s`, `steady_evaporated_mass_kg`, `startup_unmodeled_pool_mass_kg`, `integration_scope`

적용 범위: Optional native packages required: tested mapping slabx1.0.8 and slabx-lh2 0.2.0. Each run uses a fresh Python subprocess so LH2 module-global corrections cannot alter host calculations. No silent alternate engine/version or fallback model. Only constant finite-duration ground-level pure-vapor evaporating pool at normal boiling temperature and101325Pa. Required rate is evaporated vapor, not liquid feed/orifice rate. Caller qualifies physical source, material properties, threshold, wind/stability and averaging. No automatic conversion from draft SourcePoint profiles, jets, droplets, mixtures, growing pools or source-ledger transitions. Native x_max limits the plume grid, not the final puff extent. plume_distance_limit_m maps exactly to that parameter; puff_time_limit_s maps to native t_max, or null preserves native automatic puff duration. Actual grid extent is reported. Threshold censoring uses the final returned native grid, not an assumed x_max cutoff. Returns time-averaged native centreline volume fractions and native endpoint interpolation, not a 2D contour area or flammable cloud mass. Last-node exceedance is boundary-censored, not a solved separation distance. No distance-to-circle area substitution. No LH2 safety factor is applied. LH2 premise violation makes threshold_distance_m null while native_threshold_distance_m and centreline remain diagnostics. A passing premise check is not experimental/site validation. Baseline slabx applicability remains not_evaluated. External package versions/source fingerprints accompany result; API581 software-test status is not native model certification. Initially liquid pure fluid only, atmospheric final pressure101325Pa, positive adjusted constant rate and released mass. Boiling pool requires Tb<Tground, area support and time-to-steady shorter than mass/rate supply duration. Unsupported/zero rainout source fails explicitly. Native constant source covers ONLY the steady window after time-to-steady, not startup, growing pool, depletion, post-release evaporation or simultaneous jet. Startup pool-feed mass is explicitly unmodeled; jet masses remain separate. Native time origin is start of steady window; no combined jet/pool footprint or risk is inferred. Pure-fluid normal-boiling saturated cp, densities and latent heat map to native constant properties only with an explicit qualification basis. No fluid-wide or LH2 EOS/native model validation. Native LH2 premise and censoring still gate usable spatial results. Threshold is caller supplied, not automatically LFL/toxic.

## `api581.api.dispersion.flashed_boiling_pool_footprint`

Pure-liquid flash through steady boiling-pool planar footprint

계산 ID: `dispersion/flashed-boiling-pool-footprint`

출처: Part3 §§5.7.2-5.7.4,5.8.5-5.8.6; external native planar concentration field

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `storage_pressure_pa_abs` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `storage_vapor_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `final_pressure_pa_abs` | 예 | `<class 'float'>` |
| `method` | 예 | `typing.Literal['isentropic', 'isenthalpic']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `adjusted_mass_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'post_flash_mass_balance']` |
| `atmospheric_partition_basis` | 예 | `<class 'str'>` |
| `ground_temperature_k` | 예 | `<class 'float'>` |
| `surface` | 예 | `<class 'api581.evaporation.SurfaceInteraction'>` |
| `maximum_pool_area_m2` | 예 | `<class 'float'>` |
| `engine` | 예 | `typing.Literal['slabx', 'slabx-lh2']` |
| `atmosphere` | 예 | `<class 'api581.slabx_adapter.NativeAtmosphere'>` |
| `receptor_height_m` | 예 | `<class 'float'>` |
| `averaging_time_s` | 예 | `<class 'float'>` |
| `plume_distance_limit_m` | 예 | `<class 'float'>` |
| `puff_time_limit_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `puff_steps` | 기본값/선택 | `<class 'int'>` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `threshold_source` | 예 | `<class 'str'>` |
| `meander_closure` | 예 | `typing.Literal['ermak', 'sigma_theta']` |
| `lh2_plume_width_coupling` | 예 | `<class 'bool'>` |
| `native_property_basis` | 예 | `<class 'str'>` |
| `timeout_s` | 기본값/선택 | `<class 'float'>` |
| `crosswind_half_span_m` | 예 | `<class 'float'>` |
| `crosswind_points_per_side` | 기본값/선택 | `<class 'int'>` |

출력: `flashed_temperature_k`, `vapor_mass_fraction`, `flashed_phase`, `bulk_density_kg_m3`, `conserved_property`, `conserved_value_si`, `engine_version`, `storage_phase`, `storage_vapor_mass_fraction`, `vapor_mass_fraction_change`, `storage_temperature_k`, `storage_state_basis`, `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`, `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`, `pool_liquid_mass_kg`, `jet_total_mass_kg`, `jet_liquid_rate_kg_s`, `jet_vapor_rate_kg_s`, `jet_liquid_mass_kg`, `jet_vapor_mass_kg`, `rainout_mass_fraction`, `saturation_pressure_pa_abs`, `bubble_temperature_k`, `dew_temperature_k`, `liquid_density_kg_m3`, `vapor_density_kg_m3`, `liquid_specific_heat_j_kg_k`, `vapor_specific_heat_j_kg_k`, `latent_heat_j_kg`, `molecular_weight_kg_kmol`, `equilibrium_evaporation_rate_kg_s`, `vapor_volumetric_rate_m3_s`, `time_to_steady_s`, `pool_radius_m`, `pool_area_m2`, `vapor_source_rate_kg_s`, `support_status`, `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `effective_source_half_width_m`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `steady_window_start_s`, `steady_window_duration_s`, `steady_evaporated_mass_kg`, `startup_unmodeled_pool_mass_kg`, `integration_scope`, `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`, `crosswind_distance_m`, `volume_fraction_by_crosswind_then_downwind`

적용 범위: Initially liquid pure fluid only, atmospheric final pressure101325Pa, positive adjusted constant rate and released mass. Boiling pool requires Tb<Tground, area support and time-to-steady shorter than mass/rate supply duration. Unsupported/zero rainout source fails explicitly. Native constant source covers ONLY the steady window after time-to-steady, not startup, growing pool, depletion, post-release evaporation or simultaneous jet. Startup pool-feed mass is explicitly unmodeled; jet masses remain separate. Native time origin is start of steady window; no combined jet/pool footprint or risk is inferred. Pure-fluid normal-boiling saturated cp, densities and latent heat map to native constant properties only with an explicit qualification basis. No fluid-wide or LH2 EOS/native model validation. Native LH2 premise and censoring still gate usable spatial results. Threshold is caller supplied, not automatically LFL/toxic. Same explicitly qualified finite ground-level vapor pool, package versions, property/atmosphere constraints and process isolation as native-pool-centreline. Uses native at_y on a symmetric crosswind grid at one receptor height/averaging time. No conversion from centreline distance to circular area. Area integrates a piecewise-linear triangular concentration interpolant on the native downwind grid and user crosswind grid. Not an exact continuous contour; supplied resolution and span require convergence checks. Plume x_max is not the final puff extent. Returned field includes negative/upwind positions, and source expansion remains native. Any threshold exceedance at a sampled grid edge or LH2 premise violation sets threshold_area_m2 to null. sampled_exceedance_area_m2 and native field remain diagnostics. No boundary truncation reported as a resolved footprint, no LH2 safety factor, mass integration or individual/societal-risk inference. Baseline native applicability remains not_evaluated.

## `api581.api.dispersion.flashed_boiling_pool_flash_fire`

Pure-liquid flash through steady boiling-pool flash-fire areas

계산 ID: `dispersion/flashed-boiling-pool-flash-fire`

출처: Part3 §§5.7.2-5.7.4,5.8.6,4.8.2.3; native LFL planar field

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `<class 'str'>` |
| `storage_pressure_pa_abs` | 예 | `<class 'float'>` |
| `storage_temperature_k` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `storage_vapor_mass_fraction` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Ge(ge=0), Le(le=1), AllowInfNan(allow_inf_nan=False)])] | None` |
| `final_pressure_pa_abs` | 예 | `<class 'float'>` |
| `method` | 예 | `typing.Literal['isentropic', 'isenthalpic']` |
| `qualification_basis` | 예 | `<class 'str'>` |
| `adjusted_mass_rate_kg_s` | 예 | `<class 'float'>` |
| `released_mass_kg` | 예 | `<class 'float'>` |
| `equation_basis` | 예 | `typing.Literal['api581_printed', 'post_flash_mass_balance']` |
| `atmospheric_partition_basis` | 예 | `<class 'str'>` |
| `ground_temperature_k` | 예 | `<class 'float'>` |
| `surface` | 예 | `<class 'api581.evaporation.SurfaceInteraction'>` |
| `maximum_pool_area_m2` | 예 | `<class 'float'>` |
| `engine` | 예 | `typing.Literal['slabx', 'slabx-lh2']` |
| `atmosphere` | 예 | `<class 'api581.slabx_adapter.NativeAtmosphere'>` |
| `receptor_height_m` | 예 | `typing.Literal[0.0]` |
| `averaging_time_s` | 예 | `<class 'float'>` |
| `plume_distance_limit_m` | 예 | `<class 'float'>` |
| `puff_time_limit_s` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `puff_steps` | 기본값/선택 | `<class 'int'>` |
| `threshold_volume_fraction` | 예 | `<class 'float'>` |
| `threshold_source` | 예 | `<class 'str'>` |
| `meander_closure` | 예 | `typing.Literal['ermak', 'sigma_theta']` |
| `lh2_plume_width_coupling` | 예 | `<class 'bool'>` |
| `native_property_basis` | 예 | `<class 'str'>` |
| `timeout_s` | 기본값/선택 | `<class 'float'>` |
| `crosswind_half_span_m` | 예 | `<class 'float'>` |
| `crosswind_points_per_side` | 기본값/선택 | `<class 'int'>` |
| `criterion_role` | 예 | `typing.Literal['qualified_lfl']` |

출력: `flashed_temperature_k`, `vapor_mass_fraction`, `flashed_phase`, `bulk_density_kg_m3`, `conserved_property`, `conserved_value_si`, `engine_version`, `storage_phase`, `storage_vapor_mass_fraction`, `vapor_mass_fraction_change`, `storage_temperature_k`, `storage_state_basis`, `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`, `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`, `pool_liquid_mass_kg`, `jet_total_mass_kg`, `jet_liquid_rate_kg_s`, `jet_vapor_rate_kg_s`, `jet_liquid_mass_kg`, `jet_vapor_mass_kg`, `rainout_mass_fraction`, `saturation_pressure_pa_abs`, `bubble_temperature_k`, `dew_temperature_k`, `liquid_density_kg_m3`, `vapor_density_kg_m3`, `liquid_specific_heat_j_kg_k`, `vapor_specific_heat_j_kg_k`, `latent_heat_j_kg`, `molecular_weight_kg_kmol`, `equilibrium_evaporation_rate_kg_s`, `vapor_volumetric_rate_m3_s`, `time_to_steady_s`, `pool_radius_m`, `pool_area_m2`, `vapor_source_rate_kg_s`, `support_status`, `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `effective_source_half_width_m`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `steady_window_start_s`, `steady_window_duration_s`, `steady_evaporated_mass_kg`, `startup_unmodeled_pool_mass_kg`, `integration_scope`, `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`, `crosswind_distance_m`, `volume_fraction_by_crosswind_then_downwind`, `personnel_area_m2`, `equipment_area_m2`, `criterion_role`

적용 범위: Initially liquid pure fluid only, atmospheric final pressure101325Pa, positive adjusted constant rate and released mass. Boiling pool requires Tb<Tground, area support and time-to-steady shorter than mass/rate supply duration. Unsupported/zero rainout source fails explicitly. Native constant source covers ONLY the steady window after time-to-steady, not startup, growing pool, depletion, post-release evaporation or simultaneous jet. Startup pool-feed mass is explicitly unmodeled; jet masses remain separate. Native time origin is start of steady window; no combined jet/pool footprint or risk is inferred. Pure-fluid normal-boiling saturated cp, densities and latent heat map to native constant properties only with an explicit qualification basis. No fluid-wide or LH2 EOS/native model validation. Native LH2 premise and censoring still gate usable spatial results. Threshold is caller supplied, not automatically LFL/toxic. Same explicitly qualified finite ground-level vapor pool, package versions, property/atmosphere constraints and process isolation as native-pool-centreline. Uses native at_y on a symmetric crosswind grid at one receptor height/averaging time. No conversion from centreline distance to circular area. Area integrates a piecewise-linear triangular concentration interpolant on the native downwind grid and user crosswind grid. Not an exact continuous contour; supplied resolution and span require convergence checks. Plume x_max is not the final puff extent. Returned field includes negative/upwind positions, and source expansion remains native. Any threshold exceedance at a sampled grid edge or LH2 premise violation sets threshold_area_m2 to null. sampled_exceedance_area_m2 and native field remain diagnostics. No boundary truncation reported as a resolved footprint, no LH2 safety factor, mass integration or individual/societal-risk inference. Baseline native applicability remains not_evaluated. Same explicitly qualified finite ground-level vapor pool, package versions, property/atmosphere constraints and process isolation as native-pool-centreline. Uses native at_y on a symmetric crosswind grid at one receptor height/averaging time. No conversion from centreline distance to circular area. Area integrates a piecewise-linear triangular concentration interpolant on the native downwind grid and user crosswind grid. Not an exact continuous contour; supplied resolution and span require convergence checks. Plume x_max is not the final puff extent. Returned field includes negative/upwind positions, and source expansion remains native. Any threshold exceedance at a sampled grid edge or LH2 premise violation sets threshold_area_m2 to null. sampled_exceedance_area_m2 and native field remain diagnostics. No boundary truncation reported as a resolved footprint, no LH2 safety factor, mass integration or individual/societal-risk inference. Baseline native applicability remains not_evaluated. Ground-level receptor height0 required by §5.8.6. Caller must declare threshold as a qualified fluid-specific LFL using criterion_role=qualified_lfl. A declaration does not validate thermodynamics, exposure averaging or field applicability. Censored/premise-violating footprints fail explicitly instead of becoming zero or valid fire consequence. Not-reached yields zero only on the supplied sampled interpolant. Personnel area=LFL footprint; equipment=.25*footprint. No ignition/event/GFF weighting. Only this selected steady pool vapor scenario. No startup/jet/post-release pool consequence or ignition/GFF weighting. LFL declaration and averaging require owner qualification; no automatic criterion lookup or final risk.

## `api581.api.risk.area_event_contribution`

Selected conditional event/weather area-risk contribution

계산 ID: `risk/area-event-contribution`

출처: Part1 §4.3.1 eqs(1.6)-(1.8); Part3 §5.8.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `annual_release_frequency_per_year` | 예 | `<class 'float'>` |
| `weather_probability_given_release` | 예 | `<class 'float'>` |
| `event_probability_given_release_weather` | 예 | `<class 'float'>` |
| `equipment_area_m2` | 예 | `<class 'float'>` |
| `personnel_area_m2` | 예 | `<class 'float'>` |
| `probability_source` | 예 | `<class 'str'>` |

출력: `annual_release_frequency_per_year`, `annual_selected_event_frequency_per_year`, `event_weighted_equipment_area_m2`, `event_weighted_personnel_area_m2`, `equipment_area_risk_contribution_m2_per_year`, `personnel_area_risk_contribution_m2_per_year`, `area_risk_contribution_m2_per_year`, `conditional_joint_probability`, `contribution_scope`

적용 범위: Partial contribution only; does not require or imply complete terminal outcomes/weather/holes. Event probability is conditional on the supplied release AND weather, so multiplying by weather probability is the chain rule, not an independence assertion. Raw event areas must not already be event/weather weighted. Release frequency must not already contain these probabilities. Each probability and annual release frequency is applied once. No financial, individual or societal risk; no zero-consequence assertion for omitted events.

## `api581.api.risk.flashed_pool_flash_fire_contribution`

Selected hole/weather EOS-to-flash-fire annual area-risk contribution

계산 ID: `risk/flashed-pool-flash-fire-contribution`

출처: Part1 §4.3.1; Part2 Table3.1,eqs(2.1),(2.9)-(2.10); Part3 §§5.7.4,5.8.6-5.8.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `fire` | 예 | `<class 'api581.flash_pool.FlashedBoilingPoolFlashFire'>` |
| `component_type` | 예 | `<class 'str'>` |
| `hole` | 예 | `typing.Literal['small', 'medium', 'large', 'rupture']` |
| `management_score` | 예 | `<class 'float'>` |
| `total_damage_factor` | 예 | `<class 'float'>` |
| `damage_factor_source` | 예 | `<class 'str'>` |
| `hole_release_basis` | 예 | `<class 'str'>` |
| `weather_probability_given_release` | 예 | `<class 'float'>` |
| `event_probability_given_release_weather` | 예 | `<class 'float'>` |
| `probability_source` | 예 | `<class 'str'>` |

출력: `flashed_temperature_k`, `vapor_mass_fraction`, `flashed_phase`, `bulk_density_kg_m3`, `conserved_property`, `conserved_value_si`, `engine_version`, `storage_phase`, `storage_vapor_mass_fraction`, `vapor_mass_fraction_change`, `storage_temperature_k`, `storage_state_basis`, `entrained_liquid_mass_fraction`, `jet_vapor_mass_fraction`, `physical_range`, `jet_fraction_nonzero`, `equation_basis`, `pool_liquid_rate_kg_s`, `jet_total_rate_kg_s`, `pool_liquid_mass_kg`, `jet_total_mass_kg`, `jet_liquid_rate_kg_s`, `jet_vapor_rate_kg_s`, `jet_liquid_mass_kg`, `jet_vapor_mass_kg`, `rainout_mass_fraction`, `saturation_pressure_pa_abs`, `bubble_temperature_k`, `dew_temperature_k`, `liquid_density_kg_m3`, `vapor_density_kg_m3`, `liquid_specific_heat_j_kg_k`, `vapor_specific_heat_j_kg_k`, `latent_heat_j_kg`, `molecular_weight_kg_kmol`, `equilibrium_evaporation_rate_kg_s`, `vapor_volumetric_rate_m3_s`, `time_to_steady_s`, `pool_radius_m`, `pool_area_m2`, `vapor_source_rate_kg_s`, `support_status`, `engine`, `engine_versions`, `engine_source_fingerprints`, `downwind_distance_m`, `centreline_volume_fraction`, `native_grid_maximum_downwind_distance_m`, `native_threshold_distance_m`, `threshold_distance_m`, `threshold_status`, `premise_status`, `maximum_vertical_to_horizontal_velocity_ratio`, `used_source_area_m2`, `effective_source_half_width_m`, `native_messages`, `averaging_time_s`, `receptor_height_m`, `spatial_output_scope`, `steady_window_start_s`, `steady_window_duration_s`, `steady_evaporated_mass_kg`, `startup_unmodeled_pool_mass_kg`, `integration_scope`, `sampled_exceedance_area_m2`, `threshold_area_m2`, `footprint_status`, `boundary_sides`, `positive_area_cell_count`, `downwind_node_count`, `crosswind_node_count`, `interpolation_basis`, `crosswind_distance_m`, `volume_fraction_by_crosswind_then_downwind`, `personnel_area_m2`, `equipment_area_m2`, `criterion_role`, `annual_release_frequency_per_year`, `annual_selected_event_frequency_per_year`, `event_weighted_equipment_area_m2`, `event_weighted_personnel_area_m2`, `equipment_area_risk_contribution_m2_per_year`, `personnel_area_risk_contribution_m2_per_year`, `area_risk_contribution_m2_per_year`, `conditional_joint_probability`, `contribution_scope`, `generic_hole_frequency_per_year`, `management_factor`, `total_damage_factor`, `selected_hole`

적용 범위: Partial contribution only; does not require or imply complete terminal outcomes/weather/holes. Event probability is conditional on the supplied release AND weather, so multiplying by weather probability is the chain rule, not an independence assertion. Raw event areas must not already be event/weather weighted. Release frequency must not already contain these probabilities. Each probability and annual release frequency is applied once. No financial, individual or societal risk; no zero-consequence assertion for omitted events. Uses only the selected non-tank GFF hole, supplied governing DF and management score. Hole-specific adjusted rate/mass and applicability must be qualified externally; this API does not derive hydraulic hole size, isolation/inventory or damage applicability. Probability is for this selected steady pool flash-fire scenario, not total ignition probability. EOS/native source scope, constant-property qualification, ground LFL, sampled-grid censoring and LH2 premise restrictions are inherited. No startup/jet/post-release pool or other outcome contribution. Omitted scenarios remain unassessed; this result is not a whole-component or four-hole risk assessment.

## `api581.api.damage.groundwater_tks`

Groundwater Total Key Species on a qualified common concentration basis

계산 ID: `damage/groundwater-tks`

출처: Part2 Annex2.B §11.3.3; PDF p405

| 입력 | 필수 | 타입 |
|---|---|---|
| `chloride_mg_l` | 예 | `<class 'float'>` |
| `sulfate_mg_l` | 예 | `<class 'float'>` |
| `dissolved_co2_mg_l` | 예 | `<class 'float'>` |
| `bicarbonate_mg_l` | 예 | `<class 'float'>` |
| `carbonate_mg_l` | 예 | `<class 'float'>` |
| `sulfide_mg_l` | 예 | `<class 'float'>` |
| `ammonia_mg_l` | 예 | `<class 'float'>` |
| `concentration_basis` | 예 | `<class 'str'>` |

출력: `total_key_species_mg_l`

적용 범위: Sum of seven explicitly supplied species concentrations, public mg/L on a qualified common analytical basis. No missing species assumed zero, molar/mass conversion, speciation or charge balance. Inputs must not double-count total inorganic carbon or report nitrogen/sulfur equivalents without conversion qualification. Source supplies no TKS thresholds or TKS-to-corrosion-rate equation; no automatic corrosivity or corrosion rate inferred.

## `api581.api.damage.groundwater_rate_classification`

Groundwater steel corrosivity category from supplied corrosion rate

계산 ID: `damage/groundwater-rate-classification`

출처: Part2 Annex2.B §11.3.3(a)-(d); PDF p405

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion_rate_m_year` | 예 | `<class 'float'>` |
| `unit_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `shared_boundary_policy` | 기본값/선택 | `typing.Literal['lower_severity', 'higher_severity'] | None` |

출력: `corrosion_rate_m_year`, `corrosivity_category`, `selected_unit_basis`, `category_lower_bound_m_year`, `category_upper_bound_m_year`, `lower_bound_relation`, `upper_bound_relation`, `shared_boundary_encountered`

적용 범위: Classifies a supplied steel corrosion rate, not TKS. Printed SI limits.03/.25/1.27mm/year differ from1/10/50mpy converted exactly. Explicit unit basis required. The medium/high shared.25mm/year or10mpy endpoint needs explicit lower/higher severity policy. Low is strictly below first threshold; very high strictly above last. No material-specific rate prediction, treatment credit or degradation immunity.

## `api581.api.damage.groundwater_assessment`

Qualified groundwater chemistry and externally established steel corrosion rate

계산 ID: `damage/groundwater-assessment`

출처: Part2 Annex2.B §11.3.3; PDF p405

| 입력 | 필수 | 타입 |
|---|---|---|
| `chemistry` | 예 | `<class 'api581.groundwater.GroundwaterChemistry'>` |
| `qualified_rate` | 예 | `<class 'api581.groundwater.GroundwaterRate'>` |
| `steel_applicability_basis` | 예 | `<class 'str'>` |
| `specialist_rate_basis` | 예 | `<class 'str'>` |

출력: `total_key_species_mg_l`, `corrosion_rate_m_year`, `corrosivity_category`, `selected_unit_basis`, `category_lower_bound_m_year`, `category_upper_bound_m_year`, `lower_bound_relation`, `upper_bound_relation`, `shared_boundary_encountered`, `rate_source`, `tks_to_rate_model_available`

적용 범위: Competent water-corrosivity specialist must establish the steel corrosion rate independently. TKS is reported alongside that rate, never used to invent source cutoffs or a rate regression. No groundwater-specific quantitative rate equation is provided by the standard. Chemistry, material and specialist qualifications are supplied, not independently verified.

## `api581.api.damage.groundwater_thinning_assessment`

Qualified groundwater rate through non-AST unclad thinning

계산 ID: `damage/groundwater-thinning-assessment`

출처: Part2 Annex2.B §11.3.3; Part2 §4.5.7,Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `corrosion` | 예 | `<class 'api581.groundwater.GroundwaterAssessment'>` |
| `assessment_distribution` | 예 | `typing.Literal['general', 'local']` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `total_key_species_mg_l`, `corrosion_rate_m_year`, `corrosivity_category`, `selected_unit_basis`, `category_lower_bound_m_year`, `category_upper_bound_m_year`, `lower_bound_relation`, `upper_bound_relation`, `shared_boundary_encountered`, `rate_source`, `tks_to_rate_model_available`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`, `assessment_distribution`

적용 범위: Same externally qualified groundwater rate drives loss and non-AST unclad thinning; general/local inspection and steel applicability require explicit basis. No automatic pitting multiplier, TKS-derived rate, MIC/deposit exclusions or treatment credit. Monitoring row must be other; no borrowed acid/sour-water credits. Qualified experience replacement remains separately available under Table4.8. No cladding, AST, FFS or all-mechanism assessment.

## `api581.api.damage.thinning_rate_selection`

Measured-first and maximum-mechanism rate with governing thinning type

계산 ID: `damage/thinning-rate-selection`

출처: Part2 §§4.5.2,4.5.4; PDF pp150-151

| 입력 | 필수 | 타입 |
|---|---|---|
| `mechanisms` | 예 | `list[api581.thinning_selection.MechanismThinningRate]` |
| `applicability_and_period_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `assessment_distribution`, `governing_rate_mechanism_ids`, `governing_type_mechanism_ids`, `rate_by_mechanism_m_year`, `selection_source_by_mechanism`, `fallback_ignored_by_mechanism`

적용 범위: Caller supplies all applicable mechanisms for one component, assessed surface and common current-process plan period. Representative measured CML/history rate wins within each mechanism, including explicit zero. Otherwise exactly the supplied calculated/estimated fallback is used; no invented priority between estimated and calculated rates. Rate is maximum across mechanisms, not sum. Local inspection type governs if any applicable mechanism is local, even when its rate is lower. No missing mechanism assumed absent, automatic mechanism screening, CML regression, rate confidence inference or forecast. Long-term current-process representativeness and rate/type provenance require qualification.

## `api581.api.damage.thinning_selected_mechanisms`

Selected multi-mechanism rate through qualified non-AST thinning

계산 ID: `damage/thinning-selected-mechanisms`

출처: Part2 §§4.5.2,4.5.4,4.5.7; Table4.8

| 입력 | 필수 | 타입 |
|---|---|---|
| `selection` | 예 | `<class 'api581.thinning_selection.ThinningRateSelection'>` |
| `starting_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `inspections` | 예 | `<class 'api581.thinning.Posterior'>` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `corrosion_rate_m_year`, `assessment_distribution`, `governing_rate_mechanism_ids`, `governing_type_mechanism_ids`, `rate_by_mechanism_m_year`, `selection_source_by_mechanism`, `fallback_ignored_by_mechanism`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`

적용 범위: Maximum selected rate drives one common wall/strength baseline; most localized assigned mechanism governs inspection scope. Caller must qualify inspections for that governing type and all applicable loss locations. Generic composition uses other monitoring row with table factor1; mechanism-specific credits cannot be borrowed across mechanisms. Qualified Table4.8 experience replacement is explicit. Custom priors remain supported. No rate summation, multiple-surface loss, all-mechanism DF, AST, cladding, CML history interpretation or whole-asset risk.

## `api581.api.damage.thinning_assessment_period`

Consistent furnished/measured thickness baseline and elapsed period

계산 ID: `damage/thinning-assessment-period`

출처: Part2 §4.5.5; PDF p151

| 입력 | 필수 | 타입 |
|---|---|---|
| `installed_at` | 예 | `<class 'pydantic.types.AwareDatetime'>` |
| `assessment_at` | 예 | `<class 'pydantic.types.AwareDatetime'>` |
| `baseline_type` | 예 | `typing.Literal['furnished', 'measured']` |
| `furnished_thickness_m` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `measured_baseline` | 기본값/선택 | `api581.thinning_history.MeasuredBaseline | None` |
| `days_per_year` | 예 | `<class 'float'>` |
| `period_and_year_basis` | 예 | `<class 'str'>` |

출력: `baseline_type`, `baseline_at`, `assessment_at`, `baseline_thickness_m`, `baseline_inspection_id`, `elapsed_days`, `elapsed_years`, `days_per_year`

적용 범위: Timezone-aware timestamps normalized to UTC. Furnished thickness starts at installation; selected measured thickness starts at its qualified inspection time, requiring high-quality inspection, high-confidence accuracy and reset basis. Year conversion is explicit caller convention, not an API581-mandated constant. No process-change detection, measurement uncertainty correction, automatic reset selection or thickness reconciliation.

## `api581.api.damage.thinning_inspection_history`

Assessment-period inspection eligibility and direct A-D counts

계산 ID: `damage/thinning-inspection-history`

출처: Part2 §§4.5.5-4.5.6; Tables4.6,2.C inspection guidance; PDF pp151-152

| 입력 | 필수 | 타입 |
|---|---|---|
| `installed_at` | 예 | `<class 'pydantic.types.AwareDatetime'>` |
| `assessment_at` | 예 | `<class 'pydantic.types.AwareDatetime'>` |
| `baseline_type` | 예 | `typing.Literal['furnished', 'measured']` |
| `furnished_thickness_m` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `measured_baseline` | 기본값/선택 | `api581.thinning_history.MeasuredBaseline | None` |
| `days_per_year` | 예 | `<class 'float'>` |
| `period_and_year_basis` | 예 | `<class 'str'>` |
| `inspections` | 예 | `list[api581.thinning_history.ThinningInspectionRecord]` |
| `baseline_boundary_policy` | 예 | `typing.Literal['include_baseline_time', 'exclude_baseline_time']` |

출력: `baseline_type`, `baseline_at`, `assessment_at`, `baseline_thickness_m`, `baseline_inspection_id`, `elapsed_days`, `elapsed_years`, `days_per_year`, `inspections_a`, `inspections_b`, `inspections_c`, `inspections_d`, `eligible_inspection_ids`, `excluded_inspection_reasons`, `baseline_boundary_policy`

적용 범위: Only performed, qualified inspections in the selected period receive A-D counts; E receives no credit. Before-baseline and after-assessment records remain excluded diagnostics. Exact baseline-time inclusion is explicit owner policy; source does not resolve duplicate use of a baseline-setting inspection. End time is included. Duplicate IDs or a baseline inspection ID with conflicting timestamp fail. No automatic NDE effectiveness grading, equivalent-count conversion, geometry/coverage qualification or credit for planned inspections.

## `api581.api.damage.thinning_history_assessment`

Thickness/history/rate selection through period-consistent thinning DF

계산 ID: `damage/thinning-history-assessment`

출처: Part2 §§4.5.2-4.5.7; PDF pp150-156

| 입력 | 필수 | 타입 |
|---|---|---|
| `history` | 예 | `<class 'api581.thinning_history.ThinningInspectionHistory'>` |
| `selection` | 예 | `<class 'api581.thinning_selection.ThinningRateSelection'>` |
| `prior` | 예 | `<class 'api581.thinning.PriorSelection'>` |
| `strength` | 예 | `api581.clad_thinning.PressureStrength | api581.clad_thinning.CodeStrength` |
| `conditions` | 예 | `<class 'api581.thinning_conditions.ThinningConditions'>` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `baseline_type`, `baseline_at`, `assessment_at`, `baseline_thickness_m`, `baseline_inspection_id`, `elapsed_days`, `elapsed_years`, `days_per_year`, `inspections_a`, `inspections_b`, `inspections_c`, `inspections_d`, `eligible_inspection_ids`, `excluded_inspection_reasons`, `baseline_boundary_policy`, `corrosion_rate_m_year`, `assessment_distribution`, `governing_rate_mechanism_ids`, `governing_type_mechanism_ids`, `rate_by_mechanism_m_year`, `selection_source_by_mechanism`, `fallback_ignored_by_mechanism`, `wall_loss_fraction`, `strength_ratio`, `posterior_probabilities`, `reliability_indices`, `damage_state_failure_probabilities`, `weighted_failure_probability`, `base_damage_factor`, `thinning_damage_factor`, `monitoring_row`, `velocity_threshold_m_s`, `online_monitoring_factor`, `candidate_method_factors`, `monitoring_credit_basis`, `joint_exception_applied`, `injection_point_factor`, `deadleg_factor`, `strength_method`

적용 범위: Selected baseline derives both wall thickness and elapsed period; eligible dated inspection records derive counts, with independently selected table/custom prior. No competing manually supplied age/counts. Strength baseline must agree with derived wall baseline. Rate-selection common-period and inspection coverage/type qualifications remain external. Generic other monitoring row only, no borrowed mechanism credits. Non-AST unclad scope; no automatic process-change reset, inspection scheduling, cladding or all-mechanism/asset risk.

## `api581.api.damage.caustic_screening`

Caustic cracking material and any-concentration exposure screen

계산 ID: `damage/caustic-screening`

출처: Part2 §6.3; PDF p172

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel', 'other_material']` |
| `caustic_present` | 예 | `<class 'bool'>` |
| `screening_basis` | 예 | `<class 'str'>` |

출력: `evaluate_caustic_cracking`, `screening_reason`

적용 범위: Carbon/low-alloy steel with caustic at any concentration requires evaluation. Presence includes qualified local/upset/residual exposure; no5wtpct or normal-process-temperature cutoff is used for screening. Screen-out means outside this procedure, not material immunity, zero overall DF or exclusion of other mechanisms.

## `api581.api.damage.caustic_figure_susceptibility`

Qualified caustic graph area through Figure6.2 and crack-history gate

계산 ID: `damage/caustic-figure-susceptibility`

출처: Part2 §6.5,Figure6.2; Figures6.1/6.1M; PDF pp172-173,176-178

| 입력 | 필수 | 타입 |
|---|---|---|
| `stress_relieved` | 예 | `<class 'bool'>` |
| `cracking_history` | 예 | `typing.Literal['never_detected', 'detected_repaired', 'unrepaired', 'specialist_reassigned_after_clear_inspection']` |
| `adequate_subsequent_clear_inspection` | 기본값/선택 | `<class 'bool'>` |
| `specialist_reassignment_basis` | 기본값/선택 | `str | None` |
| `fabrication_history_basis` | 예 | `<class 'str'>` |
| `plot` | 기본값/선택 | `api581.caustic_screening.CausticPlotEvidence | None` |

출력: `susceptibility`, `decision_branch`, `plot_evidence_used`, `historical_high_retained`

적용 범위: Figure6.1/6.1M area is independently qualified from actual maximum metal temperature and effective local NaOH concentration. This API routes the area; it does not digitize/interpolate the graph or certify PWHT. Plot concentration0..50wtpct; exactly5wtpct follows the not-less-than5 branch. Heat tracing and steam-out before water flushing follow Figure6.2. Detected/repaired historical cracking stays High until an adequately effective subsequent clear inspection AND specialist reassignment basis. Stress relief cannot erase that history. Unrepaired cracks require separate FFS and fail explicitly. No automatic stress-relief temperature/hold-time qualification, alloy immunity or local boiling concentration model.

## `api581.api.damage.caustic_screened_assessment`

Caustic screen and Figure6.2 through SCC severity/inspection/age DF

계산 ID: `damage/caustic-screened-assessment`

출처: Part2 §§6.3,6.5-6.6; Tables6.2-6.3; Figure6.2; eq(2.25); PDF pp172-178

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.caustic_screening.CausticScreen'>` |
| `susceptibility` | 예 | `<class 'api581.caustic_screening.CausticFigureSusceptibility'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `assessment_basis` | 예 | `<class 'str'>` |

출력: `evaluate_caustic_cracking`, `screening_reason`, `susceptibility`, `decision_branch`, `plot_evidence_used`, `historical_high_retained`, `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/exposure screen must pass; outside-scope input fails instead of manufacturing DF0. Figure area/PWHT and crack-history/reassignment declarations require qualification. Uses existing caustic SVI, equivalent highest inspection and age escalation unchanged; source ambiguous E/500 cell and counts beyond6 remain unsupported. Inspection coverage and qualifying age are externally established per §6.6.3, not inferred from generic thinning history. No FFS, graph interpolation or all-mechanism risk.

## `api581.api.damage.amine_cracking_screening`

Any-concentration acid-gas-treating amine SCC material screen

계산 ID: `damage/amine-cracking-screening`

출처: Part2 §7.3; PDF p179

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel', 'other_material']` |
| `acid_gas_treating_amine_present` | 예 | `<class 'bool'>` |
| `screening_basis` | 예 | `<class 'str'>` |

출력: `evaluate_amine_cracking`, `screening_reason`

적용 범위: Carbon/low-alloy steel with acid-gas-treating amines in any concentration requires susceptibility evaluation. No concentration, normal-temperature, amine-type, rich-service or PWHT exclusion is inferred. Lean/rich/fresh composition, actual metal temperature, heat tracing, steam-out and other cracking mechanisms require separate evaluation. Screen-out is outside this procedure, not overall immunity or DF0.

## `api581.api.damage.amine_cracking_screened_assessment`

Screened amine exposure through qualified SCC susceptibility and DF

계산 ID: `damage/amine-cracking-screened-assessment`

출처: Part2 §§7.3,7.5-7.6; Table7.2,Table6.3; eq(2.26); PDF pp179-181

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.amine_screening.AmineCrackingScreen'>` |
| `cracking` | 예 | `<class 'api581.scc_mechanisms.Assessment'>` |
| `susceptibility_and_inspection_basis` | 예 | `<class 'str'>` |

출력: `evaluate_amine_cracking`, `screening_reason`, `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Supplied susceptibility must be independently qualified using Figure7.1 or expert assessment; this API does not implement the figure or predict from amine chemistry. Screening must pass; no synthetic zero DF on screen-out. Confirmed cracking forces High; unrepaired cracks require FFS. Inspection grade/count and time since qualifying A/B/C clear/repaired inspection follow section7.6.3 and remain externally qualified. Existing six-equivalent-inspection support is retained; no all-mechanism assessment.

## `api581.api.damage.amine_figure_susceptibility`

Figure7.1 amine cracking susceptibility

계산 ID: `damage/amine-figure-susceptibility`

출처: Part2 Figure7.1,Table7.1; PDF pp182-183

| 입력 | 필수 | 타입 |
|---|---|---|
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `stress_relieved` | 예 | `<class 'bool'>` |
| `solution` | 예 | `typing.Literal['fresh', 'rich', 'lean', 'lean_and_rich']` |
| `amine_group` | 예 | `typing.Literal['mea_or_dipa', 'dea', 'other_treating_amine']` |
| `maximum_metal_temperature_k` | 예 | `<class 'float'>` |
| `heat_traced` | 예 | `<class 'bool'>` |
| `steamed_out_before_water_flush` | 예 | `<class 'bool'>` |
| `applicability_basis` | 예 | `<class 'str'>` |

출력: `susceptibility`, `decision_branch`, `lean_exposure_selected`

적용 범위: Literal Fahrenheit flowchart thresholds100/140/180F converted exactly to kelvin.100..180 and140..180 include endpoints after the prior >180 test. Both lean/rich exposure routes lean per Table7.1. Other treating amines follow the printed not-MEA/DIPA/not-DEA branch; mixtures spanning groups require independent qualification, not automatic worst-group selection. Actual maximum metal temperature, heat tracing, steam-out before flushing and effective stress relief require qualification. Confirmed cracks forceHigh before stress relief/composition; unrepaired cracks require FFS. Not an amine corrosion-rate model or automatic chemical speciation/PWHT validation.

## `api581.api.damage.amine_figure_assessment`

Figure7.1 susceptibility through amine SCC DF

계산 ID: `damage/amine-figure-assessment`

출처: Part2 §7.6.3,Figure7.1,Tables7.2/6.3,eq(2.26); PDF pp180,182-183

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.amine_screening.AmineCrackingScreen'>` |
| `service` | 예 | `<class 'api581.amine_screening.AmineFigure'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `inspection_basis` | 예 | `<class 'str'>` |

출력: `evaluate_amine_cracking`, `screening_reason`, `susceptibility`, `decision_branch`, `lean_exposure_selected`, `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Material/exposure screen, Figure7.1 service declarations and mechanism-specific qualifying inspection age/count require qualification. Reuses existing SVI, equivalent inspection and age escalation, with maximum supported equivalent count6. Rich/fresh none applies only to this amine SCC mechanism, not SSC/HIC/SOHIC or other damage. No whole-component risk, FFS or automatic inspection grading.

## `api581.api.damage.ssc_screening`

SSC carbon/low-alloy steel wet-H2S any-concentration screen

계산 ID: `damage/ssc-screening`

출처: Part2 §8.3; PDF p184

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel', 'other_material']` |
| `water_present` | 예 | `<class 'bool'>` |
| `h2s_present` | 예 | `<class 'bool'>` |
| `exposure_basis` | 예 | `<class 'str'>` |

출력: `evaluate_ssc`, `screening_reason`

적용 범위: Evaluate carbon/low-alloy steel whenever both water and H2S are present at any concentration. No1ppm, partial-pressure, pH, temperature, hardness or PWHT cutoff is used to exclude the mechanism at this screen. Presence flags require qualified local/process/upset exposure evidence. Environmental hydrogen severity, cyanide, weld/HAZ Brinnell hardness and heat treatment remain separate susceptibility inputs. Screen-out is outside this procedure, not DF0, FFS acceptance or immunity to other mechanisms.

## `api581.api.damage.hic_h2s_screening`

HIC/SOHIC-H2S steel and wet-H2S any-concentration screen

계산 ID: `damage/hic-h2s-screening`

출처: Part2 §9.3; PDF p189

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel', 'other_material']` |
| `water_present` | 예 | `<class 'bool'>` |
| `h2s_present` | 예 | `<class 'bool'>` |
| `exposure_basis` | 예 | `<class 'str'>` |

출력: `evaluate_hic_sohic_h2s`, `screening_reason`

적용 범위: Source material/water/H2S screening criteria coincide with SSC, but this identifier explicitly evaluates HIC/SOHIC-H2S. Carbon and low-alloy steel both enter screening; downstream Table9.3 carbon-steel material/sulfur/product assumptions require independent qualification. PWHT, seamless pipe, low sulfur or low H2S concentration alone do not exclude screening. No automatic SSC/HIC equivalence, SOHIC immunity, blister/crack FFS acceptance or zero DF.

## `api581.api.damage.ssc_qualified_susceptibility`

SSC environment and measured hardness with cyanide susceptibility upgrade

계산 ID: `damage/ssc-qualified-susceptibility`

출처: Part2 Tables8.2-8.3; PDF p187

| 입력 | 필수 | 타입 |
|---|---|---|
| `environment` | 예 | `<class 'api581.scc_mechanisms.WetH2sEnvironment'>` |
| `measured_brinnell_hardness` | 예 | `<class 'float'>` |
| `pwht` | 예 | `<class 'bool'>` |
| `service_basis` | 예 | `<class 'str'>` |

출력: `environmental_severity`, `susceptibility_upgrade_required`, `unadjusted_susceptibility`, `susceptibility`, `cyanide_upgrade_applied`

적용 범위: Cyanide note upgrades susceptibility, not environmental severity, one category none->low->medium->high, capped at high, only when pH>8.3 and water H2S>1000ppm. Brinnell must be actually measured, not converted microhardness; PWHT and process chemistry require qualification. Existing source pH gaps and overlapping1000ppm columns fail explicitly. No automatic material applicability or chemical speciation.

## `api581.api.damage.ssc_qualified_assessment`

SSC material/exposure through environment/hardness/cyanide and DF

계산 ID: `damage/ssc-qualified-assessment`

출처: Part2 §§8.3,8.5-8.6,Tables8.2-8.4,Table6.3; eq(2.27); PDF pp184-188

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.ssc_screening.SscScreen'>` |
| `service` | 예 | `<class 'api581.ssc_screening.SscQualifiedService'>` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `inspection_basis` | 예 | `<class 'str'>` |

출력: `evaluate_ssc`, `screening_reason`, `environmental_severity`, `susceptibility_upgrade_required`, `unadjusted_susceptibility`, `susceptibility`, `cyanide_upgrade_applied`, `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Selected material/wet-H2S screen must pass. Reuses existing Table8.2 gaps/overlap guards, Table8.3 actual Brinnell/PWHT susceptibility and one-category cyanide note before crack override. Confirmed cracking forces high; unrepaired cracks require FFS. Caller qualifies mechanism-specific inspection period and coverage. Existing equivalent-count support up to6, age escalation and table DF preserved. No generic thinning-history reuse, FFS or total asset risk.

## `api581.api.damage.hic_h2s_qualified_susceptibility`

HIC/SOHIC-H2S environment/material/cyanide susceptibility

계산 ID: `damage/hic-h2s-qualified-susceptibility`

출처: Part2 §9.6.4 STEP1-2,Tables9.2-9.3; PDF pp190,193

| 입력 | 필수 | 타입 |
|---|---|---|
| `environment` | 예 | `<class 'api581.scc_mechanisms.WetH2sEnvironment'>` |
| `steel_sulfur_weight_percent` | 예 | `<class 'float'>` |
| `product_form` | 예 | `typing.Literal['plate_or_welded', 'seamless_or_extruded_pipe']` |
| `pwht` | 예 | `<class 'bool'>` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `service_basis` | 예 | `<class 'str'>` |

출력: `environmental_severity`, `susceptibility_upgrade_required`, `effective_environmental_severity`, `unadjusted_susceptibility`, `cyanide_adjusted_susceptibility`, `susceptibility`

적용 범위: Carbon-steel Table9.3 applicability qualified externally. Sulfur input is weight percent, not mass fraction. Confirmed cracking forces environmental severity high under STEP1 and final susceptibility high under section9.5; measured environment remains diagnostic. Cyanide note upgrades subsequent susceptibility one category capped high, not environment. Existing pH gaps/1000ppm overlap fail. No sulfur inference from steel grade/year or automatic low-alloy table applicability.

## `api581.api.damage.hic_h2s_monitoring_selection`

Table9.5 or qualified experience replacement monitoring factor

계산 ID: `damage/hic-h2s-monitoring-selection`

출처: Part2 Table9.5 note; PDF p193

| 입력 | 필수 | 타입 |
|---|---|---|
| `monitoring` | 예 | `typing.Literal['none', 'process_variables', 'hydrogen_probes', 'both']` |
| `experience_factor` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `experience_basis` | 기본값/선택 | `str | None` |

출력: `table_monitoring_factor`, `monitoring_factor`, `monitoring_factor_source`

적용 범위: Table factors1/2/2/4 or one positive finite experience-based replacement with nonblank basis. Replacement is not multiplied by the table factor. Source gives no numeric range for experience substitutes; no automatic clamp or empirical calibration. Replacement requires an active monitoring method; no credit inferred for absent monitoring. Physical program effectiveness remains owner-qualified.

## `api581.api.damage.hic_h2s_qualified_assessment`

Screened HIC/SOHIC-H2S service through monitoring-adjusted DF

계산 ID: `damage/hic-h2s-qualified-assessment`

출처: Part2 §§9.3,9.5-9.6,Tables9.2-9.5,eq(2.28); PDF pp189-193

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.ssc_screening.SscScreen'>` |
| `service` | 예 | `<class 'api581.hic_screened.HicQualifiedService'>` |
| `known_blisters_or_cracks` | 예 | `<class 'bool'>` |
| `ffs_disposition` | 예 | `typing.Literal['not_required', 'repaired', 'qualified_ffs_basis']` |
| `ffs_basis` | 기본값/선택 | `str | None` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `monitoring` | 예 | `typing.Literal['none', 'process_variables', 'hydrogen_probes', 'both']` |
| `experience_factor` | 기본값/선택 | `typing.Annotated[float, FieldInfo(annotation=NoneType, required=True, metadata=[Strict(strict=True), Gt(gt=0), AllowInfNan(allow_inf_nan=False)])] | None` |
| `experience_basis` | 기본값/선택 | `str | None` |
| `inspection_monitoring_basis` | 예 | `<class 'str'>` |

출력: `evaluate_hic_sohic_h2s`, `screening_reason`, `environmental_severity`, `susceptibility_upgrade_required`, `effective_environmental_severity`, `unadjusted_susceptibility`, `cyanide_adjusted_susceptibility`, `susceptibility`, `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`, `ffs_disposition`, `table_monitoring_factor`, `monitoring_factor_source`

적용 범위: Carbon-steel integration only, despite broader carbon/low-alloy screening. Known blisters/cracks require explicit repaired or externally qualified FFS disposition and basis; this API performs no FFS. Confirmed cracking must also be declared known. Inspection and age follow section9.6.4, not generic thinning periods. Monitoring is applied once using existing factors1/2/2/4; qualification is mandatory. Existing six-equivalent-inspection and source table guards retained. No whole-asset risk or automatic damage detection.

## `api581.api.damage.acscc_screening`

ACSCC alkaline-water and FCCU feed-change evaluation triggers

계산 ID: `damage/acscc-screening`

출처: Part2 §10.3; PDF p196

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['carbon_steel', 'low_alloy_steel', 'other_material']` |
| `water_present` | 예 | `<class 'bool'>` |
| `water_ph` | 기본값/선택 | `float | None` |
| `fccu_feed_sulfur_reduced` | 예 | `<class 'bool'>` |
| `fccu_feed_nitrogen_increased` | 예 | `<class 'bool'>` |
| `screening_basis` | 예 | `<class 'str'>` |

출력: `evaluate_acscc`, `material_in_scope`, `evaluation_triggers`

적용 범위: Carbon/low-alloy steel: alkaline water pH>7.5 or reduced-sulfur/increased-nitrogen FCCU feed changes trigger evaluation. Exactly7.5 does not pass the strict water trigger. Feed-change triggers are independent review flags, not proof of carbonate concentration or susceptibility. Water presence requires its qualified pH; absent water must omit pH. No H2S threshold, cyanide exclusion, carbonate estimate, PWHT credit or damage factor is inferred. Outside scope is not overall immunity or zero risk.

## `api581.api.damage.acscc_water_susceptibility`

Qualified numeric water pH to ACSCC carbonate/PWHT susceptibility

계산 ID: `damage/acscc-water-susceptibility`

출처: Part2 Table10.2 and note1; PDF p199

| 입력 | 필수 | 타입 |
|---|---|---|
| `water_ph` | 예 | `<class 'float'>` |
| `carbonate_ppm` | 예 | `<class 'float'>` |
| `pwht` | 예 | `<class 'bool'>` |
| `shared_ph_boundary_policy` | 기본값/선택 | `typing.Literal['lower_ph_row', 'higher_ph_row'] | None` |
| `carbonate_measurement_basis` | 예 | `<class 'str'>` |
| `traditional_alkalinity_only` | 예 | `<class 'bool'>` |
| `service_fabrication_basis` | 예 | `<class 'str'>` |

출력: `susceptibility`, `selected_ph_band`, `shared_ph_boundary_encountered`

적용 범위: Numeric pH mapped to existing Table10.2 bands. Shared8.0/9.0 endpoints require explicit lower/higher-pH row selection; no automatic susceptibility-maximizing policy.7.5 enters7.5_to_8, independently of screening strict>7.5.100ppm carbonate belongs high-concentration column. Traditional P/M alkalinity alone is rejected per note1; caller supplies qualified carbonate method. No carbonate inference from total alkalinity, PWHT certification, numeric pH rounding allowance or material applicability.

## `api581.api.damage.acscc_qualified_assessment`

ACSCC screen and common water chemistry through inspection/age DF

계산 ID: `damage/acscc-qualified-assessment`

출처: Part2 §§10.3,10.6.3,Table10.2-10.3,Table6.3; eq(2.29); PDF pp196-199

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.acscc_screening.AcsccScreen'>` |
| `water` | 예 | `<class 'api581.acscc_screening.AcsccWaterSusceptibility'>` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `inspection_basis` | 예 | `<class 'str'>` |

출력: `evaluate_acscc`, `material_in_scope`, `evaluation_triggers`, `susceptibility`, `selected_ph_band`, `shared_ph_boundary_encountered`, `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Requires positive screening and water-present numeric pH consistent with susceptibility input. FCCU feed change can trigger review but cannot replace water/carbonate data needed by Table10.2. Shared pH8/9 policy, qualified carbonate measurement and PWHT remain explicit. Confirmed cracking forceshigh; unrepaired cracks requireFFS. Independent mechanism-specific inspection age/coverage required; existing six-equivalent-inspection support retained. No chemical speciation, automatic damage detection, FFS or whole-asset risk.

## `api581.api.damage.pascc_screening`

PASCC austenitic stainless/nickel alloy sulfur exposure screen

계산 ID: `damage/pascc-screening`

출처: Part2 §11.3; PDF p201

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['austenitic_stainless_steel', 'nickel_based_alloy', 'other_material']` |
| `sulfur_bearing_compounds_exposure` | 예 | `<class 'bool'>` |
| `exposure_basis` | 예 | `<class 'str'>` |

출력: `evaluate_pascc`, `screening_reason`

적용 범위: Austenitic stainless steel or nickel-based alloy exposed to sulfur-bearing compounds requires PASCC susceptibility evaluation. No automatic exclusion for normal-operation dryness, low-carbon/stabilized grade, low operating temperature, alkaline wash or nitrogen purge; shutdown air/moisture and mitigation remain separate evaluation. Material category does not authorize every Table11.2 cell. Screen-out is outside this procedure, not global immunity or zero DF.

## `api581.api.damage.pascc_figure_susceptibility`

PASCC Figure11.1 exposure and qualified downtime protection

계산 ID: `damage/pascc-figure-susceptibility`

출처: Part2 Figure11.1,Table11.2; PDF pp205-206

| 입력 | 필수 | 타입 |
|---|---|---|
| `alloy` | 예 | `<class 'api581.scc_mechanisms.PasccSusceptibility'>` |
| `sulfur_oxygen_water_during_operation` | 예 | `<class 'bool'>` |
| `sulfur_oxygen_water_during_shutdown` | 예 | `<class 'bool'>` |
| `qualified_rp0170_downtime_protection` | 예 | `<class 'bool'>` |
| `protection_basis` | 기본값/선택 | `str | None` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `service_alloy_basis` | 예 | `<class 'str'>` |

출력: `table_or_override_susceptibility`, `susceptibility`, `downtime_reduction_applied`

적용 범위: Caller qualifies simultaneous sulfur/oxygen/water exposure in operation/shutdown and Table11.2 alloy/thermal history. No exposure in either phase returns none without table lookup. RP0170 downtime protection, when qualified, reduces table susceptibility one level high->medium->low->none exactly as Figure11.1. Confirmed cracks forcehigh before exposure/protection; unrepaired cracks requireFFS. No RP0170 compliance verification or automatic shutdown exposure inference. Existing SI427C table threshold/unsupported cells retained.

## `api581.api.damage.pascc_qualified_assessment`

PASCC screen/Figure11.1 through inspection and age DF

계산 ID: `damage/pascc-qualified-assessment`

출처: Part2 §§11.3,11.6.3,Figure11.1,Tables11.2-11.3; eq(2.30); PDF pp201-206

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.pascc_screening.PasccScreen'>` |
| `service` | 예 | `<class 'api581.pascc_screening.PasccFigure'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `inspection_basis` | 예 | `<class 'str'>` |

출력: `evaluate_pascc`, `screening_reason`, `table_or_override_susceptibility`, `susceptibility`, `downtime_reduction_applied`, `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Requires positive material/sulfur screen and independent alloy-group identity/thermal-history qualification. Nickel-family screening cannot use H/L-grade300SS or321SS table groups. Mixed-named table groups require owner matching, not automatic grade inference. Figure11.1 exposures/protection and mechanism-specific inspection period remain explicit. Confirmed cracks override mitigation; unrepairedFFS. Existing equivalent-count/age rules retained. No whole-asset risk or FFS.

## `api581.api.damage.clscc_screening`

CLSCC material/potential wet-chloride and operating-temperature screen

계산 ID: `damage/clscc-screening`

출처: Part2 §12.3; PDF p207

| 입력 | 필수 | 타입 |
|---|---|---|
| `material` | 예 | `typing.Literal['austenitic_stainless_steel', 'other_material']` |
| `actual_or_potential_wet_chloride_exposure` | 예 | `<class 'bool'>` |
| `operating_temperature_k` | 예 | `<class 'float'>` |
| `temperature_basis` | 예 | `typing.Literal['printed_si', 'printed_us_converted']` |
| `exposure_basis` | 예 | `<class 'str'>` |

출력: `evaluate_clscc`, `material_in_scope`, `temperature_screen_passed`, `screening_temperature_threshold_k`, `selected_temperature_basis`

적용 범위: Austenitic stainless steel, actual/potential chlorides AND water and operating temperature strictly above selected38C or100F threshold. Paired source thresholds differ; unit basis explicit. Exposure qualification includes upsets, retained hydrotest water, cooling tower drift and insulation/process conditions. No concentration cutoff, bulk-to-local enrichment, nickel-content exemption, material immunity or DF0 inferred. A negative screen does not invalidate observed cracks or replace FFS.

## `api581.api.damage.clscc_qualified_assessment`

CLSCC wet-chloride screen through SI susceptibility and inspection DF

계산 ID: `damage/clscc-qualified-assessment`

출처: Part2 §§12.3,12.6.3,Tables12.2M/12.3,Table6.3; eq(2.31); PDF pp207-211

| 입력 | 필수 | 타입 |
|---|---|---|
| `screening` | 예 | `<class 'api581.clscc_screening.ClsccScreen'>` |
| `ph_over_10` | 예 | `<class 'bool'>` |
| `chloride_band_ppm` | 예 | `typing.Literal['1-10', '11-100', '101-1000', '>1000']` |
| `chemistry_basis` | 예 | `<class 'str'>` |
| `confirmed_cracking` | 예 | `<class 'bool'>` |
| `unrepaired_cracks` | 예 | `<class 'bool'>` |
| `years_since_qualifying_inspection` | 예 | `<class 'float'>` |
| `inspections` | 예 | `<class 'api581.scc_mechanisms.InspectionCounts'>` |
| `inspection_basis` | 예 | `<class 'str'>` |

출력: `evaluate_clscc`, `material_in_scope`, `temperature_screen_passed`, `screening_temperature_threshold_k`, `selected_temperature_basis`, `susceptibility`, `effective_susceptibility`, `severity_index`, `equivalent_inspection_grade`, `equivalent_inspection_count`, `base_damage_factor`, `age_factor`, `monitoring_factor`, `damage_factor`

적용 범위: Uses the selected printed SI Table12.2M or US Table12.2 and the same operating temperature for susceptibility. Qualified chloride ion band and pH>10 classification supplied; no bulk-to-local chloride enrichment or interpolation through concentration gaps. No synthetic DF0 on screen-out. Confirmed cracking forces high; unrepaired cracks require FFS. Inspection period/coverage are mechanism-specific external qualifications. Source pH>10/93C overlap in the SI table and existing equivalent count support are retained; no whole-asset risk.

## `api581.api.api520.critical_pressure_ratio`

API 520 critical-flow pressure ratio

계산 ID: `api520/critical-pressure-ratio`

출처: API RP 520 7th ed. §3.6.1.4, Eq. 3.1

| 입력 | 필수 | 타입 |
|---|---|---|
| `heat_capacity_ratio` | 예 | `<class 'float'>` |

출력: `critical_pressure_ratio`

적용 범위: Ideal-gas relation; use qualified property data for real-gas/high-pressure service.

## `api581.api.api520.flow_coefficient_c`

API 520 gas/vapor flow coefficient C

계산 ID: `api520/flow-coefficient-c`

출처: API RP 520 7th ed. §3.6.2, Eq. 3.2-3.4; Fig. 32

| 입력 | 필수 | 타입 |
|---|---|---|
| `heat_capacity_ratio` | 예 | `<class 'float'>` |

출력: `flow_coefficient_c`

적용 범위: Ideal-gas coefficient; API 520 recommends qualified data or C=315 when k is unavailable.

## `api581.api.api520.relieving_pressure`

API 520 relieving pressure

계산 ID: `api520/relieving-pressure`

출처: API RP 520 7th ed. §3.5, Tables 1-6

| 입력 | 필수 | 타입 |
|---|---|---|
| `set_pressure_psig` | 예 | `<class 'float'>` |
| `allowable_overpressure_fraction` | 예 | `<class 'float'>` |
| `atmospheric_pressure_kpa` | 기본값/선택 | `<class 'float'>` |

출력: `relieving_pressure_psig`, `relieving_pressure_kpaa`

적용 범위: Overpressure fraction is supplied by the contingency/code basis; no automatic ASME scenario selection.

## `api581.api.api520.gas_critical_area`

API 520 critical gas/vapor effective area

계산 ID: `api520/gas-critical-area`

출처: API RP 520 7th ed. §3.6.2, Eqs. 3.2-3.4

| 입력 | 필수 | 타입 |
|---|---|---|
| `required_mass_flow_kg_h` | 예 | `<class 'float'>` |
| `relieving_temperature_k` | 예 | `<class 'float'>` |
| `compressibility_factor` | 기본값/선택 | `<class 'float'>` |
| `molecular_weight_kg_kmol` | 예 | `<class 'float'>` |
| `relief_pressure_kpaa` | 예 | `<class 'float'>` |
| `heat_capacity_ratio` | 예 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `back_pressure_factor` | 기본값/선택 | `<class 'float'>` |
| `combination_factor` | 기본값/선택 | `<class 'float'>` |

출력: `required_area_mm2`

적용 범위: SI mass-flow form; assumes critical ideal-gas/nozzle behavior and supplied correction factors.

## `api581.api.api520.gas_subcritical_area`

API 520 subcritical gas/vapor effective area

계산 ID: `api520/gas-subcritical-area`

출처: API RP 520 7th ed. §3.6.3, Eqs. 3.5-3.7

| 입력 | 필수 | 타입 |
|---|---|---|
| `required_mass_flow_kg_h` | 예 | `<class 'float'>` |
| `relieving_temperature_k` | 예 | `<class 'float'>` |
| `compressibility_factor` | 기본값/선택 | `<class 'float'>` |
| `molecular_weight_kg_kmol` | 예 | `<class 'float'>` |
| `relief_pressure_kpaa` | 예 | `<class 'float'>` |
| `heat_capacity_ratio` | 예 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `back_pressure_factor` | 기본값/선택 | `<class 'float'>` |
| `combination_factor` | 기본값/선택 | `<class 'float'>` |
| `downstream_pressure_kpaa` | 예 | `<class 'float'>` |

출력: `required_area_mm2`, `back_pressure_ratio`, `subcritical_flow_factor`

적용 범위: SI mass-flow form; conventional/pilot valve route only; use balanced-bellows manufacturer factors where applicable.

## `api581.api.api520.liquid_area`

API 520 liquid relief effective area

계산 ID: `api520/liquid-area`

출처: API RP 520 7th ed. §3.8-3.9, Eqs. 3.9 and 3.12

| 입력 | 필수 | 타입 |
|---|---|---|
| `required_flow_l_min` | 예 | `<class 'float'>` |
| `specific_gravity` | 예 | `<class 'float'>` |
| `set_pressure_kpag` | 예 | `<class 'float'>` |
| `back_pressure_kpag` | 기본값/선택 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `back_pressure_factor` | 기본값/선택 | `<class 'float'>` |
| `combination_factor` | 기본값/선택 | `<class 'float'>` |
| `viscosity_factor` | 기본값/선택 | `<class 'float'>` |
| `overpressure_factor` | 기본값/선택 | `<class 'float'>` |

출력: `required_area_mm2`

적용 범위: SI form; Kp/Kv/Kw are supplied or separately calculated; certified capacity and two-phase flashing are separate routes.

## `api581.api.api520.liquid_viscosity_factor`

API 520 liquid viscosity correction Kv

계산 ID: `api520/liquid-viscosity-factor`

출처: API RP 520 7th ed. §3.8.1.3, Eqs. 3.10-3.11; Fig. 36

| 입력 | 필수 | 타입 |
|---|---|---|
| `reynolds_number` | 예 | `<class 'float'>` |

출력: `viscosity_factor`

적용 범위: Correlation is not recommended below 100 SSU when using the alternate viscosity basis.

## `api581.api.api520.gas_critical_capacity`

API 520 critical gas/vapor mass capacity

계산 ID: `api520/gas-critical-capacity`

출처: API RP 520 7th ed. §3.6.2, Eqs. 3.2-3.4 (inverse sizing)

| 입력 | 필수 | 타입 |
|---|---|---|
| `effective_area_mm2` | 예 | `<class 'float'>` |
| `relieving_temperature_k` | 예 | `<class 'float'>` |
| `compressibility_factor` | 기본값/선택 | `<class 'float'>` |
| `molecular_weight_kg_kmol` | 예 | `<class 'float'>` |
| `relief_pressure_kpaa` | 예 | `<class 'float'>` |
| `heat_capacity_ratio` | 예 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `back_pressure_factor` | 기본값/선택 | `<class 'float'>` |
| `combination_factor` | 기본값/선택 | `<class 'float'>` |

출력: `mass_capacity_kg_h`

적용 범위: Inverse of the SI effective-area relation; use certified valve capacity and qualified real-gas data for selection.

## `api581.api.api520.gas_subcritical_capacity`

API 520 subcritical gas/vapor mass capacity

계산 ID: `api520/gas-subcritical-capacity`

출처: API RP 520 7th ed. §3.6.3, Eqs. 3.5-3.7 (inverse sizing)

| 입력 | 필수 | 타입 |
|---|---|---|
| `effective_area_mm2` | 예 | `<class 'float'>` |
| `relieving_temperature_k` | 예 | `<class 'float'>` |
| `compressibility_factor` | 기본값/선택 | `<class 'float'>` |
| `molecular_weight_kg_kmol` | 예 | `<class 'float'>` |
| `relief_pressure_kpaa` | 예 | `<class 'float'>` |
| `heat_capacity_ratio` | 예 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `combination_factor` | 기본값/선택 | `<class 'float'>` |
| `downstream_pressure_kpaa` | 예 | `<class 'float'>` |

출력: `mass_capacity_kg_h`, `back_pressure_ratio`, `subcritical_flow_factor`

적용 범위: Inverse of the SI effective-area relation; downstream pressure and manufacturer correction factors remain caller-qualified.

## `api581.api.api520.liquid_capacity`

API 520 liquid relief volumetric capacity

계산 ID: `api520/liquid-capacity`

출처: API RP 520 7th ed. §3.8-3.9, Eqs. 3.9 and 3.12 (inverse sizing)

| 입력 | 필수 | 타입 |
|---|---|---|
| `effective_area_mm2` | 예 | `<class 'float'>` |
| `specific_gravity` | 예 | `<class 'float'>` |
| `set_pressure_kpag` | 예 | `<class 'float'>` |
| `back_pressure_kpag` | 기본값/선택 | `<class 'float'>` |
| `discharge_coefficient` | 기본값/선택 | `<class 'float'>` |
| `back_pressure_factor` | 기본값/선택 | `<class 'float'>` |
| `combination_factor` | 기본값/선택 | `<class 'float'>` |
| `viscosity_factor` | 기본값/선택 | `<class 'float'>` |
| `overpressure_factor` | 기본값/선택 | `<class 'float'>` |

출력: `flow_capacity_l_min`

적용 범위: Inverse of the SI effective-area relation; flashing/two-phase capacity and certified valve coefficients remain separate routes.

## `api581.api.risk.portfolio`

Aggregate qualified component risks for a site or digital-twin portfolio

계산 ID: `risk/portfolio`

출처: Part 1 §4.3.1; Part 1 §4.3.2

| 입력 | 필수 | 타입 |
|---|---|---|
| `components` | 예 | `list[api581.portfolio.PortfolioComponent]` |
| `currency` | 예 | `<class 'str'>` |
| `disjointness_basis` | 예 | `<class 'str'>` |

출력: `component_count`, `annual_failure_frequency`, `equipment_area_risk_m2_per_year`, `personnel_area_risk_m2_per_year`, `area_risk_m2_per_year`, `financial_risk_per_year`, `currency`, `disjointness_basis`, `component_contributions`

적용 범위: Each component row must already be a mutually exclusive annual risk contribution on the same currency and consequence basis. This API does not deduplicate shared release scenarios, normalize currencies, or infer individual/societal risk. The disjointness_basis is an auditable owner declaration, not an automatic proof of independence.

## `api581.api.properties.acid_caustic_representative_fluid`

API 581 acid/caustic representative-fluid selection

계산 ID: `properties/acid-caustic-representative-fluid`

출처: Part 3 §4.1.3, §4.1.6; PDF p483-484

| 입력 | 필수 | 타입 |
|---|---|---|
| `is_acid_or_caustic` | 예 | `<class 'bool'>` |
| `is_flammable` | 예 | `<class 'bool'>` |
| `is_toxic` | 예 | `<class 'bool'>` |
| `personnel_contact_hazard` | 예 | `<class 'bool'>` |

출력: `selection`, `representative_fluid`, `release_phase`, `consequence_model`, `selection_basis`

적용 범위: Implements only the printed screening rule: ACID is selected for a nonflammable, nontoxic acid/caustic that still presents personnel contact hazard. It does not determine chemistry, concentration, toxicity, flammability or splash hazard from plant data.

## `api581.api.properties.mixture_representative_fluid`

Annex 3.A mole-weighted representative-fluid selection

계산 ID: `properties/mixture-representative-fluid`

출처: Part 3 Annex A §3.1.2.1, §3.1.2.3-§3.1.2.4, eq (3.A.1); PDF pp614-615

| 입력 | 필수 | 타입 |
|---|---|---|
| `components` | 예 | `list[api581.representative_fluids.MixturePropertyComponent]` |

출력: `molecular_weight_kg_kmol`, `normal_boiling_point_k`, `liquid_density_kg_m3`, `autoignition_temperature_k`, `selected_fluid`, `relevant_mole_fraction`, `selection_basis`, `level2_recommended`

적용 범위: Uses Table 4.2M properties and mole-fraction weighting for MW, NBP, density and AIT. Inert/non-consequence-relevant components are excluded as the printed conservative Level 1 rule directs. Hydrocarbon pseudo-components are selected only from the hydrocarbon rows; selection then prioritizes the highest candidate NBP that does not exceed the weighted NBP. Chemistry outside the table remains Level 2 recommended and is not silently mapped.

## `api581.api.properties.representative_fluid`

API 581 Table 4.2M representative-fluid properties

계산 ID: `properties/representative-fluid`

출처: Part 3 §4.1.1-§4.1.2, Table 4.2/Table 4.2M; PDF pp515-517

| 입력 | 필수 | 타입 |
|---|---|---|
| `fluid` | 예 | `typing.Literal['C1-C2', 'C3-C4', 'C5', 'C6-C8', 'C9-C12', 'C13-C16', 'C17-C25', 'C25+', 'Water', 'Steam', 'Acid', 'H2', 'H2S', 'HF', 'CO', 'DEE', 'HCL', 'Nitric Acid', 'ALCL3', 'NO2', 'Phosgene', 'TDI', 'Methanol', 'PO', 'Styrene', 'EEA', 'EE', 'EG', 'EO', 'Pyrophoric']` |
| `temperature_k` | 예 | `<class 'float'>` |

출력: `fluid`, `molecular_weight_kg_kmol`, `liquid_density_kg_m3`, `normal_boiling_point_k`, `ambient_state`, `cp_note`, `cp_value_table_units`, `cp_basis`, `autoignition_temperature_k`, `source_table`

적용 범위: Returns tabulated representative properties, not a real-fluid property package. Cp note 1 and note 3 are evaluated as printed polynomials; note 2 uses Cp=A+B((C/T)/sinh(C/T))²+D((E/T)/cosh(E/T))². Rows with --- have no tabulated Cp or AIT. Ambient-state and phase-selection rules remain a separate Table 4.3 decision.

## `api581.api.damage.measured_corrosion_rate`

Measured thickness-loss corrosion rate

계산 ID: `damage/measured-corrosion-rate`

출처: Part 2 Annex B §1.1-§1.2; Part 2 §4.5.5, PDF pp143-152

| 입력 | 필수 | 타입 |
|---|---|---|
| `initial_thickness_m` | 예 | `<class 'float'>` |
| `current_thickness_m` | 예 | `<class 'float'>` |
| `elapsed_years` | 예 | `<class 'float'>` |
| `measurement_basis` | 예 | `<class 'str'>` |

출력: `metal_loss_m`, `corrosion_rate_m_year`, `initial_thickness_m`, `current_thickness_m`, `elapsed_years`, `measurement_basis`, `rate_basis`

적용 범위: Computes the direct constant-rate interpretation (initial thickness minus current thickness divided by elapsed time). It does not select inspection history, uncertainty distributions, mechanism applicability or a future thinning rate. Thickness increase is rejected as a measurement/baseline inconsistency rather than silently converted to zero corrosion. The caller must qualify comparable locations, units, dates and measurement quality.

## `api581.api.damage.thinning_type`

API 581 Annex 2.B.1.2 general versus localized thinning designation

계산 ID: `damage/thinning-type`

출처: Part 2 Annex B §1.2; Part 2 §4.5.2, PDF p321

| 입력 | 필수 | 타입 |
|---|---|---|
| `effective_inspection_types` | 기본값/선택 | `list[typing.Literal['general', 'localized']]` |
| `applicable_mechanism_types` | 예 | `list[typing.Literal['general', 'localized']]` |
| `qualification_basis` | 예 | `<class 'str'>` |

출력: `thinning_type`, `selection_source`, `effective_inspection_types`, `applicable_mechanism_types`, `qualification_basis`

적용 범위: Effective inspection designation takes precedence. If no effective inspection type is supplied, any applicable localized mechanism conservatively selects localized thinning. This API does not screen mechanisms or calculate corrosion rates. The caller must qualify the mechanism list and inspection effectiveness; an empty inspection list is treated as unknown, not as evidence of general thinning.
