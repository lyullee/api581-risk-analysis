"""Output specifications for generation and runtime Python contracts."""
from typing import Any, Literal
from .core import Model, Context, NonNegative, Fraction

# Required fields, including required nullable values, are intentional. No silent output-field loss.
NUMBER = NonNegative
SPECS = {
    "frequency/generic": {"by_hole_per_year": dict[str, NUMBER], "total_per_year": NUMBER},
    "frequency/management-factor": {"score_percent": NUMBER, "management_factor": NUMBER},
    "frequency/adjusted": {"annual_failure_frequency": NUMBER, "unit": Literal["1/year"]},
    "frequency/pof-method-selection": {
        "method": Literal["structural_reliability", "statistical_generic_data", "expert_judgment", "combined"],
        "qualification_basis": str, "uncertainty_quantified": bool,
        "numeric_pof_route": Literal["gff_df_fms", "external_method_result"]},
    "damage/combine": {k: NUMBER for k in ["governing_thinning", "governing_external", "governing_scc", "governing_brittle", "total_damage_factor"]},
    "damage/measured-corrosion-rate": {
        "metal_loss_m": NUMBER, "corrosion_rate_m_year": NUMBER,
        "initial_thickness_m": NUMBER, "current_thickness_m": NUMBER,
        "elapsed_years": NUMBER, "measurement_basis": str, "rate_basis": str,
    },
    "damage/thinning-type": {
        "thinning_type": Literal["general", "localized"],
        "selection_source": Literal["effective_inspection_results", "applicable_mechanism_conservative_default"],
        "effective_inspection_types": list[str],
        "applicable_mechanism_types": list[str],
        "qualification_basis": str,
    },
    "inspection/equivalent": {k: int for k in "abcd"},
    "inspection/effectiveness-category": {
        "category": Literal["A", "B", "C", "D", "E"],
        "ordinal": int,
        "label": str,
        "inspection_credit_allowed": bool,
        "owner_user_basis": str,
    },
    "inspection/effectiveness-summary": {
        "mechanism": Literal["scc", "external_clscc", "cui_clscc", "htha"],
        "highest_effectiveness_category": Literal["A", "B", "C", "D", "E"],
        "inspection_count": int,
        "creditable_inspection_count": int,
        "counts": dict[str, int],
        "equivalent_counts": dict[str, int],
        "e_inspection_count": int,
        "qualification_status": str,
    },
    "inspection/thinning-effectiveness": {
        "effectiveness_category": Literal["A", "B", "C", "D", "E"],
        "damage_type": Literal["general", "local"],
        "inspection_mode": Literal["intrusive", "non_intrusive"],
        "qualification_status": Literal["qualified", "failed"],
        "basis": str,
    },
    "inspection/scc-effectiveness": {
        "effectiveness_category": Literal["A", "B", "C", "D", "E"],
        "mechanism_family": Literal["weld_scc", "clscc_pta"],
        "inspection_mode": Literal["intrusive", "non_intrusive"],
        "qualification_status": Literal["qualified", "failed"],
        "basis": str,
    },
    "inspection/external-effectiveness": {
        "effectiveness_category": Literal["A", "B", "C", "D", "E"],
        "mechanism_family": Literal["external_corrosion", "external_clscc", "cui", "cui_clscc"],
        "insulation_status": Literal["not_applicable", "removed", "not_removed"],
        "qualification_status": Literal["qualified", "failed"],
        "basis": str,
    },
    "inspection/buried-effectiveness": {
        "effectiveness_category": Literal["A", "B", "C", "D", "E"],
        "inspection_mode": Literal["intrusive", "non_intrusive"],
        "qualification_status": Literal["qualified", "failed"],
        "basis": str,
    },
    "inspection/prd-effectiveness": {
        "effectiveness_category": Literal["A", "B", "C", "D", "E"],
        "component_type": Literal["pressure_relief_device", "rupture_disk"],
        "qualification_status": Literal["qualified", "failed"],
        "basis": str,
    },
    "inspection/lining-effectiveness": {
        "effectiveness_category": Literal["A", "B", "C", "D", "E"],
        "inspection_mode": Literal["intrusive", "non_intrusive"],
        "qualification_status": Literal["qualified", "failed"],
        "basis": str,
    },
    "inspection/tube-bundle-uncertainty": {
        "inspection_effectiveness": Literal["A", "B", "C", "D", "E"],
        "uncertainty_percent": float,
        "uncertainty_fraction": Fraction,
        "baseline_no_history_percent": float,
        "owner_user_basis": str,
    },
    "inspection/ast-effectiveness": {
        "effectiveness_category": Literal["A", "B", "C", "D", "E"],
        "component_type": Literal["shell_internal", "shell_external", "tank_bottom"],
        "inspection_side": Literal["internal", "external", "soil_side", "product_side"],
        "qualification_status": Literal["qualified", "failed"],
        "basis": str,
    },
    "reliability/weibull": {"cumulative_failure_probability": Fraction, "survival_probability": Fraction,
                            "hazard_per_year": NUMBER | None, "hazard_singular_at_origin": bool},
    "reliability/weibull-quantile": {"age_years": NUMBER},
    "reliability/weibull-from-mttf": {"characteristic_life_years": NUMBER},
    "reliability/poisson-probability": {"period_failure_probability": Fraction},
    "release/orifice-area": {"area_m2": NUMBER},
    "release/viscosity-factor": {"viscosity_factor": NUMBER},
    "release/liquid": {"mass_rate_kg_s": NUMBER, "area_m2": NUMBER, "regime": Literal["liquid"]},
    "release/gas": {"mass_rate_kg_s": NUMBER, "area_m2": NUMBER, "regime": Literal["sonic", "subsonic"],
                    "critical_downstream_upstream_ratio": Fraction, "transition_pressure_pa_abs": NUMBER},
    "api520/critical-pressure-ratio": {"critical_pressure_ratio": Fraction},
    "api520/flow-coefficient-c": {"flow_coefficient_c": NUMBER},
    "api520/relieving-pressure": {"relieving_pressure_psig": NUMBER, "relieving_pressure_kpaa": NUMBER},
    "api520/gas-critical-area": {"required_area_mm2": NUMBER},
    "api520/gas-subcritical-area": {"required_area_mm2": NUMBER, "back_pressure_ratio": Fraction, "subcritical_flow_factor": NUMBER},
    "api520/liquid-area": {"required_area_mm2": NUMBER},
    "api520/liquid-viscosity-factor": {"viscosity_factor": NUMBER},
    "api520/gas-critical-capacity": {"mass_capacity_kg_h": NUMBER},
    "api520/gas-subcritical-capacity": {"mass_capacity_kg_h": NUMBER, "back_pressure_ratio": Fraction, "subcritical_flow_factor": NUMBER},
    "api520/liquid-capacity": {"flow_capacity_l_min": NUMBER},
    "properties/heat-capacity-ratio": {"heat_capacity_ratio": NUMBER},
    "properties/representative-fluid": {
        "fluid": str, "molecular_weight_kg_kmol": NUMBER,
        "liquid_density_kg_m3": NUMBER, "normal_boiling_point_k": float,
        "ambient_state": str, "cp_note": int | None,
        "cp_value_table_units": float | None, "cp_basis": str,
        "autoignition_temperature_k": float | None, "source_table": str},
    "properties/acid-caustic-representative-fluid": {
        "selection": Literal["acid_reference", "not_applicable"],
        "representative_fluid": str | None, "release_phase": Literal["liquid"] | None,
        "consequence_model": Literal["acid_splash"] | None, "selection_basis": str},
    "properties/mixture-representative-fluid": {
        "molecular_weight_kg_kmol": NUMBER, "normal_boiling_point_k": float,
        "liquid_density_kg_m3": NUMBER, "autoignition_temperature_k": float,
        "selected_fluid": str, "relevant_mole_fraction": Fraction,
        "selection_basis": str, "level2_recommended": bool},
    "release/available-inventory": {"added_mass_kg": NUMBER, "available_mass_kg": NUMBER},
    "release/type": {"release_type": Literal["continuous", "instantaneous"], "time_to_4536kg_s": NUMBER | None},
    "release/magnitude": {"adjusted_rate_kg_s": NUMBER, "duration_s": NUMBER, "released_mass_kg": NUMBER},
    "release/detection-isolation": {"release_reduction_fraction": Fraction,
        "adjusted_rate_kg_s": NUMBER, "maximum_leak_duration_s": NUMBER | None,
        "duration_s": NUMBER | None, "released_mass_kg": NUMBER,
        "detection_rating": Literal["A", "B", "C"],
        "isolation_rating": Literal["A", "B", "C"],
        "hole_size": Literal["small", "medium", "large", "rupture"]},
    "release/detection-isolation-rating": {
        "detection_rating": Literal["A", "B", "C"],
        "isolation_rating": Literal["A", "B", "C"],
        "detection_type": str, "isolation_type": str, "qualification_basis": str},
    "release/hole-size-selection": {
        "selected_hole": Literal["small", "medium", "large", "rupture"],
        "representative_diameter_m": NUMBER, "lower_bound_m": NUMBER,
        "upper_bound_m": NUMBER | None, "diameter_basis": str, "source_table": str},
    "release/integrate-profile": {"released_mass_kg": NUMBER, "duration_s": NUMBER},
    "properties/mixture-molecular-weight": {"molecular_weight_kg_kmol": NUMBER, "mass_fractions": list[Fraction]},
    "effects/jet-fire-power": {"radiated_power_w": NUMBER},
    "effects/jet-fire-flux": {"received_flux_w_m2": NUMBER},
    "effects/jet-fire-distance": {"threshold_distance_m": NUMBER, "consequence_area_m2": NUMBER, "transmissivity_at_distance": Fraction | None},
    "effects/flash-fire": {"personnel_area_m2": NUMBER, "equipment_area_m2": NUMBER},
    "effects/pool-fire-area": {k: NUMBER for k in ["burning_area_m2", "inventory_limited_area_m2", "pool_area_m2", "pool_radius_m"]},
    "consequence/power-law-area": {"area_m2": NUMBER, "coefficient_source": str},
    "events/leakage-tree": {"terminal_probabilities": dict[str, Fraction], "probability_sum": NUMBER},
    "effects/toxic-probit": {"probit": float | None, "effect_probability": Fraction},
    "effects/pool-burning-rate": {"burning_rate_kg_m2_s": NUMBER},
    "effects/fireball-geometry": {"diameter_m": NUMBER, "center_height_m": NUMBER, "duration_s": NUMBER},
    "effects/fireball-radiative-fraction": {"radiative_fraction": Fraction},
    "effects/fireball-emissive-power": {"surface_emissive_power_w_m2": NUMBER},
    "effects/vce-tnt-equivalence": {"tnt_equivalent_mass_kg": NUMBER},
    "consequence/expected": {"equipment_area_m2": NUMBER, "personnel_area_m2": NUMBER, "financial_consequence": NUMBER, "currency": str},
    "risk/aggregate": {"annual_failure_frequency": NUMBER, "equipment_area_risk_m2_per_year": NUMBER,
                       "personnel_area_risk_m2_per_year": NUMBER, "area_risk_m2_per_year": NUMBER,
                       "financial_risk_per_year": NUMBER, "currency": str,
                       "frequency_weighted_equipment_area_m2": NUMBER | None, "frequency_weighted_personnel_area_m2": NUMBER | None},
    "risk/portfolio": {"component_count": int, "annual_failure_frequency": NUMBER,
                       "equipment_area_risk_m2_per_year": NUMBER,
                       "personnel_area_risk_m2_per_year": NUMBER,
                       "area_risk_m2_per_year": NUMBER, "financial_risk_per_year": NUMBER,
                       "currency": str, "disjointness_basis": str,
                       "component_contributions": dict[str, dict[str, NUMBER]]},
    "consequence/financial-total": {"financial_consequence": NUMBER, "currency": str, "cost_basis_year": int},
    "risk/matrix": {"frequency_category": int, "consequence_category": int, "risk_label": str, "policy_id": str},
    "damage/thinning-wall-loss": {"wall_loss_fraction": NUMBER},
    "damage/flow-stress": {"flow_stress_pa": NUMBER},
    "damage/thinning-strength-ratio": {"strength_ratio": NUMBER},
    "damage/thinning-posterior": {"posterior_probabilities": list[Fraction]},
    "damage/thinning-base": {"reliability_indices": list[float], "damage_state_failure_probabilities": list[Fraction],
                             "weighted_failure_probability": Fraction, "base_damage_factor": NUMBER},
    "damage/thinning-adjust": {"thinning_damage_factor": NUMBER},
    "damage/scc-base": {"base_damage_factor": NUMBER},
    "damage/caustic-severity": {"severity_index": int},
    "damage/caustic-escalation": {"damage_factor": NUMBER},
    "damage/lining-adjust": {"condition_factor": NUMBER, "monitoring_factor": NUMBER, "lining_damage_factor": NUMBER},
}
SPECS["damage/thinning-unclad"] = {**SPECS["damage/thinning-wall-loss"], **SPECS["damage/thinning-strength-ratio"],
    **SPECS["damage/thinning-posterior"], **SPECS["damage/thinning-base"], **SPECS["damage/thinning-adjust"]}
SPECS.update({
    "level1/flammable-coefficients": {"a": NUMBER,"b":NUMBER,"magnitude_unit":str,"area_unit":str},
    "release/detection-reduction": {"reduction_fraction":Fraction},
    "release/detection-duration": {"maximum_duration_s":NUMBER},
    "level1/release-phase": {"release_phase":Literal["gas","liquid"]},
    "level1/energy-efficiency": {"energy_efficiency_factor":NUMBER},
    "level1/blending-factors": {"instantaneous_weight":Fraction,"autoignition_likely_weight":Fraction},
    "level1/flammable-area": {"equipment_area_m2":NUMBER,"personnel_area_m2":NUMBER,"instantaneous_weight":Fraction,
                              "autoignition_likely_weight":Fraction,"energy_efficiency_factor":NUMBER}
})
SPECS["level1/release-to-flammable"] = {"theoretical_rate_kg_s":NUMBER,"available_mass_kg":NUMBER,
    "release_type":Literal["continuous","instantaneous"],"reduction_fraction":Fraction,"maximum_duration_s":NUMBER,
    **SPECS["release/magnitude"],**SPECS["level1/flammable-area"]}
