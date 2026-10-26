"""Generated typed output models. Rebuild with scripts/build_python_api.py."""
from typing import Any, Literal
from .core import Model, NonNegative, Fraction

class FrequencyGenericOutput(Model):
    by_hole_per_year: dict[str, NonNegative]
    total_per_year: NonNegative


class FrequencyManagementFactorOutput(Model):
    score_percent: NonNegative
    management_factor: NonNegative


class FrequencyAdjustedOutput(Model):
    annual_failure_frequency: NonNegative
    unit: Literal['1/year']


class FrequencyPofMethodSelectionOutput(Model):
    method: Literal['structural_reliability', 'statistical_generic_data', 'expert_judgment', 'combined']
    qualification_basis: str
    uncertainty_quantified: bool
    numeric_pof_route: Literal['gff_df_fms', 'external_method_result']


class DamageCombineOutput(Model):
    governing_thinning: NonNegative
    governing_external: NonNegative
    governing_scc: NonNegative
    governing_brittle: NonNegative
    total_damage_factor: NonNegative


class DamageMeasuredCorrosionRateOutput(Model):
    metal_loss_m: NonNegative
    corrosion_rate_m_year: NonNegative
    initial_thickness_m: NonNegative
    current_thickness_m: NonNegative
    elapsed_years: NonNegative
    measurement_basis: str
    rate_basis: str


class DamageThinningTypeOutput(Model):
    thinning_type: Literal['general', 'localized']
    selection_source: Literal['effective_inspection_results', 'applicable_mechanism_conservative_default']
    effective_inspection_types: list[str]
    applicable_mechanism_types: list[str]
    qualification_basis: str


class InspectionEquivalentOutput(Model):
    a: int
    b: int
    c: int
    d: int


class InspectionEffectivenessCategoryOutput(Model):
    category: Literal['A', 'B', 'C', 'D', 'E']
    ordinal: int
    label: str
    inspection_credit_allowed: bool
    owner_user_basis: str


class InspectionEffectivenessSummaryOutput(Model):
    mechanism: Literal['scc', 'external_clscc', 'cui_clscc', 'htha']
    highest_effectiveness_category: Literal['A', 'B', 'C', 'D', 'E']
    inspection_count: int
    creditable_inspection_count: int
    counts: dict[str, int]
    equivalent_counts: dict[str, int]
    e_inspection_count: int
    qualification_status: str


class InspectionThinningEffectivenessOutput(Model):
    effectiveness_category: Literal['A', 'B', 'C', 'D', 'E']
    damage_type: Literal['general', 'local']
    inspection_mode: Literal['intrusive', 'non_intrusive']
    qualification_status: Literal['qualified', 'failed']
    basis: str


class InspectionSccEffectivenessOutput(Model):
    effectiveness_category: Literal['A', 'B', 'C', 'D', 'E']
    mechanism_family: Literal['weld_scc', 'clscc_pta']
    inspection_mode: Literal['intrusive', 'non_intrusive']
    qualification_status: Literal['qualified', 'failed']
    basis: str


class InspectionExternalEffectivenessOutput(Model):
    effectiveness_category: Literal['A', 'B', 'C', 'D', 'E']
    mechanism_family: Literal['external_corrosion', 'external_clscc', 'cui', 'cui_clscc']
    insulation_status: Literal['not_applicable', 'removed', 'not_removed']
    qualification_status: Literal['qualified', 'failed']
    basis: str


class InspectionBuriedEffectivenessOutput(Model):
    effectiveness_category: Literal['A', 'B', 'C', 'D', 'E']
    inspection_mode: Literal['intrusive', 'non_intrusive']
    qualification_status: Literal['qualified', 'failed']
    basis: str


class InspectionPrdEffectivenessOutput(Model):
    effectiveness_category: Literal['A', 'B', 'C', 'D', 'E']
    component_type: Literal['pressure_relief_device', 'rupture_disk']
    qualification_status: Literal['qualified', 'failed']
    basis: str


class InspectionLiningEffectivenessOutput(Model):
    effectiveness_category: Literal['A', 'B', 'C', 'D', 'E']
    inspection_mode: Literal['intrusive', 'non_intrusive']
    qualification_status: Literal['qualified', 'failed']
    basis: str


class InspectionTubeBundleUncertaintyOutput(Model):
    inspection_effectiveness: Literal['A', 'B', 'C', 'D', 'E']
    uncertainty_percent: float
    uncertainty_fraction: Fraction
    baseline_no_history_percent: float
    owner_user_basis: str


class InspectionAstEffectivenessOutput(Model):
    effectiveness_category: Literal['A', 'B', 'C', 'D', 'E']
    component_type: Literal['shell_internal', 'shell_external', 'tank_bottom']
    inspection_side: Literal['internal', 'external', 'soil_side', 'product_side']
    qualification_status: Literal['qualified', 'failed']
    basis: str


class ReliabilityWeibullOutput(Model):
    cumulative_failure_probability: Fraction
    survival_probability: Fraction
    hazard_per_year: NonNegative | None
    hazard_singular_at_origin: bool


class ReliabilityWeibullQuantileOutput(Model):
    age_years: NonNegative


class ReliabilityWeibullFromMttfOutput(Model):
    characteristic_life_years: NonNegative


class ReliabilityPoissonProbabilityOutput(Model):
    period_failure_probability: Fraction


class ReleaseOrificeAreaOutput(Model):
    area_m2: NonNegative


class ReleaseViscosityFactorOutput(Model):
    viscosity_factor: NonNegative


class ReleaseLiquidOutput(Model):
    mass_rate_kg_s: NonNegative
    area_m2: NonNegative
    regime: Literal['liquid']


class ReleaseGasOutput(Model):
    mass_rate_kg_s: NonNegative
    area_m2: NonNegative
    regime: Literal['sonic', 'subsonic']
    critical_downstream_upstream_ratio: Fraction
    transition_pressure_pa_abs: NonNegative


class Api520CriticalPressureRatioOutput(Model):
    critical_pressure_ratio: Fraction


class Api520FlowCoefficientCOutput(Model):
    flow_coefficient_c: NonNegative


class Api520RelievingPressureOutput(Model):
    relieving_pressure_psig: NonNegative
    relieving_pressure_kpaa: NonNegative


class Api520GasCriticalAreaOutput(Model):
    required_area_mm2: NonNegative


class Api520GasSubcriticalAreaOutput(Model):
    required_area_mm2: NonNegative
    back_pressure_ratio: Fraction
    subcritical_flow_factor: NonNegative


class Api520LiquidAreaOutput(Model):
    required_area_mm2: NonNegative


class Api520LiquidViscosityFactorOutput(Model):
    viscosity_factor: NonNegative


class Api520GasCriticalCapacityOutput(Model):
    mass_capacity_kg_h: NonNegative


class Api520GasSubcriticalCapacityOutput(Model):
    mass_capacity_kg_h: NonNegative
    back_pressure_ratio: Fraction
    subcritical_flow_factor: NonNegative


class Api520LiquidCapacityOutput(Model):
    flow_capacity_l_min: NonNegative


class PropertiesHeatCapacityRatioOutput(Model):
    heat_capacity_ratio: NonNegative


class PropertiesRepresentativeFluidOutput(Model):
    fluid: str
    molecular_weight_kg_kmol: NonNegative
    liquid_density_kg_m3: NonNegative
    normal_boiling_point_k: float
    ambient_state: str
    cp_note: int | None
    cp_value_table_units: float | None
    cp_basis: str
    autoignition_temperature_k: float | None
    source_table: str


class PropertiesAcidCausticRepresentativeFluidOutput(Model):
    selection: Literal['acid_reference', 'not_applicable']
    representative_fluid: str | None
    release_phase: Literal['liquid'] | None
    consequence_model: Literal['acid_splash'] | None
    selection_basis: str


class PropertiesMixtureRepresentativeFluidOutput(Model):
    molecular_weight_kg_kmol: NonNegative
    normal_boiling_point_k: float
    liquid_density_kg_m3: NonNegative
    autoignition_temperature_k: float
    selected_fluid: str
    relevant_mole_fraction: Fraction
    selection_basis: str
    level2_recommended: bool


class ReleaseAvailableInventoryOutput(Model):
    added_mass_kg: NonNegative
    available_mass_kg: NonNegative


class ReleaseTypeOutput(Model):
    release_type: Literal['continuous', 'instantaneous']
    time_to_4536kg_s: NonNegative | None


class ReleaseMagnitudeOutput(Model):
    adjusted_rate_kg_s: NonNegative
    duration_s: NonNegative
    released_mass_kg: NonNegative


class ReleaseDetectionIsolationOutput(Model):
    release_reduction_fraction: Fraction
    adjusted_rate_kg_s: NonNegative
    maximum_leak_duration_s: NonNegative | None
    duration_s: NonNegative | None
    released_mass_kg: NonNegative
    detection_rating: Literal['A', 'B', 'C']
    isolation_rating: Literal['A', 'B', 'C']
    hole_size: Literal['small', 'medium', 'large', 'rupture']


class ReleaseDetectionIsolationRatingOutput(Model):
    detection_rating: Literal['A', 'B', 'C']
    isolation_rating: Literal['A', 'B', 'C']
    detection_type: str
    isolation_type: str
    qualification_basis: str


class ReleaseHoleSizeSelectionOutput(Model):
    selected_hole: Literal['small', 'medium', 'large', 'rupture']
    representative_diameter_m: NonNegative
    lower_bound_m: NonNegative
    upper_bound_m: NonNegative | None
    diameter_basis: str
    source_table: str


class ReleaseIntegrateProfileOutput(Model):
    released_mass_kg: NonNegative
    duration_s: NonNegative


class PropertiesMixtureMolecularWeightOutput(Model):
    molecular_weight_kg_kmol: NonNegative
    mass_fractions: list[Fraction]


class EffectsJetFirePowerOutput(Model):
    radiated_power_w: NonNegative


class EffectsJetFireFluxOutput(Model):
    received_flux_w_m2: NonNegative


class EffectsJetFireDistanceOutput(Model):
    threshold_distance_m: NonNegative
    consequence_area_m2: NonNegative
    transmissivity_at_distance: Fraction | None


class EffectsFlashFireOutput(Model):
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative


class EffectsPoolFireAreaOutput(Model):
    burning_area_m2: NonNegative
    inventory_limited_area_m2: NonNegative
    pool_area_m2: NonNegative
    pool_radius_m: NonNegative


class ConsequencePowerLawAreaOutput(Model):
    area_m2: NonNegative
    coefficient_source: str


class EventsLeakageTreeOutput(Model):
    terminal_probabilities: dict[str, Fraction]
    probability_sum: NonNegative


class EffectsToxicProbitOutput(Model):
    probit: float | None
    effect_probability: Fraction


class EffectsPoolBurningRateOutput(Model):
    burning_rate_kg_m2_s: NonNegative


class EffectsFireballGeometryOutput(Model):
    diameter_m: NonNegative
    center_height_m: NonNegative
    duration_s: NonNegative


class EffectsFireballRadiativeFractionOutput(Model):
    radiative_fraction: Fraction


class EffectsFireballEmissivePowerOutput(Model):
    surface_emissive_power_w_m2: NonNegative


class EffectsVceTntEquivalenceOutput(Model):
    tnt_equivalent_mass_kg: NonNegative


class ConsequenceExpectedOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    financial_consequence: NonNegative
    currency: str


class RiskAggregateOutput(Model):
    annual_failure_frequency: NonNegative
    equipment_area_risk_m2_per_year: NonNegative
    personnel_area_risk_m2_per_year: NonNegative
    area_risk_m2_per_year: NonNegative
    financial_risk_per_year: NonNegative
    currency: str
    frequency_weighted_equipment_area_m2: NonNegative | None
    frequency_weighted_personnel_area_m2: NonNegative | None


class RiskPortfolioOutput(Model):
    component_count: int
    annual_failure_frequency: NonNegative
    equipment_area_risk_m2_per_year: NonNegative
    personnel_area_risk_m2_per_year: NonNegative
    area_risk_m2_per_year: NonNegative
    financial_risk_per_year: NonNegative
    currency: str
    disjointness_basis: str
    component_contributions: dict[str, dict[str, NonNegative]]


class ConsequenceFinancialTotalOutput(Model):
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int


class RiskMatrixOutput(Model):
    frequency_category: int
    consequence_category: int
    risk_label: str
    policy_id: str


class DamageThinningWallLossOutput(Model):
    wall_loss_fraction: NonNegative


class DamageFlowStressOutput(Model):
    flow_stress_pa: NonNegative


class DamageThinningStrengthRatioOutput(Model):
    strength_ratio: NonNegative


class DamageThinningPosteriorOutput(Model):
    posterior_probabilities: list[Fraction]


class DamageThinningBaseOutput(Model):
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative


class DamageThinningAdjustOutput(Model):
    thinning_damage_factor: NonNegative


class DamageSccBaseOutput(Model):
    base_damage_factor: NonNegative


class DamageCausticSeverityOutput(Model):
    severity_index: int


class DamageCausticEscalationOutput(Model):
    damage_factor: NonNegative


class DamageLiningAdjustOutput(Model):
    condition_factor: NonNegative
    monitoring_factor: NonNegative
    lining_damage_factor: NonNegative


class DamageThinningUncladOutput(Model):
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative


class Level1FlammableCoefficientsOutput(Model):
    a: NonNegative
    b: NonNegative
    magnitude_unit: str
    area_unit: str


class ReleaseDetectionReductionOutput(Model):
    reduction_fraction: Fraction


class ReleaseDetectionDurationOutput(Model):
    maximum_duration_s: NonNegative


class Level1ReleasePhaseOutput(Model):
    release_phase: Literal['gas', 'liquid']


class Level1EnergyEfficiencyOutput(Model):
    energy_efficiency_factor: NonNegative


class Level1BlendingFactorsOutput(Model):
    instantaneous_weight: Fraction
    autoignition_likely_weight: Fraction


class Level1FlammableAreaOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    instantaneous_weight: Fraction
    autoignition_likely_weight: Fraction
    energy_efficiency_factor: NonNegative


class Level1ReleaseToFlammableOutput(Model):
    theoretical_rate_kg_s: NonNegative
    available_mass_kg: NonNegative
    release_type: Literal['continuous', 'instantaneous']
    reduction_fraction: Fraction
    maximum_duration_s: NonNegative
    adjusted_rate_kg_s: NonNegative
    duration_s: NonNegative
    released_mass_kg: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    instantaneous_weight: Fraction
    autoignition_likely_weight: Fraction
    energy_efficiency_factor: NonNegative


class Level1MitigationOutput(Model):
    mitigation_fraction: Fraction


class Level1ToxicSourceOutput(Model):
    toxic_rate_kg_s: NonNegative
    toxic_mass_kg: NonNegative


class Level1ToxicDurationOutput(Model):
    duration_s: NonNegative


class Level1ToxicAreaOutput(Model):
    unweighted_personnel_area_m2: NonNegative
    personnel_area_m2: NonNegative


class Level1SteamAreaOutput(Model):
    continuous_area_m2: NonNegative
    instantaneous_area_m2: NonNegative
    instantaneous_weight: Fraction
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative


class Level1AcidCausticAreaOutput(Model):
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    coefficient_g: NonNegative
    exponent_h: NonNegative


class ConsequenceFinalAreaOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    consequence_area_m2: NonNegative


class ConsequenceHoleWeightedOutput(Model):
    weighted_value: NonNegative
    value_unit: str


class FinancialSurroundingDamageOutput(Model):
    cost: NonNegative
    currency: str


class FinancialProductionLossOutput(Model):
    cost: NonNegative
    currency: str


class FinancialInjuryOutput(Model):
    cost: NonNegative
    currency: str


class FinancialSpillCleanupOutput(Model):
    remediation_volume_m3: NonNegative
    cost: NonNegative
    currency: str


class Level1ConsequenceSummaryOutput(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_area_m2: NonNegative
    nfnt_personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    consequence_area_m2: NonNegative
    generic_frequency_per_year: NonNegative


class FinancialRepairTableOutput(Model):
    cost_by_hole_usd_2001: dict[str, NonNegative]
    cost_basis_year: int
    currency: str


class FinancialMaterialFactorOutput(Model):
    material_factor: NonNegative


class FinancialOutageTableOutput(Model):
    days_by_hole: dict[str, NonNegative | None]


class FinancialComponentRepairOutput(Model):
    weighted_repair_cost_usd_2001: NonNegative
    cost: NonNegative
    material_factor: NonNegative
    cost_basis_year: int
    currency: str


class FinancialComponentOutageOutput(Model):
    component_outage_days: NonNegative
    effective_days_by_hole: dict[str, NonNegative | None]


class FinancialSurroundingOutageOutput(Model):
    surrounding_outage_days: NonNegative


class PropertiesLeakTableOutput(Model):
    molecular_weight_kg_kmol: NonNegative
    tabulated_liquid_density_kg_m3: NonNegative
    normal_boiling_point_k: NonNegative
    evaporated_fraction_24h: Fraction


class FinancialCleanupEligibilityOutput(Model):
    include_cleanup_cost: bool


class FinancialHoleTotalOutput(Model):
    currency: str
    cost_basis_year: int
    total_generic_frequency_per_year: NonNegative
    per_hole: list[dict[str, NonNegative | str]]
    frequency_weighted_financial_consequence: NonNegative
    annual_financial_risk: NonNegative


class FinancialLevel1ConsequenceOutput(Model):
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int


class DamageSccSeverityOutput(Model):
    severity_index: int


class DamageHicMonitoringFactorOutput(Model):
    monitoring_factor: NonNegative


class DamageCausticOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageAmineOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageSscOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageHicSohicH2sOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageAcsccOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamagePasccOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageClsccOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageHscHfOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageHicSohicHfOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageHscHfSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']


class DamageSscSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']


class DamageHicHfSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']


class DamageHicH2sSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']


class DamageClsccSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']


class DamageAcsccSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']


class DamagePasccSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']


class DamageWetH2sEnvironmentOutput(Model):
    environmental_severity: Literal['low', 'moderate', 'high']
    susceptibility_upgrade_required: bool


class DamageExternalBaseRateOutput(Model):
    base_corrosion_rate_m_year: NonNegative


class DamageCuiBaseRateOutput(Model):
    base_corrosion_rate_m_year: NonNegative


class DamageExternalTimeWeightedRateOutput(Model):
    base_corrosion_rate_m_year: NonNegative
    period_rates_m_year: list[NonNegative]


class DamageExternalRateAdjustOutput(Model):
    design_interface_factor: NonNegative
    corrosion_rate_m_year: NonNegative


class DamageCuiRateAdjustOutput(Model):
    design_interface_factor: NonNegative
    corrosion_rate_m_year: NonNegative
    insulation_factor: NonNegative
    complexity_factor: NonNegative
    condition_factor: NonNegative


class DamageCoatingExposureOutput(Model):
    coating_credit_years: NonNegative
    corrosion_exposure_years: NonNegative


class DamageExternalCorrosionOutput(Model):
    corrosion_rate_m_year: NonNegative
    coating_credit_years: NonNegative
    corrosion_exposure_years: NonNegative
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    weighted_failure_probability: NonNegative
    damage_factor: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]


class DamageCuiOutput(Model):
    corrosion_rate_m_year: NonNegative
    coating_credit_years: NonNegative
    corrosion_exposure_years: NonNegative
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    weighted_failure_probability: NonNegative
    damage_factor: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]


class DamageExternalClsccBaseSusceptibilityOutput(Model):
    base_susceptibility: Literal['none', 'low', 'medium', 'high']


class DamageExternalClsccOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    coating_credit_years: NonNegative
    cracking_exposure_years: NonNegative
    damage_factor: NonNegative


class DamageCuiClsccOutput(Model):
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    coating_credit_years: NonNegative
    cracking_exposure_years: NonNegative
    damage_factor: NonNegative


class DamageFatigueBaseOutput(Model):
    previous_failure_factor: NonNegative
    shaking_factor: NonNegative
    shaking_duration_factor: NonNegative
    cyclic_loading_factor: NonNegative
    base_damage_factor: NonNegative


class DamageFatigueAdjustmentsOutput(Model):
    corrective_action_factor: NonNegative
    complexity_factor: NonNegative
    pipe_condition_factor: NonNegative
    joint_branch_factor: NonNegative
    branch_diameter_factor: NonNegative
    combined_adjustment_factor: NonNegative


class DamageMechanicalFatigueOutput(Model):
    previous_failure_factor: NonNegative
    shaking_factor: NonNegative
    shaking_duration_factor: NonNegative
    cyclic_loading_factor: NonNegative
    base_damage_factor: NonNegative
    corrective_action_factor: NonNegative
    complexity_factor: NonNegative
    pipe_condition_factor: NonNegative
    joint_branch_factor: NonNegative
    branch_diameter_factor: NonNegative
    combined_adjustment_factor: NonNegative
    damage_factor: NonNegative


class PropertiesHydrogenPartialPressureOutput(Model):
    hydrogen_partial_pressure_pa_abs: NonNegative


class DamageHthaFactorOutput(Model):
    damage_factor: NonNegative


class DamageHthaCarbonScreenOutput(Model):
    susceptibility: str
    damage_factor: NonNegative


class DamageBrittleReferenceTemperatureOutput(Model):
    reference_temperature_k: NonNegative
    table_basis: str


class DamageBrittleServiceFactorOutput(Model):
    service_experience_factor: NonNegative
    thin_component_credit: bool
    service_criteria: dict[str, bool]


class DamageBrittleBaseOutput(Model):
    base_damage_factor: NonNegative
    table: Literal['20.4M', '20.5M']


class DamageBrittleFractureOutput(Model):
    reference_temperature_k: NonNegative
    table_basis: str
    service_experience_factor: NonNegative
    thin_component_credit: bool
    service_criteria: dict[str, bool]
    base_damage_factor: NonNegative
    table: Literal['20.4M', '20.5M']
    cet_minus_reference_k: float
    damage_factor: NonNegative


class DamageEmbrittlement885fOutput(Model):
    reference_temperature_k: NonNegative
    minimum_minus_reference_k: float
    damage_factor: NonNegative


class DamageSigmaContentOutput(Model):
    sigma_category: Literal['low', 'medium', 'high']


class DamageSigmaEmbrittlementOutput(Model):
    damage_factor: NonNegative
    sigma_category: Literal['low', 'medium', 'high']


class DamageTemperJFactorOutput(Model):
    j_factor: NonNegative


class DamageTemperXbarOutput(Model):
    xbar_factor: NonNegative


class DamageTemperXbarShiftOutput(Model):
    delta_fatt_k: NonNegative


class DamageTemperGenerationShiftOutput(Model):
    generation: int
    delta_fatt_k: NonNegative
    source_basis: Literal['printed_C', 'printed_F_difference_converted']


class DamageTemperEmbrittlementOutput(Model):
    reference_temperature_k: NonNegative
    table_basis: str
    shifted_reference_temperature_k: NonNegative
    minimum_minus_shifted_reference_k: float
    delta_fatt_k: NonNegative
    damage_factor: NonNegative
    table: Literal['20.4M', '20.5M']


class BundleWeibayesHistoryOutput(Model):
    shape: NonNegative
    characteristic_life_years: NonNegative
    failure_count: int
    record_count: int


class BundleConditionUpdateOutput(Model):
    shape: NonNegative
    characteristic_life_years: NonNegative
    failure_count: int
    record_count: int


class BundleThicknessLifeOutput(Model):
    thinning_rate_m_year: NonNegative
    predicted_bundle_life_years: NonNegative | None
    remaining_life_years: NonNegative | None
    remaining_wall_threshold_reached: bool
    formula_basis: Literal['printed_eq_1_72', 'remaining_wall_threshold']


class BundleEstimatedLifeOutput(Model):
    predicted_bundle_life_years: NonNegative


class BundleLifeExtensionOutput(Model):
    adjusted_age_at_action_years: NonNegative
    effective_age_years: NonNegative
    installation_shift_years: NonNegative


class BundleConsequenceOutput(Model):
    production_loss_cost: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int


class BundleRiskOutput(Model):
    cumulative_failure_probability: Fraction
    probability_weighted_consequence: NonNegative
    currency: str


class BundleTargetAgeOutput(Model):
    target_failure_probability: Fraction
    target_age_years: NonNegative | None
    status: Literal['finite_crossing', 'no_finite_crossing']