SPECS.update({
    "level1/mitigation":{"mitigation_fraction":Fraction},
    "level1/toxic-source":{"toxic_rate_kg_s":NUMBER,"toxic_mass_kg":NUMBER},
    "level1/toxic-duration":{"duration_s":NUMBER},
    "level1/toxic-area":{"unweighted_personnel_area_m2":NUMBER,"personnel_area_m2":NUMBER},
    "level1/steam-area":{"continuous_area_m2":NUMBER,"instantaneous_area_m2":NUMBER,"instantaneous_weight":Fraction,"personnel_area_m2":NUMBER,"equipment_area_m2":NUMBER},
    "level1/acid-caustic-area":{"personnel_area_m2":NUMBER,"equipment_area_m2":NUMBER,"coefficient_g":NUMBER,"exponent_h":NUMBER},
    "consequence/final-area":{"equipment_area_m2":NUMBER,"personnel_area_m2":NUMBER,"consequence_area_m2":NUMBER},
    "consequence/hole-weighted":{"weighted_value":NUMBER,"value_unit":str},
    **{id:{"cost":NUMBER,"currency":str} for id in ["financial/surrounding-damage","financial/production-loss","financial/injury"]},
    "financial/spill-cleanup":{"remediation_volume_m3":NUMBER,"cost":NUMBER,"currency":str}
})
SPECS["level1/consequence-summary"] = {name:NUMBER for name in ["flammable_equipment_area_m2","flammable_personnel_area_m2",
    "toxic_personnel_area_m2","nfnt_personnel_area_m2","equipment_area_m2","personnel_area_m2","consequence_area_m2","generic_frequency_per_year"]}
SPECS.update({
    "financial/repair-table":{"cost_by_hole_usd_2001":dict[str,NUMBER],"cost_basis_year":int,"currency":str},
    "financial/material-factor":{"material_factor":NUMBER},
    "financial/outage-table":{"days_by_hole":dict[str,NUMBER|None]},
    "financial/component-repair":{"weighted_repair_cost_usd_2001":NUMBER,"cost":NUMBER,"material_factor":NUMBER,"cost_basis_year":int,"currency":str},
    "financial/component-outage":{"component_outage_days":NUMBER,"effective_days_by_hole":dict[str,NUMBER|None]},
    "financial/surrounding-outage":{"surrounding_outage_days":NUMBER},
    "properties/leak-table":{"molecular_weight_kg_kmol":NUMBER,"tabulated_liquid_density_kg_m3":NUMBER,"normal_boiling_point_k":NUMBER,"evaporated_fraction_24h":Fraction},
    "financial/cleanup-eligibility":{"include_cleanup_cost":bool}
})
SPECS["financial/hole-total"] = {
    "currency": str,
    "cost_basis_year": int,
    "total_generic_frequency_per_year": NUMBER,
    "per_hole": list[dict[str, NUMBER | str]],
    "frequency_weighted_financial_consequence": NUMBER,
    "annual_financial_risk": NUMBER,
}
SPECS["financial/level1-consequence"] = {**{name:NUMBER for name in ["component_repair_cost","surrounding_equipment_cost",
    "business_interruption_cost","injury_cost","environmental_cost","component_outage_days","surrounding_outage_days",
    "surrounding_cost_reference_usd_2001","financial_consequence"]},"currency":str,"cost_basis_year":int}
SPECS["damage/scc-severity"]={"severity_index":int}
SPECS["damage/hic-monitoring-factor"]={"monitoring_factor":NUMBER}
for _id in ["caustic","amine","ssc","hic-sohic-h2s","acscc","pascc","clscc","hsc-hf","hic-sohic-hf"]:
    SPECS["damage/"+_id]={"effective_susceptibility":str,"severity_index":int,"equivalent_inspection_grade":str,
        "equivalent_inspection_count":int,"base_damage_factor":NUMBER,"age_factor":NUMBER,"monitoring_factor":NUMBER,"damage_factor":NUMBER}
for _id in ["hsc-hf","ssc","hic-hf","hic-h2s","clscc"]:
    SPECS["damage/"+_id+"-susceptibility"]={"susceptibility":Literal["none","low","medium","high"]}
SPECS["damage/acscc-susceptibility"]={"susceptibility":Literal["none","low","medium","high"]}
SPECS["damage/pascc-susceptibility"]={"susceptibility":Literal["none","low","medium","high"]}
SPECS["damage/wet-h2s-environment"]={"environmental_severity":Literal["low","moderate","high"],"susceptibility_upgrade_required":bool}
for _id in ["external-base-rate","cui-base-rate"]:
    SPECS["damage/"+_id]={"base_corrosion_rate_m_year":NUMBER}
SPECS["damage/external-time-weighted-rate"]={"base_corrosion_rate_m_year":NUMBER,"period_rates_m_year":list[NUMBER]}
SPECS["damage/external-rate-adjust"]={"design_interface_factor":NUMBER,"corrosion_rate_m_year":NUMBER}
SPECS["damage/cui-rate-adjust"]={name:NUMBER for name in ["design_interface_factor","corrosion_rate_m_year","insulation_factor","complexity_factor","condition_factor"]}
SPECS["damage/coating-exposure"]={"coating_credit_years":NUMBER,"corrosion_exposure_years":NUMBER}
for _id in ["external-corrosion","cui"]:
    SPECS["damage/"+_id]={**{name:NUMBER for name in ["corrosion_rate_m_year","coating_credit_years","corrosion_exposure_years","wall_loss_fraction","strength_ratio","weighted_failure_probability","damage_factor"]},
                          "posterior_probabilities":list[Fraction],"reliability_indices":list[float]}
SPECS["damage/external-clscc-base-susceptibility"]={"base_susceptibility":Literal["none","low","medium","high"]}
for _id in ["external-clscc","cui-clscc"]:
    SPECS["damage/"+_id]={"effective_susceptibility":str,"severity_index":int,"equivalent_inspection_grade":str,
        "equivalent_inspection_count":int,**{name:NUMBER for name in ["base_damage_factor","age_factor","coating_credit_years","cracking_exposure_years","damage_factor"]}}
SPECS["damage/fatigue-base"]={name:NUMBER for name in ["previous_failure_factor","shaking_factor","shaking_duration_factor","cyclic_loading_factor","base_damage_factor"]}
SPECS["damage/fatigue-adjustments"]={name:NUMBER for name in ["corrective_action_factor","complexity_factor","pipe_condition_factor","joint_branch_factor","branch_diameter_factor","combined_adjustment_factor"]}
SPECS["damage/mechanical-fatigue"]={**SPECS["damage/fatigue-base"],**SPECS["damage/fatigue-adjustments"],"damage_factor":NUMBER}
SPECS["properties/hydrogen-partial-pressure"]={"hydrogen_partial_pressure_pa_abs":NUMBER}
SPECS["damage/htha-factor"]={"damage_factor":NUMBER}
SPECS["damage/htha-carbon-screen"]={"susceptibility":str,"damage_factor":NUMBER}

SPECS["damage/brittle-reference-temperature"] = {"reference_temperature_k": NUMBER, "table_basis": str}
SPECS["damage/brittle-service-factor"] = {"service_experience_factor": NUMBER, "thin_component_credit": bool, "service_criteria": dict[str, bool]}
SPECS["damage/brittle-base"] = {"base_damage_factor": NUMBER, "table": Literal["20.4M", "20.5M"]}
SPECS["damage/brittle-fracture"] = {**SPECS["damage/brittle-reference-temperature"], **SPECS["damage/brittle-service-factor"],
                                   **SPECS["damage/brittle-base"], "cet_minus_reference_k": float, "damage_factor": NUMBER}
SPECS["damage/embrittlement-885f"] = {"reference_temperature_k": NUMBER, "minimum_minus_reference_k": float, "damage_factor": NUMBER}
SPECS["damage/sigma-content"] = {"sigma_category": Literal["low", "medium", "high"]}
SPECS["damage/sigma-embrittlement"] = {"damage_factor": NUMBER, "sigma_category": Literal["low", "medium", "high"]}

SPECS["damage/temper-j-factor"] = {"j_factor": NUMBER}
SPECS["damage/temper-xbar"] = {"xbar_factor": NUMBER}
SPECS["damage/temper-xbar-shift"] = {"delta_fatt_k": NUMBER}
SPECS["damage/temper-generation-shift"] = {"generation": int, "delta_fatt_k": NUMBER, "source_basis": Literal["printed_C", "printed_F_difference_converted"]}
SPECS["damage/temper-embrittlement"] = {**SPECS["damage/brittle-reference-temperature"],
    "shifted_reference_temperature_k": NUMBER, "minimum_minus_shifted_reference_k": float,
    "delta_fatt_k": NUMBER, "damage_factor": NUMBER, "table": Literal["20.4M", "20.5M"]}

SPECS["bundle/weibayes-history"] = {"shape": NUMBER, "characteristic_life_years": NUMBER, "failure_count": int, "record_count": int}
SPECS["bundle/condition-update"] = SPECS["bundle/weibayes-history"]
SPECS["bundle/thickness-life"] = {"thinning_rate_m_year": NUMBER, "predicted_bundle_life_years": NUMBER | None,
    "remaining_life_years": NUMBER | None, "remaining_wall_threshold_reached": bool,
    "formula_basis": Literal["printed_eq_1_72", "remaining_wall_threshold"]}
SPECS["bundle/estimated-life"] = {"predicted_bundle_life_years": NUMBER}
SPECS["bundle/life-extension"] = {"adjusted_age_at_action_years": NUMBER, "effective_age_years": NUMBER, "installation_shift_years": NUMBER}
SPECS["bundle/consequence"] = {"production_loss_cost": NUMBER, "financial_consequence": NUMBER, "currency": str, "cost_basis_year": int}
SPECS["bundle/risk"] = {"cumulative_failure_probability": Fraction, "probability_weighted_consequence": NUMBER, "currency": str}
SPECS["bundle/target-age"] = {"target_failure_probability": Fraction, "target_age_years": NUMBER | None, "status": Literal["finite_crossing", "no_finite_crossing"]}
SPECS["bundle/deferral-decision"] = {"conditional_failure_probability": Fraction, "expected_incremental_risk": NUMBER,
    "inspection_hurdle_cost": NUMBER, "replacement_hurdle_cost": NUMBER,
    "inspection_economically_justified": bool, "replacement_economically_justified": bool, "currency": str}
SPECS["bundle/replacement-optimization"] = {"optimal_grid_age_years": NUMBER, "minimum_cost_per_day": NUMBER,
    "minimum_at_grid_boundary": bool, "grid_points": int, "samples": list[dict[str, NUMBER]], "currency": str}
SPECS["prd/default-weibull"] = {"shape": NUMBER, "default_characteristic_life_years": NUMBER, "design_factor": NUMBER, "design_adjusted_characteristic_life_years": NUMBER}
SPECS["prd/environment-factor"] = {"environment_factor": Fraction, "individual_factors": dict[str, Fraction]}
SPECS["prd/set-pressure-factor"] = {"set_pressure_factor": Fraction}
SPECS["prd/overpressure-factor"] = {"overpressure_factor": Fraction}
SPECS["prd/demand-rate"] = {"case_demand_rates_per_year": list[NUMBER], "total_demand_rate_per_year": NUMBER}
SPECS["prd/inspection-update"] = {"prior_failure_probability": Fraction, "conditional_failure_probability": Fraction | None,
    "weighted_failure_probability": Fraction, "updated_characteristic_life_years": NUMBER, "update_applied": bool, "effective_failed_result": bool}
SPECS["prd/protected-equipment"] = {"normal_failure_frequency_per_year": NUMBER, "source_model_loc_probability": Fraction, "by_hole_loc_probability": dict[str, Fraction]}
SPECS["prd/fail-frequency"] = {"annual_failure_frequency": NUMBER}
SPECS["prd/base-reliability"] = {"shape": NUMBER, "modified_characteristic_life_years": NUMBER, "environment_factor": Fraction,
    "scenario_probability_factor": Fraction, "unadjusted_cumulative_probability": Fraction, "scenario_adjusted_probability": Fraction}
SPECS["bundle/material-factor"] = {"material_factor": NUMBER}
SPECS["bundle/replacement-cost"] = {"bundle_volume_m3": NUMBER, "reference_basis_cost_usd": NUMBER, "replacement_cost": NUMBER, "currency": str, "cost_basis_year": int}
SPECS["bundle/life-extension-factor"] = {"life_extension_factor": Fraction}
SPECS["bundle/categories"] = {"probability_category": int, "consequence_category": Literal["A", "B", "C", "D", "E"]}

SPECS["prd/leakage-rates"] = {name: NUMBER for name in ["minor_rate_kg_s", "moderate_table_rate_kg_s", "mild_moderate_equation_rate_kg_s", "stuck_open_rate_kg_s"]}
SPECS["prd/leakage-duration"] = {"mild_moderate_duration_s": NUMBER, "stuck_open_duration_s": NUMBER}
SPECS["prd/inventory-loss-factor"] = {"inventory_loss_factor": Fraction}
_MONEY = {"currency": str, "cost_basis_year": int}
SPECS["prd/inventory-loss"] = {"leaked_mass_kg": NUMBER, "inventory_loss_equivalent_mass_kg": NUMBER, "inventory_loss_cost": NUMBER, **_MONEY}
SPECS["prd/repair-cost"] = {"reference_cost_usd": NUMBER, "repair_cost": NUMBER, **_MONEY}
SPECS["prd/production-loss"] = {"production_loss_cost": NUMBER, "shutdown_loss_applied": bool, **_MONEY}
SPECS["prd/leakage-consequence"] = {"financial_consequence": NUMBER, "case_weights": dict[str, Fraction],
    "costs_by_case": dict[str, dict[str, NUMBER]], "inventory_loss_factor": Fraction,
    "model_basis": Literal["two_case_equations", "three_case_table_7_15"], **_MONEY}