class BundleDeferralDecisionOutput(Model):
    conditional_failure_probability: Fraction
    expected_incremental_risk: NonNegative
    inspection_hurdle_cost: NonNegative
    replacement_hurdle_cost: NonNegative
    inspection_economically_justified: bool
    replacement_economically_justified: bool
    currency: str


class BundleReplacementOptimizationOutput(Model):
    optimal_grid_age_years: NonNegative
    minimum_cost_per_day: NonNegative
    minimum_at_grid_boundary: bool
    grid_points: int
    samples: list[dict[str, NonNegative]]
    currency: str


class PrdDefaultWeibullOutput(Model):
    shape: NonNegative
    default_characteristic_life_years: NonNegative
    design_factor: NonNegative
    design_adjusted_characteristic_life_years: NonNegative


class PrdEnvironmentFactorOutput(Model):
    environment_factor: Fraction
    individual_factors: dict[str, Fraction]


class PrdSetPressureFactorOutput(Model):
    set_pressure_factor: Fraction


class PrdOverpressureFactorOutput(Model):
    overpressure_factor: Fraction


class PrdDemandRateOutput(Model):
    case_demand_rates_per_year: list[NonNegative]
    total_demand_rate_per_year: NonNegative


class PrdInspectionUpdateOutput(Model):
    prior_failure_probability: Fraction
    conditional_failure_probability: Fraction | None
    weighted_failure_probability: Fraction
    updated_characteristic_life_years: NonNegative
    update_applied: bool
    effective_failed_result: bool


class PrdProtectedEquipmentOutput(Model):
    normal_failure_frequency_per_year: NonNegative
    source_model_loc_probability: Fraction
    by_hole_loc_probability: dict[str, Fraction]


class PrdFailFrequencyOutput(Model):
    annual_failure_frequency: NonNegative


class PrdBaseReliabilityOutput(Model):
    shape: NonNegative
    modified_characteristic_life_years: NonNegative
    environment_factor: Fraction
    scenario_probability_factor: Fraction
    unadjusted_cumulative_probability: Fraction
    scenario_adjusted_probability: Fraction


class BundleMaterialFactorOutput(Model):
    material_factor: NonNegative


class BundleReplacementCostOutput(Model):
    bundle_volume_m3: NonNegative
    reference_basis_cost_usd: NonNegative
    replacement_cost: NonNegative
    currency: str
    cost_basis_year: int


class BundleLifeExtensionFactorOutput(Model):
    life_extension_factor: Fraction


class BundleCategoriesOutput(Model):
    probability_category: int
    consequence_category: Literal['A', 'B', 'C', 'D', 'E']


class PrdLeakageRatesOutput(Model):
    minor_rate_kg_s: NonNegative
    moderate_table_rate_kg_s: NonNegative
    mild_moderate_equation_rate_kg_s: NonNegative
    stuck_open_rate_kg_s: NonNegative


class PrdLeakageDurationOutput(Model):
    mild_moderate_duration_s: NonNegative
    stuck_open_duration_s: NonNegative


class PrdInventoryLossFactorOutput(Model):
    inventory_loss_factor: Fraction


class PrdInventoryLossOutput(Model):
    leaked_mass_kg: NonNegative
    inventory_loss_equivalent_mass_kg: NonNegative
    inventory_loss_cost: NonNegative
    currency: str
    cost_basis_year: int


class PrdRepairCostOutput(Model):
    reference_cost_usd: NonNegative
    repair_cost: NonNegative
    currency: str
    cost_basis_year: int


class PrdProductionLossOutput(Model):
    production_loss_cost: NonNegative
    shutdown_loss_applied: bool
    currency: str
    cost_basis_year: int


class PrdLeakageConsequenceOutput(Model):
    financial_consequence: NonNegative
    case_weights: dict[str, Fraction]
    costs_by_case: dict[str, dict[str, NonNegative]]
    inventory_loss_factor: Fraction
    model_basis: Literal['two_case_equations', 'three_case_table_7_15']
    currency: str
    cost_basis_year: int


class PrdMultipleDevicePressureOutput(Model):
    multiple_device_factor: Fraction
    protected_equipment_pressure_pa_gauge: NonNegative
    unreduced_pressure_for_fop_pa_gauge: NonNegative


class PrdFailRiskOutput(Model):
    protected_equipment_risks_per_year: dict[str, NonNegative]
    maximum_fail_risk_per_year: NonNegative
    governing_equipment_ids: list[str]
    currency: str
    cost_basis_year: int


class PrdLeakageRiskOutput(Model):
    leakage_risk_value: NonNegative
    measure_basis: Literal['annual_frequency', 'source_cumulative_probability']
    risk_unit: Literal['currency', 'currency/year']
    currency: str
    cost_basis_year: int


class PrdTotalRiskOutput(Model):
    annual_financial_risk: NonNegative | None
    source_total_risk_index: NonNegative | None
    leakage_measure_basis: Literal['annual_frequency', 'source_cumulative_probability']
    currency: str
    cost_basis_year: int


class PrdRiskAssessmentOutput(Model):
    protected_equipment_risks_per_year: dict[str, NonNegative]
    maximum_fail_risk_per_year: NonNegative
    governing_equipment_ids: list[str]
    currency: str
    cost_basis_year: int
    annual_financial_risk: NonNegative | None
    source_total_risk_index: NonNegative | None
    leakage_measure_basis: Literal['annual_frequency', 'source_cumulative_probability']
    leakage_risk_value: NonNegative
    leakage_risk_unit: Literal['currency', 'currency/year']


class PrdServiceAgeOutput(Model):
    effective_age_years: NonNegative
    elapsed_since_original_installation_years: NonNegative
    last_age_reset_date: str
    last_age_reset_type: Literal['installation', 'overhaul', 'replacement']
    parameter_history_valid_from_date: str
    inspection_update_start_date: str
    last_test_date: str | None
    days_per_year: NonNegative


class ReleaseControlledScenarioOutput(Model):
    theoretical_rate_kg_s: NonNegative
    available_mass_kg: NonNegative
    release_type: Literal['continuous', 'instantaneous']
    reduction_fraction: Fraction
    maximum_duration_s: NonNegative
    adjusted_rate_kg_s: NonNegative
    duration_s: NonNegative
    released_mass_kg: NonNegative


class Level1Type1FlammableAreaOutput(Model):
    area_m2: NonNegative
    coefficient_a: NonNegative
    coefficient_b: NonNegative
    energy_efficiency_factor: NonNegative


class Level1Type1FlammableConsequenceOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    energy_efficiency_factor: NonNegative
    fluid_type: Literal[1]


class Level1ReleaseToType1FlammableOutput(Model):
    theoretical_rate_kg_s: NonNegative
    available_mass_kg: NonNegative
    release_type: Literal['continuous', 'instantaneous']
    reduction_fraction: Fraction
    maximum_duration_s: NonNegative
    adjusted_rate_kg_s: NonNegative
    duration_s: NonNegative
    released_mass_kg: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    energy_efficiency_factor: NonNegative
    fluid_type: Literal[1]


class Level1ReleaseToAcidOutput(Model):
    theoretical_rate_kg_s: NonNegative
    available_mass_kg: NonNegative
    release_type: Literal['continuous', 'instantaneous']
    reduction_fraction: Fraction
    maximum_duration_s: NonNegative
    adjusted_rate_kg_s: NonNegative
    duration_s: NonNegative
    released_mass_kg: NonNegative
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    coefficient_g: NonNegative
    exponent_h: NonNegative
    representative_fluid: Literal['Acid']
    release_phase: Literal['liquid']


class Level1ReleaseToSteamOutput(Model):
    theoretical_rate_kg_s: NonNegative
    available_mass_kg: NonNegative
    release_type: Literal['continuous', 'instantaneous']
    reduction_fraction: Fraction
    maximum_duration_s: NonNegative
    adjusted_rate_kg_s: NonNegative
    duration_s: NonNegative
    released_mass_kg: NonNegative
    continuous_area_m2: NonNegative
    instantaneous_area_m2: NonNegative
    instantaneous_weight: Fraction
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    representative_fluid: Literal['Steam']
    release_phase: Literal['gas']


class Level1HfH2sToxicCoefficientsOutput(Model):
    c: NonNegative
    d: float
    native_magnitude_unit: Literal['lb/s', 'lb']
    native_area_unit: Literal['ft2']
    si_mass_multiplier: NonNegative
    si_area_multiplier: NonNegative
    source_cell_status: Literal['clear', 'ambiguous_print', 'qualified_override']


class Level1HfH2sToxicAreaOutput(Model):
    unweighted_personnel_area_m2: NonNegative
    personnel_area_m2: NonNegative


class Level1MiscToxicCoefficientsOutput(Model):
    e: NonNegative
    f: NonNegative
    native_rate_unit: Literal['kg/s']
    native_area_unit: Literal['m2']
    si_mass_multiplier: NonNegative
    si_area_multiplier: NonNegative


class Level1MiscToxicAreaOutput(Model):
    unweighted_personnel_area_m2: NonNegative
    personnel_area_m2: NonNegative


class Level1ToxicCutoffOutput(Model):
    idlh_ppm: NonNegative
    requires_toxic_evaluation: bool


class Level1ToxicMitigationOutput(Model):
    toxic_rate_kg_s: NonNegative
    toxic_mass_kg: NonNegative
    duration_s: NonNegative


class Level1ToxicComponentConsequenceOutput(Model):
    toxic_rate_kg_s: NonNegative
    toxic_mass_kg: NonNegative
    duration_s: NonNegative
    unweighted_personnel_area_m2: NonNegative
    personnel_area_m2: NonNegative
    unmitigated_duration_s: NonNegative
    screening_applied: bool
    requires_toxic_evaluation: bool


class Level1ReleaseToToxicOutput(Model):
    theoretical_rate_kg_s: NonNegative
    available_mass_kg: NonNegative
    release_type: Literal['continuous', 'instantaneous']
    reduction_fraction: Fraction
    maximum_duration_s: NonNegative
    adjusted_rate_kg_s: NonNegative
    duration_s: NonNegative
    released_mass_kg: NonNegative
    toxic_rate_kg_s: NonNegative
    toxic_mass_kg: NonNegative
    unweighted_personnel_area_m2: NonNegative
    personnel_area_m2: NonNegative
    unmitigated_duration_s: NonNegative
    screening_applied: bool
    requires_toxic_evaluation: bool


class Level1ToxicMixtureConsequenceOutput(Model):
    personnel_area_m2: NonNegative
    critical_component_id: str
    component_areas_m2: dict[str, NonNegative]
    component_count: int


class Level1ToxicHoleSummaryOutput(Model):
    personnel_area_m2: NonNegative
    total_generic_frequency_per_year: NonNegative
    by_hole_personnel_area_m2: dict[str, NonNegative]


class PropertiesWaterPartialPressureOutput(Model):
    water_partial_pressure_pa: NonNegative


class EffectsAtmosphericTransmissivityOutput(Model):
    transmissivity: Fraction
    uncapped_transmissivity: NonNegative | None
    dry_air_limit: bool


class EffectsPoolMixtureBurningRateOutput(Model):
    burning_rate_kg_m2_s: NonNegative


class EffectsPoolFlameGeometryOutput(Model):
    nondimensional_wind_speed: NonNegative
    flame_length_m: NonNegative
    flame_tilt_rad: NonNegative
    vertical_flame_height_m: NonNegative
    downwind_axis_extension_m: NonNegative


class EffectsPoolSurfaceEmissivePowerOutput(Model):
    burning_mass_rate_kg_s: NonNegative
    radiated_power_w: NonNegative
    emitting_surface_area_m2: NonNegative
    surface_emissive_power_w_m2: NonNegative


class EffectsPoolCylinderViewFactorOutput(Model):
    vertical_view_factor: float
    horizontal_view_factor: float
    maximum_view_factor: NonNegative
    physical_range: bool
    equation_basis: Literal['api581_printed', 'geometry_checked']


class EffectsPoolRadiationFluxOutput(Model):
    received_flux_w_m2: NonNegative
    transmissivity: Fraction
    maximum_view_factor: NonNegative
    view_factor_distance_m: NonNegative
    equation_basis: Literal['api581_printed', 'geometry_checked']
    distance_convention: Literal['printed_surface_ratio', 'surface_to_axis']


class EffectsPoolFireDistanceOutput(Model):
    safe_surface_distance_m: NonNegative
    consequence_radius_m: NonNegative
    consequence_area_m2: NonNegative
    status: Literal['threshold_solved', 'below_limit_at_domain_boundary']
    iterations: int
    flux_residual_w_m2: float | None
    minimum_surface_domain_m: NonNegative
    equation_basis: Literal['api581_printed', 'geometry_checked']
    distance_convention: Literal['printed_surface_ratio', 'surface_to_axis']


class EffectsPoolFireConsequenceOutput(Model):
    burning_rate_kg_m2_s: NonNegative
    burning_area_m2: NonNegative
    inventory_limited_area_m2: NonNegative
    pool_area_m2: NonNegative
    pool_radius_m: NonNegative
    flame_length_m: NonNegative
    flame_tilt_rad: NonNegative
    surface_emissive_power_w_m2: NonNegative
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_safe_surface_distance_m: NonNegative
    equipment_safe_surface_distance_m: NonNegative
    personnel_status: Literal['no_pool', 'threshold_solved', 'below_limit_at_domain_boundary']
    equipment_status: Literal['no_pool', 'threshold_solved', 'below_limit_at_domain_boundary']
    equation_basis: Literal['api581_printed', 'geometry_checked']
    distance_convention: Literal['printed_surface_ratio', 'surface_to_axis']


class EffectsFireballMassOutput(Model):
    flammable_mass_kg: NonNegative


class EffectsFireballViewFactorOutput(Model):
    view_factor: Fraction
    model_center_distance_m: NonNegative
    attenuation_path_m: NonNegative
    geometry_basis: Literal['api581_printed', 'elevated_sphere_maximum']


class EffectsFireballRadiationFluxOutput(Model):
    view_factor: Fraction
    model_center_distance_m: NonNegative
    attenuation_path_m: NonNegative
    geometry_basis: Literal['api581_printed', 'elevated_sphere_maximum']
    transmissivity: Fraction
    received_flux_w_m2: NonNegative


class EffectsFireballDistanceOutput(Model):
    safe_distance_m: NonNegative
    consequence_area_m2: NonNegative
    status: Literal['threshold_solved', 'below_limit_at_origin']
    iterations: int
    flux_residual_w_m2: float | None
    geometry_basis: Literal['api581_printed', 'elevated_sphere_maximum']


class EffectsFireballConsequenceOutput(Model):
    flammable_mass_kg: NonNegative
    diameter_m: NonNegative
    center_height_m: NonNegative
    duration_s: NonNegative
    radiative_fraction: Fraction
    surface_emissive_power_w_m2: NonNegative
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_safe_distance_m: NonNegative
    equipment_safe_distance_m: NonNegative
    personnel_status: Literal['no_flammable_mass', 'threshold_solved', 'below_limit_at_origin']
    equipment_status: Literal['no_flammable_mass', 'threshold_solved', 'below_limit_at_origin']
    geometry_basis: Literal['api581_printed', 'elevated_sphere_maximum']


class EffectsVceScaledDistanceOutput(Model):
    scaled_distance_m_kg13: NonNegative


class EffectsVceScaledOverpressureOutput(Model):
    side_on_overpressure_pa: NonNegative
    slope_pa_per_scaled_distance: float


class EffectsVceBlastOverpressureOutput(Model):
    scaled_distance_m_kg13: NonNegative
    side_on_overpressure_pa: NonNegative
    slope_pa_per_scaled_distance: float


class EffectsBlastBuildingProbitOutput(Model):
    probit: float
    building_collapse_probability: Fraction


class EffectsBlastBuildingPressureThresholdOutput(Model):
    probit: float
    side_on_overpressure_pa: NonNegative


class EffectsVceBlastDistanceOutput(Model):
    safe_distance_m: NonNegative
    consequence_area_m2: NonNegative
    scaled_distance_m_kg13: NonNegative | None
    status: Literal['threshold_solved', 'no_explosion']
    iterations: int
    pressure_residual_pa: float | None


class EffectsVceBlastConsequenceOutput(Model):
    tnt_equivalent_mass_kg: NonNegative
    personnel_threshold_overpressure_pa: NonNegative
    personnel_building_collapse_probability: Fraction
    equipment_threshold_overpressure_pa: NonNegative
    personnel_safe_distance_m: NonNegative
    equipment_safe_distance_m: NonNegative
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_status: Literal['threshold_solved', 'no_explosion']
    equipment_status: Literal['threshold_solved', 'no_explosion']
    mass_basis: Literal['between_flammability_limits', 'total_released_flammable']


class EffectsPhysicalExplosionTntOutput(Model):
    vapor_stored_energy_j: NonNegative
    tnt_equivalent_mass_kg: NonNegative


class ReleaseBleveFlashedAmountOutput(Model):
    flashed_liquid_mass_kg: NonNegative
    flashed_amount_kmol: NonNegative


class EffectsBleveLiquidTntOutput(Model):
    liquid_expansion_energy_j: NonNegative
    tnt_equivalent_mass_kg: NonNegative


class EffectsPhysicalExplosionConsequenceOutput(Model):
    vapor_stored_energy_j: NonNegative
    potential_tnt_equivalent_mass_kg: NonNegative
    event_tnt_equivalent_mass_kg: NonNegative
    personnel_threshold_overpressure_pa: NonNegative
    equipment_threshold_overpressure_pa: NonNegative
    personnel_building_collapse_probability: Fraction
    personnel_safe_distance_m: NonNegative
    equipment_safe_distance_m: NonNegative
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_status: Literal['threshold_solved', 'no_explosion', 'not_rupture']
    equipment_status: Literal['threshold_solved', 'no_explosion', 'not_rupture']
    hole: Literal['small', 'medium', 'large', 'rupture']


class EffectsBleveConsequenceOutput(Model):
    liquid_expansion_energy_j: NonNegative
    vapor_stored_energy_j: NonNegative
    liquid_tnt_equivalent_mass_kg: NonNegative
    vapor_tnt_equivalent_mass_kg: NonNegative
    potential_tnt_equivalent_mass_kg: NonNegative
    event_tnt_equivalent_mass_kg: NonNegative
    personnel_threshold_overpressure_pa: NonNegative
    equipment_threshold_overpressure_pa: NonNegative
    personnel_building_collapse_probability: Fraction
    personnel_safe_distance_m: NonNegative
    equipment_safe_distance_m: NonNegative
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_status: Literal['threshold_solved', 'no_explosion', 'not_rupture']
    equipment_status: Literal['threshold_solved', 'no_explosion', 'not_rupture']
    hole: Literal['small', 'medium', 'large', 'rupture']


class ConsequenceLevel2NfntCaseOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative


class ConsequenceLevel2NfntSummaryOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    total_generic_frequency_per_year: NonNegative
    by_hole_equipment_area_m2: dict[str, NonNegative]
    by_hole_personnel_area_m2: dict[str, NonNegative]


class PropertiesToxicImpactTableOutput(Model):
    probit_intercept: float | None
    probit_slope: NonNegative | None
    concentration_exponent: NonNegative | None
    probit_available: bool
    probit_concentration_unit: Literal['ppm']
    probit_duration_unit: Literal['s']
    idlh_ppm: NonNegative | None
    aegl3_ppm: dict[str, NonNegative]
    epa_toxic_endpoint_mg_l: NonNegative | None
    erpg3_ppm: NonNegative | None


class EffectsToxicSpeciesProbitOutput(Model):
    probit: float | None
    fatality_probability: Fraction


class EffectsToxicSpeciesThresholdOutput(Model):
    concentration_ppm: NonNegative
    probit: float
    within_pure_species_limit: bool


class EffectsToxicDoseProfileOutput(Model):
    probit: float | None
    fatality_probability: Fraction
    dose_ppm_power_n_s: NonNegative | None
    log_dose: float | None
    dose_representable: bool
    duration_s: NonNegative
    equivalent_constant_concentration_ppm: NonNegative


class ReleaseLevel2ToxicDurationOutput(Model):
    release_duration_s: NonNegative
    governing_limit: Literal['no_release', 'no_inventory', 'one_hour', 'inventory', 'detection_isolation']


class ConsequenceToxicMixtureLimitOutput(Model):
    modified_mixture_limit_ppm: NonNegative | None
    component_present: bool
    attainable_in_mixture: bool


class ConsequenceLevel2ToxicCaseOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    unweighted_cloud_area_m2: NonNegative
    critical_component_id: str
    component_cloud_areas_m2: dict[str, NonNegative]


class ConsequenceLevel2ToxicSummaryOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    total_generic_frequency_per_year: NonNegative
    by_hole_personnel_area_m2: dict[str, NonNegative]