SPECS["prd/multiple-device-pressure"] = {"multiple_device_factor": Fraction,
    "protected_equipment_pressure_pa_gauge": NUMBER, "unreduced_pressure_for_fop_pa_gauge": NUMBER}
SPECS["prd/fail-risk"] = {"protected_equipment_risks_per_year": dict[str, NUMBER], "maximum_fail_risk_per_year": NUMBER,
    "governing_equipment_ids": list[str], **_MONEY}
_LEAK_BASIS = Literal["annual_frequency", "source_cumulative_probability"]
SPECS["prd/leakage-risk"] = {"leakage_risk_value": NUMBER, "measure_basis": _LEAK_BASIS, "risk_unit": Literal["currency", "currency/year"], **_MONEY}
SPECS["prd/total-risk"] = {"annual_financial_risk": NUMBER | None, "source_total_risk_index": NUMBER | None,
    "leakage_measure_basis": _LEAK_BASIS, **_MONEY}
SPECS["prd/risk-assessment"] = {**SPECS["prd/fail-risk"], **SPECS["prd/total-risk"],
    "leakage_risk_value": NUMBER, "leakage_risk_unit": Literal["currency", "currency/year"]}
SPECS["prd/service-age"] = {"effective_age_years": NUMBER, "elapsed_since_original_installation_years": NUMBER,
    "last_age_reset_date": str, "last_age_reset_type": Literal["installation", "overhaul", "replacement"],
    "parameter_history_valid_from_date": str, "inspection_update_start_date": str, "last_test_date": str | None, "days_per_year": NUMBER}

SPECS["release/controlled-scenario"] = {"theoretical_rate_kg_s": NUMBER, "available_mass_kg": NUMBER,
    "release_type": Literal["continuous", "instantaneous"], "reduction_fraction": Fraction,
    "maximum_duration_s": NUMBER, "adjusted_rate_kg_s": NUMBER, "duration_s": NUMBER, "released_mass_kg": NUMBER}
SPECS["level1/type1-flammable-area"] = {"area_m2": NUMBER, "coefficient_a": NUMBER, "coefficient_b": NUMBER, "energy_efficiency_factor": NUMBER}
SPECS["level1/type1-flammable-consequence"] = {"equipment_area_m2": NUMBER, "personnel_area_m2": NUMBER, "energy_efficiency_factor": NUMBER, "fluid_type": Literal[1]}
SPECS["level1/release-to-type1-flammable"] = {**SPECS["release/controlled-scenario"], **SPECS["level1/type1-flammable-consequence"]}
SPECS["level1/release-to-acid"] = {**SPECS["release/controlled-scenario"],
    "personnel_area_m2": NUMBER, "equipment_area_m2": NUMBER,
    "coefficient_g": NUMBER, "exponent_h": NUMBER,
    "representative_fluid": Literal["Acid"], "release_phase": Literal["liquid"]}
SPECS["level1/release-to-steam"] = {**SPECS["release/controlled-scenario"],
    "continuous_area_m2": NUMBER, "instantaneous_area_m2": NUMBER,
    "instantaneous_weight": Fraction, "personnel_area_m2": NUMBER,
    "equipment_area_m2": NUMBER, "representative_fluid": Literal["Steam"],
    "release_phase": Literal["gas"]}
SPECS["level1/hf-h2s-toxic-coefficients"] = {"c": NUMBER, "d": float, "native_magnitude_unit": Literal["lb/s", "lb"],
    "native_area_unit": Literal["ft2"], "si_mass_multiplier": NUMBER, "si_area_multiplier": NUMBER,
    "source_cell_status": Literal["clear", "ambiguous_print", "qualified_override"]}
SPECS["level1/hf-h2s-toxic-area"] = {"unweighted_personnel_area_m2": NUMBER, "personnel_area_m2": NUMBER}
SPECS["level1/misc-toxic-coefficients"] = {"e": NUMBER, "f": NUMBER, "native_rate_unit": Literal["kg/s"],
    "native_area_unit": Literal["m2"], "si_mass_multiplier": NUMBER, "si_area_multiplier": NUMBER}
SPECS["level1/misc-toxic-area"] = SPECS["level1/hf-h2s-toxic-area"]
SPECS["level1/toxic-cutoff"] = {"idlh_ppm": NUMBER, "requires_toxic_evaluation": bool}
SPECS["level1/toxic-mitigation"] = {"toxic_rate_kg_s": NUMBER, "toxic_mass_kg": NUMBER, "duration_s": NUMBER}
SPECS["level1/toxic-component-consequence"] = {**SPECS["level1/toxic-mitigation"], **SPECS["level1/hf-h2s-toxic-area"],
    "unmitigated_duration_s": NUMBER, "screening_applied": bool, "requires_toxic_evaluation": bool}
SPECS["level1/release-to-toxic"] = {**SPECS["release/controlled-scenario"],
    **SPECS["level1/toxic-component-consequence"]}
SPECS["level1/toxic-mixture-consequence"] = {
    "personnel_area_m2": NUMBER, "critical_component_id": str,
    "component_areas_m2": dict[str, NUMBER], "component_count": int}
SPECS["level1/toxic-hole-summary"] = {
    "personnel_area_m2": NUMBER, "total_generic_frequency_per_year": NUMBER,
    "by_hole_personnel_area_m2": dict[str, NUMBER]}

SPECS["properties/water-partial-pressure"] = {"water_partial_pressure_pa": NUMBER}
SPECS["effects/atmospheric-transmissivity"] = {"transmissivity": Fraction, "uncapped_transmissivity": NUMBER | None, "dry_air_limit": bool}
SPECS["effects/pool-mixture-burning-rate"] = {"burning_rate_kg_m2_s": NUMBER}
SPECS["effects/pool-flame-geometry"] = {"nondimensional_wind_speed": NUMBER, "flame_length_m": NUMBER,
    "flame_tilt_rad": NUMBER, "vertical_flame_height_m": NUMBER, "downwind_axis_extension_m": NUMBER}
SPECS["effects/pool-surface-emissive-power"] = {"burning_mass_rate_kg_s": NUMBER, "radiated_power_w": NUMBER,
    "emitting_surface_area_m2": NUMBER, "surface_emissive_power_w_m2": NUMBER}
_POOL_BASIS = Literal["api581_printed", "geometry_checked"]
_POOL_DISTANCE = Literal["printed_surface_ratio", "surface_to_axis"]
_POOL_STATUS = Literal["threshold_solved", "below_limit_at_domain_boundary"]
SPECS["effects/pool-cylinder-view-factor"] = {"vertical_view_factor": float, "horizontal_view_factor": float,
    "maximum_view_factor": NUMBER, "physical_range": bool, "equation_basis": _POOL_BASIS}
SPECS["effects/pool-radiation-flux"] = {"received_flux_w_m2": NUMBER, "transmissivity": Fraction,
    "maximum_view_factor": NUMBER, "view_factor_distance_m": NUMBER, "equation_basis": _POOL_BASIS, "distance_convention": _POOL_DISTANCE}
SPECS["effects/pool-fire-distance"] = {"safe_surface_distance_m": NUMBER, "consequence_radius_m": NUMBER,
    "consequence_area_m2": NUMBER, "status": _POOL_STATUS, "iterations": int, "flux_residual_w_m2": float | None,
    "minimum_surface_domain_m": NUMBER, "equation_basis": _POOL_BASIS, "distance_convention": _POOL_DISTANCE}
SPECS["effects/pool-fire-consequence"] = {"burning_rate_kg_m2_s": NUMBER, **SPECS["effects/pool-fire-area"],
    "flame_length_m": NUMBER, "flame_tilt_rad": NUMBER, "surface_emissive_power_w_m2": NUMBER,
    "personnel_area_m2": NUMBER, "equipment_area_m2": NUMBER,
    "personnel_safe_surface_distance_m": NUMBER, "equipment_safe_surface_distance_m": NUMBER,
    "personnel_status": Literal["no_pool", "threshold_solved", "below_limit_at_domain_boundary"],
    "equipment_status": Literal["no_pool", "threshold_solved", "below_limit_at_domain_boundary"],
    "equation_basis": _POOL_BASIS, "distance_convention": _POOL_DISTANCE}

_FIREBALL_BASIS = Literal["api581_printed", "elevated_sphere_maximum"]
_FIREBALL_STATUS = Literal["threshold_solved", "below_limit_at_origin"]
SPECS["effects/fireball-mass"] = {"flammable_mass_kg": NUMBER}
SPECS["effects/fireball-view-factor"] = {"view_factor": Fraction, "model_center_distance_m": NUMBER,
    "attenuation_path_m": NUMBER, "geometry_basis": _FIREBALL_BASIS}
SPECS["effects/fireball-radiation-flux"] = {**SPECS["effects/fireball-view-factor"],
    "transmissivity": Fraction, "received_flux_w_m2": NUMBER}
SPECS["effects/fireball-distance"] = {"safe_distance_m": NUMBER, "consequence_area_m2": NUMBER,
    "status": _FIREBALL_STATUS, "iterations": int, "flux_residual_w_m2": float | None, "geometry_basis": _FIREBALL_BASIS}
SPECS["effects/fireball-consequence"] = {**SPECS["effects/fireball-mass"], **SPECS["effects/fireball-geometry"],
    **SPECS["effects/fireball-radiative-fraction"], **SPECS["effects/fireball-emissive-power"],
    "personnel_area_m2": NUMBER, "equipment_area_m2": NUMBER, "personnel_safe_distance_m": NUMBER,
    "equipment_safe_distance_m": NUMBER, "personnel_status": Literal["no_flammable_mass", "threshold_solved", "below_limit_at_origin"],
    "equipment_status": Literal["no_flammable_mass", "threshold_solved", "below_limit_at_origin"], "geometry_basis": _FIREBALL_BASIS}

SPECS["effects/vce-scaled-distance"] = {"scaled_distance_m_kg13": NUMBER}
SPECS["effects/vce-scaled-overpressure"] = {"side_on_overpressure_pa": NUMBER, "slope_pa_per_scaled_distance": float}
SPECS["effects/vce-blast-overpressure"] = {**SPECS["effects/vce-scaled-distance"], **SPECS["effects/vce-scaled-overpressure"]}
SPECS["effects/blast-building-probit"] = {"probit": float, "building_collapse_probability": Fraction}
SPECS["effects/blast-building-pressure-threshold"] = {"probit": float, "side_on_overpressure_pa": NUMBER}
_BLAST_STATUS = Literal["threshold_solved", "no_explosion"]
SPECS["effects/vce-blast-distance"] = {"safe_distance_m": NUMBER, "consequence_area_m2": NUMBER,
    "scaled_distance_m_kg13": NUMBER | None, "status": _BLAST_STATUS, "iterations": int, "pressure_residual_pa": float | None}
SPECS["effects/vce-blast-consequence"] = {"tnt_equivalent_mass_kg": NUMBER,
    "personnel_threshold_overpressure_pa": NUMBER, "personnel_building_collapse_probability": Fraction,
    "equipment_threshold_overpressure_pa": NUMBER, "personnel_safe_distance_m": NUMBER, "equipment_safe_distance_m": NUMBER,
    "personnel_area_m2": NUMBER, "equipment_area_m2": NUMBER, "personnel_status": _BLAST_STATUS, "equipment_status": _BLAST_STATUS,
    "mass_basis": Literal["between_flammability_limits", "total_released_flammable"]}

SPECS["effects/physical-explosion-tnt"] = {"vapor_stored_energy_j": NUMBER, "tnt_equivalent_mass_kg": NUMBER}
SPECS["release/bleve-flashed-amount"] = {"flashed_liquid_mass_kg": NUMBER, "flashed_amount_kmol": NUMBER}
SPECS["effects/bleve-liquid-tnt"] = {"liquid_expansion_energy_j": NUMBER, "tnt_equivalent_mass_kg": NUMBER}
_RUPTURE_STATUS = Literal["threshold_solved", "no_explosion", "not_rupture"]
_RUPTURE_AREAS = {"potential_tnt_equivalent_mass_kg": NUMBER, "event_tnt_equivalent_mass_kg": NUMBER,
    "personnel_threshold_overpressure_pa": NUMBER, "equipment_threshold_overpressure_pa": NUMBER,
    "personnel_building_collapse_probability": Fraction, "personnel_safe_distance_m": NUMBER, "equipment_safe_distance_m": NUMBER,
    "personnel_area_m2": NUMBER, "equipment_area_m2": NUMBER, "personnel_status": _RUPTURE_STATUS, "equipment_status": _RUPTURE_STATUS,
    "hole": Literal["small", "medium", "large", "rupture"]}
SPECS["effects/physical-explosion-consequence"] = {"vapor_stored_energy_j": NUMBER, **_RUPTURE_AREAS}
SPECS["effects/bleve-consequence"] = {"liquid_expansion_energy_j": NUMBER, "vapor_stored_energy_j": NUMBER,
    "liquid_tnt_equivalent_mass_kg": NUMBER, "vapor_tnt_equivalent_mass_kg": NUMBER, **_RUPTURE_AREAS}
SPECS["consequence/level2-nfnt-case"] = {"equipment_area_m2": NUMBER, "personnel_area_m2": NUMBER}
SPECS["consequence/level2-nfnt-summary"] = {**SPECS["consequence/level2-nfnt-case"], "total_generic_frequency_per_year": NUMBER,
    "by_hole_equipment_area_m2": dict[str, NUMBER], "by_hole_personnel_area_m2": dict[str, NUMBER]}

SPECS["properties/toxic-impact-table"] = {"probit_intercept": float | None, "probit_slope": NUMBER | None,
    "concentration_exponent": NUMBER | None, "probit_available": bool, "probit_concentration_unit": Literal["ppm"],
    "probit_duration_unit": Literal["s"], "idlh_ppm": NUMBER | None, "aegl3_ppm": dict[str, NUMBER],
    "epa_toxic_endpoint_mg_l": NUMBER | None, "erpg3_ppm": NUMBER | None}