class Level2FlammableCaseOutput(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    non_ignition_probability: Fraction
    terminal_probability_sum: NonNegative


class Level2FinalAreaOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    consequence_area_m2: NonNegative
    non_ignition_personnel_area_m2: NonNegative
    governing_non_ignition_personnel_mechanism: Literal['toxic', 'nfnt', 'equal']


class Level2ConsequenceSummaryOutput(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_area_m2: NonNegative
    nfnt_equipment_area_m2: NonNegative
    nfnt_personnel_area_m2: NonNegative
    generic_frequency_per_year: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    consequence_area_m2: NonNegative
    non_ignition_personnel_area_m2: NonNegative
    governing_non_ignition_personnel_mechanism: Literal['toxic', 'nfnt', 'equal']


class Level2ScenarioConsequenceOutput(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    non_ignition_probability: Fraction
    terminal_probability_sum: NonNegative
    toxic_personnel_area_m2: NonNegative
    nfnt_equipment_area_m2: NonNegative
    nfnt_personnel_area_m2: NonNegative
    hole: Literal['small', 'medium', 'large', 'rupture']


class Level2ScenarioSummaryOutput(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_area_m2: NonNegative
    nfnt_equipment_area_m2: NonNegative
    nfnt_personnel_area_m2: NonNegative
    generic_frequency_per_year: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    consequence_area_m2: NonNegative
    non_ignition_personnel_area_m2: NonNegative
    governing_non_ignition_personnel_mechanism: Literal['toxic', 'nfnt', 'equal']


class Level2AssessmentOutput(Model):
    integration_scope: Literal['supplied_level2_event_probabilities_areas_and_damage']
    management_factor: NonNegative
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_area_m2: NonNegative
    nfnt_equipment_area_m2: NonNegative
    nfnt_personnel_area_m2: NonNegative
    generic_frequency_per_year: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    consequence_area_m2: NonNegative
    non_ignition_personnel_area_m2: NonNegative
    governing_non_ignition_personnel_mechanism: Literal['toxic', 'nfnt', 'equal']
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int
    annual_failure_frequency: NonNegative
    equipment_area_risk_m2_per_year: NonNegative
    personnel_area_risk_m2_per_year: NonNegative
    area_risk_m2_per_year: NonNegative
    financial_risk_per_year: NonNegative
    frequency_weighted_equipment_area_m2: NonNegative | None
    frequency_weighted_personnel_area_m2: NonNegative | None


class PropertiesPoolSurfaceInteractionOutput(Model):
    thermal_conductivity_w_m_k: NonNegative
    thermal_diffusivity_m2_s: NonNegative
    roughness_factor: NonNegative


class ReleasePoolEvaporationRegimeOutput(Model):
    regime: Literal['boiling', 'non_boiling', 'boundary_requires_qualification']


class ReleaseBoilingPoolEvaporationOutput(Model):
    evaporation_rate_kg_s: NonNegative
    latent_heat_rate_w: NonNegative


class ReleaseBoilingPoolRadiusOutput(Model):
    pool_radius_m: NonNegative
    pool_area_m2: NonNegative


class ReleaseBoilingPoolSteadySourceOutput(Model):
    equilibrium_evaporation_rate_kg_s: NonNegative
    vapor_volumetric_rate_m3_s: NonNegative
    time_to_steady_s: NonNegative | None
    pool_radius_m: NonNegative
    pool_area_m2: NonNegative
    vapor_source_rate_kg_s: NonNegative | None
    support_status: Literal['supported', 'duration_limited', 'area_limited', 'duration_and_area_limited', 'no_feed']


class ReleaseNonboilingPoolEvaporationOutput(Model):
    evaporation_rate_kg_s: NonNegative


class ReleaseNonboilingPoolSteadySourceOutput(Model):
    equilibrium_evaporation_rate_kg_s: NonNegative | None
    pool_radius_m: NonNegative | None
    pool_area_m2: NonNegative | None
    vapor_source_rate_kg_s: NonNegative | None
    support_status: Literal['supported', 'area_limited', 'no_feed', 'no_finite_steady_state']


class ReleaseLevel2ReleasePhaseOutput(Model):
    release_phase: Literal['vapor', 'liquid', 'two_phase'] | None
    status: Literal['classified', 'no_driving_pressure', 'saturation_storage_boundary', 'saturation_ambient_boundary']


class ReleaseLevel2OrificeRateOutput(Model):
    mass_rate_kg_s: NonNegative
    area_m2: NonNegative
    release_phase: Literal['vapor', 'liquid', 'two_phase'] | None
    rate_method: Literal['ideal_gas', 'liquid', 'liquid_conservative_two_phase', 'no_driving_pressure']
    phase_basis: Literal['pressure_screen', 'qualified_boundary']


class ReleaseKletzRainoutFractionOutput(Model):
    rainout_mass_fraction: Fraction


class ReleaseRainoutRateSplitOutput(Model):
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative


class ReleaseJetLiquidEntrainmentOutput(Model):
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']


class ReleaseLevel2SourcePartitionOutput(Model):
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative
    pool_liquid_mass_kg: NonNegative
    jet_total_mass_kg: NonNegative
    jet_liquid_rate_kg_s: NonNegative
    jet_vapor_rate_kg_s: NonNegative
    jet_liquid_mass_kg: NonNegative
    jet_vapor_mass_kg: NonNegative


class ReleaseFlammablePhaseRatesOutput(Model):
    flammable_rate_kg_s: NonNegative
    flammable_vapor_rate_kg_s: NonNegative
    flammable_liquid_rate_kg_s: NonNegative


class EventsAmbientIgnitionOutput(Model):
    ambient_ignition_probability: Fraction
    evaluated_rate_kg_s: NonNegative
    rate_capped: bool


class EventsAitIgnitionMaximumOutput(Model):
    maximum_ignition_probability: Fraction


class EventsProbabilityTemperatureOutput(Model):
    probability: Fraction
    temperature_weight: Fraction
    reference_temperature_k: NonNegative


class EventsConditionalTableOutput(Model):
    immediate_at_reference: Fraction
    immediate_at_ait: Fraction
    vce_given_delayed: Fraction
    flash_given_delayed: Fraction


class EventsTwoPhaseProbabilityOutput(Model):
    probability: Fraction
    mixing_basis: Literal['api581_printed_liquid_weight', 'qualified_vapor_weight']


class EventsSinglePhaseTreeOutput(Model):
    terminal_probabilities: dict[str, Fraction]
    non_ignition_probability: Fraction
    probability_sum: NonNegative
    fireball_applicability_basis: Literal['rupture_only_text', 'figure53_instantaneous']


class EventsSinglePhaseIgnitionOutput(Model):
    ambient_ignition_probability: Fraction
    evaluated_rate_kg_s: NonNegative
    rate_capped: bool
    maximum_ignition_probability: Fraction
    terminal_probabilities: dict[str, Fraction]
    non_ignition_probability: Fraction
    probability_sum: NonNegative
    fireball_applicability_basis: Literal['rupture_only_text', 'figure53_instantaneous']
    ignition_probability: Fraction
    immediate_given_ignition: Fraction
    vce_given_delayed: Fraction
    flash_given_delayed: Fraction
    reference_temperature_k: NonNegative
    temperature_weight: Fraction


class Level2CorrelatedJetPoolOutput(Model):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    maximum_equipment_area_m2: NonNegative
    maximum_personnel_area_m2: NonNegative
    governing_equipment: Literal['jet', 'pool', 'equal']
    governing_personnel: Literal['jet', 'pool', 'equal']


class EventsFireballGivenImmediateOutput(Model):
    fireball_given_immediate: Fraction


class EventsTwoPhaseTreeOutput(Model):
    terminal_probabilities: dict[str, Fraction]
    non_ignition_probability: Fraction
    probability_sum: NonNegative
    fireball_applicability_basis: Literal['rupture_only_text', 'figure53_instantaneous']
    fireball_given_immediate: Fraction
    fireball_probability_basis: Literal['api581_eq3_123_124', 'qualified_figure54_branch']


class EventsTwoPhaseIgnitionOutput(Model):
    terminal_probabilities: dict[str, Fraction]
    non_ignition_probability: Fraction
    probability_sum: NonNegative
    fireball_applicability_basis: Literal['rupture_only_text', 'figure53_instantaneous']
    fireball_given_immediate: Fraction
    fireball_probability_basis: Literal['api581_eq3_123_124', 'qualified_figure54_branch']
    flammable_rate_kg_s: NonNegative
    flammable_vapor_rate_kg_s: NonNegative
    flammable_liquid_rate_kg_s: NonNegative
    ignition_probability: Fraction
    immediate_given_ignition: Fraction
    vce_given_delayed: Fraction
    flash_given_delayed: Fraction
    liquid_ignition_probability: Fraction
    vapor_ignition_probability: Fraction
    liquid_immediate_given_ignition: Fraction
    vapor_immediate_given_ignition: Fraction
    temperature_weight: Fraction
    reference_temperature_k: NonNegative
    mixing_basis: Literal['api581_printed_liquid_weight', 'qualified_vapor_weight']


class TankFluidTableOutput(Model):
    molecular_weight_kg_kmol: NonNegative
    liquid_density_kg_m3: NonNegative
    dynamic_viscosity_pa_s: NonNegative


class TankSoilTableOutput(Model):
    printed_lower_bound_cm_s: NonNegative
    printed_upper_bound_cm_s: NonNegative
    porosity: Fraction


class TankSoilWaterConductivityOutput(Model):
    water_hydraulic_conductivity_m_day: NonNegative


class TankFluidConductivityOutput(Model):
    product_hydraulic_conductivity_m_day: NonNegative


class TankSeepageVelocityOutput(Model):
    seepage_velocity_m_day: NonNegative


class TankBottomHoleCountOutput(Model):
    small_hole_count: int
    medium_hole_count: int
    large_hole_count: int
    outside_tabulated_diameter_range: bool


class TankBottomInventoryOutput(Model):
    available_volume_m3: NonNegative
    available_volume_bbl: NonNegative
    available_mass_kg: NonNegative


class TankShellCourseInventoryOutput(Model):
    available_volume_m3: NonNegative
    available_volume_bbl: NonNegative
    available_mass_kg: NonNegative
    course_bottom_elevation_m: NonNegative
    available_liquid_head_m: NonNegative
    course_wet: bool


class TankShellFlowOutput(Model):
    native_rate_bbl_day: NonNegative
    volume_rate_m3_s: NonNegative
    mass_rate_kg_s: NonNegative
    hole_area_m2: NonNegative


class TankBottomFlowOutput(Model):
    native_rate_bbl_day: NonNegative
    volume_rate_m3_s: NonNegative
    mass_rate_kg_s: NonNegative
    per_hole_native_rate_bbl_day: NonNegative
    equation: Literal['3.210', '3.211', '3.212', 'zero_flow']
    liquid_head_used_m: NonNegative
    lower_conductivity_threshold_m_day: NonNegative | None
    upper_conductivity_threshold_m_day: NonNegative | None
    applied_hole_multiplier: int
    transition_hole_basis: Literal['api581_printed', 'per_hole_scaled']


class TankShellDetectionTimeOutput(Model):
    detection_time_days: NonNegative
    diameter_boundary_m: NonNegative


class TankBottomDetectionTimeOutput(Model):
    detection_time_days: NonNegative
    selected_basis: Literal['concrete_asphalt', 'barrier', 'unprotected']


class TankReleaseVolumeOutput(Model):
    release_duration_days: NonNegative | None
    released_volume_bbl: NonNegative
    released_volume_m3: NonNegative
    released_mass_kg: NonNegative
    printed_mass_index: NonNegative
    release_type: Literal['continuous']


class TankEnvironmentCostTableOutput(Model):
    cost_by_location_usd_per_bbl: dict[str, NonNegative]


class TankSurfaceSpillPartitionOutput(Model):
    in_dike_bbl: NonNegative
    surface_on_site_bbl: NonNegative
    surface_off_site_bbl: NonNegative
    surface_water_bbl: NonNegative


class TankGroundwaterArrivalOutput(Model):
    arrival_time_days: NonNegative | None
    arrival_status: Literal['already_at_groundwater', 'no_finite_arrival', 'finite_travel']


class TankSubsurfaceSpillPartitionOutput(Model):
    groundwater_bbl: NonNegative
    subsoil_bbl: NonNegative
    groundwater_fraction: Fraction


class TankShellEnvironmentCostOutput(Model):
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    environment_cost: NonNegative
    currency: str
    cost_basis: str
    weighted_leak_volume_bbl: NonNegative
    weighted_rupture_volume_bbl: NonNegative
    weighted_leak_surface_volumes_bbl: dict[str, NonNegative]
    weighted_rupture_surface_volumes_bbl: dict[str, NonNegative]


class TankBottomEnvironmentCostOutput(Model):
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    environment_cost: NonNegative
    currency: str
    cost_basis: str
    weighted_groundwater_volume_bbl: NonNegative
    weighted_subsoil_volume_bbl: NonNegative
    weighted_rupture_volume_bbl: NonNegative
    weighted_rupture_surface_volumes_bbl: dict[str, NonNegative]


class TankBottomRepairCostOutput(Model):
    component_repair_cost: NonNegative
    currency: str
    cost_basis: str


class TankGenericFrequencyOutput(Model):
    by_hole_per_year: dict[str, NonNegative]
    total_per_year: NonNegative
    printed_total_per_year: NonNegative
    sum_minus_printed_per_year: float
    total_basis: Literal['hole_sum_eq3_208']


class TankComponentOutageOutput(Model):
    component_outage_days: NonNegative
    effective_days_by_hole: dict[str, NonNegative | None]


class TankBottomFinancialConsequenceOutput(Model):
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int
    cost_basis: str


class TankShellFinancialConsequenceOutput(Model):
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int
    cost_basis: str


class TankBottomRiskAssessmentOutput(Model):
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int
    cost_basis: str
    generic_frequency_per_year: NonNegative
    management_factor: NonNegative
    annual_failure_frequency: NonNegative
    financial_risk_per_year: NonNegative
    annual_frequency_by_hole: dict[str, NonNegative]
    integration_scope: Literal['supplied_uniform_df_and_tank_release_consequences']


class TankShellRiskAssessmentOutput(Model):
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int
    cost_basis: str
    generic_frequency_per_year: NonNegative
    management_factor: NonNegative
    annual_failure_frequency: NonNegative
    financial_risk_per_year: NonNegative
    annual_frequency_by_hole: dict[str, NonNegative]
    integration_scope: Literal['supplied_uniform_df_and_tank_release_consequences']
    equipment_area_risk_m2_per_year: NonNegative
    personnel_area_risk_m2_per_year: NonNegative


class TankShellHoleSizesOutput(Model):
    diameter_by_hole_m: dict[str, NonNegative]
    area_by_hole_m2: dict[str, NonNegative]


class TankBottomHoleSizesOutput(Model):
    diameter_by_hole_m: dict[str, NonNegative]
    area_by_hole_m2: dict[str, NonNegative]


class TankShellSourceAssessmentOutput(Model):
    diameter_by_hole_m: dict[str, NonNegative]
    area_by_hole_m2: dict[str, NonNegative]
    available_volume_m3: NonNegative
    available_volume_bbl: NonNegative
    available_mass_kg: NonNegative
    generic_frequency_by_hole_per_year: dict[str, NonNegative]
    generic_total_per_year: NonNegative
    printed_generic_total_per_year: NonNegative
    generic_total_basis: Literal['hole_sum_eq3_208']
    native_rate_by_hole_bbl_day: dict[str, NonNegative | None]
    mass_rate_by_hole_kg_s: dict[str, NonNegative | None]
    detection_time_by_hole_days: dict[str, NonNegative | None]
    release_duration_by_hole_days: dict[str, NonNegative | None]
    released_volume_by_hole_bbl: dict[str, NonNegative]
    released_volume_by_hole_m3: dict[str, NonNegative]
    released_mass_by_hole_kg: dict[str, NonNegative]
    release_type: Literal['continuous']
    liquid_density_kg_m3: NonNegative
    course_bottom_elevation_m: NonNegative
    available_liquid_head_m: NonNegative
    course_wet: bool
    source_scope: Literal['single_shell_course']


class TankBottomSourceAssessmentOutput(Model):
    diameter_by_hole_m: dict[str, NonNegative]
    area_by_hole_m2: dict[str, NonNegative]
    available_volume_m3: NonNegative
    available_volume_bbl: NonNegative
    available_mass_kg: NonNegative
    generic_frequency_by_hole_per_year: dict[str, NonNegative]
    generic_total_per_year: NonNegative
    printed_generic_total_per_year: NonNegative
    generic_total_basis: Literal['hole_sum_eq3_208']
    native_rate_by_hole_bbl_day: dict[str, NonNegative | None]
    mass_rate_by_hole_kg_s: dict[str, NonNegative | None]
    detection_time_by_hole_days: dict[str, NonNegative | None]
    release_duration_by_hole_days: dict[str, NonNegative | None]
    released_volume_by_hole_bbl: dict[str, NonNegative]
    released_volume_by_hole_m3: dict[str, NonNegative]
    released_mass_by_hole_kg: dict[str, NonNegative]
    release_type: Literal['continuous']
    liquid_density_kg_m3: NonNegative
    small_hole_count: int
    medium_hole_count: int
    large_hole_count: int
    outside_tabulated_diameter_range: bool
    product_hydraulic_conductivity_m_day: NonNegative
    seepage_velocity_m_day: NonNegative
    bottom_flow_equation: Literal['3.210', '3.211', '3.212', 'zero_flow']
    applied_small_hole_multiplier: int
    detection_time_days: NonNegative
    detection_selected_basis: Literal['concrete_asphalt', 'barrier', 'unprotected']
    source_scope: Literal['single_tank_bottom']


class TankBottomIntegratedAssessmentOutput(Model):
    diameter_by_hole_m: dict[str, NonNegative]
    area_by_hole_m2: dict[str, NonNegative]
    available_volume_m3: NonNegative
    available_volume_bbl: NonNegative
    available_mass_kg: NonNegative
    generic_frequency_by_hole_per_year: dict[str, NonNegative]
    generic_total_per_year: NonNegative
    printed_generic_total_per_year: NonNegative
    generic_total_basis: Literal['hole_sum_eq3_208']
    native_rate_by_hole_bbl_day: dict[str, NonNegative | None]
    mass_rate_by_hole_kg_s: dict[str, NonNegative | None]
    detection_time_by_hole_days: dict[str, NonNegative | None]
    release_duration_by_hole_days: dict[str, NonNegative | None]
    released_volume_by_hole_bbl: dict[str, NonNegative]
    released_volume_by_hole_m3: dict[str, NonNegative]
    released_mass_by_hole_kg: dict[str, NonNegative]
    release_type: Literal['continuous']
    liquid_density_kg_m3: NonNegative
    small_hole_count: int
    medium_hole_count: int
    large_hole_count: int
    outside_tabulated_diameter_range: bool
    product_hydraulic_conductivity_m_day: NonNegative
    seepage_velocity_m_day: NonNegative
    bottom_flow_equation: Literal['3.210', '3.211', '3.212', 'zero_flow']
    applied_small_hole_multiplier: int
    detection_time_days: NonNegative
    detection_selected_basis: Literal['concrete_asphalt', 'barrier', 'unprotected']
    source_scope: Literal['single_tank_bottom']
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int
    cost_basis: str
    generic_frequency_per_year: NonNegative
    management_factor: NonNegative
    annual_failure_frequency: NonNegative
    financial_risk_per_year: NonNegative
    annual_frequency_by_hole: dict[str, NonNegative]
    integration_scope: Literal['bottom_geometry_soil_source_financial_risk_with_supplied_df']
    groundwater_arrival_time_days: NonNegative | None


class TankDikedPoolConsequenceOutput(Model):
    burning_rate_kg_m2_s: NonNegative
    burning_area_m2: NonNegative
    inventory_limited_area_m2: NonNegative
    pool_area_m2: NonNegative
    pool_radius_m: NonNegative
    flame_length_m: NonNegative
    flame_tilt_rad: NonNegative
    surface_emissive_power_w_m2: NonNegative
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_status: Literal['no_pool', 'threshold_solved', 'below_limit_at_domain_boundary']
    equipment_status: Literal['no_pool', 'threshold_solved', 'below_limit_at_domain_boundary']
    equation_basis: Literal['api581_printed', 'geometry_checked']
    distance_convention: Literal['printed_surface_ratio', 'surface_to_axis']
    unclipped_personnel_safe_surface_distance_m: NonNegative
    unclipped_equipment_safe_surface_distance_m: NonNegative
    unclipped_equipment_area_m2: NonNegative
    unclipped_personnel_area_m2: NonNegative
    effective_pool_area_limit_m2: NonNegative
    dike_area_m2: NonNegative
    equipment_area_clipped: bool
    personnel_area_clipped: bool
    dike_limit_basis: Literal['burning_pool_area', 'burning_and_consequence_area']


class TankShellLevel2CaseOutput(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    non_ignition_probability: Fraction
    terminal_probability_sum: NonNegative
    toxic_personnel_area_m2: NonNegative
    nfnt_status: Literal['not_determined_for_ast']


class TankShellLevel2SummaryOutput(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    consequence_area_m2: NonNegative
    generic_frequency_per_year: NonNegative
    by_hole_flammable_equipment_area_m2: dict[str, NonNegative]
    by_hole_flammable_personnel_area_m2: dict[str, NonNegative]
    by_hole_toxic_personnel_area_m2: dict[str, NonNegative]
    nfnt_status: Literal['not_determined_for_ast']


class TankShellIntegratedAssessmentOutput(Model):
    diameter_by_hole_m: dict[str, NonNegative]
    area_by_hole_m2: dict[str, NonNegative]
    available_volume_m3: NonNegative
    available_volume_bbl: NonNegative
    available_mass_kg: NonNegative
    generic_frequency_by_hole_per_year: dict[str, NonNegative]
    generic_total_per_year: NonNegative
    printed_generic_total_per_year: NonNegative
    generic_total_basis: Literal['hole_sum_eq3_208']
    native_rate_by_hole_bbl_day: dict[str, NonNegative | None]
    mass_rate_by_hole_kg_s: dict[str, NonNegative | None]
    detection_time_by_hole_days: dict[str, NonNegative | None]
    release_duration_by_hole_days: dict[str, NonNegative | None]
    released_volume_by_hole_bbl: dict[str, NonNegative]
    released_volume_by_hole_m3: dict[str, NonNegative]
    released_mass_by_hole_kg: dict[str, NonNegative]
    release_type: Literal['continuous']
    liquid_density_kg_m3: NonNegative
    course_bottom_elevation_m: NonNegative
    available_liquid_head_m: NonNegative
    course_wet: bool
    source_scope: Literal['single_shell_course']
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    consequence_area_m2: NonNegative
    generic_frequency_per_year: NonNegative
    by_hole_flammable_equipment_area_m2: dict[str, NonNegative]
    by_hole_flammable_personnel_area_m2: dict[str, NonNegative]
    by_hole_toxic_personnel_area_m2: dict[str, NonNegative]
    nfnt_status: Literal['not_determined_for_ast']
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int
    cost_basis: str
    management_factor: NonNegative
    annual_failure_frequency: NonNegative
    financial_risk_per_year: NonNegative
    annual_frequency_by_hole: dict[str, NonNegative]
    integration_scope: Literal['shell_geometry_source_supplied_event_footprints_financial_risk']
    equipment_area_risk_m2_per_year: NonNegative
    personnel_area_risk_m2_per_year: NonNegative


class DispersionNativeEngineCapabilitiesOutput(Model):
    requested_engines: list[Literal['slabx', 'slabx-lh2']]
    required_versions: dict[str, str]
    installed_versions: dict[str, str | None]
    engine_status: dict[str, Literal['missing', 'available', 'version_mismatch', 'not_importable']]
    module_import_status: dict[str, Literal['not_installed', 'importable', 'not_importable']]
    worker_isolation: Literal['subprocess']
    supported_operations: list[str]
    probe_scope: Literal['package_presence_version_and_importability']


class DispersionNativePoolCentrelineOutput(Model):
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    effective_source_half_width_m: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: NonNegative
    spatial_output_scope: Literal['centreline_only_no_footprint_area']


class DispersionThresholdGridAreaOutput(Model):
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']


class DispersionNativePoolFootprintOutput(Model):
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    effective_source_half_width_m: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: NonNegative
    spatial_output_scope: Literal['planar_sampled_threshold_field']
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached', 'premise_violated']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']
    crosswind_distance_m: list[float]
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]


class DispersionNativePoolFlashFireOutput(Model):
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    effective_source_half_width_m: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: Literal[0.0]
    spatial_output_scope: Literal['planar_sampled_threshold_field']
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached', 'premise_violated']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']
    crosswind_distance_m: list[float]
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    criterion_role: Literal['qualified_lfl']


class DispersionNativeJetCentrelineOutput(Model):
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: NonNegative
    spatial_output_scope: Literal['centreline_only_no_footprint_area']
    orientation: Literal['horizontal_downwind', 'vertical_up']
    jet_exit_area_m2: NonNegative
    geometric_exit_half_width_m: NonNegative
    native_exit_velocity_m_s: NonNegative
    requested_source_temperature_k: NonNegative
    used_source_temperature_k: NonNegative
    source_temperature_clamped: bool
    native_jet_liquid_mass_fraction: Fraction
    native_initial_downwind_distance_m: NonNegative
    native_near_field_status: Literal['not_reconstructed_before_native_handoff', 'briggs_buoyant_effective_horizontal_source']


class DispersionNativeJetFootprintOutput(Model):
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: NonNegative
    spatial_output_scope: Literal['planar_sampled_threshold_field']
    orientation: Literal['horizontal_downwind', 'vertical_up']
    jet_exit_area_m2: NonNegative
    geometric_exit_half_width_m: NonNegative
    native_exit_velocity_m_s: NonNegative
    requested_source_temperature_k: NonNegative
    used_source_temperature_k: NonNegative
    source_temperature_clamped: bool
    native_jet_liquid_mass_fraction: Fraction
    native_initial_downwind_distance_m: NonNegative
    native_near_field_status: Literal['not_reconstructed_before_native_handoff', 'briggs_buoyant_effective_horizontal_source']
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached', 'premise_violated']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']
    crosswind_distance_m: list[float]
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]


class DispersionPartitionedJetCentrelineOutput(Model):
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: NonNegative
    spatial_output_scope: Literal['centreline_only_no_footprint_area']
    orientation: Literal['horizontal_downwind', 'vertical_up']
    jet_exit_area_m2: NonNegative
    geometric_exit_half_width_m: NonNegative
    native_exit_velocity_m_s: NonNegative
    requested_source_temperature_k: NonNegative
    used_source_temperature_k: NonNegative
    source_temperature_clamped: bool
    native_jet_liquid_mass_fraction: Fraction
    native_initial_downwind_distance_m: NonNegative
    native_near_field_status: Literal['not_reconstructed_before_native_handoff', 'briggs_buoyant_effective_horizontal_source']
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative
    pool_liquid_mass_kg: NonNegative
    jet_total_mass_kg: NonNegative
    jet_liquid_rate_kg_s: NonNegative
    jet_vapor_rate_kg_s: NonNegative
    jet_liquid_mass_kg: NonNegative
    jet_vapor_mass_kg: NonNegative
    release_duration_s: NonNegative
    integration_scope: Literal['qualified_partition_to_native_jet']


class DispersionPartitionedJetFootprintOutput(Model):
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: NonNegative
    spatial_output_scope: Literal['planar_sampled_threshold_field']
    orientation: Literal['horizontal_downwind', 'vertical_up']
    jet_exit_area_m2: NonNegative
    geometric_exit_half_width_m: NonNegative
    native_exit_velocity_m_s: NonNegative
    requested_source_temperature_k: NonNegative
    used_source_temperature_k: NonNegative
    source_temperature_clamped: bool
    native_jet_liquid_mass_fraction: Fraction
    native_initial_downwind_distance_m: NonNegative
    native_near_field_status: Literal['not_reconstructed_before_native_handoff', 'briggs_buoyant_effective_horizontal_source']
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached', 'premise_violated']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']
    crosswind_distance_m: list[float]
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative
    pool_liquid_mass_kg: NonNegative
    jet_total_mass_kg: NonNegative
    jet_liquid_rate_kg_s: NonNegative
    jet_vapor_rate_kg_s: NonNegative
    jet_liquid_mass_kg: NonNegative
    jet_vapor_mass_kg: NonNegative
    release_duration_s: NonNegative
    integration_scope: Literal['qualified_partition_to_native_jet']


class ConsequenceSelectToxicCriterionOutput(Model):
    fluid_id: str
    selected_criterion_id: str
    selected_kind: Literal['probit50', 'lc50', 'erpg3', 'aegl3', 'teel3', 'idlh', 'epa_endpoint']
    priority_tier: Literal[1, 2, 3]
    pure_component_limit_ppm: NonNegative
    modified_mixture_limit_ppm: NonNegative | None
    threshold_volume_fraction: Fraction | None
    component_present: bool
    attainable_in_mixture: bool
    exposure_duration_s: NonNegative
    criterion_source: str
    eligible_candidate_ids: list[str]
    excluded_candidate_ids: dict[str, str]
    unavailable_candidate_reasons: dict[str, str]


class DispersionNativePoolToxicConsequenceOutput(Model):
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    effective_source_half_width_m: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: Literal[0.0]
    spatial_output_scope: Literal['planar_sampled_threshold_field']
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached', 'premise_violated']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']
    crosswind_distance_m: list[float]
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]
    fluid_id: str
    selected_criterion_id: str
    selected_kind: Literal['probit50', 'lc50', 'erpg3', 'aegl3', 'teel3', 'idlh', 'epa_endpoint']
    priority_tier: Literal[1, 2, 3]
    pure_component_limit_ppm: NonNegative
    modified_mixture_limit_ppm: NonNegative | None
    threshold_volume_fraction: Fraction | None
    component_present: bool
    attainable_in_mixture: bool
    exposure_duration_s: NonNegative
    criterion_source: str
    eligible_candidate_ids: list[str]
    excluded_candidate_ids: dict[str, str]
    unavailable_candidate_reasons: dict[str, str]
    equipment_area_m2: Literal[0.0]
    personnel_area_m2: NonNegative
    unweighted_cloud_area_m2: NonNegative
    critical_component_id: str
    component_cloud_areas_m2: dict[str, NonNegative]
    release_duration_s: NonNegative
    release_duration_governing_limit: Literal['one_hour', 'inventory', 'detection_isolation', 'no_release', 'no_inventory']
    exposure_model_basis: Literal['constant_exposure_equivalent_native_time_average']


class DamageSoilBaseRateTableOutput(Model):
    corrosion_rate_m_year: NonNegative
    printed_si_rate_mm_year: NonNegative
    printed_us_rate_mpy: NonNegative
    selected_unit_basis: Literal['printed_si', 'printed_us_mpy']
    condition_description: str


class DamageSoilResistivityFactorOutput(Model):
    resistivity_factor: NonNegative
    source_row: int


class DamageSoilTemperatureFactorOutput(Model):
    temperature_factor: NonNegative
    lower_boundary_k: NonNegative
    upper_boundary_k: NonNegative
    threshold_basis: Literal['printed_si', 'printed_us_converted']


class DamageSoilCpFactorOutput(Model):
    cathodic_protection_factor: NonNegative


class DamageSoilCoatingFactorOutput(Model):
    coating_effectiveness_factor: NonNegative
    base_factor: NonNegative
    age_factor: NonNegative
    temperature_abuse_factor: NonNegative
    maintenance_factor: NonNegative
    calculation_basis: Literal['table_factor_product']
    printed_example_discrepancy_applies: bool
    printed_example_reported_factor: NonNegative | None


class DamageSoilRateEquationOutput(Model):
    corrosion_rate_m_year: NonNegative


class DamageSoilCorrosionRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    resistivity_factor: NonNegative
    temperature_factor: NonNegative
    cathodic_protection_factor: NonNegative
    coating_effectiveness_factor: NonNegative
    base_corrosion_rate_m_year: NonNegative
    thinning_type: Literal['local']
    resistivity_application: Literal['apply', 'already_in_base', 'omitted_by_qualification']
    coating_calculation_basis: Literal['table_factor_product']
    coating_example_discrepancy_applies: bool


class DamageSoilThinningAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    resistivity_factor: NonNegative
    temperature_factor: NonNegative
    cathodic_protection_factor: NonNegative
    coating_effectiveness_factor: NonNegative
    base_corrosion_rate_m_year: NonNegative
    thinning_type: Literal['local']
    resistivity_application: Literal['apply', 'already_in_base', 'omitted_by_qualification']
    coating_calculation_basis: Literal['table_factor_product']
    coating_example_discrepancy_applies: bool
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    assessment_scope: Literal['unclad_internal_pressure_governed_non_ast']


class TankBottomBaseCorrosionRateOutput(Model):
    base_corrosion_rate_m_year: NonNegative
    printed_si_rate_mm_year: NonNegative
    printed_us_rate_mpy: NonNegative
    side: Literal['soil', 'product']
    unit_basis: Literal['printed_si', 'printed_us_mpy']


class TankBottomSoilRateEquationOutput(Model):
    soil_corrosion_rate_m_year: NonNegative


class TankBottomProductRateEquationOutput(Model):
    product_corrosion_rate_m_year: NonNegative


class TankBottomSoilResistivityFactorOutput(Model):
    resistivity_factor: NonNegative
    selection_reason: Literal['rpb', 'unknown_assume_moderate', 'resistivity_table']


class TankBottomPadFactorOutput(Model):
    pad_factor: NonNegative


class TankBottomDrainageFactorOutput(Model):
    drainage_factor: NonNegative


class TankBottomTypeFactorOutput(Model):
    bottom_type_factor: NonNegative


class TankBottomProductConditionFactorOutput(Model):
    product_condition_factor: NonNegative


class TankBottomSteamCoilFactorOutput(Model):
    steam_coil_factor: NonNegative


class TankBottomWaterDrawFactorOutput(Model):
    water_draw_factor: NonNegative


class TankBottomCpFactorOutput(Model):
    nominal_table_factor: NonNegative
    cathodic_protection_factor: NonNegative
    credit_applied: bool


class TankBottomTemperatureFactorOutput(Model):
    temperature_factor: NonNegative
    source_row: int
    threshold_basis: Literal['printed_si', 'printed_us_converted']


class TankBottomCorrosionRateCombineOutput(Model):
    raw_combined_rate_m_year: NonNegative
    combined_corrosion_rate_m_year: NonNegative
    recommended_minimum_rate_m_year: NonNegative
    minimum_applied: bool
    combination_rule: Literal['sum', 'maximum']


class TankBottomCorrosionAssessmentOutput(Model):
    raw_combined_rate_m_year: NonNegative
    combined_corrosion_rate_m_year: NonNegative
    recommended_minimum_rate_m_year: NonNegative
    minimum_applied: bool
    combination_rule: Literal['sum', 'maximum']
    soil_corrosion_rate_m_year: NonNegative
    product_corrosion_rate_m_year: NonNegative
    resistivity_factor: NonNegative
    pad_factor: NonNegative
    drainage_factor: NonNegative
    cathodic_protection_factor: NonNegative
    bottom_type_factor: NonNegative
    temperature_factor: NonNegative
    product_condition_factor: NonNegative
    steam_coil_factor: NonNegative
    water_draw_factor: NonNegative
    cp_credit_applied: bool


class TankBottomMinimumThicknessOutput(Model):
    minimum_thickness_m: NonNegative
    thickness_basis: Literal['api581_2016_default', 'documented_owner_method']


class TankBottomWallParameterOutput(Model):
    art_parameter: NonNegative
    predicted_remaining_thickness_m: float
    predicted_wall_loss_m: NonNegative
    reference_thickness_m: NonNegative
    at_or_below_minimum_thickness: bool
    predicted_penetration: bool


class TankBottomInspectionSelectionOutput(Model):
    selected_inspection_grade: Literal['a', 'b', 'c', 'd', 'e']
    credited_inspection_count: int
    eligible_inspection_count: int


class TankBottomThinningBaseOutput(Model):
    base_damage_factor: NonNegative
    lower_art_row: NonNegative
    upper_art_row: NonNegative
    interpolation_weight: NonNegative
    lookup_policy: Literal['exact_rows_only', 'linear_between_rows', 'conservative_upper_row']


class TankBottomThinningAdjustmentFactorsOutput(Model):
    welded_construction_factor: NonNegative
    maintenance_factor: NonNegative
    settlement_factor: NonNegative


class TankBottomThinningAssessmentOutput(Model):
    minimum_thickness_m: NonNegative
    thickness_basis: Literal['api581_2016_default', 'documented_owner_method']
    art_parameter: NonNegative
    predicted_remaining_thickness_m: float
    predicted_wall_loss_m: NonNegative
    reference_thickness_m: NonNegative
    at_or_below_minimum_thickness: bool
    predicted_penetration: bool
    selected_inspection_grade: Literal['a', 'b', 'c', 'd', 'e']
    credited_inspection_count: int
    eligible_inspection_count: int
    base_damage_factor: NonNegative
    lower_art_row: NonNegative
    upper_art_row: NonNegative
    interpolation_weight: NonNegative
    lookup_policy: Literal['exact_rows_only', 'linear_between_rows', 'conservative_upper_row']
    welded_construction_factor: NonNegative
    maintenance_factor: NonNegative
    settlement_factor: NonNegative
    thinning_damage_factor: NonNegative
    online_monitoring_factor: Literal[1.0]


class TankBottomCorrosionThinningAssessmentOutput(Model):
    raw_combined_rate_m_year: NonNegative
    combined_corrosion_rate_m_year: NonNegative
    recommended_minimum_rate_m_year: NonNegative
    minimum_applied: bool
    combination_rule: Literal['sum', 'maximum']
    soil_corrosion_rate_m_year: NonNegative
    product_corrosion_rate_m_year: NonNegative
    resistivity_factor: NonNegative
    pad_factor: NonNegative
    drainage_factor: NonNegative
    cathodic_protection_factor: NonNegative
    bottom_type_factor: NonNegative
    temperature_factor: NonNegative
    product_condition_factor: NonNegative
    steam_coil_factor: NonNegative
    water_draw_factor: NonNegative
    cp_credit_applied: bool
    minimum_thickness_m: NonNegative
    thickness_basis: Literal['api581_2016_default', 'documented_owner_method']
    art_parameter: NonNegative
    predicted_remaining_thickness_m: float
    predicted_wall_loss_m: NonNegative
    reference_thickness_m: NonNegative
    at_or_below_minimum_thickness: bool
    predicted_penetration: bool
    selected_inspection_grade: Literal['a', 'b', 'c', 'd', 'e']
    credited_inspection_count: int
    eligible_inspection_count: int
    base_damage_factor: NonNegative
    lower_art_row: NonNegative
    upper_art_row: NonNegative
    interpolation_weight: NonNegative
    lookup_policy: Literal['exact_rows_only', 'linear_between_rows', 'conservative_upper_row']
    welded_construction_factor: NonNegative
    maintenance_factor: NonNegative
    settlement_factor: NonNegative
    thinning_damage_factor: NonNegative
    online_monitoring_factor: Literal[1.0]


class TankBottomCorrosionRiskAssessmentOutput(Model):
    raw_combined_rate_m_year: NonNegative
    combined_corrosion_rate_m_year: NonNegative
    recommended_minimum_rate_m_year: NonNegative
    minimum_applied: bool
    combination_rule: Literal['sum', 'maximum']
    soil_corrosion_rate_m_year: NonNegative
    product_corrosion_rate_m_year: NonNegative
    resistivity_factor: NonNegative
    pad_factor: NonNegative
    drainage_factor: NonNegative
    cathodic_protection_factor: NonNegative
    bottom_type_factor: NonNegative
    temperature_factor: NonNegative
    product_condition_factor: NonNegative
    steam_coil_factor: NonNegative
    water_draw_factor: NonNegative
    cp_credit_applied: bool
    minimum_thickness_m: NonNegative
    thickness_basis: Literal['api581_2016_default', 'documented_owner_method']
    art_parameter: NonNegative
    predicted_remaining_thickness_m: float
    predicted_wall_loss_m: NonNegative
    reference_thickness_m: NonNegative
    at_or_below_minimum_thickness: bool
    predicted_penetration: bool
    selected_inspection_grade: Literal['a', 'b', 'c', 'd', 'e']
    credited_inspection_count: int
    eligible_inspection_count: int
    base_damage_factor: NonNegative
    lower_art_row: NonNegative
    upper_art_row: NonNegative
    interpolation_weight: NonNegative
    lookup_policy: Literal['exact_rows_only', 'linear_between_rows', 'conservative_upper_row']
    welded_construction_factor: NonNegative
    maintenance_factor: NonNegative
    settlement_factor: NonNegative
    thinning_damage_factor: NonNegative
    online_monitoring_factor: Literal[1.0]
    diameter_by_hole_m: dict[str, NonNegative]
    area_by_hole_m2: dict[str, NonNegative]
    available_volume_m3: NonNegative
    available_volume_bbl: NonNegative
    available_mass_kg: NonNegative
    generic_frequency_by_hole_per_year: dict[str, NonNegative]
    generic_total_per_year: NonNegative
    printed_generic_total_per_year: NonNegative
    generic_total_basis: Literal['hole_sum_eq3_208']
    native_rate_by_hole_bbl_day: dict[str, NonNegative | None]
    mass_rate_by_hole_kg_s: dict[str, NonNegative | None]
    detection_time_by_hole_days: dict[str, NonNegative | None]
    release_duration_by_hole_days: dict[str, NonNegative | None]
    released_volume_by_hole_bbl: dict[str, NonNegative]
    released_volume_by_hole_m3: dict[str, NonNegative]
    released_mass_by_hole_kg: dict[str, NonNegative]
    release_type: Literal['continuous']
    liquid_density_kg_m3: NonNegative
    small_hole_count: int
    medium_hole_count: int
    large_hole_count: int
    outside_tabulated_diameter_range: bool
    product_hydraulic_conductivity_m_day: NonNegative
    seepage_velocity_m_day: NonNegative
    bottom_flow_equation: Literal['3.210', '3.211', '3.212', 'zero_flow']
    applied_small_hole_multiplier: int
    detection_time_days: NonNegative
    detection_selected_basis: Literal['concrete_asphalt', 'barrier', 'unprotected']
    source_scope: Literal['single_tank_bottom']
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    surrounding_cost_reference_usd_2001: NonNegative
    leak_environment_cost: NonNegative
    rupture_environment_cost: NonNegative
    financial_consequence: NonNegative
    currency: str
    cost_basis_year: int
    cost_basis: str
    generic_frequency_per_year: NonNegative
    management_factor: NonNegative
    annual_failure_frequency: NonNegative
    financial_risk_per_year: NonNegative
    annual_frequency_by_hole: dict[str, NonNegative]
    integration_scope: Literal['bottom_corrosion_thinning_source_financial_risk_qualified_thinning_only']
    groundwater_arrival_time_days: NonNegative | None
    total_damage_factor: NonNegative


class DamageCladdingRemainingLifeOutput(Model):
    remaining_cladding_at_baseline_m: NonNegative
    cladding_depletion_age_years: NonNegative | None
    cladding_baseline_state: Literal['already_depleted', 'noncorroding_present', 'finite_depletion']


class DamageThinningCladWallLossOutput(Model):
    remaining_cladding_at_baseline_m: NonNegative
    cladding_depletion_age_years: NonNegative | None
    cladding_baseline_state: Literal['already_depleted', 'noncorroding_present', 'finite_depletion']
    wall_loss_fraction: NonNegative
    cladding_wall_loss_m: NonNegative
    base_material_wall_loss_m: NonNegative
    base_material_exposure_years: NonNegative
    predicted_remaining_thickness_m: float
    predicted_penetration: bool
    wall_loss_branch: Literal['base_only_eq2_13', 'noncorroding_cladding_extension', 'cladding_only_eq2_14', 'cladding_then_base_eq2_15']


class DamageThinningDesignStrengthRatioOutput(Model):
    strength_ratio: NonNegative
    governing_minimum_thickness_m: NonNegative
    governing_thickness_source: Literal['equal_minima', 'structural_minimum', 'required_minimum']


class DamageThinningCladOutput(Model):
    remaining_cladding_at_baseline_m: NonNegative
    cladding_depletion_age_years: NonNegative | None
    cladding_baseline_state: Literal['already_depleted', 'noncorroding_present', 'finite_depletion']
    wall_loss_fraction: NonNegative
    cladding_wall_loss_m: NonNegative
    base_material_wall_loss_m: NonNegative
    base_material_exposure_years: NonNegative
    predicted_remaining_thickness_m: float
    predicted_penetration: bool
    wall_loss_branch: Literal['base_only_eq2_13', 'noncorroding_cladding_extension', 'cladding_only_eq2_14', 'cladding_then_base_eq2_15']
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    strength_ratio: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']


class DamageThinningUncladDesignOutput(Model):
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    governing_minimum_thickness_m: NonNegative
    governing_thickness_source: Literal['equal_minima', 'structural_minimum', 'required_minimum']
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative


class DamageThinningMonitoringRowOutput(Model):
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None


class DamageThinningMonitoringTableFactorOutput(Model):
    table_monitoring_factor: NonNegative


class DamageThinningOnlineMonitoringFactorOutput(Model):
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool


class DamageThinningInjectionPointFactorOutput(Model):
    injection_point_factor: NonNegative


class DamageThinningDeadlegFactorOutput(Model):
    deadleg_factor: NonNegative


class DamageThinningConditionalAdjustmentOutput(Model):
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative


class DamageThinningUncladQualifiedOutput(Model):
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']


class DamageThinningCladQualifiedOutput(Model):
    remaining_cladding_at_baseline_m: NonNegative
    cladding_depletion_age_years: NonNegative | None
    cladding_baseline_state: Literal['already_depleted', 'noncorroding_present', 'finite_depletion']
    wall_loss_fraction: NonNegative
    cladding_wall_loss_m: NonNegative
    base_material_wall_loss_m: NonNegative
    base_material_exposure_years: NonNegative
    predicted_remaining_thickness_m: float
    predicted_penetration: bool
    wall_loss_branch: Literal['base_only_eq2_13', 'noncorroding_cladding_extension', 'cladding_only_eq2_14', 'cladding_then_base_eq2_15']
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    strength_ratio: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative


class DamageLiningEffectiveAgeOutput(Model):
    effective_age_years: NonNegative
    elapsed_service_years: NonNegative
    age_baseline_date: str
    age_baseline_source: Literal['qualified_ab_inspection', 'installation']
    reset_inspection_id: str | None
    qualified_ab_inspection_count: int
    age_basis_policy: Literal['step1_installation_or_last_ab', 'figure51_organic_service_only']


class DamageLiningBaseFactorOutput(Model):
    base_damage_factor: NonNegative
    lower_age_row_years: NonNegative
    upper_age_row_years: NonNegative
    age_interpolation_weight: NonNegative
    first_year_value_used: bool
    source_table: Literal['5.4', '5.5']


class DamageLiningConditionFactorOutput(Model):
    condition_factor: NonNegative


class DamageLiningMonitoringFactorOutput(Model):
    monitoring_factor: NonNegative


class DamageLiningGoverningThinningOutput(Model):
    governing_thinning_damage_factor: NonNegative
    governing_source: Literal['equal', 'lining', 'base_material_thinning']


class DamageLiningAssessmentOutput(Model):
    effective_age_years: NonNegative
    elapsed_service_years: NonNegative
    age_baseline_date: str
    age_baseline_source: Literal['qualified_ab_inspection', 'installation']
    reset_inspection_id: str | None
    qualified_ab_inspection_count: int
    age_basis_policy: Literal['step1_installation_or_last_ab', 'figure51_organic_service_only']
    base_damage_factor: NonNegative
    lower_age_row_years: NonNegative
    upper_age_row_years: NonNegative
    age_interpolation_weight: NonNegative
    first_year_value_used: bool
    source_table: Literal['5.4', '5.5']
    condition_factor: NonNegative
    monitoring_factor: NonNegative
    lining_damage_factor: NonNegative
    governing_thinning_damage_factor: NonNegative
    governing_source: Literal['equal', 'lining', 'base_material_thinning']
    base_material_thinning_damage_factor: NonNegative


class DamageCoolingWaterPhCoefficientsOutput(Model):
    c1: NonNegative
    c2: NonNegative
    c3: NonNegative
    c4: NonNegative
    c4_printed_literal_used: bool


class DamageCoolingWaterRateFactorsOutput(Model):
    scale_potential: bool
    deposit_risk: bool
    biological_or_mic_risk: bool
    underdeposit_risk: bool
    factor_flags: list[str]


class DamageCoolingWaterSaturationPhOutput(Model):
    saturation_ph: float


class DamageCoolingWaterStabilityIndicesOutput(Model):
    langelier_saturation_index: float
    ryznar_stability_index: float


class DamageCoolingWaterBaseRateOutput(Model):
    base_corrosion_rate_m_year: NonNegative
    base_column: Literal['unprotected_high', 'scaling_low']
    base_velocity_threshold_m_s: NonNegative


class DamageCoolingWaterTemperatureFactorOutput(Model):
    temperature_factor: NonNegative
    temperature_table_argument: float
    misordered_row_ignored: bool


class DamageCoolingWaterVelocityFactorOutput(Model):
    velocity_factor: NonNegative


class DamageCoolingWaterRateEquationOutput(Model):
    corrosion_rate_m_year: NonNegative


class DamageCoolingWaterSeawaterRateOutput(Model):
    corrosion_rate_m_year: NonNegative


class DamageCoolingWaterCouponPittingRateOutput(Model):
    pitting_corrosion_rate_m_year: NonNegative


class DamageCoolingWaterFreshAssessmentOutput(Model):
    langelier_saturation_index: float
    ryznar_stability_index: float
    base_corrosion_rate_m_year: NonNegative
    base_column: Literal['unprotected_high', 'scaling_low']
    base_velocity_threshold_m_s: NonNegative
    temperature_factor: NonNegative
    temperature_table_argument: float
    misordered_row_ignored: bool
    velocity_factor: NonNegative
    corrosion_rate_m_year: NonNegative


class DamageCoolingWaterThinningAssessmentOutput(Model):
    langelier_saturation_index: float
    ryznar_stability_index: float
    base_corrosion_rate_m_year: NonNegative
    base_column: Literal['unprotected_high', 'scaling_low']
    base_velocity_threshold_m_s: NonNegative
    temperature_factor: NonNegative
    temperature_table_argument: float
    misordered_row_ignored: bool
    velocity_factor: NonNegative
    corrosion_rate_m_year: NonNegative
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    thinning_type: Literal['general', 'local']


class DamageCoolingWaterTreatmentBoundsOutput(Model):
    general_upper_bound_m_year: NonNegative
    pitting_upper_bound_m_year: NonNegative
    source_rate_relation: Literal['strictly_less_than']


class DamageCoolingWaterSystemTypeOutput(Model):
    system: Literal['once_through', 'closed_recirculated', 'open_recirculated']
    water_source: Literal['fresh', 'seawater', 'brackish', 'unknown']
    requires_continual_makeup: bool
    has_evaporation_or_blowdown_loss: bool
    classification_basis: Literal['supplied_operating_premise']


class DamageCoolingWaterOtherMaterialEstimateOutput(Model):
    nominal_corrosion_rate_m_year: NonNegative


class DamageCoolingWaterMeasuredRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    selection_source: Literal['component_measurement', 'coupon_general', 'coupon_pitting_rule']


class DamageCoolingWaterRateSelectionOutput(Model):
    corrosion_rate_m_year: NonNegative
    selection_source: Literal['component_measurement', 'coupon_general', 'coupon_pitting_rule', 'freshwater_model', 'seawater_model', 'treated_screening_bound', 'treated_owner_rate', 'other_material_nominal']
    assessment_distribution: Literal['general', 'local']
    source_strict_upper_bound_m_year: NonNegative | None
    selected_rate_is_screening_bound: bool
    fallback_ignored_due_to_measurement: bool