SPECS["effects/toxic-species-probit"] = {"probit": float | None, "fatality_probability": Fraction}
SPECS["effects/toxic-species-threshold"] = {"concentration_ppm": NUMBER, "probit": float, "within_pure_species_limit": bool}
SPECS["effects/toxic-dose-profile"] = {**SPECS["effects/toxic-species-probit"], "dose_ppm_power_n_s": NUMBER | None,
    "log_dose": float | None, "dose_representable": bool, "duration_s": NUMBER, "equivalent_constant_concentration_ppm": NUMBER}
SPECS["release/level2-toxic-duration"] = {"release_duration_s": NUMBER,
    "governing_limit": Literal["no_release","no_inventory","one_hour","inventory","detection_isolation"]}
SPECS["consequence/toxic-mixture-limit"] = {"modified_mixture_limit_ppm": NUMBER | None, "component_present": bool, "attainable_in_mixture": bool}
SPECS["consequence/level2-toxic-case"] = {"equipment_area_m2": NUMBER, "personnel_area_m2": NUMBER,
    "unweighted_cloud_area_m2": NUMBER, "critical_component_id": str, "component_cloud_areas_m2": dict[str, NUMBER]}
SPECS["consequence/level2-toxic-summary"] = {"equipment_area_m2": NUMBER, "personnel_area_m2": NUMBER,
    "total_generic_frequency_per_year": NUMBER, "by_hole_personnel_area_m2": dict[str, NUMBER]}

SPECS["level2/flammable-case"] = {"flammable_equipment_area_m2": NUMBER,"flammable_personnel_area_m2": NUMBER,
    "non_ignition_probability": Fraction,"terminal_probability_sum": NUMBER}
SPECS["level2/final-area"] = {"equipment_area_m2": NUMBER,"personnel_area_m2": NUMBER,"consequence_area_m2": NUMBER,
    "non_ignition_personnel_area_m2": NUMBER,"governing_non_ignition_personnel_mechanism": Literal["toxic","nfnt","equal"]}
SPECS["level2/consequence-summary"] = {**{name:NUMBER for name in ["flammable_equipment_area_m2","flammable_personnel_area_m2",
    "toxic_personnel_area_m2","nfnt_equipment_area_m2","nfnt_personnel_area_m2","generic_frequency_per_year"]}, **SPECS["level2/final-area"]}
SPECS["level2/scenario-consequence"] = {**SPECS["level2/flammable-case"],"toxic_personnel_area_m2": NUMBER,
    "nfnt_equipment_area_m2": NUMBER,"nfnt_personnel_area_m2": NUMBER,"hole": Literal["small","medium","large","rupture"]}
SPECS["level2/scenario-summary"] = SPECS["level2/consequence-summary"]
SPECS["level2/assessment"] = {"integration_scope": Literal["supplied_level2_event_probabilities_areas_and_damage"],
    "management_factor": NUMBER, **SPECS["level2/consequence-summary"], **SPECS["financial/level1-consequence"], **SPECS["risk/aggregate"]}

SPECS["properties/pool-surface-interaction"] = {"thermal_conductivity_w_m_k": NUMBER,"thermal_diffusivity_m2_s": NUMBER,"roughness_factor": NUMBER}
SPECS["release/pool-evaporation-regime"] = {"regime": Literal["boiling","non_boiling","boundary_requires_qualification"]}
SPECS["release/boiling-pool-evaporation"] = {"evaporation_rate_kg_s": NUMBER,"latent_heat_rate_w": NUMBER}
SPECS["release/boiling-pool-radius"] = {"pool_radius_m": NUMBER,"pool_area_m2": NUMBER}
SPECS["release/boiling-pool-steady-source"] = {"equilibrium_evaporation_rate_kg_s": NUMBER,"vapor_volumetric_rate_m3_s": NUMBER,
    "time_to_steady_s": NUMBER | None,"pool_radius_m": NUMBER,"pool_area_m2": NUMBER,"vapor_source_rate_kg_s": NUMBER | None,
    "support_status": Literal["supported","duration_limited","area_limited","duration_and_area_limited","no_feed"]}
SPECS["release/nonboiling-pool-evaporation"] = {"evaporation_rate_kg_s": NUMBER}
SPECS["release/nonboiling-pool-steady-source"] = {"equilibrium_evaporation_rate_kg_s": NUMBER | None,
    "pool_radius_m": NUMBER | None,"pool_area_m2": NUMBER | None,"vapor_source_rate_kg_s": NUMBER | None,
    "support_status": Literal["supported","area_limited","no_feed","no_finite_steady_state"]}

_RELEASE_PHASE = Literal["vapor","liquid","two_phase"] | None
SPECS["release/level2-release-phase"] = {"release_phase": _RELEASE_PHASE,
    "status": Literal["classified","no_driving_pressure","saturation_storage_boundary","saturation_ambient_boundary"]}
SPECS["release/level2-orifice-rate"] = {"mass_rate_kg_s": NUMBER,"area_m2": NUMBER,"release_phase": _RELEASE_PHASE,
    "rate_method": Literal["ideal_gas","liquid","liquid_conservative_two_phase","no_driving_pressure"],
    "phase_basis": Literal["pressure_screen","qualified_boundary"]}
SPECS["release/kletz-rainout-fraction"] = {"rainout_mass_fraction": Fraction}
SPECS["release/rainout-rate-split"] = {"pool_liquid_rate_kg_s": NUMBER,"jet_total_rate_kg_s": NUMBER}
SPECS["release/jet-liquid-entrainment"] = {"entrained_liquid_mass_fraction": float | None,"jet_vapor_mass_fraction": Fraction | None,
    "physical_range": bool,"jet_fraction_nonzero": bool,"equation_basis": Literal["api581_printed","post_flash_mass_balance"]}
SPECS["release/level2-source-partition"] = {**SPECS["release/jet-liquid-entrainment"], **SPECS["release/rainout-rate-split"],
    **{name:NUMBER for name in ["pool_liquid_mass_kg","jet_total_mass_kg","jet_liquid_rate_kg_s","jet_vapor_rate_kg_s","jet_liquid_mass_kg","jet_vapor_mass_kg"]}}

SPECS["release/flammable-phase-rates"] = {"flammable_rate_kg_s": NUMBER,"flammable_vapor_rate_kg_s": NUMBER,"flammable_liquid_rate_kg_s": NUMBER}
SPECS["events/ambient-ignition"] = {"ambient_ignition_probability": Fraction,"evaluated_rate_kg_s": NUMBER,"rate_capped": bool}
SPECS["events/ait-ignition-maximum"] = {"maximum_ignition_probability": Fraction}
SPECS["events/probability-temperature"] = {"probability": Fraction,"temperature_weight": Fraction,"reference_temperature_k": NUMBER}
SPECS["events/conditional-table"] = {"immediate_at_reference": Fraction,"immediate_at_ait": Fraction,"vce_given_delayed": Fraction,"flash_given_delayed": Fraction}
SPECS["events/two-phase-probability"] = {"probability": Fraction,"mixing_basis": Literal["api581_printed_liquid_weight","qualified_vapor_weight"]}
SPECS["events/single-phase-tree"] = {"terminal_probabilities": dict[str,Fraction],"non_ignition_probability": Fraction,
    "probability_sum": NUMBER,"fireball_applicability_basis": Literal["rupture_only_text","figure53_instantaneous"]}
SPECS["events/single-phase-ignition"] = {**SPECS["events/ambient-ignition"],**SPECS["events/ait-ignition-maximum"],**SPECS["events/single-phase-tree"],
    "ignition_probability": Fraction,"immediate_given_ignition": Fraction,"vce_given_delayed": Fraction,"flash_given_delayed": Fraction,
    "reference_temperature_k": NUMBER,"temperature_weight": Fraction}

SPECS["level2/correlated-jet-pool"] = {"equipment_area_m2": NUMBER,"personnel_area_m2": NUMBER,
    "maximum_equipment_area_m2": NUMBER,"maximum_personnel_area_m2": NUMBER,
    "governing_equipment": Literal["jet","pool","equal"],"governing_personnel": Literal["jet","pool","equal"]}
SPECS["events/fireball-given-immediate"] = {"fireball_given_immediate": Fraction}
SPECS["events/two-phase-tree"] = {**SPECS["events/single-phase-tree"],"fireball_given_immediate": Fraction,
    "fireball_probability_basis": Literal["api581_eq3_123_124","qualified_figure54_branch"]}
SPECS["events/two-phase-ignition"] = {**SPECS["events/two-phase-tree"],**SPECS["release/flammable-phase-rates"],
    **{name:Fraction for name in ["ignition_probability","immediate_given_ignition","vce_given_delayed","flash_given_delayed",
        "liquid_ignition_probability","vapor_ignition_probability","liquid_immediate_given_ignition","vapor_immediate_given_ignition","temperature_weight"]},
    "reference_temperature_k": NUMBER,"mixing_basis": Literal["api581_printed_liquid_weight","qualified_vapor_weight"]}

SPECS["tank/fluid-table"] = {"molecular_weight_kg_kmol":NUMBER,"liquid_density_kg_m3":NUMBER,"dynamic_viscosity_pa_s":NUMBER}
SPECS["tank/soil-table"] = {"printed_lower_bound_cm_s":NUMBER,"printed_upper_bound_cm_s":NUMBER,"porosity":Fraction}
SPECS["tank/soil-water-conductivity"] = {"water_hydraulic_conductivity_m_day":NUMBER}
SPECS["tank/fluid-conductivity"] = {"product_hydraulic_conductivity_m_day":NUMBER}
SPECS["tank/seepage-velocity"] = {"seepage_velocity_m_day":NUMBER}
SPECS["tank/bottom-hole-count"] = {"small_hole_count":int,"medium_hole_count":int,"large_hole_count":int,"outside_tabulated_diameter_range":bool}
SPECS["tank/bottom-inventory"] = {"available_volume_m3":NUMBER,"available_volume_bbl":NUMBER,"available_mass_kg":NUMBER}
SPECS["tank/shell-course-inventory"] = {**SPECS["tank/bottom-inventory"],"course_bottom_elevation_m":NUMBER,"available_liquid_head_m":NUMBER,"course_wet":bool}
_TANK_FLOW = {"native_rate_bbl_day":NUMBER,"volume_rate_m3_s":NUMBER,"mass_rate_kg_s":NUMBER}
SPECS["tank/shell-flow"] = {**_TANK_FLOW,"hole_area_m2":NUMBER}
SPECS["tank/bottom-flow"] = {**_TANK_FLOW,"per_hole_native_rate_bbl_day":NUMBER,"equation":Literal["3.210","3.211","3.212","zero_flow"],
    "liquid_head_used_m":NUMBER,"lower_conductivity_threshold_m_day":NUMBER | None,"upper_conductivity_threshold_m_day":NUMBER | None,
    "applied_hole_multiplier":int,"transition_hole_basis":Literal["api581_printed","per_hole_scaled"]}
SPECS["tank/shell-detection-time"] = {"detection_time_days":NUMBER,"diameter_boundary_m":NUMBER}
SPECS["tank/bottom-detection-time"] = {"detection_time_days":NUMBER,"selected_basis":Literal["concrete_asphalt","barrier","unprotected"]}
SPECS["tank/release-volume"] = {"release_duration_days":NUMBER | None,"released_volume_bbl":NUMBER,"released_volume_m3":NUMBER,
    "released_mass_kg":NUMBER,"printed_mass_index":NUMBER,"release_type":Literal["continuous"]}

SPECS["tank/environment-cost-table"] = {"cost_by_location_usd_per_bbl":dict[str,NUMBER]}
_SURFACE_VOLUMES = {k+"_bbl":NUMBER for k in ["in_dike","surface_on_site","surface_off_site","surface_water"]}
SPECS["tank/surface-spill-partition"] = _SURFACE_VOLUMES
SPECS["tank/groundwater-arrival"] = {"arrival_time_days":NUMBER | None,"arrival_status":Literal["already_at_groundwater","no_finite_arrival","finite_travel"]}
SPECS["tank/subsurface-spill-partition"] = {"groundwater_bbl":NUMBER,"subsoil_bbl":NUMBER,"groundwater_fraction":Fraction}
_ENV_COST_OUTPUT = {"leak_environment_cost":NUMBER,"rupture_environment_cost":NUMBER,"environment_cost":NUMBER,"currency":str,"cost_basis":str}
SPECS["tank/shell-environment-cost"] = {**_ENV_COST_OUTPUT,"weighted_leak_volume_bbl":NUMBER,"weighted_rupture_volume_bbl":NUMBER,
    "weighted_leak_surface_volumes_bbl":dict[str,NUMBER],"weighted_rupture_surface_volumes_bbl":dict[str,NUMBER]}
SPECS["tank/bottom-environment-cost"] = {**_ENV_COST_OUTPUT,"weighted_groundwater_volume_bbl":NUMBER,"weighted_subsoil_volume_bbl":NUMBER,
    "weighted_rupture_volume_bbl":NUMBER,"weighted_rupture_surface_volumes_bbl":dict[str,NUMBER]}
SPECS["tank/bottom-repair-cost"] = {"component_repair_cost":NUMBER,"currency":str,"cost_basis":str}

SPECS["tank/generic-frequency"] = {"by_hole_per_year":dict[str,NUMBER],"total_per_year":NUMBER,"printed_total_per_year":NUMBER,
    "sum_minus_printed_per_year":float,"total_basis":Literal["hole_sum_eq3_208"]}
SPECS["tank/component-outage"] = {"component_outage_days":NUMBER,"effective_days_by_hole":dict[str,NUMBER | None]}
_TANK_FINANCIAL = {**{k:NUMBER for k in ["component_repair_cost","surrounding_equipment_cost","business_interruption_cost",
    "injury_cost","environmental_cost","component_outage_days","surrounding_outage_days","surrounding_cost_reference_usd_2001",
    "leak_environment_cost","rupture_environment_cost","financial_consequence"]},"currency":str,"cost_basis_year":int,"cost_basis":str}