class DamageCoolingWaterSelectedThinningOutput(Model):
    corrosion_rate_m_year: NonNegative
    selection_source: Literal['component_measurement', 'coupon_general', 'coupon_pitting_rule', 'freshwater_model', 'seawater_model', 'treated_screening_bound', 'treated_owner_rate', 'other_material_nominal']
    assessment_distribution: Literal['general', 'local']
    source_strict_upper_bound_m_year: NonNegative | None
    selected_rate_is_screening_bound: bool
    fallback_ignored_due_to_measurement: bool
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']


class DamageCo2RelativeHumidityOutput(Model):
    water_dry_gas_mass_ratio: NonNegative
    relative_humidity_fraction: NonNegative
    supersaturated: bool
    saturated: bool


class DamageCo2DewPointOutput(Model):
    dew_point_temperature_k: NonNegative


class DamageCo2TemperaturePhFactorOutput(Model):
    temperature_ph_factor: NonNegative
    sharp_temperature_interval_interpolated: bool


class DamageCo2PhEstimateOutput(Model):
    estimated_ph: float


class DamageCo2FugacityOutput(Model):
    fugacity_pa: NonNegative
    fugacity_coefficient: NonNegative


class DamageCo2ReynoldsOutput(Model):
    reynolds_number: NonNegative


class DamageCo2FrictionFactorOutput(Model):
    friction_factor: NonNegative


class DamageCo2ShearStressOutput(Model):
    shear_stress_pa: NonNegative


class DamageCo2BaseRateOutput(Model):
    base_corrosion_rate_m_year: NonNegative
    applied_shear_stress_pa: NonNegative
    shear_cap_applied: bool


class DamageCo2GlycolFactorOutput(Model):
    glycol_factor: NonNegative
    glycol_floor_applied: bool


class DamageCo2RateAdjustmentOutput(Model):
    glycol_factor: NonNegative
    inhibitor_factor: NonNegative
    applied_reduction_factor: NonNegative
    corrosion_rate_m_year: NonNegative


class DamageCo2CorrosionAssessmentOutput(Model):
    glycol_factor: NonNegative
    inhibitor_factor: NonNegative
    applied_reduction_factor: NonNegative
    corrosion_rate_m_year: NonNegative
    base_corrosion_rate_m_year: NonNegative
    calculation_branch: Literal['no_free_water', 'no_co2', 'wet_carbonic_acid_model']
    model_ph: float | None
    temperature_ph_factor: NonNegative | None
    fugacity_pa: NonNegative | None
    requested_shear_stress_pa: NonNegative | None
    applied_shear_stress_pa: NonNegative | None
    shear_cap_applied: bool
    sharp_temperature_interval_interpolated: bool


class DamageCo2ThinningAssessmentOutput(Model):
    glycol_factor: NonNegative
    inhibitor_factor: NonNegative
    applied_reduction_factor: NonNegative
    corrosion_rate_m_year: NonNegative
    base_corrosion_rate_m_year: NonNegative
    calculation_branch: Literal['no_free_water', 'no_co2', 'wet_carbonic_acid_model']
    model_ph: float | None
    temperature_ph_factor: NonNegative | None
    fugacity_pa: NonNegative | None
    requested_shear_stress_pa: NonNegative | None
    applied_shear_stress_pa: NonNegative | None
    shear_cap_applied: bool
    sharp_temperature_interval_interpolated: bool
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']


class PropertiesCo2PartialPressureOutput(Model):
    co2_partial_pressure_pa_abs: NonNegative


class DamageCo2ReynoldsMassFlowOutput(Model):
    mass_flux_kg_m2_s: NonNegative
    reynolds_number: NonNegative


class DamageCo2MaterialScreenOutput(Model):
    material_screen_decision: Literal['evaluate_co2', 'source_assumed_resistant', 'not_covered']
    source_material_resistance_assumed: bool


class DamageCo2HydrocarbonWettingScreenOutput(Model):
    wetting_screen_decision: Literal['figure_low_water_high_velocity_exemption', 'proceed_to_water_check']
    water_content_percent_used: NonNegative | None
    source_water_default_used: bool


class DamageCo2MoistureScreenOutput(Model):
    free_water_screen_state: Literal['present', 'absent', 'indeterminate']
    free_water_assumed_from_missing_data: bool


class DamageCo2ScreenedAssessmentOutput(Model):
    glycol_factor: NonNegative
    inhibitor_factor: NonNegative
    applied_reduction_factor: NonNegative
    corrosion_rate_m_year: NonNegative
    base_corrosion_rate_m_year: NonNegative
    model_ph: float | None
    temperature_ph_factor: NonNegative | None
    fugacity_pa: NonNegative | None
    requested_shear_stress_pa: NonNegative | None
    applied_shear_stress_pa: NonNegative | None
    shear_cap_applied: bool
    sharp_temperature_interval_interpolated: bool
    co2_partial_pressure_pa_abs: NonNegative
    material_screen_decision: Literal['evaluate_co2', 'source_assumed_resistant', 'not_covered']
    source_material_resistance_assumed: bool
    wetting_screen_decision: Literal['figure_low_water_high_velocity_exemption', 'proceed_to_water_check'] | None
    water_content_percent_used: NonNegative | None
    source_water_default_used: bool
    free_water_screen_state: Literal['present', 'absent', 'indeterminate'] | None
    free_water_assumed_from_missing_data: bool
    screened_calculation_branch: Literal['source_material_resistance', 'no_co2', 'figure_hydrocarbon_exemption', 'qualified_no_free_water', 'wet_carbonic_acid_model']


class DamageCo2ScreenedThinningOutput(Model):
    glycol_factor: NonNegative
    inhibitor_factor: NonNegative
    applied_reduction_factor: NonNegative
    corrosion_rate_m_year: NonNegative
    base_corrosion_rate_m_year: NonNegative
    model_ph: float | None
    temperature_ph_factor: NonNegative | None
    fugacity_pa: NonNegative | None
    requested_shear_stress_pa: NonNegative | None
    applied_shear_stress_pa: NonNegative | None
    shear_cap_applied: bool
    sharp_temperature_interval_interpolated: bool
    co2_partial_pressure_pa_abs: NonNegative
    material_screen_decision: Literal['evaluate_co2', 'source_assumed_resistant', 'not_covered']
    source_material_resistance_assumed: bool
    wetting_screen_decision: Literal['figure_low_water_high_velocity_exemption', 'proceed_to_water_check'] | None
    water_content_percent_used: NonNegative | None
    source_water_default_used: bool
    free_water_screen_state: Literal['present', 'absent', 'indeterminate'] | None
    free_water_assumed_from_missing_data: bool
    screened_calculation_branch: Literal['source_material_resistance', 'no_co2', 'figure_hydrocarbon_exemption', 'qualified_no_free_water', 'wet_carbonic_acid_model']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']


class DamageOxidationScreenOutput(Model):
    screen_temperature_threshold_k: NonNegative
    temperature_screen_met: bool
    evaluate_high_temperature_oxidation: bool


class DamageOxidationTableRowOutput(Model):
    temperature_nodes_k: list[NonNegative]
    corrosion_rates_m_year: list[NonNegative | None]
    native_rates: list[NonNegative | None]
    native_rate_unit: Literal['mm/year', 'mpy']
    source_table_ids: list[str]


class DamageOxidationRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    lower_temperature_node_k: NonNegative
    upper_temperature_node_k: NonNegative
    interpolation_weight: NonNegative
    rate_calculation_basis: Literal['qualified_first_node', 'exact_cell', 'upper_temperature_node', 'linear_between_nodes']
    first_node_value_used: bool


class DamageOxidationAssessmentOutput(Model):
    screen_temperature_threshold_k: NonNegative
    temperature_screen_met: bool
    evaluate_high_temperature_oxidation: bool
    corrosion_rate_m_year: NonNegative
    lower_temperature_node_k: NonNegative
    upper_temperature_node_k: NonNegative
    interpolation_weight: NonNegative
    rate_calculation_basis: Literal['qualified_first_node', 'exact_cell', 'upper_temperature_node', 'linear_between_nodes']
    first_node_value_used: bool
    thinning_type: Literal['general']


class DamageOxidationThinningAssessmentOutput(Model):
    screen_temperature_threshold_k: NonNegative
    temperature_screen_met: bool
    evaluate_high_temperature_oxidation: bool
    corrosion_rate_m_year: NonNegative
    lower_temperature_node_k: NonNegative
    upper_temperature_node_k: NonNegative
    interpolation_weight: NonNegative
    rate_calculation_basis: Literal['qualified_first_node', 'exact_cell', 'upper_temperature_node', 'linear_between_nodes']
    first_node_value_used: bool
    thinning_type: Literal['general']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']


class DamageAcidSourWaterRouteOutput(Model):
    corrosion_route: Literal['no_free_water', 'hydrochloric_acid', 'alkaline_sour_water', 'neutral_boundary_unclassified', 'acid_sour_water']


class DamageAcidSourWaterBaseRateOutput(Model):
    base_corrosion_rate_m_year: NonNegative
    ph_for_lookup: NonNegative
    ph_edge_row_used: bool


class DamageAcidSourWaterOxygenFactorOutput(Model):
    oxygen_factor: NonNegative
    high_oxygen_localized_review: bool


class DamageAcidSourWaterVelocityFactorOutput(Model):
    velocity_factor: NonNegative
    high_velocity_localized_review: bool


class DamageAcidSourWaterRateEquationOutput(Model):
    corrosion_rate_m_year: NonNegative


class DamageAcidSourWaterOtherMaterialRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    selected_rate_is_screening_bound: bool


class DamageAcidSourWaterAssessmentOutput(Model):
    corrosion_route: Literal['no_free_water', 'hydrochloric_acid', 'alkaline_sour_water', 'neutral_boundary_unclassified', 'acid_sour_water']
    corrosion_rate_m_year: NonNegative
    base_corrosion_rate_m_year: NonNegative | None
    ph_for_lookup: NonNegative | None
    ph_edge_row_used: bool
    oxygen_factor: NonNegative | None
    velocity_factor: NonNegative | None
    localized_attack_review_required: bool
    selected_rate_is_screening_bound: bool
    default_thinning_type: Literal['general']


class DamageAcidSourWaterThinningAssessmentOutput(Model):
    corrosion_route: Literal['no_free_water', 'hydrochloric_acid', 'alkaline_sour_water', 'neutral_boundary_unclassified', 'acid_sour_water']
    corrosion_rate_m_year: NonNegative
    base_corrosion_rate_m_year: NonNegative | None
    ph_for_lookup: NonNegative | None
    ph_edge_row_used: bool
    oxygen_factor: NonNegative | None
    velocity_factor: NonNegative | None
    localized_attack_review_required: bool
    selected_rate_is_screening_bound: bool
    default_thinning_type: Literal['general']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class PropertiesH2sPartialPressureOutput(Model):
    h2s_partial_pressure_pa_abs: NonNegative


class DamageAlkalineSourWaterNh4hsEstimateOutput(Model):
    estimated_nh4hs_mass_fraction: NonNegative
    concentration_estimate_branch: Literal['printed_excess_h2s', 'printed_lower_h2s', 'qualified_equality_upper', 'qualified_equality_lower']
    estimated_fraction_exceeds_one: bool


class DamageAlkalineSourWaterVelocitySelectionOutput(Model):
    selected_velocity_m_s: NonNegative
    selected_velocity_phase: Literal['vapor', 'liquid']


class DamageAlkalineSourWaterBaseRateOutput(Model):
    baseline_corrosion_rate_m_year: NonNegative


class DamageAlkalineSourWaterPressureAdjustmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    unclamped_pressure_factor: float
    pressure_correction_factor: NonNegative
    negative_pressure_factor_clamped: bool
    pressure_correction_branch: Literal['at_reference', 'below_reference', 'above_reference']


class DamageAlkalineSourWaterAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    baseline_corrosion_rate_m_year: NonNegative | None
    nh4hs_mass_fraction_used: NonNegative | None
    concentration_source: Literal['supplied', 'source_approximation'] | None
    selected_velocity_m_s: NonNegative | None
    selected_velocity_phase: Literal['vapor', 'liquid'] | None
    unclamped_pressure_factor: float | None
    pressure_correction_factor: NonNegative | None
    negative_pressure_factor_clamped: bool
    pressure_correction_branch: Literal['at_reference', 'below_reference', 'above_reference'] | None
    source_thinning_type: Literal['general', 'local'] | None
    calculation_branch: Literal['no_free_water', 'wet_nh4hs_model']


class DamageAlkalineSourWaterThinningAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    baseline_corrosion_rate_m_year: NonNegative | None
    nh4hs_mass_fraction_used: NonNegative | None
    concentration_source: Literal['supplied', 'source_approximation'] | None
    selected_velocity_m_s: NonNegative | None
    selected_velocity_phase: Literal['vapor', 'liquid'] | None
    unclamped_pressure_factor: float | None
    pressure_correction_factor: NonNegative | None
    negative_pressure_factor_clamped: bool
    pressure_correction_branch: Literal['at_reference', 'below_reference', 'above_reference'] | None
    source_thinning_type: Literal['general', 'local'] | None
    calculation_branch: Literal['no_free_water', 'wet_nh4hs_model']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class DamageSourWaterAssessmentOutput(Model):
    corrosion_route: Literal['no_free_water', 'hydrochloric_acid', 'alkaline_sour_water', 'neutral_boundary_unclassified', 'acid_sour_water']
    corrosion_rate_m_year: NonNegative
    selected_model_base_rate_m_year: NonNegative | None
    selected_rate_is_screening_bound: bool
    localized_attack_review_required: bool


class DamageHclPhFromChlorideOutput(Model):
    estimated_ph: NonNegative
    chloride_band_lower_wppm: NonNegative
    chloride_band_upper_wppm: NonNegative
    chloride_band_upper_inclusive: bool


class DamageHclChlorideIntervalFromPhOutput(Model):
    chloride_band_lower_wppm: NonNegative
    chloride_band_upper_wppm: NonNegative
    chloride_band_upper_inclusive: bool


class DamageHclPhRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_999_corner_used: bool
    localized_pitting_already_included: bool
    source_table_id: str


class DamageHclAlloyRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_999_corner_used: bool
    localized_pitting_already_included: bool
    source_table_id: str


class DamageHclAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_999_corner_used: bool
    localized_pitting_already_included: bool
    source_table_id: str | None
    ph_used: NonNegative | None
    chloride_mass_fraction_used: Fraction | None
    chemistry_method: Literal['supplied_ph', 'chloride_table', 'supplied_chloride', 'ph_interval_selection'] | None
    source_thinning_type: Literal['local'] | None
    calculation_branch: Literal['no_free_water', 'wet_dilute_hcl_model']


class DamageHclThinningAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_999_corner_used: bool
    localized_pitting_already_included: bool
    source_table_id: str | None
    ph_used: NonNegative | None
    chloride_mass_fraction_used: Fraction | None
    chemistry_method: Literal['supplied_ph', 'chloride_table', 'supplied_chloride', 'ph_interval_selection'] | None
    source_thinning_type: Literal['local'] | None
    calculation_branch: Literal['no_free_water', 'wet_dilute_hcl_model']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class DamageHfConcentrationSelectionOutput(Model):
    hf_mass_fraction_for_lookup: Fraction
    concentrated_81_node_extension_used: bool


class DamageHfCarbonVelocityBandOutput(Model):
    velocity_band: Literal['low', 'high']
    velocity_threshold_m_s: NonNegative


class DamageHfCarbonRateOutput(Model):
    hf_mass_fraction_for_lookup: Fraction
    concentrated_81_node_extension_used: bool
    velocity_band: Literal['low', 'high']
    velocity_threshold_m_s: NonNegative
    corrosion_rate_m_year: NonNegative
    source_999_corner_used: bool
    residual_column_used: Literal['low', 'high'] | None
    source_table_id: str


class DamageHfAlloy400RateOutput(Model):
    hf_mass_fraction_for_lookup: Fraction
    concentrated_81_node_extension_used: bool
    corrosion_rate_m_year: NonNegative
    source_999_corner_used: bool
    source_table_id: str


class DamageHfAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_table_id: str | None
    rate_source: Literal['carbon_steel_table', 'alloy400_table', 'qualified_published_rate'] | None
    source_999_corner_used: bool
    hf_mass_fraction_for_lookup: Fraction | None
    concentrated_81_node_extension_used: bool
    velocity_band: Literal['low', 'high'] | None
    velocity_threshold_m_s: NonNegative | None
    residual_column_used: Literal['low', 'high'] | None
    source_thinning_type: Literal['general', 'local'] | None
    calculation_branch: Literal['no_hf_exposure', 'qualified_hf_service']


class DamageHfThinningAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_table_id: str | None
    rate_source: Literal['carbon_steel_table', 'alloy400_table', 'qualified_published_rate'] | None
    source_999_corner_used: bool
    hf_mass_fraction_for_lookup: Fraction | None
    concentrated_81_node_extension_used: bool
    velocity_band: Literal['low', 'high'] | None
    velocity_threshold_m_s: NonNegative | None
    residual_column_used: Literal['low', 'high'] | None
    source_thinning_type: Literal['general', 'local'] | None
    calculation_branch: Literal['no_hf_exposure', 'qualified_hf_service']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class DamageAmineAcidGasLoadingOutput(Model):
    acid_gas_loading_mol_mol: NonNegative


class DamageAmineLoadingSelectionOutput(Model):
    lower_loading_row_index: int
    upper_loading_row_index: int
    loading_interpolation_weight: Fraction
    table_loading_regime: Literal['lean', 'rich']
    loading_gap_mapping_used: bool


class DamageAmineContaminantRowOutput(Model):
    contaminant_row: Literal['low', 'middle', 'high']
    printed_hsas_row_mass_fraction: Fraction


class DamageAmineStrengthFactorOutput(Model):
    amine_strength_factor: NonNegative


class DamageAmineCarbonBaseRateOutput(Model):
    lower_loading_row_index: int
    upper_loading_row_index: int
    loading_interpolation_weight: Fraction
    table_loading_regime: Literal['lean', 'rich']
    loading_gap_mapping_used: bool
    base_corrosion_rate_m_year: NonNegative
    velocity_band: Literal['low', 'high']
    velocity_threshold_m_s: NonNegative
    source_table_id: str


class DamageAmineStainlessRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    low_loading_first_row_used: bool
    source_table_id: str


class DamageAmineCorrosionAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    base_corrosion_rate_m_year: NonNegative | None
    amine_strength_factor: NonNegative | None
    contaminant_row: Literal['low', 'middle', 'high'] | None
    printed_hsas_row_mass_fraction: Fraction | None
    table_loading_regime: Literal['lean', 'rich'] | None
    loading_gap_mapping_used: bool
    velocity_band: Literal['low', 'high'] | None
    velocity_threshold_m_s: NonNegative | None
    low_loading_first_row_used: bool
    source_table_id: str | None
    source_thinning_type: Literal['general', 'local'] | None
    calculation_branch: Literal['no_amine_service', 'carbon_amine_model', 'type300_stainless_model']


class DamageAmineThinningAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    base_corrosion_rate_m_year: NonNegative | None
    amine_strength_factor: NonNegative | None
    contaminant_row: Literal['low', 'middle', 'high'] | None
    printed_hsas_row_mass_fraction: Fraction | None
    table_loading_regime: Literal['lean', 'rich'] | None
    loading_gap_mapping_used: bool
    velocity_band: Literal['low', 'high'] | None
    velocity_threshold_m_s: NonNegative | None
    low_loading_first_row_used: bool
    source_table_id: str | None
    source_thinning_type: Literal['general', 'local'] | None
    calculation_branch: Literal['no_amine_service', 'carbon_amine_model', 'type300_stainless_model']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class DamageSulfuricTableAxesOutput(Model):
    acid_mass_fraction_nodes: list[Fraction]
    temperature_nodes_k: list[NonNegative]
    velocity_nodes_m_s: list[NonNegative]
    source_table_id: str
    carbon_si_velocity_interpretation: Literal['not_applicable', 'qualified_printed_m_s', 'qualified_us_ft_s_header']


class DamageSulfuricTableRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_table_id: str
    carbon_si_velocity_interpretation: Literal['not_applicable', 'qualified_printed_m_s', 'qualified_us_ft_s_header']
    source_999_corner_used: bool
    disputed_304_cell_used: bool
    source_localized_enhancement_already_included: bool


class DamageSulfuricThinningClassificationOutput(Model):
    source_thinning_type: Literal['general', 'local']
    thinning_velocity_threshold_m_s: NonNegative
    thinning_velocity_boundary_resolved: bool


class DamageSulfuricCorrosionAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_table_id: str | None
    carbon_si_velocity_interpretation: Literal['not_applicable', 'qualified_printed_m_s', 'qualified_us_ft_s_header']
    source_999_corner_used: bool
    disputed_304_cell_used: bool
    source_localized_enhancement_already_included: bool
    source_thinning_type: Literal['general', 'local'] | None
    thinning_velocity_threshold_m_s: NonNegative | None
    thinning_velocity_boundary_resolved: bool
    rate_source: Literal['source_maximum_estimate', 'qualified_specialist_estimate'] | None
    calculation_branch: Literal['no_sulfuric_service', 'qualified_sulfuric_service']


class DamageSulfuricThinningAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_table_id: str | None
    carbon_si_velocity_interpretation: Literal['not_applicable', 'qualified_printed_m_s', 'qualified_us_ft_s_header']
    source_999_corner_used: bool
    disputed_304_cell_used: bool
    source_localized_enhancement_already_included: bool
    source_thinning_type: Literal['general', 'local'] | None
    thinning_velocity_threshold_m_s: NonNegative | None
    thinning_velocity_boundary_resolved: bool
    rate_source: Literal['source_maximum_estimate', 'qualified_specialist_estimate'] | None
    calculation_branch: Literal['no_sulfuric_service', 'qualified_sulfuric_service']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class DamageH2sh2TableAxesOutput(Model):
    h2s_mole_fraction_nodes: list[Fraction]
    temperature_nodes_k: list[NonNegative]
    table_group: Literal['carbon_low_alloy', 'cr5', 'cr7', 'cr9', 'cr12', 'stainless']
    hydrocarbon_curve_required: bool
    source_table_id: str


class DamageH2sh2TableRateOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_table_id: str
    selected_hydrocarbon_curve: Literal['naphtha', 'gas_oil'] | None
    hydrocarbon_free_curve_selection_used: bool
    source_thinning_type: Literal['general']


class DamageH2sh2CorrosionAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_table_id: str | None
    selected_hydrocarbon_curve: Literal['naphtha', 'gas_oil'] | None
    hydrocarbon_free_curve_selection_used: bool
    source_thinning_type: Literal['general'] | None
    calculation_branch: Literal['no_h2s_h2_service', 'qualified_high_temperature_h2s_h2']


class DamageH2sh2ThinningAssessmentOutput(Model):
    corrosion_rate_m_year: NonNegative
    source_table_id: str | None
    selected_hydrocarbon_curve: Literal['naphtha', 'gas_oil'] | None
    hydrocarbon_free_curve_selection_used: bool
    source_thinning_type: Literal['general'] | None
    calculation_branch: Literal['no_h2s_h2_service', 'qualified_high_temperature_h2s_h2']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class DamageSulfidicMaterialSelectionOutput(Model):
    table_group: Literal['carbon_steel', 'low_alloy', 'cr5', 'cr7', 'cr9', 'cr12', 'stainless_no_mo', 'stainless_low_mo', 'stainless_high_mo']
    unknown_molybdenum_low_assumed: bool


class DamageSulfidicTableAxesOutput(Model):
    table_group: Literal['carbon_steel', 'low_alloy', 'cr5', 'cr7', 'cr9', 'cr12', 'stainless_no_mo', 'stainless_low_mo', 'stainless_high_mo']
    unknown_molybdenum_low_assumed: bool
    sulfur_mass_fraction_nodes: list[Fraction]
    tan_nodes_mg_koh_g: list[NonNegative]
    lower_temperature_bin_upper_k: NonNegative
    interior_temperature_nodes_k: list[NonNegative]
    upper_temperature_bin_lower_exclusive_k: NonNegative
    source_table_id: str


class DamageSulfidicTableRateOutput(Model):
    base_corrosion_rate_m_year: NonNegative
    source_table_id: str
    table_group: Literal['carbon_steel', 'low_alloy', 'cr5', 'cr7', 'cr9', 'cr12', 'stainless_no_mo', 'stainless_low_mo', 'stainless_high_mo']
    unknown_molybdenum_low_assumed: bool
    source_temperature_bin_used: Literal['lower', 'upper'] | None
    first_temperature_threshold_anchor_used: bool
    below_first_tan_row_used: bool


class DamageSulfidicVelocityFactorOutput(Model):
    velocity_factor: NonNegative
    velocity_boundary_conflict_encountered: bool


class DamageSulfidicThinningClassificationOutput(Model):
    source_thinning_type: Literal['general', 'local']


class DamageSulfidicCorrosionAssessmentOutput(Model):
    base_corrosion_rate_m_year: NonNegative | None
    source_table_id: str | None
    table_group: Literal['carbon_steel', 'low_alloy', 'cr5', 'cr7', 'cr9', 'cr12', 'stainless_no_mo', 'stainless_low_mo', 'stainless_high_mo'] | None
    unknown_molybdenum_low_assumed: bool
    source_temperature_bin_used: Literal['lower', 'upper'] | None
    first_temperature_threshold_anchor_used: bool
    below_first_tan_row_used: bool
    velocity_factor: NonNegative | None
    velocity_boundary_conflict_encountered: bool
    source_thinning_type: Literal['general', 'local'] | None
    corrosion_rate_m_year: NonNegative
    calculation_branch: Literal['no_sulfidic_service', 'qualified_sulfidic_naphthenic_service']


class DamageSulfidicThinningAssessmentOutput(Model):
    base_corrosion_rate_m_year: NonNegative | None
    source_table_id: str | None
    table_group: Literal['carbon_steel', 'low_alloy', 'cr5', 'cr7', 'cr9', 'cr12', 'stainless_no_mo', 'stainless_low_mo', 'stainless_high_mo'] | None
    unknown_molybdenum_low_assumed: bool
    source_temperature_bin_used: Literal['lower', 'upper'] | None
    first_temperature_threshold_anchor_used: bool
    below_first_tan_row_used: bool
    velocity_factor: NonNegative | None
    velocity_boundary_conflict_encountered: bool
    source_thinning_type: Literal['general', 'local'] | None
    corrosion_rate_m_year: NonNegative
    calculation_branch: Literal['no_sulfidic_service', 'qualified_sulfidic_naphthenic_service']
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class PropertiesPureFluidFlashOutput(Model):
    flashed_temperature_k: NonNegative
    vapor_mass_fraction: Fraction
    flashed_phase: Literal['twophase', 'liquid', 'supercritical_liquid', 'gas', 'supercritical_gas']
    bulk_density_kg_m3: NonNegative
    conserved_property: Literal['Smass', 'Hmass']
    conserved_value_si: float
    engine_version: str
    storage_phase: Literal['liquid', 'supercritical_liquid', 'gas', 'supercritical_gas', 'twophase']
    storage_vapor_mass_fraction: Fraction
    vapor_mass_fraction_change: float
    storage_temperature_k: NonNegative
    storage_state_basis: Literal['pressure_temperature', 'pressure_quality']


class ReleasePureLiquidFlashPartitionOutput(Model):
    flashed_temperature_k: NonNegative
    vapor_mass_fraction: Fraction
    flashed_phase: Literal['twophase', 'liquid', 'supercritical_liquid', 'gas', 'supercritical_gas']
    bulk_density_kg_m3: NonNegative
    conserved_property: Literal['Smass', 'Hmass']
    conserved_value_si: float
    engine_version: str
    storage_phase: Literal['liquid', 'supercritical_liquid', 'gas', 'supercritical_gas', 'twophase']
    storage_vapor_mass_fraction: Fraction
    vapor_mass_fraction_change: float
    storage_temperature_k: NonNegative
    storage_state_basis: Literal['pressure_temperature', 'pressure_quality']
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative
    pool_liquid_mass_kg: NonNegative
    jet_total_mass_kg: NonNegative
    jet_liquid_rate_kg_s: NonNegative
    jet_vapor_rate_kg_s: NonNegative
    jet_liquid_mass_kg: NonNegative
    jet_vapor_mass_kg: NonNegative
    rainout_mass_fraction: Fraction


class PropertiesPureFluidSaturationPressureOutput(Model):
    saturation_pressure_pa_abs: NonNegative
    bubble_temperature_k: NonNegative
    dew_temperature_k: NonNegative
    liquid_density_kg_m3: NonNegative
    vapor_density_kg_m3: NonNegative
    liquid_specific_heat_j_kg_k: NonNegative
    vapor_specific_heat_j_kg_k: NonNegative
    latent_heat_j_kg: NonNegative
    molecular_weight_kg_kmol: NonNegative
    engine_version: str


class PropertiesPureFluidSaturationTemperatureOutput(Model):
    saturation_pressure_pa_abs: NonNegative
    bubble_temperature_k: NonNegative
    dew_temperature_k: NonNegative
    liquid_density_kg_m3: NonNegative
    vapor_density_kg_m3: NonNegative
    liquid_specific_heat_j_kg_k: NonNegative
    vapor_specific_heat_j_kg_k: NonNegative
    latent_heat_j_kg: NonNegative
    molecular_weight_kg_kmol: NonNegative
    engine_version: str


class DispersionFlashedBoilingPoolCentrelineOutput(Model):
    flashed_temperature_k: NonNegative
    vapor_mass_fraction: Fraction
    flashed_phase: Literal['twophase', 'liquid', 'supercritical_liquid', 'gas', 'supercritical_gas']
    bulk_density_kg_m3: NonNegative
    conserved_property: Literal['Smass', 'Hmass']
    conserved_value_si: float
    engine_version: str
    storage_phase: Literal['liquid', 'supercritical_liquid', 'gas', 'supercritical_gas', 'twophase']
    storage_vapor_mass_fraction: Fraction
    vapor_mass_fraction_change: float
    storage_temperature_k: NonNegative
    storage_state_basis: Literal['pressure_temperature', 'pressure_quality']
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative
    pool_liquid_mass_kg: NonNegative
    jet_total_mass_kg: NonNegative
    jet_liquid_rate_kg_s: NonNegative
    jet_vapor_rate_kg_s: NonNegative
    jet_liquid_mass_kg: NonNegative
    jet_vapor_mass_kg: NonNegative
    rainout_mass_fraction: Fraction
    saturation_pressure_pa_abs: NonNegative
    bubble_temperature_k: NonNegative
    dew_temperature_k: NonNegative
    liquid_density_kg_m3: NonNegative
    vapor_density_kg_m3: NonNegative
    liquid_specific_heat_j_kg_k: NonNegative
    vapor_specific_heat_j_kg_k: NonNegative
    latent_heat_j_kg: NonNegative
    molecular_weight_kg_kmol: NonNegative
    equilibrium_evaporation_rate_kg_s: NonNegative
    vapor_volumetric_rate_m3_s: NonNegative
    time_to_steady_s: NonNegative | None
    pool_radius_m: NonNegative
    pool_area_m2: NonNegative
    vapor_source_rate_kg_s: NonNegative | None
    support_status: Literal['supported', 'duration_limited', 'area_limited', 'duration_and_area_limited', 'no_feed']
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    effective_source_half_width_m: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: NonNegative
    spatial_output_scope: Literal['centreline_only_no_footprint_area']
    steady_window_start_s: NonNegative
    steady_window_duration_s: NonNegative
    steady_evaporated_mass_kg: NonNegative
    startup_unmodeled_pool_mass_kg: NonNegative
    integration_scope: Literal['flashed_pure_liquid_boiling_pool_steady_window_centreline']


class DispersionFlashedBoilingPoolFootprintOutput(Model):
    flashed_temperature_k: NonNegative
    vapor_mass_fraction: Fraction
    flashed_phase: Literal['twophase', 'liquid', 'supercritical_liquid', 'gas', 'supercritical_gas']
    bulk_density_kg_m3: NonNegative
    conserved_property: Literal['Smass', 'Hmass']
    conserved_value_si: float
    engine_version: str
    storage_phase: Literal['liquid', 'supercritical_liquid', 'gas', 'supercritical_gas', 'twophase']
    storage_vapor_mass_fraction: Fraction
    vapor_mass_fraction_change: float
    storage_temperature_k: NonNegative
    storage_state_basis: Literal['pressure_temperature', 'pressure_quality']
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative
    pool_liquid_mass_kg: NonNegative
    jet_total_mass_kg: NonNegative
    jet_liquid_rate_kg_s: NonNegative
    jet_vapor_rate_kg_s: NonNegative
    jet_liquid_mass_kg: NonNegative
    jet_vapor_mass_kg: NonNegative
    rainout_mass_fraction: Fraction
    saturation_pressure_pa_abs: NonNegative
    bubble_temperature_k: NonNegative
    dew_temperature_k: NonNegative
    liquid_density_kg_m3: NonNegative
    vapor_density_kg_m3: NonNegative
    liquid_specific_heat_j_kg_k: NonNegative
    vapor_specific_heat_j_kg_k: NonNegative
    latent_heat_j_kg: NonNegative
    molecular_weight_kg_kmol: NonNegative
    equilibrium_evaporation_rate_kg_s: NonNegative
    vapor_volumetric_rate_m3_s: NonNegative
    time_to_steady_s: NonNegative | None
    pool_radius_m: NonNegative
    pool_area_m2: NonNegative
    vapor_source_rate_kg_s: NonNegative | None
    support_status: Literal['supported', 'duration_limited', 'area_limited', 'duration_and_area_limited', 'no_feed']
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    effective_source_half_width_m: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: NonNegative
    spatial_output_scope: Literal['planar_sampled_threshold_field']
    steady_window_start_s: NonNegative
    steady_window_duration_s: NonNegative
    steady_evaporated_mass_kg: NonNegative
    startup_unmodeled_pool_mass_kg: NonNegative
    integration_scope: Literal['flashed_pure_liquid_boiling_pool_steady_window_footprint']
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached', 'premise_violated']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']
    crosswind_distance_m: list[float]
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]


class DispersionFlashedBoilingPoolFlashFireOutput(Model):
    flashed_temperature_k: NonNegative
    vapor_mass_fraction: Fraction
    flashed_phase: Literal['twophase', 'liquid', 'supercritical_liquid', 'gas', 'supercritical_gas']
    bulk_density_kg_m3: NonNegative
    conserved_property: Literal['Smass', 'Hmass']
    conserved_value_si: float
    engine_version: str
    storage_phase: Literal['liquid', 'supercritical_liquid', 'gas', 'supercritical_gas', 'twophase']
    storage_vapor_mass_fraction: Fraction
    vapor_mass_fraction_change: float
    storage_temperature_k: NonNegative
    storage_state_basis: Literal['pressure_temperature', 'pressure_quality']
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative
    pool_liquid_mass_kg: NonNegative
    jet_total_mass_kg: NonNegative
    jet_liquid_rate_kg_s: NonNegative
    jet_vapor_rate_kg_s: NonNegative
    jet_liquid_mass_kg: NonNegative
    jet_vapor_mass_kg: NonNegative
    rainout_mass_fraction: Fraction
    saturation_pressure_pa_abs: NonNegative
    bubble_temperature_k: NonNegative
    dew_temperature_k: NonNegative
    liquid_density_kg_m3: NonNegative
    vapor_density_kg_m3: NonNegative
    liquid_specific_heat_j_kg_k: NonNegative
    vapor_specific_heat_j_kg_k: NonNegative
    latent_heat_j_kg: NonNegative
    molecular_weight_kg_kmol: NonNegative
    equilibrium_evaporation_rate_kg_s: NonNegative
    vapor_volumetric_rate_m3_s: NonNegative
    time_to_steady_s: NonNegative | None
    pool_radius_m: NonNegative
    pool_area_m2: NonNegative
    vapor_source_rate_kg_s: NonNegative | None
    support_status: Literal['supported', 'duration_limited', 'area_limited', 'duration_and_area_limited', 'no_feed']
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    effective_source_half_width_m: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: Literal[0.0]
    spatial_output_scope: Literal['planar_sampled_threshold_field']
    steady_window_start_s: NonNegative
    steady_window_duration_s: NonNegative
    steady_evaporated_mass_kg: NonNegative
    startup_unmodeled_pool_mass_kg: NonNegative
    integration_scope: Literal['flashed_pure_liquid_boiling_pool_steady_window_flash_fire']
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached', 'premise_violated']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']
    crosswind_distance_m: list[float]
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    criterion_role: Literal['qualified_lfl']


class RiskAreaEventContributionOutput(Model):
    annual_release_frequency_per_year: NonNegative
    annual_selected_event_frequency_per_year: NonNegative
    event_weighted_equipment_area_m2: NonNegative
    event_weighted_personnel_area_m2: NonNegative
    equipment_area_risk_contribution_m2_per_year: NonNegative
    personnel_area_risk_contribution_m2_per_year: NonNegative
    area_risk_contribution_m2_per_year: NonNegative
    conditional_joint_probability: Fraction
    contribution_scope: Literal['selected_event_weather_case']


class RiskFlashedPoolFlashFireContributionOutput(Model):
    flashed_temperature_k: NonNegative
    vapor_mass_fraction: Fraction
    flashed_phase: Literal['twophase', 'liquid', 'supercritical_liquid', 'gas', 'supercritical_gas']
    bulk_density_kg_m3: NonNegative
    conserved_property: Literal['Smass', 'Hmass']
    conserved_value_si: float
    engine_version: str
    storage_phase: Literal['liquid', 'supercritical_liquid', 'gas', 'supercritical_gas', 'twophase']
    storage_vapor_mass_fraction: Fraction
    vapor_mass_fraction_change: float
    storage_temperature_k: NonNegative
    storage_state_basis: Literal['pressure_temperature', 'pressure_quality']
    entrained_liquid_mass_fraction: float | None
    jet_vapor_mass_fraction: Fraction | None
    physical_range: bool
    jet_fraction_nonzero: bool
    equation_basis: Literal['api581_printed', 'post_flash_mass_balance']
    pool_liquid_rate_kg_s: NonNegative
    jet_total_rate_kg_s: NonNegative
    pool_liquid_mass_kg: NonNegative
    jet_total_mass_kg: NonNegative
    jet_liquid_rate_kg_s: NonNegative
    jet_vapor_rate_kg_s: NonNegative
    jet_liquid_mass_kg: NonNegative
    jet_vapor_mass_kg: NonNegative
    rainout_mass_fraction: Fraction
    saturation_pressure_pa_abs: NonNegative
    bubble_temperature_k: NonNegative
    dew_temperature_k: NonNegative
    liquid_density_kg_m3: NonNegative
    vapor_density_kg_m3: NonNegative
    liquid_specific_heat_j_kg_k: NonNegative
    vapor_specific_heat_j_kg_k: NonNegative
    latent_heat_j_kg: NonNegative
    molecular_weight_kg_kmol: NonNegative
    equilibrium_evaporation_rate_kg_s: NonNegative
    vapor_volumetric_rate_m3_s: NonNegative
    time_to_steady_s: NonNegative | None
    pool_radius_m: NonNegative
    pool_area_m2: NonNegative
    vapor_source_rate_kg_s: NonNegative | None
    support_status: Literal['supported', 'duration_limited', 'area_limited', 'duration_and_area_limited', 'no_feed']
    engine: Literal['slabx', 'slabx-lh2']
    engine_versions: dict[str, str]
    engine_source_fingerprints: dict[str, str]
    downwind_distance_m: list[float]
    centreline_volume_fraction: list[Fraction]
    native_grid_maximum_downwind_distance_m: NonNegative
    native_threshold_distance_m: NonNegative | None
    threshold_distance_m: NonNegative | None
    threshold_status: Literal['premise_violated', 'boundary_censored', 'interpolated', 'not_reached']
    premise_status: Literal['not_evaluated', 'violated', 'within_premise']
    maximum_vertical_to_horizontal_velocity_ratio: NonNegative | None
    used_source_area_m2: NonNegative
    effective_source_half_width_m: NonNegative
    native_messages: str
    averaging_time_s: NonNegative
    receptor_height_m: Literal[0.0]
    spatial_output_scope: Literal['planar_sampled_threshold_field']
    steady_window_start_s: NonNegative
    steady_window_duration_s: NonNegative
    steady_evaporated_mass_kg: NonNegative
    startup_unmodeled_pool_mass_kg: NonNegative
    integration_scope: Literal['selected_hole_weather_steady_pool_flash_fire_risk_contribution']
    sampled_exceedance_area_m2: NonNegative
    threshold_area_m2: NonNegative | None
    footprint_status: Literal['boundary_censored', 'closed_on_supplied_grid', 'not_reached', 'premise_violated']
    boundary_sides: list[Literal['upwind', 'downwind', 'negative_crosswind', 'positive_crosswind']]
    positive_area_cell_count: int
    downwind_node_count: int
    crosswind_node_count: int
    interpolation_basis: Literal['piecewise_linear_main_diagonal_triangles']
    crosswind_distance_m: list[float]
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]
    personnel_area_m2: NonNegative
    equipment_area_m2: NonNegative
    criterion_role: Literal['qualified_lfl']
    annual_release_frequency_per_year: NonNegative
    annual_selected_event_frequency_per_year: NonNegative
    event_weighted_equipment_area_m2: NonNegative
    event_weighted_personnel_area_m2: NonNegative
    equipment_area_risk_contribution_m2_per_year: NonNegative
    personnel_area_risk_contribution_m2_per_year: NonNegative
    area_risk_contribution_m2_per_year: NonNegative
    conditional_joint_probability: Fraction
    contribution_scope: Literal['selected_hole_weather_steady_pool_flash_fire']
    generic_hole_frequency_per_year: NonNegative
    management_factor: NonNegative
    total_damage_factor: NonNegative
    selected_hole: Literal['small', 'medium', 'large', 'rupture']


class DamageGroundwaterTksOutput(Model):
    total_key_species_mg_l: NonNegative


class DamageGroundwaterRateClassificationOutput(Model):
    corrosion_rate_m_year: NonNegative
    corrosivity_category: Literal['low', 'medium', 'high', 'very_high']
    selected_unit_basis: Literal['printed_si', 'printed_us_converted']
    category_lower_bound_m_year: NonNegative
    category_upper_bound_m_year: NonNegative | None
    lower_bound_relation: Literal['inclusive', 'exclusive']
    upper_bound_relation: Literal['inclusive', 'exclusive', 'unbounded']
    shared_boundary_encountered: bool


class DamageGroundwaterAssessmentOutput(Model):
    total_key_species_mg_l: NonNegative
    corrosion_rate_m_year: NonNegative
    corrosivity_category: Literal['low', 'medium', 'high', 'very_high']
    selected_unit_basis: Literal['printed_si', 'printed_us_converted']
    category_lower_bound_m_year: NonNegative
    category_upper_bound_m_year: NonNegative | None
    lower_bound_relation: Literal['inclusive', 'exclusive']
    upper_bound_relation: Literal['inclusive', 'exclusive', 'unbounded']
    shared_boundary_encountered: bool
    rate_source: Literal['qualified_external_groundwater_rate']
    tks_to_rate_model_available: Literal[False]


class DamageGroundwaterThinningAssessmentOutput(Model):
    total_key_species_mg_l: NonNegative
    corrosion_rate_m_year: NonNegative
    corrosivity_category: Literal['low', 'medium', 'high', 'very_high']
    selected_unit_basis: Literal['printed_si', 'printed_us_converted']
    category_lower_bound_m_year: NonNegative
    category_upper_bound_m_year: NonNegative | None
    lower_bound_relation: Literal['inclusive', 'exclusive']
    upper_bound_relation: Literal['inclusive', 'exclusive', 'unbounded']
    shared_boundary_encountered: bool
    rate_source: Literal['qualified_external_groundwater_rate']
    tks_to_rate_model_available: Literal[False]
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']
    assessment_distribution: Literal['general', 'local']


class DamageThinningPriorSelectionOutput(Model):
    prior_probabilities: list[Fraction]
    prior_source: Literal['table4_5', 'qualified_custom']
    confidence: Literal['low', 'medium', 'high'] | None
    zero_prior_state_indices: list[int]


class DamageThinningRateSelectionOutput(Model):
    corrosion_rate_m_year: NonNegative
    assessment_distribution: Literal['general', 'local']
    governing_rate_mechanism_ids: list[str]
    governing_type_mechanism_ids: list[str]
    rate_by_mechanism_m_year: dict[str, NonNegative]
    selection_source_by_mechanism: dict[str, Literal['measured', 'calculated', 'estimated']]
    fallback_ignored_by_mechanism: dict[str, bool]


class DamageThinningSelectedMechanismsOutput(Model):
    corrosion_rate_m_year: NonNegative
    assessment_distribution: Literal['general', 'local']
    governing_rate_mechanism_ids: list[str]
    governing_type_mechanism_ids: list[str]
    rate_by_mechanism_m_year: dict[str, NonNegative]
    selection_source_by_mechanism: dict[str, Literal['measured', 'calculated', 'estimated']]
    fallback_ignored_by_mechanism: dict[str, bool]
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']


class DamageThinningAssessmentPeriodOutput(Model):
    baseline_type: Literal['furnished', 'measured']
    baseline_at: str
    assessment_at: str
    baseline_thickness_m: NonNegative
    baseline_inspection_id: str | None
    elapsed_days: NonNegative
    elapsed_years: NonNegative
    days_per_year: NonNegative


class DamageThinningInspectionHistoryOutput(Model):
    baseline_type: Literal['furnished', 'measured']
    baseline_at: str
    assessment_at: str
    baseline_thickness_m: NonNegative
    baseline_inspection_id: str | None
    elapsed_days: NonNegative
    elapsed_years: NonNegative
    days_per_year: NonNegative
    inspections_a: int
    inspections_b: int
    inspections_c: int
    inspections_d: int
    eligible_inspection_ids: list[str]
    excluded_inspection_reasons: dict[str, Literal['before_baseline', 'after_assessment', 'baseline_boundary', 'unqualified', 'ineffective_e']]
    baseline_boundary_policy: Literal['include_baseline_time', 'exclude_baseline_time']


class DamageThinningHistoryAssessmentOutput(Model):
    baseline_type: Literal['furnished', 'measured']
    baseline_at: str
    assessment_at: str
    baseline_thickness_m: NonNegative
    baseline_inspection_id: str | None
    elapsed_days: NonNegative
    elapsed_years: NonNegative
    days_per_year: NonNegative
    inspections_a: int
    inspections_b: int
    inspections_c: int
    inspections_d: int
    eligible_inspection_ids: list[str]
    excluded_inspection_reasons: dict[str, Literal['before_baseline', 'after_assessment', 'baseline_boundary', 'unqualified', 'ineffective_e']]
    baseline_boundary_policy: Literal['include_baseline_time', 'exclude_baseline_time']
    corrosion_rate_m_year: NonNegative
    assessment_distribution: Literal['general', 'local']
    governing_rate_mechanism_ids: list[str]
    governing_type_mechanism_ids: list[str]
    rate_by_mechanism_m_year: dict[str, NonNegative]
    selection_source_by_mechanism: dict[str, Literal['measured', 'calculated', 'estimated']]
    fallback_ignored_by_mechanism: dict[str, bool]
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior_probabilities: list[Fraction]
    reliability_indices: list[float]
    damage_state_failure_probabilities: list[Fraction]
    weighted_failure_probability: Fraction
    base_damage_factor: NonNegative
    thinning_damage_factor: NonNegative
    monitoring_row: Literal['hydrochloric_acid', 'high_temperature_sulfidic_naphthenic', 'high_temperature_h2s_h2', 'sulfuric_low_velocity', 'sulfuric_high_velocity', 'hydrofluoric_acid', 'sour_water_low_velocity', 'sour_water_high_velocity', 'amine_low_velocity', 'amine_high_velocity', 'other']
    velocity_threshold_m_s: NonNegative | None
    online_monitoring_factor: NonNegative
    candidate_method_factors: dict[str, NonNegative]
    monitoring_credit_basis: Literal['no_organized_plan', 'qualified_experience_replacement', 'maximum_table_method', 'no_monitoring_methods']
    joint_exception_applied: bool
    injection_point_factor: NonNegative
    deadleg_factor: NonNegative
    strength_method: Literal['internal_pressure_eq2_18', 'design_thickness_eq2_17']