SPECS["tank/bottom-financial-consequence"] = _TANK_FINANCIAL
SPECS["tank/shell-financial-consequence"] = _TANK_FINANCIAL
_TANK_RISK = {**_TANK_FINANCIAL,**{k:NUMBER for k in ["generic_frequency_per_year","management_factor","annual_failure_frequency","financial_risk_per_year"]},
    "annual_frequency_by_hole":dict[str,NUMBER],"integration_scope":Literal["supplied_uniform_df_and_tank_release_consequences"]}
SPECS["tank/bottom-risk-assessment"] = _TANK_RISK
SPECS["tank/shell-risk-assessment"] = {**_TANK_RISK,"equipment_area_risk_m2_per_year":NUMBER,"personnel_area_risk_m2_per_year":NUMBER}

_TANK_HOLES = {"diameter_by_hole_m":dict[str,NUMBER],"area_by_hole_m2":dict[str,NUMBER]}
SPECS["tank/shell-hole-sizes"] = _TANK_HOLES
SPECS["tank/bottom-hole-sizes"] = _TANK_HOLES
_TANK_SOURCE = {**_TANK_HOLES,**SPECS["tank/bottom-inventory"],"generic_frequency_by_hole_per_year":dict[str,NUMBER],
    "generic_total_per_year":NUMBER,"printed_generic_total_per_year":NUMBER,"generic_total_basis":Literal["hole_sum_eq3_208"],
    **{k:dict[str,NUMBER | None] for k in ["native_rate_by_hole_bbl_day","mass_rate_by_hole_kg_s","detection_time_by_hole_days","release_duration_by_hole_days"]},
    **{k:dict[str,NUMBER] for k in ["released_volume_by_hole_bbl","released_volume_by_hole_m3","released_mass_by_hole_kg"]},
    "release_type":Literal["continuous"],"liquid_density_kg_m3":NUMBER}
SPECS["tank/shell-source-assessment"] = {**_TANK_SOURCE,**SPECS["tank/shell-course-inventory"],"source_scope":Literal["single_shell_course"]}
SPECS["tank/bottom-source-assessment"] = {**_TANK_SOURCE,**SPECS["tank/bottom-hole-count"],
    "product_hydraulic_conductivity_m_day":NUMBER,"seepage_velocity_m_day":NUMBER,
    "bottom_flow_equation":Literal["3.210","3.211","3.212","zero_flow"],"applied_small_hole_multiplier":int,
    "detection_time_days":NUMBER,"detection_selected_basis":Literal["concrete_asphalt","barrier","unprotected"],"source_scope":Literal["single_tank_bottom"]}

SPECS["tank/bottom-integrated-assessment"] = {**SPECS["tank/bottom-source-assessment"],**_TANK_RISK,
    "groundwater_arrival_time_days":NUMBER | None,
    "integration_scope":Literal["bottom_geometry_soil_source_financial_risk_with_supplied_df"]}

_DIKED_POOL = dict(SPECS["effects/pool-fire-consequence"])
for _name in ("personnel_safe_surface_distance_m","equipment_safe_surface_distance_m"):
    _DIKED_POOL["unclipped_"+_name] = _DIKED_POOL.pop(_name)
SPECS["tank/diked-pool-consequence"] = {**_DIKED_POOL,
    **{k:NUMBER for k in ["unclipped_equipment_area_m2","unclipped_personnel_area_m2","effective_pool_area_limit_m2","dike_area_m2"]},
    "equipment_area_clipped":bool,"personnel_area_clipped":bool,"dike_limit_basis":Literal["burning_pool_area","burning_and_consequence_area"]}
SPECS["tank/shell-level2-case"] = {**SPECS["level2/flammable-case"],"toxic_personnel_area_m2":NUMBER,"nfnt_status":Literal["not_determined_for_ast"]}
_AST_MECHANISMS = ["flammable_equipment_area_m2","flammable_personnel_area_m2","toxic_personnel_area_m2"]
SPECS["tank/shell-level2-summary"] = {**{k:NUMBER for k in [*_AST_MECHANISMS,"equipment_area_m2","personnel_area_m2","consequence_area_m2","generic_frequency_per_year"]},
    **{"by_hole_"+k:dict[str,NUMBER] for k in _AST_MECHANISMS},"nfnt_status":Literal["not_determined_for_ast"]}
SPECS["tank/shell-integrated-assessment"] = {**SPECS["tank/shell-source-assessment"],**SPECS["tank/shell-level2-summary"],
    **SPECS["tank/shell-risk-assessment"],"integration_scope":Literal["shell_geometry_source_supplied_event_footprints_financial_risk"]}

SPECS["dispersion/native-engine-capabilities"] = {"requested_engines":list[Literal["slabx","slabx-lh2"]],
    "required_versions":dict[str,str],"installed_versions":dict[str,str | None],
    "engine_status":dict[str,Literal["missing","available","version_mismatch","not_importable"]],
    "module_import_status":dict[str,Literal["not_installed","importable","not_importable"]],
    "worker_isolation":Literal["subprocess"],
    "supported_operations":list[str],"probe_scope":Literal["package_presence_version_and_importability"]}
SPECS["dispersion/native-pool-centreline"] = {"engine":Literal["slabx","slabx-lh2"],"engine_versions":dict[str,str],
    "engine_source_fingerprints":dict[str,str],"downwind_distance_m":list[float],"centreline_volume_fraction":list[Fraction],
    "native_grid_maximum_downwind_distance_m":NUMBER,
    "native_threshold_distance_m":NUMBER | None,"threshold_distance_m":NUMBER | None,
    "threshold_status":Literal["premise_violated","boundary_censored","interpolated","not_reached"],
    "premise_status":Literal["not_evaluated","violated","within_premise"],
    "maximum_vertical_to_horizontal_velocity_ratio":NUMBER | None,
    "used_source_area_m2":NUMBER,"effective_source_half_width_m":NUMBER,"native_messages":str,"averaging_time_s":NUMBER,"receptor_height_m":NUMBER,
    "spatial_output_scope":Literal["centreline_only_no_footprint_area"]}

_GRID_AREA = {"sampled_exceedance_area_m2":NUMBER,"threshold_area_m2":NUMBER | None,
    "footprint_status":Literal["boundary_censored","closed_on_supplied_grid","not_reached"],
    "boundary_sides":list[Literal["upwind","downwind","negative_crosswind","positive_crosswind"]],
    "positive_area_cell_count":int,"downwind_node_count":int,"crosswind_node_count":int,
    "interpolation_basis":Literal["piecewise_linear_main_diagonal_triangles"]}
SPECS["dispersion/threshold-grid-area"] = _GRID_AREA
SPECS["dispersion/native-pool-footprint"] = {**SPECS["dispersion/native-pool-centreline"],**_GRID_AREA,
    "footprint_status":Literal["boundary_censored","closed_on_supplied_grid","not_reached","premise_violated"],
    "crosswind_distance_m":list[float],"volume_fraction_by_crosswind_then_downwind":list[list[Fraction]],
    "spatial_output_scope":Literal["planar_sampled_threshold_field"]}
SPECS["dispersion/native-pool-flash-fire"] = {**SPECS["dispersion/native-pool-footprint"],**SPECS["effects/flash-fire"],
    "criterion_role":Literal["qualified_lfl"],"receptor_height_m":Literal[0.0]}
_NATIVE_JET = {k:v for k,v in SPECS["dispersion/native-pool-centreline"].items() if k != "effective_source_half_width_m"}
_NATIVE_JET.update(orientation=Literal["horizontal_downwind","vertical_up"],jet_exit_area_m2=NUMBER,
    geometric_exit_half_width_m=NUMBER,native_exit_velocity_m_s=NUMBER,requested_source_temperature_k=NUMBER,
    used_source_temperature_k=NUMBER,source_temperature_clamped=bool,native_jet_liquid_mass_fraction=Fraction)
_NATIVE_JET.update(native_initial_downwind_distance_m=NUMBER,
    native_near_field_status=Literal["not_reconstructed_before_native_handoff","briggs_buoyant_effective_horizontal_source"])
SPECS["dispersion/native-jet-centreline"] = _NATIVE_JET
SPECS["dispersion/native-jet-footprint"] = {**_NATIVE_JET,**_GRID_AREA,
    "footprint_status":Literal["boundary_censored","closed_on_supplied_grid","not_reached","premise_violated"],
    "crosswind_distance_m":list[float],"volume_fraction_by_crosswind_then_downwind":list[list[Fraction]],
    "spatial_output_scope":Literal["planar_sampled_threshold_field"]}
_JET_HANDOFF = {**SPECS["release/level2-source-partition"],"release_duration_s":NUMBER,
    "integration_scope":Literal["qualified_partition_to_native_jet"]}
SPECS["dispersion/partitioned-jet-centreline"] = {**SPECS["dispersion/native-jet-centreline"],**_JET_HANDOFF}
SPECS["dispersion/partitioned-jet-footprint"] = {**SPECS["dispersion/native-jet-footprint"],**_JET_HANDOFF}

SPECS["consequence/select-toxic-criterion"] = {"fluid_id":str,"selected_criterion_id":str,
    "selected_kind":Literal["probit50","lc50","erpg3","aegl3","teel3","idlh","epa_endpoint"],"priority_tier":Literal[1,2,3],
    "pure_component_limit_ppm":NUMBER,"modified_mixture_limit_ppm":NUMBER | None,"threshold_volume_fraction":Fraction | None,
    "component_present":bool,"attainable_in_mixture":bool,"exposure_duration_s":NUMBER,"criterion_source":str,
    "eligible_candidate_ids":list[str],"excluded_candidate_ids":dict[str,str],"unavailable_candidate_reasons":dict[str,str]}
SPECS["dispersion/native-pool-toxic-consequence"] = {**SPECS["dispersion/native-pool-footprint"],
    **SPECS["consequence/select-toxic-criterion"],**SPECS["consequence/level2-toxic-case"],"release_duration_s":NUMBER,
    "release_duration_governing_limit":Literal["one_hour","inventory","detection_isolation","no_release","no_inventory"],
    "exposure_model_basis":Literal["constant_exposure_equivalent_native_time_average"],"receptor_height_m":Literal[0.0],"equipment_area_m2":Literal[0.0]}

SPECS["damage/soil-base-rate-table"] = {"corrosion_rate_m_year":NUMBER,"printed_si_rate_mm_year":NUMBER,
    "printed_us_rate_mpy":NUMBER,"selected_unit_basis":Literal["printed_si","printed_us_mpy"],"condition_description":str}
SPECS["damage/soil-resistivity-factor"] = {"resistivity_factor":NUMBER,"source_row":int}
SPECS["damage/soil-temperature-factor"] = {"temperature_factor":NUMBER,"lower_boundary_k":NUMBER,"upper_boundary_k":NUMBER,
    "threshold_basis":Literal["printed_si","printed_us_converted"]}
SPECS["damage/soil-cp-factor"] = {"cathodic_protection_factor":NUMBER}
SPECS["damage/soil-coating-factor"] = {**{k:NUMBER for k in ["coating_effectiveness_factor","base_factor","age_factor","temperature_abuse_factor","maintenance_factor"]},
    "calculation_basis":Literal["table_factor_product"],"printed_example_discrepancy_applies":bool,"printed_example_reported_factor":NUMBER | None}
SPECS["damage/soil-rate-equation"] = {"corrosion_rate_m_year":NUMBER}
SPECS["damage/soil-corrosion-rate"] = {**SPECS["damage/soil-rate-equation"],**{k:NUMBER for k in ["resistivity_factor","temperature_factor","cathodic_protection_factor","coating_effectiveness_factor","base_corrosion_rate_m_year"]},
    "thinning_type":Literal["local"],"resistivity_application":Literal["apply","already_in_base","omitted_by_qualification"],
    "coating_calculation_basis":Literal["table_factor_product"],"coating_example_discrepancy_applies":bool}
SPECS["damage/soil-thinning-assessment"] = {**SPECS["damage/soil-corrosion-rate"],**SPECS["damage/thinning-unclad"],
    "assessment_scope":Literal["unclad_internal_pressure_governed_non_ast"]}

SPECS["tank/bottom-base-corrosion-rate"] = {"base_corrosion_rate_m_year":NUMBER,"printed_si_rate_mm_year":NUMBER,"printed_us_rate_mpy":NUMBER,
    "side":Literal["soil","product"],"unit_basis":Literal["printed_si","printed_us_mpy"]}
SPECS["tank/bottom-soil-rate-equation"] = {"soil_corrosion_rate_m_year":NUMBER}
SPECS["tank/bottom-product-rate-equation"] = {"product_corrosion_rate_m_year":NUMBER}
SPECS["tank/bottom-soil-resistivity-factor"] = {"resistivity_factor":NUMBER,"selection_reason":Literal["rpb","unknown_assume_moderate","resistivity_table"]}
for identifier, field in [("pad","pad_factor"),("drainage","drainage_factor"),("type","bottom_type_factor"),
    ("product-condition","product_condition_factor"),("steam-coil","steam_coil_factor"),("water-draw","water_draw_factor")]:
    SPECS[f"tank/bottom-{identifier}-factor"] = {field:NUMBER}
SPECS["tank/bottom-cp-factor"] = {"nominal_table_factor":NUMBER,"cathodic_protection_factor":NUMBER,"credit_applied":bool}
SPECS["tank/bottom-temperature-factor"] = {"temperature_factor":NUMBER,"source_row":int,"threshold_basis":Literal["printed_si","printed_us_converted"]}
SPECS["tank/bottom-corrosion-rate-combine"] = {"raw_combined_rate_m_year":NUMBER,"combined_corrosion_rate_m_year":NUMBER,
    "recommended_minimum_rate_m_year":NUMBER,"minimum_applied":bool,"combination_rule":Literal["sum","maximum"]}