class DamageCausticScreeningOutput(Model):
    evaluate_caustic_cracking: bool
    screening_reason: Literal['evaluate', 'outside_material_scope', 'caustic_absent']


class DamageCausticFigureSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']
    decision_branch: str
    plot_evidence_used: bool
    historical_high_retained: bool


class DamageCausticScreenedAssessmentOutput(Model):
    evaluate_caustic_cracking: bool
    screening_reason: Literal['evaluate', 'outside_material_scope', 'caustic_absent']
    susceptibility: Literal['none', 'low', 'medium', 'high']
    decision_branch: str
    plot_evidence_used: bool
    historical_high_retained: bool
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageAmineCrackingScreeningOutput(Model):
    evaluate_amine_cracking: bool
    screening_reason: Literal['evaluate', 'outside_material_scope', 'treating_amine_absent']


class DamageAmineCrackingScreenedAssessmentOutput(Model):
    evaluate_amine_cracking: bool
    screening_reason: Literal['evaluate', 'outside_material_scope', 'treating_amine_absent']
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageAmineFigureSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']
    decision_branch: str
    lean_exposure_selected: bool


class DamageAmineFigureAssessmentOutput(Model):
    evaluate_amine_cracking: bool
    screening_reason: Literal['evaluate', 'outside_material_scope', 'treating_amine_absent']
    susceptibility: Literal['none', 'low', 'medium', 'high']
    decision_branch: str
    lean_exposure_selected: bool
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageSscScreeningOutput(Model):
    evaluate_ssc: bool
    screening_reason: Literal['outside_material_scope', 'water_absent', 'h2s_absent', 'evaluate']


class DamageSscQualifiedSusceptibilityOutput(Model):
    environmental_severity: Literal['low', 'moderate', 'high']
    susceptibility_upgrade_required: bool
    unadjusted_susceptibility: Literal['none', 'low', 'medium', 'high']
    susceptibility: Literal['none', 'low', 'medium', 'high']
    cyanide_upgrade_applied: bool


class DamageSscQualifiedAssessmentOutput(Model):
    evaluate_ssc: bool
    screening_reason: Literal['outside_material_scope', 'water_absent', 'h2s_absent', 'evaluate']
    environmental_severity: Literal['low', 'moderate', 'high']
    susceptibility_upgrade_required: bool
    unadjusted_susceptibility: Literal['none', 'low', 'medium', 'high']
    susceptibility: Literal['none', 'low', 'medium', 'high']
    cyanide_upgrade_applied: bool
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageHicH2sScreeningOutput(Model):
    evaluate_hic_sohic_h2s: bool
    screening_reason: Literal['outside_material_scope', 'water_absent', 'h2s_absent', 'evaluate']


class DamageHicH2sQualifiedSusceptibilityOutput(Model):
    environmental_severity: Literal['low', 'moderate', 'high']
    susceptibility_upgrade_required: bool
    effective_environmental_severity: Literal['low', 'moderate', 'high']
    unadjusted_susceptibility: Literal['none', 'low', 'medium', 'high']
    cyanide_adjusted_susceptibility: Literal['none', 'low', 'medium', 'high']
    susceptibility: Literal['none', 'low', 'medium', 'high']


class DamageHicH2sQualifiedAssessmentOutput(Model):
    evaluate_hic_sohic_h2s: bool
    screening_reason: Literal['outside_material_scope', 'water_absent', 'h2s_absent', 'evaluate']
    environmental_severity: Literal['low', 'moderate', 'high']
    susceptibility_upgrade_required: bool
    effective_environmental_severity: Literal['low', 'moderate', 'high']
    unadjusted_susceptibility: Literal['none', 'low', 'medium', 'high']
    cyanide_adjusted_susceptibility: Literal['none', 'low', 'medium', 'high']
    susceptibility: Literal['none', 'low', 'medium', 'high']
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative
    ffs_disposition: Literal['not_required', 'repaired', 'qualified_ffs_basis']
    table_monitoring_factor: NonNegative
    monitoring_factor_source: Literal['table9_5', 'qualified_experience_replacement']


class DamageHicH2sMonitoringSelectionOutput(Model):
    table_monitoring_factor: NonNegative
    monitoring_factor: NonNegative
    monitoring_factor_source: Literal['table9_5', 'qualified_experience_replacement']


class DamageAcsccScreeningOutput(Model):
    evaluate_acscc: bool
    material_in_scope: bool
    evaluation_triggers: list[Literal['alkaline_water_ph_above_7_5', 'fccu_feed_sulfur_reduced', 'fccu_feed_nitrogen_increased']]


class DamageAcsccWaterSusceptibilityOutput(Model):
    susceptibility: Literal['none', 'low', 'medium', 'high']
    selected_ph_band: Literal['below_7.5', '7.5_to_8', '8_to_9', 'at_least_9']
    shared_ph_boundary_encountered: bool


class DamageAcsccQualifiedAssessmentOutput(Model):
    evaluate_acscc: bool
    material_in_scope: bool
    evaluation_triggers: list[Literal['alkaline_water_ph_above_7_5', 'fccu_feed_sulfur_reduced', 'fccu_feed_nitrogen_increased']]
    susceptibility: Literal['none', 'low', 'medium', 'high']
    selected_ph_band: Literal['below_7.5', '7.5_to_8', '8_to_9', 'at_least_9']
    shared_ph_boundary_encountered: bool
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamagePasccScreeningOutput(Model):
    evaluate_pascc: bool
    screening_reason: Literal['outside_material_scope', 'sulfur_exposure_absent', 'evaluate']


class DamagePasccFigureSusceptibilityOutput(Model):
    table_or_override_susceptibility: Literal['none', 'low', 'medium', 'high']
    susceptibility: Literal['none', 'low', 'medium', 'high']
    downtime_reduction_applied: bool


class DamagePasccQualifiedAssessmentOutput(Model):
    evaluate_pascc: bool
    screening_reason: Literal['outside_material_scope', 'sulfur_exposure_absent', 'evaluate']
    table_or_override_susceptibility: Literal['none', 'low', 'medium', 'high']
    susceptibility: Literal['none', 'low', 'medium', 'high']
    downtime_reduction_applied: bool
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class DamageClsccScreeningOutput(Model):
    evaluate_clscc: bool
    material_in_scope: bool
    temperature_screen_passed: bool
    screening_temperature_threshold_k: NonNegative
    selected_temperature_basis: Literal['printed_si', 'printed_us_converted']


class DamageClsccQualifiedAssessmentOutput(Model):
    evaluate_clscc: bool
    material_in_scope: bool
    temperature_screen_passed: bool
    screening_temperature_threshold_k: NonNegative
    selected_temperature_basis: Literal['printed_si', 'printed_us_converted']
    susceptibility: Literal['none', 'low', 'medium', 'high']
    effective_susceptibility: str
    severity_index: int
    equivalent_inspection_grade: str
    equivalent_inspection_count: int
    base_damage_factor: NonNegative
    age_factor: NonNegative
    monitoring_factor: NonNegative
    damage_factor: NonNegative


class PlanningTargetCrossingOutput(Model):
    status: Literal["already_exceeded", "crossing", "not_crossed_within_horizon"]
    crossing_years: NonNegative | None
    horizon_years: NonNegative | None = None


class RiskAssessmentOutput(Model):
    integration_scope: Literal["supplied_damage_and_consequences"]
    management_factor: NonNegative
    generic_frequencies: FrequencyGenericOutput
    scenarios: list[dict[str, Any]]
    risk: RiskAggregateOutput


class RiskAssessmentFromDamageOutput(Model):
    integration_scope: Literal["combined_damage_and_supplied_consequences"]
    management_factor: NonNegative
    generic_frequencies: FrequencyGenericOutput
    scenarios: list[dict[str, Any]]
    risk: RiskAggregateOutput
    damage_factor: DamageCombineOutput