SPECS["tank/bottom-corrosion-assessment"] = {**SPECS["tank/bottom-corrosion-rate-combine"], **{k:NUMBER for k in [
    "soil_corrosion_rate_m_year","product_corrosion_rate_m_year","resistivity_factor","pad_factor","drainage_factor",
    "cathodic_protection_factor","bottom_type_factor","temperature_factor","product_condition_factor","steam_coil_factor","water_draw_factor"]},"cp_credit_applied":bool}

SPECS["tank/bottom-minimum-thickness"] = {"minimum_thickness_m":NUMBER,"thickness_basis":Literal["api581_2016_default","documented_owner_method"]}
SPECS["tank/bottom-wall-parameter"] = {"art_parameter":NUMBER,"predicted_remaining_thickness_m":float,"predicted_wall_loss_m":NUMBER,
    "reference_thickness_m":NUMBER,"at_or_below_minimum_thickness":bool,"predicted_penetration":bool}
SPECS["tank/bottom-inspection-selection"] = {"selected_inspection_grade":Literal["a","b","c","d","e"],"credited_inspection_count":int,"eligible_inspection_count":int}
SPECS["tank/bottom-thinning-base"] = {"base_damage_factor":NUMBER,"lower_art_row":NUMBER,"upper_art_row":NUMBER,"interpolation_weight":NUMBER,
    "lookup_policy":Literal["exact_rows_only","linear_between_rows","conservative_upper_row"]}
SPECS["tank/bottom-thinning-adjustment-factors"] = {"welded_construction_factor":NUMBER,"maintenance_factor":NUMBER,"settlement_factor":NUMBER}
SPECS["tank/bottom-thinning-assessment"] = {**SPECS["tank/bottom-minimum-thickness"],**SPECS["tank/bottom-wall-parameter"],
    **SPECS["tank/bottom-inspection-selection"],**SPECS["tank/bottom-thinning-base"],**SPECS["tank/bottom-thinning-adjustment-factors"],
    "thinning_damage_factor":NUMBER,"online_monitoring_factor":Literal[1.0]}
SPECS["tank/bottom-corrosion-thinning-assessment"] = {**SPECS["tank/bottom-corrosion-assessment"],**SPECS["tank/bottom-thinning-assessment"]}
SPECS["tank/bottom-corrosion-risk-assessment"] = {**SPECS["tank/bottom-corrosion-thinning-assessment"],**SPECS["tank/bottom-integrated-assessment"],
    "total_damage_factor":NUMBER,"integration_scope":Literal["bottom_corrosion_thinning_source_financial_risk_qualified_thinning_only"]}

SPECS["damage/cladding-remaining-life"] = {"remaining_cladding_at_baseline_m":NUMBER,"cladding_depletion_age_years":NUMBER | None,
    "cladding_baseline_state":Literal["already_depleted","noncorroding_present","finite_depletion"]}
SPECS["damage/thinning-clad-wall-loss"] = {**SPECS["damage/cladding-remaining-life"],"wall_loss_fraction":NUMBER,
    "cladding_wall_loss_m":NUMBER,"base_material_wall_loss_m":NUMBER,"base_material_exposure_years":NUMBER,
    "predicted_remaining_thickness_m":float,"predicted_penetration":bool,
    "wall_loss_branch":Literal["base_only_eq2_13","noncorroding_cladding_extension","cladding_only_eq2_14","cladding_then_base_eq2_15"]}
SPECS["damage/thinning-design-strength-ratio"] = {"strength_ratio":NUMBER,"governing_minimum_thickness_m":NUMBER,
    "governing_thickness_source":Literal["equal_minima","structural_minimum","required_minimum"]}
SPECS["damage/thinning-clad"] = {**SPECS["damage/thinning-clad-wall-loss"],**SPECS["damage/thinning-posterior"],
    **SPECS["damage/thinning-base"],**SPECS["damage/thinning-adjust"],"strength_ratio":NUMBER,
    "strength_method":Literal["internal_pressure_eq2_18","design_thickness_eq2_17"]}
SPECS["damage/thinning-unclad-design"] = {**SPECS["damage/thinning-wall-loss"],**SPECS["damage/thinning-design-strength-ratio"],
    **SPECS["damage/thinning-posterior"],**SPECS["damage/thinning-base"],**SPECS["damage/thinning-adjust"]}

from .thinning_conditions import Row as MonitoringRow
SPECS["damage/thinning-monitoring-row"] = {"monitoring_row":MonitoringRow,"velocity_threshold_m_s":NUMBER | None}
SPECS["damage/thinning-monitoring-table-factor"] = {"table_monitoring_factor":NUMBER}
SPECS["damage/thinning-online-monitoring-factor"] = {**SPECS["damage/thinning-monitoring-row"],"online_monitoring_factor":NUMBER,
    "candidate_method_factors":dict[str,NUMBER],"monitoring_credit_basis":Literal["no_organized_plan","qualified_experience_replacement","maximum_table_method","no_monitoring_methods"],"joint_exception_applied":bool}
SPECS["damage/thinning-injection-point-factor"] = {"injection_point_factor":NUMBER}
SPECS["damage/thinning-deadleg-factor"] = {"deadleg_factor":NUMBER}
_THINNING_CONDITIONS = {**SPECS["damage/thinning-online-monitoring-factor"],**SPECS["damage/thinning-injection-point-factor"],**SPECS["damage/thinning-deadleg-factor"]}
SPECS["damage/thinning-conditional-adjustment"] = {**_THINNING_CONDITIONS,"base_damage_factor":NUMBER,"thinning_damage_factor":NUMBER}
SPECS["damage/thinning-unclad-qualified"] = {**SPECS["damage/thinning-unclad"],**_THINNING_CONDITIONS,
    "strength_method":Literal["internal_pressure_eq2_18","design_thickness_eq2_17"]}
SPECS["damage/thinning-clad-qualified"] = {**SPECS["damage/thinning-clad"],**_THINNING_CONDITIONS}

SPECS["damage/lining-effective-age"] = {"effective_age_years":NUMBER,"elapsed_service_years":NUMBER,"age_baseline_date":str,
    "age_baseline_source":Literal["qualified_ab_inspection","installation"],"reset_inspection_id":str | None,
    "qualified_ab_inspection_count":int,"age_basis_policy":Literal["step1_installation_or_last_ab","figure51_organic_service_only"]}
SPECS["damage/lining-base-factor"] = {"base_damage_factor":NUMBER,"lower_age_row_years":NUMBER,"upper_age_row_years":NUMBER,
    "age_interpolation_weight":NUMBER,"first_year_value_used":bool,"source_table":Literal["5.4","5.5"]}
SPECS["damage/lining-condition-factor"] = {"condition_factor":NUMBER}
SPECS["damage/lining-monitoring-factor"] = {"monitoring_factor":NUMBER}
SPECS["damage/lining-governing-thinning"] = {"governing_thinning_damage_factor":NUMBER,"governing_source":Literal["equal","lining","base_material_thinning"]}
SPECS["damage/lining-assessment"] = {**SPECS["damage/lining-effective-age"],**SPECS["damage/lining-base-factor"],
    **SPECS["damage/lining-adjust"],**SPECS["damage/lining-governing-thinning"],"base_material_thinning_damage_factor":NUMBER}

SPECS["damage/cooling-water-ph-coefficients"] = {"c1":NUMBER,"c2":NUMBER,"c3":NUMBER,"c4":NUMBER,"c4_printed_literal_used":bool}
SPECS["damage/cooling-water-rate-factors"] = {"scale_potential":bool,"deposit_risk":bool,
    "biological_or_mic_risk":bool,"underdeposit_risk":bool,"factor_flags":list[str]}
SPECS["damage/cooling-water-saturation-ph"] = {"saturation_ph":float}
SPECS["damage/cooling-water-stability-indices"] = {"langelier_saturation_index":float,"ryznar_stability_index":float}
SPECS["damage/cooling-water-base-rate"] = {"base_corrosion_rate_m_year":NUMBER,"base_column":Literal["unprotected_high","scaling_low"],"base_velocity_threshold_m_s":NUMBER}
SPECS["damage/cooling-water-temperature-factor"] = {"temperature_factor":NUMBER,"temperature_table_argument":float,"misordered_row_ignored":bool}
SPECS["damage/cooling-water-velocity-factor"] = {"velocity_factor":NUMBER}
SPECS["damage/cooling-water-rate-equation"] = {"corrosion_rate_m_year":NUMBER}
SPECS["damage/cooling-water-seawater-rate"] = {"corrosion_rate_m_year":NUMBER}
SPECS["damage/cooling-water-coupon-pitting-rate"] = {"pitting_corrosion_rate_m_year":NUMBER}
SPECS["damage/cooling-water-fresh-assessment"] = {**SPECS["damage/cooling-water-stability-indices"],**SPECS["damage/cooling-water-base-rate"],
    **SPECS["damage/cooling-water-temperature-factor"],**SPECS["damage/cooling-water-velocity-factor"],**SPECS["damage/cooling-water-rate-equation"]}
SPECS["damage/cooling-water-thinning-assessment"] = {**SPECS["damage/cooling-water-fresh-assessment"],**SPECS["damage/thinning-unclad-qualified"],"thinning_type":Literal["general","local"]}

SPECS["damage/cooling-water-treatment-bounds"] = {"general_upper_bound_m_year":NUMBER,"pitting_upper_bound_m_year":NUMBER,"source_rate_relation":Literal["strictly_less_than"]}
SPECS["damage/cooling-water-system-type"] = {"system":Literal["once_through","closed_recirculated","open_recirculated"],
    "water_source":Literal["fresh","seawater","brackish","unknown"],"requires_continual_makeup":bool,
    "has_evaporation_or_blowdown_loss":bool,"classification_basis":Literal["supplied_operating_premise"]}
SPECS["damage/cooling-water-other-material-estimate"] = {"nominal_corrosion_rate_m_year":NUMBER}
SPECS["damage/cooling-water-measured-rate"] = {"corrosion_rate_m_year":NUMBER,"selection_source":Literal["component_measurement","coupon_general","coupon_pitting_rule"]}
SPECS["damage/cooling-water-rate-selection"] = {"corrosion_rate_m_year":NUMBER,
    "selection_source":Literal["component_measurement","coupon_general","coupon_pitting_rule","freshwater_model","seawater_model","treated_screening_bound","treated_owner_rate","other_material_nominal"],
    "assessment_distribution":Literal["general","local"],"source_strict_upper_bound_m_year":NUMBER | None,
    "selected_rate_is_screening_bound":bool,"fallback_ignored_due_to_measurement":bool}
SPECS["damage/cooling-water-selected-thinning"] = {**SPECS["damage/cooling-water-rate-selection"],**SPECS["damage/thinning-unclad-qualified"]}

SPECS["damage/co2-relative-humidity"] = {"water_dry_gas_mass_ratio":NUMBER,"relative_humidity_fraction":NUMBER,"supersaturated":bool,"saturated":bool}
SPECS["damage/co2-dew-point"] = {"dew_point_temperature_k":NUMBER}
SPECS["damage/co2-temperature-ph-factor"] = {"temperature_ph_factor":NUMBER,"sharp_temperature_interval_interpolated":bool}
SPECS["damage/co2-ph-estimate"] = {"estimated_ph":float}
SPECS["damage/co2-fugacity"] = {"fugacity_pa":NUMBER,"fugacity_coefficient":NUMBER}
SPECS["damage/co2-reynolds"] = {"reynolds_number":NUMBER}
SPECS["damage/co2-friction-factor"] = {"friction_factor":NUMBER}
SPECS["damage/co2-shear-stress"] = {"shear_stress_pa":NUMBER}
SPECS["damage/co2-base-rate"] = {"base_corrosion_rate_m_year":NUMBER,"applied_shear_stress_pa":NUMBER,"shear_cap_applied":bool}
SPECS["damage/co2-glycol-factor"] = {"glycol_factor":NUMBER,"glycol_floor_applied":bool}
SPECS["damage/co2-rate-adjustment"] = {"glycol_factor":NUMBER,"inhibitor_factor":NUMBER,"applied_reduction_factor":NUMBER,"corrosion_rate_m_year":NUMBER}
SPECS["damage/co2-corrosion-assessment"] = {**SPECS["damage/co2-rate-adjustment"],"base_corrosion_rate_m_year":NUMBER,
    "calculation_branch":Literal["no_free_water","no_co2","wet_carbonic_acid_model"],"model_ph":float | None,
    "temperature_ph_factor":NUMBER | None,"fugacity_pa":NUMBER | None,"requested_shear_stress_pa":NUMBER | None,
    "applied_shear_stress_pa":NUMBER | None,"shear_cap_applied":bool,"sharp_temperature_interval_interpolated":bool}
SPECS["damage/co2-thinning-assessment"] = {**SPECS["damage/co2-corrosion-assessment"],**SPECS["damage/thinning-unclad-qualified"]}

SPECS["properties/co2-partial-pressure"] = {"co2_partial_pressure_pa_abs":NUMBER}
SPECS["damage/co2-reynolds-mass-flow"] = {"mass_flux_kg_m2_s":NUMBER,"reynolds_number":NUMBER}
SPECS["damage/co2-material-screen"] = {"material_screen_decision":Literal["evaluate_co2","source_assumed_resistant","not_covered"],"source_material_resistance_assumed":bool}
SPECS["damage/co2-hydrocarbon-wetting-screen"] = {"wetting_screen_decision":Literal["figure_low_water_high_velocity_exemption","proceed_to_water_check"],
    "water_content_percent_used":NUMBER | None,"source_water_default_used":bool}
SPECS["damage/co2-moisture-screen"] = {"free_water_screen_state":Literal["present","absent","indeterminate"],"free_water_assumed_from_missing_data":bool}
SPECS["damage/co2-screened-assessment"] = {**{k:v for k,v in SPECS["damage/co2-corrosion-assessment"].items() if k != "calculation_branch"},
    **SPECS["properties/co2-partial-pressure"],**SPECS["damage/co2-material-screen"],
    "wetting_screen_decision":Literal["figure_low_water_high_velocity_exemption","proceed_to_water_check"] | None,
    "water_content_percent_used":NUMBER | None,"source_water_default_used":bool,
    "free_water_screen_state":Literal["present","absent","indeterminate"] | None,"free_water_assumed_from_missing_data":bool,
    "screened_calculation_branch":Literal["source_material_resistance","no_co2","figure_hydrocarbon_exemption","qualified_no_free_water","wet_carbonic_acid_model"]}
SPECS["damage/co2-screened-thinning"] = {**SPECS["damage/co2-screened-assessment"],**SPECS["damage/thinning-unclad-qualified"]}

SPECS["damage/oxidation-screen"] = {"screen_temperature_threshold_k":NUMBER,"temperature_screen_met":bool,"evaluate_high_temperature_oxidation":bool}
SPECS["damage/oxidation-table-row"] = {"temperature_nodes_k":list[NUMBER],"corrosion_rates_m_year":list[NUMBER | None],
    "native_rates":list[NUMBER | None],"native_rate_unit":Literal["mm/year","mpy"],"source_table_ids":list[str]}
SPECS["damage/oxidation-rate"] = {"corrosion_rate_m_year":NUMBER,"lower_temperature_node_k":NUMBER,"upper_temperature_node_k":NUMBER,
    "interpolation_weight":NUMBER,"rate_calculation_basis":Literal["qualified_first_node","exact_cell","upper_temperature_node","linear_between_nodes"],"first_node_value_used":bool}
SPECS["damage/oxidation-assessment"] = {**SPECS["damage/oxidation-screen"],**SPECS["damage/oxidation-rate"],"thinning_type":Literal["general"]}
SPECS["damage/oxidation-thinning-assessment"] = {**SPECS["damage/oxidation-assessment"],**SPECS["damage/thinning-unclad-qualified"]}

SPECS["damage/acid-sour-water-route"] = {"corrosion_route":Literal["no_free_water","hydrochloric_acid","alkaline_sour_water","neutral_boundary_unclassified","acid_sour_water"]}
SPECS["damage/acid-sour-water-base-rate"] = {"base_corrosion_rate_m_year":NUMBER,"ph_for_lookup":NUMBER,"ph_edge_row_used":bool}
SPECS["damage/acid-sour-water-oxygen-factor"] = {"oxygen_factor":NUMBER,"high_oxygen_localized_review":bool}
SPECS["damage/acid-sour-water-velocity-factor"] = {"velocity_factor":NUMBER,"high_velocity_localized_review":bool}
SPECS["damage/acid-sour-water-rate-equation"] = {"corrosion_rate_m_year":NUMBER}
SPECS["damage/acid-sour-water-other-material-rate"] = {"corrosion_rate_m_year":NUMBER,"selected_rate_is_screening_bound":bool}
SPECS["damage/acid-sour-water-assessment"] = {**SPECS["damage/acid-sour-water-route"],"corrosion_rate_m_year":NUMBER,
    "base_corrosion_rate_m_year":NUMBER | None,"ph_for_lookup":NUMBER | None,"ph_edge_row_used":bool,
    "oxygen_factor":NUMBER | None,"velocity_factor":NUMBER | None,"localized_attack_review_required":bool,
    "selected_rate_is_screening_bound":bool,"default_thinning_type":Literal["general"]}
SPECS["damage/acid-sour-water-thinning-assessment"] = {**SPECS["damage/acid-sour-water-assessment"],**SPECS["damage/thinning-unclad-qualified"],"assessment_distribution":Literal["general","local"]}

SPECS["properties/h2s-partial-pressure"] = {"h2s_partial_pressure_pa_abs":NUMBER}
SPECS["damage/alkaline-sour-water-nh4hs-estimate"] = {"estimated_nh4hs_mass_fraction":NUMBER,
    "concentration_estimate_branch":Literal["printed_excess_h2s","printed_lower_h2s","qualified_equality_upper","qualified_equality_lower"],"estimated_fraction_exceeds_one":bool}
SPECS["damage/alkaline-sour-water-velocity-selection"] = {"selected_velocity_m_s":NUMBER,"selected_velocity_phase":Literal["vapor","liquid"]}
SPECS["damage/alkaline-sour-water-base-rate"] = {"baseline_corrosion_rate_m_year":NUMBER}
SPECS["damage/alkaline-sour-water-pressure-adjustment"] = {"corrosion_rate_m_year":NUMBER,"unclamped_pressure_factor":float,
    "pressure_correction_factor":NUMBER,"negative_pressure_factor_clamped":bool,"pressure_correction_branch":Literal["at_reference","below_reference","above_reference"]}
SPECS["damage/alkaline-sour-water-assessment"] = {"corrosion_rate_m_year":NUMBER,"baseline_corrosion_rate_m_year":NUMBER | None,
    "nh4hs_mass_fraction_used":NUMBER | None,"concentration_source":Literal["supplied","source_approximation"] | None,
    "selected_velocity_m_s":NUMBER | None,"selected_velocity_phase":Literal["vapor","liquid"] | None,
    "unclamped_pressure_factor":float | None,"pressure_correction_factor":NUMBER | None,"negative_pressure_factor_clamped":bool,
    "pressure_correction_branch":Literal["at_reference","below_reference","above_reference"] | None,
    "source_thinning_type":Literal["general","local"] | None,"calculation_branch":Literal["no_free_water","wet_nh4hs_model"]}
SPECS["damage/alkaline-sour-water-thinning-assessment"] = {**SPECS["damage/alkaline-sour-water-assessment"],**SPECS["damage/thinning-unclad-qualified"],"assessment_distribution":Literal["general","local"]}
SPECS["damage/sour-water-assessment"] = {**SPECS["damage/acid-sour-water-route"],"corrosion_rate_m_year":NUMBER,
    "selected_model_base_rate_m_year":NUMBER | None,"selected_rate_is_screening_bound":bool,"localized_attack_review_required":bool}

SPECS["damage/hcl-ph-from-chloride"] = {"estimated_ph":NUMBER,"chloride_band_lower_wppm":NUMBER,"chloride_band_upper_wppm":NUMBER,"chloride_band_upper_inclusive":bool}
SPECS["damage/hcl-chloride-interval-from-ph"] = {k:v for k,v in SPECS["damage/hcl-ph-from-chloride"].items() if k != "estimated_ph"}
SPECS["damage/hcl-ph-rate"] = {"corrosion_rate_m_year":NUMBER,"source_999_corner_used":bool,"localized_pitting_already_included":bool,"source_table_id":str}
SPECS["damage/hcl-alloy-rate"] = SPECS["damage/hcl-ph-rate"].copy()
SPECS["damage/hcl-assessment"] = {"corrosion_rate_m_year":NUMBER,"source_999_corner_used":bool,"localized_pitting_already_included":bool,"source_table_id":str | None,
    "ph_used":NUMBER | None,"chloride_mass_fraction_used":Fraction | None,
    "chemistry_method":Literal["supplied_ph","chloride_table","supplied_chloride","ph_interval_selection"] | None,
    "source_thinning_type":Literal["local"] | None,"calculation_branch":Literal["no_free_water","wet_dilute_hcl_model"]}
SPECS["damage/hcl-thinning-assessment"] = {**SPECS["damage/hcl-assessment"],**SPECS["damage/thinning-unclad-qualified"],"assessment_distribution":Literal["general","local"]}

SPECS["damage/hf-concentration-selection"] = {"hf_mass_fraction_for_lookup":Fraction,"concentrated_81_node_extension_used":bool}
SPECS["damage/hf-carbon-velocity-band"] = {"velocity_band":Literal["low","high"],"velocity_threshold_m_s":NUMBER}
SPECS["damage/hf-carbon-rate"] = {**SPECS["damage/hf-concentration-selection"],**SPECS["damage/hf-carbon-velocity-band"],
    "corrosion_rate_m_year":NUMBER,"source_999_corner_used":bool,"residual_column_used":Literal["low","high"] | None,"source_table_id":str}
SPECS["damage/hf-alloy400-rate"] = {**SPECS["damage/hf-concentration-selection"],"corrosion_rate_m_year":NUMBER,"source_999_corner_used":bool,"source_table_id":str}
SPECS["damage/hf-assessment"] = {"corrosion_rate_m_year":NUMBER,"source_table_id":str | None,
    "rate_source":Literal["carbon_steel_table","alloy400_table","qualified_published_rate"] | None,"source_999_corner_used":bool,
    "hf_mass_fraction_for_lookup":Fraction | None,"concentrated_81_node_extension_used":bool,"velocity_band":Literal["low","high"] | None,
    "velocity_threshold_m_s":NUMBER | None,"residual_column_used":Literal["low","high"] | None,
    "source_thinning_type":Literal["general","local"] | None,"calculation_branch":Literal["no_hf_exposure","qualified_hf_service"]}
SPECS["damage/hf-thinning-assessment"] = {**SPECS["damage/hf-assessment"],**SPECS["damage/thinning-unclad-qualified"],"assessment_distribution":Literal["general","local"]}

SPECS["damage/amine-acid-gas-loading"] = {"acid_gas_loading_mol_mol":NUMBER}
SPECS["damage/amine-loading-selection"] = {"lower_loading_row_index":int,"upper_loading_row_index":int,"loading_interpolation_weight":Fraction,
    "table_loading_regime":Literal["lean","rich"],"loading_gap_mapping_used":bool}
SPECS["damage/amine-contaminant-row"] = {"contaminant_row":Literal["low","middle","high"],"printed_hsas_row_mass_fraction":Fraction}
SPECS["damage/amine-strength-factor"] = {"amine_strength_factor":NUMBER}
SPECS["damage/amine-carbon-base-rate"] = {**SPECS["damage/amine-loading-selection"],"base_corrosion_rate_m_year":NUMBER,
    "velocity_band":Literal["low","high"],"velocity_threshold_m_s":NUMBER,"source_table_id":str}
SPECS["damage/amine-stainless-rate"] = {"corrosion_rate_m_year":NUMBER,"low_loading_first_row_used":bool,"source_table_id":str}
SPECS["damage/amine-corrosion-assessment"] = {"corrosion_rate_m_year":NUMBER,"base_corrosion_rate_m_year":NUMBER | None,
    "amine_strength_factor":NUMBER | None,"contaminant_row":Literal["low","middle","high"] | None,"printed_hsas_row_mass_fraction":Fraction | None,
    "table_loading_regime":Literal["lean","rich"] | None,"loading_gap_mapping_used":bool,"velocity_band":Literal["low","high"] | None,
    "velocity_threshold_m_s":NUMBER | None,"low_loading_first_row_used":bool,"source_table_id":str | None,
    "source_thinning_type":Literal["general","local"] | None,"calculation_branch":Literal["no_amine_service","carbon_amine_model","type300_stainless_model"]}
SPECS["damage/amine-thinning-assessment"] = {**SPECS["damage/amine-corrosion-assessment"],**SPECS["damage/thinning-unclad-qualified"],"assessment_distribution":Literal["general","local"]}

SPECS["damage/sulfuric-table-axes"] = {"acid_mass_fraction_nodes":list[Fraction],"temperature_nodes_k":list[NUMBER],"velocity_nodes_m_s":list[NUMBER],"source_table_id":str,
    "carbon_si_velocity_interpretation":Literal["not_applicable","qualified_printed_m_s","qualified_us_ft_s_header"]}
SPECS["damage/sulfuric-table-rate"] = {"corrosion_rate_m_year":NUMBER,"source_table_id":str,
    "carbon_si_velocity_interpretation":Literal["not_applicable","qualified_printed_m_s","qualified_us_ft_s_header"],"source_999_corner_used":bool,
    "disputed_304_cell_used":bool,"source_localized_enhancement_already_included":bool}
SPECS["damage/sulfuric-thinning-classification"] = {"source_thinning_type":Literal["general","local"],"thinning_velocity_threshold_m_s":NUMBER,"thinning_velocity_boundary_resolved":bool}
SPECS["damage/sulfuric-corrosion-assessment"] = {**SPECS["damage/sulfuric-table-rate"],"source_table_id":str | None,
    "source_thinning_type":Literal["general","local"] | None,"thinning_velocity_threshold_m_s":NUMBER | None,"thinning_velocity_boundary_resolved":bool,
    "rate_source":Literal["source_maximum_estimate","qualified_specialist_estimate"] | None,
    "calculation_branch":Literal["no_sulfuric_service","qualified_sulfuric_service"]}
SPECS["damage/sulfuric-thinning-assessment"] = {**SPECS["damage/sulfuric-corrosion-assessment"],**SPECS["damage/thinning-unclad-qualified"],"assessment_distribution":Literal["general","local"]}

SPECS["damage/h2sh2-table-axes"] = {"h2s_mole_fraction_nodes":list[Fraction],"temperature_nodes_k":list[NUMBER],
    "table_group":Literal["carbon_low_alloy","cr5","cr7","cr9","cr12","stainless"],"hydrocarbon_curve_required":bool,"source_table_id":str}
SPECS["damage/h2sh2-table-rate"] = {"corrosion_rate_m_year":NUMBER,"source_table_id":str,
    "selected_hydrocarbon_curve":Literal["naphtha","gas_oil"] | None,"hydrocarbon_free_curve_selection_used":bool,"source_thinning_type":Literal["general"]}
SPECS["damage/h2sh2-corrosion-assessment"] = {**SPECS["damage/h2sh2-table-rate"],"source_table_id":str | None,"source_thinning_type":Literal["general"] | None,
    "calculation_branch":Literal["no_h2s_h2_service","qualified_high_temperature_h2s_h2"]}
SPECS["damage/h2sh2-thinning-assessment"] = {**SPECS["damage/h2sh2-corrosion-assessment"],**SPECS["damage/thinning-unclad-qualified"],"assessment_distribution":Literal["general","local"]}