OUTPUT_MODELS = {
    'frequency/generic': FrequencyGenericOutput,
    'frequency/management-factor': FrequencyManagementFactorOutput,
    'frequency/adjusted': FrequencyAdjustedOutput,
    'frequency/pof-method-selection': FrequencyPofMethodSelectionOutput,
    'damage/combine': DamageCombineOutput,
    'inspection/equivalent': InspectionEquivalentOutput,
    'inspection/effectiveness-summary': InspectionEffectivenessSummaryOutput,
    'reliability/weibull': ReliabilityWeibullOutput,
    'reliability/weibull-quantile': ReliabilityWeibullQuantileOutput,
    'reliability/weibull-from-mttf': ReliabilityWeibullFromMttfOutput,
    'reliability/poisson-probability': ReliabilityPoissonProbabilityOutput,
    'release/hole-size-selection': ReleaseHoleSizeSelectionOutput,
    'release/detection-isolation-rating': ReleaseDetectionIsolationRatingOutput,
    'release/orifice-area': ReleaseOrificeAreaOutput,
    'release/viscosity-factor': ReleaseViscosityFactorOutput,
    'release/liquid': ReleaseLiquidOutput,
    'release/gas': ReleaseGasOutput,
    'properties/heat-capacity-ratio': PropertiesHeatCapacityRatioOutput,
    'release/available-inventory': ReleaseAvailableInventoryOutput,
    'release/type': ReleaseTypeOutput,
    'release/magnitude': ReleaseMagnitudeOutput,
    'release/detection-isolation': ReleaseDetectionIsolationOutput,
    'release/integrate-profile': ReleaseIntegrateProfileOutput,
    'properties/mixture-molecular-weight': PropertiesMixtureMolecularWeightOutput,
    'effects/jet-fire-power': EffectsJetFirePowerOutput,
    'effects/jet-fire-flux': EffectsJetFireFluxOutput,
    'effects/jet-fire-distance': EffectsJetFireDistanceOutput,
    'effects/flash-fire': EffectsFlashFireOutput,
    'effects/pool-fire-area': EffectsPoolFireAreaOutput,
    'consequence/power-law-area': ConsequencePowerLawAreaOutput,
    'events/leakage-tree': EventsLeakageTreeOutput,
    'effects/toxic-probit': EffectsToxicProbitOutput,
    'effects/pool-burning-rate': EffectsPoolBurningRateOutput,
    'effects/fireball-geometry': EffectsFireballGeometryOutput,
    'effects/fireball-radiative-fraction': EffectsFireballRadiativeFractionOutput,
    'effects/fireball-emissive-power': EffectsFireballEmissivePowerOutput,
    'effects/vce-tnt-equivalence': EffectsVceTntEquivalenceOutput,
    'consequence/expected': ConsequenceExpectedOutput,
    'risk/aggregate': RiskAggregateOutput,
    'risk/assessment': RiskAssessmentOutput,
    'risk/assessment-from-damage': RiskAssessmentFromDamageOutput,
    'consequence/financial-total': ConsequenceFinancialTotalOutput,
    'risk/matrix': RiskMatrixOutput,
    'planning/target-crossing': PlanningTargetCrossingOutput,
    'damage/thinning-wall-loss': DamageThinningWallLossOutput,
    'damage/flow-stress': DamageFlowStressOutput,
    'damage/thinning-strength-ratio': DamageThinningStrengthRatioOutput,
    'damage/thinning-prior-selection': DamageThinningPriorSelectionOutput,
    'damage/thinning-posterior': DamageThinningPosteriorOutput,
    'damage/thinning-base': DamageThinningBaseOutput,
    'damage/thinning-adjust': DamageThinningAdjustOutput,
    'damage/thinning-unclad': DamageThinningUncladOutput,
    'damage/scc-base': DamageSccBaseOutput,
    'damage/caustic-severity': DamageCausticSeverityOutput,
    'damage/caustic-escalation': DamageCausticEscalationOutput,
    'damage/lining-adjust': DamageLiningAdjustOutput,
    'level1/mitigation': Level1MitigationOutput,
    'level1/toxic-source': Level1ToxicSourceOutput,
    'level1/toxic-duration': Level1ToxicDurationOutput,
    'level1/toxic-area': Level1ToxicAreaOutput,
    'level1/steam-area': Level1SteamAreaOutput,
    'level1/acid-caustic-area': Level1AcidCausticAreaOutput,
    'consequence/final-area': ConsequenceFinalAreaOutput,
    'consequence/hole-weighted': ConsequenceHoleWeightedOutput,
    'financial/surrounding-damage': FinancialSurroundingDamageOutput,
    'financial/production-loss': FinancialProductionLossOutput,
    'financial/injury': FinancialInjuryOutput,
    'financial/spill-cleanup': FinancialSpillCleanupOutput,
    'financial/hole-total': FinancialHoleTotalOutput,
    'level1/hf-h2s-toxic-coefficients': Level1HfH2sToxicCoefficientsOutput,
    'level1/hf-h2s-toxic-area': Level1HfH2sToxicAreaOutput,
    'level1/misc-toxic-coefficients': Level1MiscToxicCoefficientsOutput,
    'level1/misc-toxic-area': Level1MiscToxicAreaOutput,
    'level1/toxic-cutoff': Level1ToxicCutoffOutput,
    'level1/toxic-mitigation': Level1ToxicMitigationOutput,
    'level1/toxic-component-consequence': Level1ToxicComponentConsequenceOutput,
    'level1/toxic-mixture-consequence': Level1ToxicMixtureConsequenceOutput,
    'level1/toxic-hole-summary': Level1ToxicHoleSummaryOutput,
    'level1/flammable-coefficients': Level1FlammableCoefficientsOutput,
    'release/detection-reduction': ReleaseDetectionReductionOutput,
    'release/detection-duration': ReleaseDetectionDurationOutput,
    'level1/release-phase': Level1ReleasePhaseOutput,
    'level1/energy-efficiency': Level1EnergyEfficiencyOutput,
    'level1/blending-factors': Level1BlendingFactorsOutput,
    'level1/flammable-area': Level1FlammableAreaOutput,
    'release/controlled-scenario': ReleaseControlledScenarioOutput,
    'level1/release-to-flammable': Level1ReleaseToFlammableOutput,
    'level1/release-to-acid': Level1ReleaseToAcidOutput,
    'level1/release-to-steam': Level1ReleaseToSteamOutput,
    'level1/release-to-toxic': Level1ReleaseToToxicOutput,
    'level1/consequence-summary': Level1ConsequenceSummaryOutput,
    'financial/repair-table': FinancialRepairTableOutput,
    'financial/material-factor': FinancialMaterialFactorOutput,
    'financial/outage-table': FinancialOutageTableOutput,
    'financial/component-repair': FinancialComponentRepairOutput,
    'financial/component-outage': FinancialComponentOutageOutput,
    'financial/surrounding-outage': FinancialSurroundingOutageOutput,
    'properties/leak-table': PropertiesLeakTableOutput,
    'financial/cleanup-eligibility': FinancialCleanupEligibilityOutput,
    'financial/level1-consequence': FinancialLevel1ConsequenceOutput,
    'damage/scc-severity': DamageSccSeverityOutput,
    'damage/hic-monitoring-factor': DamageHicMonitoringFactorOutput,
    'damage/caustic': DamageCausticOutput,
    'damage/amine': DamageAmineOutput,
    'damage/ssc': DamageSscOutput,
    'damage/hic-sohic-h2s': DamageHicSohicH2sOutput,
    'damage/acscc': DamageAcsccOutput,
    'damage/pascc': DamagePasccOutput,
    'damage/clscc': DamageClsccOutput,
    'damage/hsc-hf': DamageHscHfOutput,
    'damage/hic-sohic-hf': DamageHicSohicHfOutput,
    'damage/hsc-hf-susceptibility': DamageHscHfSusceptibilityOutput,
    'damage/ssc-susceptibility': DamageSscSusceptibilityOutput,
    'damage/hic-hf-susceptibility': DamageHicHfSusceptibilityOutput,
    'damage/hic-h2s-susceptibility': DamageHicH2sSusceptibilityOutput,
    'damage/clscc-susceptibility': DamageClsccSusceptibilityOutput,
    'damage/wet-h2s-environment': DamageWetH2sEnvironmentOutput,
    'damage/acscc-susceptibility': DamageAcsccSusceptibilityOutput,
    'damage/pascc-susceptibility': DamagePasccSusceptibilityOutput,
    'damage/external-base-rate': DamageExternalBaseRateOutput,
    'damage/cui-base-rate': DamageCuiBaseRateOutput,
    'damage/external-time-weighted-rate': DamageExternalTimeWeightedRateOutput,
    'damage/external-rate-adjust': DamageExternalRateAdjustOutput,
    'damage/cui-rate-adjust': DamageCuiRateAdjustOutput,
    'damage/coating-exposure': DamageCoatingExposureOutput,
    'damage/external-corrosion': DamageExternalCorrosionOutput,
    'damage/cui': DamageCuiOutput,
    'damage/external-clscc-base-susceptibility': DamageExternalClsccBaseSusceptibilityOutput,
    'damage/external-clscc': DamageExternalClsccOutput,
    'damage/cui-clscc': DamageCuiClsccOutput,
    'damage/fatigue-base': DamageFatigueBaseOutput,
    'damage/fatigue-adjustments': DamageFatigueAdjustmentsOutput,
    'damage/mechanical-fatigue': DamageMechanicalFatigueOutput,
    'properties/hydrogen-partial-pressure': PropertiesHydrogenPartialPressureOutput,
    'damage/htha-factor': DamageHthaFactorOutput,
    'damage/htha-carbon-screen': DamageHthaCarbonScreenOutput,
    'damage/brittle-reference-temperature': DamageBrittleReferenceTemperatureOutput,
    'damage/brittle-service-factor': DamageBrittleServiceFactorOutput,
    'damage/brittle-base': DamageBrittleBaseOutput,
    'damage/brittle-fracture': DamageBrittleFractureOutput,
    'damage/embrittlement-885f': DamageEmbrittlement885fOutput,
    'damage/sigma-content': DamageSigmaContentOutput,
    'damage/sigma-embrittlement': DamageSigmaEmbrittlementOutput,
    'damage/temper-j-factor': DamageTemperJFactorOutput,
    'damage/temper-xbar': DamageTemperXbarOutput,
    'damage/temper-xbar-shift': DamageTemperXbarShiftOutput,
    'damage/temper-generation-shift': DamageTemperGenerationShiftOutput,
    'damage/temper-embrittlement': DamageTemperEmbrittlementOutput,
    'bundle/weibayes-history': BundleWeibayesHistoryOutput,
    'bundle/condition-update': BundleConditionUpdateOutput,
    'bundle/thickness-life': BundleThicknessLifeOutput,
    'bundle/estimated-life': BundleEstimatedLifeOutput,
    'bundle/life-extension': BundleLifeExtensionOutput,
    'bundle/consequence': BundleConsequenceOutput,
    'bundle/risk': BundleRiskOutput,
    'bundle/target-age': BundleTargetAgeOutput,
    'bundle/deferral-decision': BundleDeferralDecisionOutput,
    'bundle/replacement-optimization': BundleReplacementOptimizationOutput,
    'bundle/material-factor': BundleMaterialFactorOutput,
    'bundle/replacement-cost': BundleReplacementCostOutput,
    'bundle/life-extension-factor': BundleLifeExtensionFactorOutput,
    'bundle/categories': BundleCategoriesOutput,
    'prd/default-weibull': PrdDefaultWeibullOutput,
    'prd/environment-factor': PrdEnvironmentFactorOutput,
    'prd/set-pressure-factor': PrdSetPressureFactorOutput,
    'prd/overpressure-factor': PrdOverpressureFactorOutput,
    'prd/demand-rate': PrdDemandRateOutput,
    'prd/inspection-update': PrdInspectionUpdateOutput,
    'prd/protected-equipment': PrdProtectedEquipmentOutput,
    'prd/fail-frequency': PrdFailFrequencyOutput,
    'prd/base-reliability': PrdBaseReliabilityOutput,
    'prd/leakage-rates': PrdLeakageRatesOutput,
    'prd/leakage-duration': PrdLeakageDurationOutput,
    'prd/inventory-loss-factor': PrdInventoryLossFactorOutput,
    'prd/inventory-loss': PrdInventoryLossOutput,
    'prd/repair-cost': PrdRepairCostOutput,
    'prd/production-loss': PrdProductionLossOutput,
    'prd/leakage-consequence': PrdLeakageConsequenceOutput,
    'prd/multiple-device-pressure': PrdMultipleDevicePressureOutput,
    'prd/fail-risk': PrdFailRiskOutput,
    'prd/leakage-risk': PrdLeakageRiskOutput,
    'prd/total-risk': PrdTotalRiskOutput,
    'prd/risk-assessment': PrdRiskAssessmentOutput,
    'prd/service-age': PrdServiceAgeOutput,
    'level1/type1-flammable-area': Level1Type1FlammableAreaOutput,
    'level1/type1-flammable-consequence': Level1Type1FlammableConsequenceOutput,
    'level1/release-to-type1-flammable': Level1ReleaseToType1FlammableOutput,
    'properties/water-partial-pressure': PropertiesWaterPartialPressureOutput,
    'effects/atmospheric-transmissivity': EffectsAtmosphericTransmissivityOutput,
    'effects/pool-mixture-burning-rate': EffectsPoolMixtureBurningRateOutput,
    'effects/pool-flame-geometry': EffectsPoolFlameGeometryOutput,
    'effects/pool-surface-emissive-power': EffectsPoolSurfaceEmissivePowerOutput,
    'effects/pool-cylinder-view-factor': EffectsPoolCylinderViewFactorOutput,
    'effects/pool-radiation-flux': EffectsPoolRadiationFluxOutput,
    'effects/pool-fire-distance': EffectsPoolFireDistanceOutput,
    'effects/pool-fire-consequence': EffectsPoolFireConsequenceOutput,
    'inspection/effectiveness-category': InspectionEffectivenessCategoryOutput,
    'inspection/thinning-effectiveness': InspectionThinningEffectivenessOutput,
    'inspection/scc-effectiveness': InspectionSccEffectivenessOutput,
    'inspection/external-effectiveness': InspectionExternalEffectivenessOutput,
    'inspection/buried-effectiveness': InspectionBuriedEffectivenessOutput,
    'inspection/prd-effectiveness': InspectionPrdEffectivenessOutput,
    'inspection/lining-effectiveness': InspectionLiningEffectivenessOutput,
    'inspection/tube-bundle-uncertainty': InspectionTubeBundleUncertaintyOutput,
    'inspection/ast-effectiveness': InspectionAstEffectivenessOutput,
    'effects/fireball-mass': EffectsFireballMassOutput,
    'effects/fireball-view-factor': EffectsFireballViewFactorOutput,
    'effects/fireball-radiation-flux': EffectsFireballRadiationFluxOutput,
    'effects/fireball-distance': EffectsFireballDistanceOutput,
    'effects/fireball-consequence': EffectsFireballConsequenceOutput,
    'effects/vce-scaled-distance': EffectsVceScaledDistanceOutput,
    'effects/vce-scaled-overpressure': EffectsVceScaledOverpressureOutput,
    'effects/vce-blast-overpressure': EffectsVceBlastOverpressureOutput,
    'effects/blast-building-probit': EffectsBlastBuildingProbitOutput,
    'effects/blast-building-pressure-threshold': EffectsBlastBuildingPressureThresholdOutput,
    'effects/vce-blast-distance': EffectsVceBlastDistanceOutput,
    'effects/vce-blast-consequence': EffectsVceBlastConsequenceOutput,
    'effects/physical-explosion-tnt': EffectsPhysicalExplosionTntOutput,
    'release/bleve-flashed-amount': ReleaseBleveFlashedAmountOutput,
    'effects/bleve-liquid-tnt': EffectsBleveLiquidTntOutput,
    'effects/physical-explosion-consequence': EffectsPhysicalExplosionConsequenceOutput,
    'effects/bleve-consequence': EffectsBleveConsequenceOutput,
    'consequence/level2-nfnt-case': ConsequenceLevel2NfntCaseOutput,
    'consequence/level2-nfnt-summary': ConsequenceLevel2NfntSummaryOutput,
    'properties/toxic-impact-table': PropertiesToxicImpactTableOutput,
    'effects/toxic-species-probit': EffectsToxicSpeciesProbitOutput,
    'effects/toxic-species-threshold': EffectsToxicSpeciesThresholdOutput,
    'effects/toxic-dose-profile': EffectsToxicDoseProfileOutput,
    'release/level2-toxic-duration': ReleaseLevel2ToxicDurationOutput,
    'consequence/toxic-mixture-limit': ConsequenceToxicMixtureLimitOutput,
    'consequence/level2-toxic-case': ConsequenceLevel2ToxicCaseOutput,
    'consequence/level2-toxic-summary': ConsequenceLevel2ToxicSummaryOutput,
    'level2/correlated-jet-pool': Level2CorrelatedJetPoolOutput,
    'level2/flammable-case': Level2FlammableCaseOutput,
    'level2/final-area': Level2FinalAreaOutput,
    'level2/consequence-summary': Level2ConsequenceSummaryOutput,
    'level2/scenario-consequence': Level2ScenarioConsequenceOutput,
    'level2/scenario-summary': Level2ScenarioSummaryOutput,
    'level2/assessment': Level2AssessmentOutput,
    'properties/pool-surface-interaction': PropertiesPoolSurfaceInteractionOutput,
    'release/pool-evaporation-regime': ReleasePoolEvaporationRegimeOutput,
    'release/boiling-pool-evaporation': ReleaseBoilingPoolEvaporationOutput,
    'release/boiling-pool-radius': ReleaseBoilingPoolRadiusOutput,
    'release/boiling-pool-steady-source': ReleaseBoilingPoolSteadySourceOutput,
    'release/nonboiling-pool-evaporation': ReleaseNonboilingPoolEvaporationOutput,
    'release/nonboiling-pool-steady-source': ReleaseNonboilingPoolSteadySourceOutput,
    'release/level2-release-phase': ReleaseLevel2ReleasePhaseOutput,
    'release/level2-orifice-rate': ReleaseLevel2OrificeRateOutput,
    'release/kletz-rainout-fraction': ReleaseKletzRainoutFractionOutput,
    'release/rainout-rate-split': ReleaseRainoutRateSplitOutput,
    'release/jet-liquid-entrainment': ReleaseJetLiquidEntrainmentOutput,
    'release/level2-source-partition': ReleaseLevel2SourcePartitionOutput,
    'release/flammable-phase-rates': ReleaseFlammablePhaseRatesOutput,
    'events/ambient-ignition': EventsAmbientIgnitionOutput,
    'events/ait-ignition-maximum': EventsAitIgnitionMaximumOutput,
    'events/probability-temperature': EventsProbabilityTemperatureOutput,
    'events/conditional-table': EventsConditionalTableOutput,
    'events/two-phase-probability': EventsTwoPhaseProbabilityOutput,
    'events/single-phase-tree': EventsSinglePhaseTreeOutput,
    'events/single-phase-ignition': EventsSinglePhaseIgnitionOutput,
    'events/fireball-given-immediate': EventsFireballGivenImmediateOutput,
    'events/two-phase-tree': EventsTwoPhaseTreeOutput,
    'events/two-phase-ignition': EventsTwoPhaseIgnitionOutput,
    'tank/fluid-table': TankFluidTableOutput,
    'tank/soil-table': TankSoilTableOutput,
    'tank/soil-water-conductivity': TankSoilWaterConductivityOutput,
    'tank/fluid-conductivity': TankFluidConductivityOutput,
    'tank/seepage-velocity': TankSeepageVelocityOutput,
    'tank/bottom-hole-count': TankBottomHoleCountOutput,
    'tank/bottom-inventory': TankBottomInventoryOutput,
    'tank/shell-course-inventory': TankShellCourseInventoryOutput,
    'tank/shell-flow': TankShellFlowOutput,
    'tank/bottom-flow': TankBottomFlowOutput,
    'tank/shell-detection-time': TankShellDetectionTimeOutput,
    'tank/bottom-detection-time': TankBottomDetectionTimeOutput,
    'tank/release-volume': TankReleaseVolumeOutput,
    'tank/environment-cost-table': TankEnvironmentCostTableOutput,
    'tank/surface-spill-partition': TankSurfaceSpillPartitionOutput,
    'tank/groundwater-arrival': TankGroundwaterArrivalOutput,
    'tank/subsurface-spill-partition': TankSubsurfaceSpillPartitionOutput,
    'tank/shell-environment-cost': TankShellEnvironmentCostOutput,
    'tank/bottom-environment-cost': TankBottomEnvironmentCostOutput,
    'tank/bottom-repair-cost': TankBottomRepairCostOutput,
    'tank/generic-frequency': TankGenericFrequencyOutput,
    'tank/component-outage': TankComponentOutageOutput,
    'tank/bottom-financial-consequence': TankBottomFinancialConsequenceOutput,
    'tank/shell-financial-consequence': TankShellFinancialConsequenceOutput,
    'tank/bottom-risk-assessment': TankBottomRiskAssessmentOutput,
    'tank/shell-risk-assessment': TankShellRiskAssessmentOutput,
    'tank/shell-hole-sizes': TankShellHoleSizesOutput,
    'tank/bottom-hole-sizes': TankBottomHoleSizesOutput,
    'tank/shell-source-assessment': TankShellSourceAssessmentOutput,
    'tank/bottom-source-assessment': TankBottomSourceAssessmentOutput,
    'tank/bottom-integrated-assessment': TankBottomIntegratedAssessmentOutput,
    'tank/diked-pool-consequence': TankDikedPoolConsequenceOutput,
    'tank/shell-level2-case': TankShellLevel2CaseOutput,
    'tank/shell-level2-summary': TankShellLevel2SummaryOutput,
    'tank/shell-integrated-assessment': TankShellIntegratedAssessmentOutput,
    'dispersion/native-engine-capabilities': DispersionNativeEngineCapabilitiesOutput,
    'dispersion/native-pool-centreline': DispersionNativePoolCentrelineOutput,
    'dispersion/native-pool-footprint': DispersionNativePoolFootprintOutput,
    'dispersion/native-pool-flash-fire': DispersionNativePoolFlashFireOutput,
    'dispersion/native-jet-centreline': DispersionNativeJetCentrelineOutput,
    'dispersion/native-jet-footprint': DispersionNativeJetFootprintOutput,
    'dispersion/threshold-grid-area': DispersionThresholdGridAreaOutput,
    'dispersion/partitioned-jet-centreline': DispersionPartitionedJetCentrelineOutput,
    'dispersion/partitioned-jet-footprint': DispersionPartitionedJetFootprintOutput,
    'consequence/select-toxic-criterion': ConsequenceSelectToxicCriterionOutput,
    'dispersion/native-pool-toxic-consequence': DispersionNativePoolToxicConsequenceOutput,
    'damage/soil-base-rate-table': DamageSoilBaseRateTableOutput,
    'damage/soil-resistivity-factor': DamageSoilResistivityFactorOutput,
    'damage/soil-temperature-factor': DamageSoilTemperatureFactorOutput,
    'damage/soil-cp-factor': DamageSoilCpFactorOutput,
    'damage/soil-coating-factor': DamageSoilCoatingFactorOutput,
    'damage/soil-rate-equation': DamageSoilRateEquationOutput,
    'damage/soil-corrosion-rate': DamageSoilCorrosionRateOutput,
    'damage/soil-thinning-assessment': DamageSoilThinningAssessmentOutput,
    'tank/bottom-base-corrosion-rate': TankBottomBaseCorrosionRateOutput,
    'tank/bottom-soil-rate-equation': TankBottomSoilRateEquationOutput,
    'tank/bottom-product-rate-equation': TankBottomProductRateEquationOutput,
    'tank/bottom-soil-resistivity-factor': TankBottomSoilResistivityFactorOutput,
    'tank/bottom-pad-factor': TankBottomPadFactorOutput,
    'tank/bottom-drainage-factor': TankBottomDrainageFactorOutput,
    'tank/bottom-cp-factor': TankBottomCpFactorOutput,
    'tank/bottom-type-factor': TankBottomTypeFactorOutput,
    'tank/bottom-temperature-factor': TankBottomTemperatureFactorOutput,
    'tank/bottom-product-condition-factor': TankBottomProductConditionFactorOutput,
    'tank/bottom-steam-coil-factor': TankBottomSteamCoilFactorOutput,
    'tank/bottom-water-draw-factor': TankBottomWaterDrawFactorOutput,
    'tank/bottom-corrosion-rate-combine': TankBottomCorrosionRateCombineOutput,
    'tank/bottom-corrosion-assessment': TankBottomCorrosionAssessmentOutput,
    'tank/bottom-minimum-thickness': TankBottomMinimumThicknessOutput,
    'tank/bottom-wall-parameter': TankBottomWallParameterOutput,
    'tank/bottom-inspection-selection': TankBottomInspectionSelectionOutput,
    'tank/bottom-thinning-base': TankBottomThinningBaseOutput,
    'tank/bottom-thinning-adjustment-factors': TankBottomThinningAdjustmentFactorsOutput,
    'tank/bottom-thinning-assessment': TankBottomThinningAssessmentOutput,
    'tank/bottom-corrosion-thinning-assessment': TankBottomCorrosionThinningAssessmentOutput,
    'tank/bottom-corrosion-risk-assessment': TankBottomCorrosionRiskAssessmentOutput,
    'damage/cladding-remaining-life': DamageCladdingRemainingLifeOutput,
    'damage/thinning-clad-wall-loss': DamageThinningCladWallLossOutput,
    'damage/thinning-design-strength-ratio': DamageThinningDesignStrengthRatioOutput,
    'damage/thinning-clad': DamageThinningCladOutput,
    'damage/thinning-unclad-design': DamageThinningUncladDesignOutput,
    'damage/thinning-monitoring-row': DamageThinningMonitoringRowOutput,
    'damage/thinning-monitoring-table-factor': DamageThinningMonitoringTableFactorOutput,
    'damage/thinning-online-monitoring-factor': DamageThinningOnlineMonitoringFactorOutput,
    'damage/thinning-injection-point-factor': DamageThinningInjectionPointFactorOutput,
    'damage/thinning-deadleg-factor': DamageThinningDeadlegFactorOutput,
    'damage/thinning-conditional-adjustment': DamageThinningConditionalAdjustmentOutput,
    'damage/thinning-unclad-qualified': DamageThinningUncladQualifiedOutput,
    'damage/thinning-clad-qualified': DamageThinningCladQualifiedOutput,
    'damage/lining-effective-age': DamageLiningEffectiveAgeOutput,
    'damage/lining-base-factor': DamageLiningBaseFactorOutput,
    'damage/lining-condition-factor': DamageLiningConditionFactorOutput,
    'damage/lining-monitoring-factor': DamageLiningMonitoringFactorOutput,
    'damage/lining-governing-thinning': DamageLiningGoverningThinningOutput,
    'damage/lining-assessment': DamageLiningAssessmentOutput,
    'damage/cooling-water-rate-factors': DamageCoolingWaterRateFactorsOutput,
    'damage/cooling-water-ph-coefficients': DamageCoolingWaterPhCoefficientsOutput,
    'damage/cooling-water-stability-indices': DamageCoolingWaterStabilityIndicesOutput,
    'damage/cooling-water-saturation-ph': DamageCoolingWaterSaturationPhOutput,
    'damage/cooling-water-base-rate': DamageCoolingWaterBaseRateOutput,
    'damage/cooling-water-temperature-factor': DamageCoolingWaterTemperatureFactorOutput,
    'damage/cooling-water-velocity-factor': DamageCoolingWaterVelocityFactorOutput,
    'damage/cooling-water-rate-equation': DamageCoolingWaterRateEquationOutput,
    'damage/cooling-water-seawater-rate': DamageCoolingWaterSeawaterRateOutput,
    'damage/cooling-water-coupon-pitting-rate': DamageCoolingWaterCouponPittingRateOutput,
    'damage/cooling-water-fresh-assessment': DamageCoolingWaterFreshAssessmentOutput,
    'damage/cooling-water-thinning-assessment': DamageCoolingWaterThinningAssessmentOutput,
    'damage/cooling-water-system-type': DamageCoolingWaterSystemTypeOutput,
    'damage/cooling-water-treatment-bounds': DamageCoolingWaterTreatmentBoundsOutput,
    'damage/cooling-water-other-material-estimate': DamageCoolingWaterOtherMaterialEstimateOutput,
    'damage/cooling-water-measured-rate': DamageCoolingWaterMeasuredRateOutput,
    'damage/cooling-water-rate-selection': DamageCoolingWaterRateSelectionOutput,
    'damage/cooling-water-selected-thinning': DamageCoolingWaterSelectedThinningOutput,
    'damage/co2-relative-humidity': DamageCo2RelativeHumidityOutput,
    'damage/co2-dew-point': DamageCo2DewPointOutput,
    'damage/co2-temperature-ph-factor': DamageCo2TemperaturePhFactorOutput,
    'damage/co2-ph-estimate': DamageCo2PhEstimateOutput,
    'damage/co2-fugacity': DamageCo2FugacityOutput,
    'damage/co2-reynolds': DamageCo2ReynoldsOutput,
    'damage/co2-friction-factor': DamageCo2FrictionFactorOutput,
    'damage/co2-shear-stress': DamageCo2ShearStressOutput,
    'damage/co2-base-rate': DamageCo2BaseRateOutput,
    'damage/co2-glycol-factor': DamageCo2GlycolFactorOutput,
    'damage/co2-rate-adjustment': DamageCo2RateAdjustmentOutput,
    'damage/co2-corrosion-assessment': DamageCo2CorrosionAssessmentOutput,
    'damage/co2-thinning-assessment': DamageCo2ThinningAssessmentOutput,
    'properties/co2-partial-pressure': PropertiesCo2PartialPressureOutput,
    'damage/co2-reynolds-mass-flow': DamageCo2ReynoldsMassFlowOutput,
    'damage/co2-material-screen': DamageCo2MaterialScreenOutput,
    'damage/co2-hydrocarbon-wetting-screen': DamageCo2HydrocarbonWettingScreenOutput,
    'damage/co2-moisture-screen': DamageCo2MoistureScreenOutput,
    'damage/co2-screened-assessment': DamageCo2ScreenedAssessmentOutput,
    'damage/co2-screened-thinning': DamageCo2ScreenedThinningOutput,
    'damage/oxidation-screen': DamageOxidationScreenOutput,
    'damage/oxidation-table-row': DamageOxidationTableRowOutput,
    'damage/oxidation-rate': DamageOxidationRateOutput,
    'damage/oxidation-assessment': DamageOxidationAssessmentOutput,
    'damage/oxidation-thinning-assessment': DamageOxidationThinningAssessmentOutput,
    'damage/acid-sour-water-route': DamageAcidSourWaterRouteOutput,
    'damage/acid-sour-water-base-rate': DamageAcidSourWaterBaseRateOutput,
    'damage/acid-sour-water-oxygen-factor': DamageAcidSourWaterOxygenFactorOutput,
    'damage/acid-sour-water-velocity-factor': DamageAcidSourWaterVelocityFactorOutput,
    'damage/acid-sour-water-rate-equation': DamageAcidSourWaterRateEquationOutput,
    'damage/acid-sour-water-other-material-rate': DamageAcidSourWaterOtherMaterialRateOutput,
    'damage/acid-sour-water-assessment': DamageAcidSourWaterAssessmentOutput,
    'damage/acid-sour-water-thinning-assessment': DamageAcidSourWaterThinningAssessmentOutput,
    'properties/h2s-partial-pressure': PropertiesH2sPartialPressureOutput,
    'damage/alkaline-sour-water-nh4hs-estimate': DamageAlkalineSourWaterNh4hsEstimateOutput,
    'damage/alkaline-sour-water-velocity-selection': DamageAlkalineSourWaterVelocitySelectionOutput,
    'damage/alkaline-sour-water-base-rate': DamageAlkalineSourWaterBaseRateOutput,
    'damage/alkaline-sour-water-pressure-adjustment': DamageAlkalineSourWaterPressureAdjustmentOutput,
    'damage/alkaline-sour-water-assessment': DamageAlkalineSourWaterAssessmentOutput,
    'damage/alkaline-sour-water-thinning-assessment': DamageAlkalineSourWaterThinningAssessmentOutput,
    'damage/hcl-ph-from-chloride': DamageHclPhFromChlorideOutput,
    'damage/hcl-chloride-interval-from-ph': DamageHclChlorideIntervalFromPhOutput,
    'damage/hcl-ph-rate': DamageHclPhRateOutput,
    'damage/hcl-alloy-rate': DamageHclAlloyRateOutput,
    'damage/hcl-assessment': DamageHclAssessmentOutput,
    'damage/hcl-thinning-assessment': DamageHclThinningAssessmentOutput,
    'damage/sour-water-assessment': DamageSourWaterAssessmentOutput,
    'damage/hf-concentration-selection': DamageHfConcentrationSelectionOutput,
    'damage/hf-carbon-velocity-band': DamageHfCarbonVelocityBandOutput,
    'damage/hf-carbon-rate': DamageHfCarbonRateOutput,
    'damage/hf-alloy400-rate': DamageHfAlloy400RateOutput,
    'damage/hf-assessment': DamageHfAssessmentOutput,
    'damage/hf-thinning-assessment': DamageHfThinningAssessmentOutput,
    'damage/amine-acid-gas-loading': DamageAmineAcidGasLoadingOutput,
    'damage/amine-loading-selection': DamageAmineLoadingSelectionOutput,
    'damage/amine-contaminant-row': DamageAmineContaminantRowOutput,
    'damage/amine-strength-factor': DamageAmineStrengthFactorOutput,
    'damage/amine-carbon-base-rate': DamageAmineCarbonBaseRateOutput,
    'damage/amine-stainless-rate': DamageAmineStainlessRateOutput,
    'damage/amine-corrosion-assessment': DamageAmineCorrosionAssessmentOutput,
    'damage/amine-thinning-assessment': DamageAmineThinningAssessmentOutput,
    'damage/sulfuric-table-axes': DamageSulfuricTableAxesOutput,
    'damage/sulfuric-table-rate': DamageSulfuricTableRateOutput,
    'damage/sulfuric-thinning-classification': DamageSulfuricThinningClassificationOutput,
    'damage/sulfuric-corrosion-assessment': DamageSulfuricCorrosionAssessmentOutput,
    'damage/sulfuric-thinning-assessment': DamageSulfuricThinningAssessmentOutput,
    'damage/h2sh2-table-axes': DamageH2sh2TableAxesOutput,
    'damage/h2sh2-table-rate': DamageH2sh2TableRateOutput,
    'damage/h2sh2-corrosion-assessment': DamageH2sh2CorrosionAssessmentOutput,
    'damage/h2sh2-thinning-assessment': DamageH2sh2ThinningAssessmentOutput,
    'damage/sulfidic-material-selection': DamageSulfidicMaterialSelectionOutput,
    'damage/sulfidic-table-axes': DamageSulfidicTableAxesOutput,
    'damage/sulfidic-table-rate': DamageSulfidicTableRateOutput,
    'damage/sulfidic-velocity-factor': DamageSulfidicVelocityFactorOutput,
    'damage/sulfidic-thinning-classification': DamageSulfidicThinningClassificationOutput,
    'damage/sulfidic-corrosion-assessment': DamageSulfidicCorrosionAssessmentOutput,
    'damage/sulfidic-thinning-assessment': DamageSulfidicThinningAssessmentOutput,
    'properties/pure-fluid-flash': PropertiesPureFluidFlashOutput,
    'release/pure-liquid-flash-partition': ReleasePureLiquidFlashPartitionOutput,
    'properties/pure-fluid-saturation-pressure': PropertiesPureFluidSaturationPressureOutput,
    'properties/pure-fluid-saturation-temperature': PropertiesPureFluidSaturationTemperatureOutput,
    'dispersion/flashed-boiling-pool-centreline': DispersionFlashedBoilingPoolCentrelineOutput,
    'dispersion/flashed-boiling-pool-footprint': DispersionFlashedBoilingPoolFootprintOutput,
    'dispersion/flashed-boiling-pool-flash-fire': DispersionFlashedBoilingPoolFlashFireOutput,
    'risk/area-event-contribution': RiskAreaEventContributionOutput,
    'risk/flashed-pool-flash-fire-contribution': RiskFlashedPoolFlashFireContributionOutput,
    'damage/groundwater-tks': DamageGroundwaterTksOutput,
    'damage/groundwater-rate-classification': DamageGroundwaterRateClassificationOutput,
    'damage/groundwater-assessment': DamageGroundwaterAssessmentOutput,
    'damage/groundwater-thinning-assessment': DamageGroundwaterThinningAssessmentOutput,
    'damage/thinning-rate-selection': DamageThinningRateSelectionOutput,
    'damage/thinning-selected-mechanisms': DamageThinningSelectedMechanismsOutput,
    'damage/thinning-assessment-period': DamageThinningAssessmentPeriodOutput,
    'damage/thinning-inspection-history': DamageThinningInspectionHistoryOutput,
    'damage/thinning-history-assessment': DamageThinningHistoryAssessmentOutput,
    'damage/caustic-screening': DamageCausticScreeningOutput,
    'damage/caustic-figure-susceptibility': DamageCausticFigureSusceptibilityOutput,
    'damage/caustic-screened-assessment': DamageCausticScreenedAssessmentOutput,
    'damage/amine-cracking-screening': DamageAmineCrackingScreeningOutput,
    'damage/amine-cracking-screened-assessment': DamageAmineCrackingScreenedAssessmentOutput,
    'damage/amine-figure-susceptibility': DamageAmineFigureSusceptibilityOutput,
    'damage/amine-figure-assessment': DamageAmineFigureAssessmentOutput,
    'damage/ssc-screening': DamageSscScreeningOutput,
    'damage/hic-h2s-screening': DamageHicH2sScreeningOutput,
    'damage/ssc-qualified-susceptibility': DamageSscQualifiedSusceptibilityOutput,
    'damage/ssc-qualified-assessment': DamageSscQualifiedAssessmentOutput,
    'damage/hic-h2s-qualified-susceptibility': DamageHicH2sQualifiedSusceptibilityOutput,
    'damage/hic-h2s-monitoring-selection': DamageHicH2sMonitoringSelectionOutput,
    'damage/hic-h2s-qualified-assessment': DamageHicH2sQualifiedAssessmentOutput,
    'damage/acscc-screening': DamageAcsccScreeningOutput,
    'damage/acscc-water-susceptibility': DamageAcsccWaterSusceptibilityOutput,
    'damage/acscc-qualified-assessment': DamageAcsccQualifiedAssessmentOutput,
    'damage/pascc-screening': DamagePasccScreeningOutput,
    'damage/pascc-figure-susceptibility': DamagePasccFigureSusceptibilityOutput,
    'damage/pascc-qualified-assessment': DamagePasccQualifiedAssessmentOutput,
    'damage/clscc-screening': DamageClsccScreeningOutput,
    'damage/clscc-qualified-assessment': DamageClsccQualifiedAssessmentOutput,
    'api520/critical-pressure-ratio': Api520CriticalPressureRatioOutput,
    'api520/flow-coefficient-c': Api520FlowCoefficientCOutput,
    'api520/relieving-pressure': Api520RelievingPressureOutput,
    'api520/gas-critical-area': Api520GasCriticalAreaOutput,
    'api520/gas-subcritical-area': Api520GasSubcriticalAreaOutput,
    'api520/liquid-area': Api520LiquidAreaOutput,
    'api520/liquid-viscosity-factor': Api520LiquidViscosityFactorOutput,
    'api520/gas-critical-capacity': Api520GasCriticalCapacityOutput,
    'api520/gas-subcritical-capacity': Api520GasSubcriticalCapacityOutput,
    'api520/liquid-capacity': Api520LiquidCapacityOutput,
    'risk/portfolio': RiskPortfolioOutput,
    'properties/acid-caustic-representative-fluid': PropertiesAcidCausticRepresentativeFluidOutput,
    'properties/mixture-representative-fluid': PropertiesMixtureRepresentativeFluidOutput,
    'properties/representative-fluid': PropertiesRepresentativeFluidOutput,
    'damage/measured-corrosion-rate': DamageMeasuredCorrosionRateOutput,
    'damage/thinning-type': DamageThinningTypeOutput,
    'risk/assessment-from-damage': RiskAssessmentFromDamageOutput,
}