_SULFIDIC_GROUP = Literal["carbon_steel","low_alloy","cr5","cr7","cr9","cr12","stainless_no_mo","stainless_low_mo","stainless_high_mo"]
SPECS["damage/sulfidic-material-selection"] = {"table_group":_SULFIDIC_GROUP,"unknown_molybdenum_low_assumed":bool}
SPECS["damage/sulfidic-table-axes"] = {**SPECS["damage/sulfidic-material-selection"],"sulfur_mass_fraction_nodes":list[Fraction],"tan_nodes_mg_koh_g":list[NUMBER],
    "lower_temperature_bin_upper_k":NUMBER,"interior_temperature_nodes_k":list[NUMBER],"upper_temperature_bin_lower_exclusive_k":NUMBER,"source_table_id":str}
SPECS["damage/sulfidic-table-rate"] = {"base_corrosion_rate_m_year":NUMBER,"source_table_id":str,**SPECS["damage/sulfidic-material-selection"],
    "source_temperature_bin_used":Literal["lower","upper"] | None,"first_temperature_threshold_anchor_used":bool,"below_first_tan_row_used":bool}
SPECS["damage/sulfidic-velocity-factor"] = {"velocity_factor":NUMBER,"velocity_boundary_conflict_encountered":bool}
SPECS["damage/sulfidic-thinning-classification"] = {"source_thinning_type":Literal["general","local"]}
SPECS["damage/sulfidic-corrosion-assessment"] = {**SPECS["damage/sulfidic-table-rate"],**SPECS["damage/sulfidic-velocity-factor"],
    "base_corrosion_rate_m_year":NUMBER | None,"source_table_id":str | None,"table_group":_SULFIDIC_GROUP | None,
    "velocity_factor":NUMBER | None,"source_thinning_type":Literal["general","local"] | None,"corrosion_rate_m_year":NUMBER,
    "calculation_branch":Literal["no_sulfidic_service","qualified_sulfidic_naphthenic_service"]}
SPECS["damage/sulfidic-thinning-assessment"] = {**SPECS["damage/sulfidic-corrosion-assessment"],**SPECS["damage/thinning-unclad-qualified"],"assessment_distribution":Literal["general","local"]}

SPECS["properties/pure-fluid-flash"] = {"flashed_temperature_k":NUMBER,"vapor_mass_fraction":Fraction,
    "flashed_phase":Literal["twophase","liquid","supercritical_liquid","gas","supercritical_gas"],"bulk_density_kg_m3":NUMBER,
    "conserved_property":Literal["Smass","Hmass"],"conserved_value_si":float,"engine_version":str,
    "storage_phase":Literal["liquid","supercritical_liquid","gas","supercritical_gas","twophase"],"storage_vapor_mass_fraction":Fraction,"vapor_mass_fraction_change":float,
    "storage_temperature_k":NUMBER,"storage_state_basis":Literal["pressure_temperature","pressure_quality"]}

SPECS['release/pure-liquid-flash-partition'] = {**SPECS['properties/pure-fluid-flash'],
    **SPECS['release/level2-source-partition'],'rainout_mass_fraction':Fraction}

_PURE_SATURATION = {name:NUMBER for name in ('saturation_pressure_pa_abs','bubble_temperature_k','dew_temperature_k',
    'liquid_density_kg_m3','vapor_density_kg_m3','liquid_specific_heat_j_kg_k','vapor_specific_heat_j_kg_k','latent_heat_j_kg','molecular_weight_kg_kmol')}
SPECS['properties/pure-fluid-saturation-pressure'] = {**_PURE_SATURATION,'engine_version':str}
SPECS['properties/pure-fluid-saturation-temperature'] = {**_PURE_SATURATION,'engine_version':str}

SPECS['dispersion/flashed-boiling-pool-centreline'] = {**SPECS['release/pure-liquid-flash-partition'],
    **SPECS['properties/pure-fluid-saturation-pressure'],**SPECS['release/boiling-pool-steady-source'],
    **SPECS['dispersion/native-pool-centreline'],
    **{name:NUMBER for name in ('steady_window_start_s','steady_window_duration_s','steady_evaporated_mass_kg','startup_unmodeled_pool_mass_kg')},
    'integration_scope':Literal['flashed_pure_liquid_boiling_pool_steady_window_centreline']}
SPECS['dispersion/flashed-boiling-pool-footprint'] = {**SPECS['dispersion/flashed-boiling-pool-centreline'],
    **SPECS['dispersion/native-pool-footprint'],
    'integration_scope':Literal['flashed_pure_liquid_boiling_pool_steady_window_footprint']}
SPECS['dispersion/flashed-boiling-pool-flash-fire'] = {**SPECS['dispersion/flashed-boiling-pool-footprint'],
    **SPECS['dispersion/native-pool-flash-fire'],
    'integration_scope':Literal['flashed_pure_liquid_boiling_pool_steady_window_flash_fire']}

SPECS['risk/area-event-contribution'] = {**{name:NUMBER for name in (
    'annual_release_frequency_per_year','annual_selected_event_frequency_per_year',
    'event_weighted_equipment_area_m2','event_weighted_personnel_area_m2',
    'equipment_area_risk_contribution_m2_per_year','personnel_area_risk_contribution_m2_per_year','area_risk_contribution_m2_per_year')},
    'conditional_joint_probability':Fraction,'contribution_scope':Literal['selected_event_weather_case']}
SPECS['risk/flashed-pool-flash-fire-contribution'] = {**SPECS['dispersion/flashed-boiling-pool-flash-fire'],
    **SPECS['risk/area-event-contribution'],'generic_hole_frequency_per_year':NUMBER,'management_factor':NUMBER,'total_damage_factor':NUMBER,
    'selected_hole':Literal['small','medium','large','rupture'],
    'contribution_scope':Literal['selected_hole_weather_steady_pool_flash_fire'],
    'integration_scope':Literal['selected_hole_weather_steady_pool_flash_fire_risk_contribution']}

SPECS['damage/groundwater-tks'] = {'total_key_species_mg_l':NUMBER}
SPECS['damage/groundwater-rate-classification'] = {'corrosion_rate_m_year':NUMBER,
    'corrosivity_category':Literal['low','medium','high','very_high'],'selected_unit_basis':Literal['printed_si','printed_us_converted'],
    'category_lower_bound_m_year':NUMBER,'category_upper_bound_m_year':NUMBER | None,
    'lower_bound_relation':Literal['inclusive','exclusive'],'upper_bound_relation':Literal['inclusive','exclusive','unbounded'],
    'shared_boundary_encountered':bool}
SPECS['damage/groundwater-assessment'] = {**SPECS['damage/groundwater-tks'],**SPECS['damage/groundwater-rate-classification'],
    'rate_source':Literal['qualified_external_groundwater_rate'],'tks_to_rate_model_available':Literal[False]}
SPECS['damage/groundwater-thinning-assessment'] = {**SPECS['damage/groundwater-assessment'],
    **SPECS['damage/thinning-unclad-qualified'],'assessment_distribution':Literal['general','local']}

SPECS['damage/thinning-prior-selection'] = {'prior_probabilities':list[Fraction],
    'prior_source':Literal['table4_5','qualified_custom'],'confidence':Literal['low','medium','high'] | None,
    'zero_prior_state_indices':list[int]}

SPECS['damage/thinning-rate-selection'] = {'corrosion_rate_m_year':NUMBER,'assessment_distribution':Literal['general','local'],
    'governing_rate_mechanism_ids':list[str],'governing_type_mechanism_ids':list[str],
    'rate_by_mechanism_m_year':dict[str,NUMBER],
    'selection_source_by_mechanism':dict[str,Literal['measured','calculated','estimated']],
    'fallback_ignored_by_mechanism':dict[str,bool]}
SPECS['damage/thinning-selected-mechanisms'] = {**SPECS['damage/thinning-rate-selection'],**SPECS['damage/thinning-unclad-qualified']}

SPECS['damage/thinning-assessment-period'] = {'baseline_type':Literal['furnished','measured'],
    'baseline_at':str,'assessment_at':str,'baseline_thickness_m':NUMBER,'baseline_inspection_id':str | None,
    'elapsed_days':NUMBER,'elapsed_years':NUMBER,'days_per_year':NUMBER}
SPECS['damage/thinning-inspection-history'] = {**SPECS['damage/thinning-assessment-period'],
    **{'inspections_'+grade:int for grade in 'abcd'},'eligible_inspection_ids':list[str],
    'excluded_inspection_reasons':dict[str,Literal['before_baseline','after_assessment','baseline_boundary','unqualified','ineffective_e']],
    'baseline_boundary_policy':Literal['include_baseline_time','exclude_baseline_time']}
SPECS['damage/thinning-history-assessment'] = {**SPECS['damage/thinning-inspection-history'],**SPECS['damage/thinning-selected-mechanisms']}

SPECS['damage/caustic-screening'] = {'evaluate_caustic_cracking':bool,
    'screening_reason':Literal['evaluate','outside_material_scope','caustic_absent']}
SPECS['damage/caustic-figure-susceptibility'] = {'susceptibility':Literal['none','low','medium','high'],
    'decision_branch':str,'plot_evidence_used':bool,'historical_high_retained':bool}
SPECS['damage/caustic-screened-assessment'] = {**SPECS['damage/caustic-screening'],
    **SPECS['damage/caustic-figure-susceptibility'],**SPECS['damage/caustic']}

SPECS['damage/amine-cracking-screening'] = {'evaluate_amine_cracking':bool,
    'screening_reason':Literal['evaluate','outside_material_scope','treating_amine_absent']}
SPECS['damage/amine-cracking-screened-assessment'] = {**SPECS['damage/amine-cracking-screening'],**SPECS['damage/amine']}

SPECS['damage/amine-figure-susceptibility'] = {'susceptibility':Literal['none','low','medium','high'],
    'decision_branch':str,'lean_exposure_selected':bool}
SPECS['damage/amine-figure-assessment'] = {**SPECS['damage/amine-cracking-screening'],
    **SPECS['damage/amine-figure-susceptibility'],**SPECS['damage/amine']}

SPECS['damage/ssc-screening'] = {'evaluate_ssc':bool,
    'screening_reason':Literal['outside_material_scope','water_absent','h2s_absent','evaluate']}

SPECS['damage/ssc-qualified-susceptibility'] = {**SPECS['damage/wet-h2s-environment'],
    'unadjusted_susceptibility':Literal['none','low','medium','high'],
    'susceptibility':Literal['none','low','medium','high'],'cyanide_upgrade_applied':bool}
SPECS['damage/ssc-qualified-assessment'] = {**SPECS['damage/ssc-screening'],
    **SPECS['damage/ssc-qualified-susceptibility'],**SPECS['damage/ssc']}

SPECS['damage/hic-h2s-screening'] = {'evaluate_hic_sohic_h2s':bool,
    'screening_reason':Literal['outside_material_scope','water_absent','h2s_absent','evaluate']}

SPECS['damage/hic-h2s-qualified-susceptibility'] = {**SPECS['damage/wet-h2s-environment'],
    'effective_environmental_severity':Literal['low','moderate','high'],
    **{name:Literal['none','low','medium','high'] for name in ('unadjusted_susceptibility','cyanide_adjusted_susceptibility','susceptibility')}}
SPECS['damage/hic-h2s-qualified-assessment'] = {**SPECS['damage/hic-h2s-screening'],
    **SPECS['damage/hic-h2s-qualified-susceptibility'],**SPECS['damage/hic-sohic-h2s'],
    'ffs_disposition':Literal['not_required','repaired','qualified_ffs_basis']}

SPECS['damage/hic-h2s-monitoring-selection'] = {'table_monitoring_factor':NUMBER,'monitoring_factor':NUMBER,
    'monitoring_factor_source':Literal['table9_5','qualified_experience_replacement']}
SPECS['damage/hic-h2s-qualified-assessment'].update(SPECS['damage/hic-h2s-monitoring-selection'])

SPECS['damage/acscc-screening'] = {'evaluate_acscc':bool,'material_in_scope':bool,
    'evaluation_triggers':list[Literal['alkaline_water_ph_above_7_5','fccu_feed_sulfur_reduced','fccu_feed_nitrogen_increased']]}

SPECS['damage/acscc-water-susceptibility'] = {'susceptibility':Literal['none','low','medium','high'],
    'selected_ph_band':Literal['below_7.5','7.5_to_8','8_to_9','at_least_9'],'shared_ph_boundary_encountered':bool}

SPECS['damage/acscc-qualified-assessment'] = {**SPECS['damage/acscc-screening'],
    **SPECS['damage/acscc-water-susceptibility'],**SPECS['damage/acscc']}

SPECS['damage/pascc-screening'] = {'evaluate_pascc':bool,
    'screening_reason':Literal['outside_material_scope','sulfur_exposure_absent','evaluate']}

SPECS['damage/pascc-figure-susceptibility'] = {'table_or_override_susceptibility':Literal['none','low','medium','high'],
    'susceptibility':Literal['none','low','medium','high'],'downtime_reduction_applied':bool}
SPECS['damage/pascc-qualified-assessment'] = {**SPECS['damage/pascc-screening'],
    **SPECS['damage/pascc-figure-susceptibility'],**SPECS['damage/pascc']}

SPECS['damage/clscc-screening'] = {'evaluate_clscc':bool,'material_in_scope':bool,'temperature_screen_passed':bool,
    'screening_temperature_threshold_k':NUMBER,'selected_temperature_basis':Literal['printed_si','printed_us_converted']}

SPECS['damage/clscc-qualified-assessment'] = {**SPECS['damage/clscc-screening'],
    'susceptibility':Literal['none','low','medium','high'],**SPECS['damage/clscc']}

# Runtime validation uses the same static output models exposed by the Python API.
from .outputs import OUTPUT_MODELS
from .result import CalculationResult

CrossingOutput = OUTPUT_MODELS["planning/target-crossing"]
AssessmentOutput = OUTPUT_MODELS["risk/assessment"]
RESPONSE_MODELS = {identifier: CalculationResult[model] for identifier, model in OUTPUT_MODELS.items()}
