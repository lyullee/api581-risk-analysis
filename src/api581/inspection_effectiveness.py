"""Inspection effectiveness classification from API 581 Annex 2.C examples."""

from typing import Literal

from pydantic import Field

from .core import Model, NonNegative, calculation, ensure


class EffectivenessCategory(Model):
    category: Literal["A", "B", "C", "D", "E"]
    owner_user_basis: str = Field(min_length=1, max_length=1000)


@calculation(
    "inspection/effectiveness-category",
    "API 581 Annex 2.C common inspection effectiveness category metadata",
    EffectivenessCategory,
    ["Part 2 Annex C §2.C.2-§2.C.2.3; PDF pp443-445"],
    origin="api581_annex_2c2_effectiveness_category",
    limitations=[
        "Returns the common qualitative category metadata only. It does not decide whether a particular NDE method satisfies a mechanism-specific table; use the dedicated inspection effectiveness APIs for that decision.",
        "Category E means ineffective or insufficiently evidenced for inspection credit. A-D labels are qualitative and do not by themselves define a numeric damage-factor reduction."
    ],
)
def effectiveness_category(x):
    labels = {
        "A": "Highly Effective", "B": "Usually Effective",
        "C": "Fairly Effective", "D": "Poorly Effective", "E": "Ineffective",
    }
    return {
        "category": x.category,
        "ordinal": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}[x.category],
        "label": labels[x.category],
        "inspection_credit_allowed": x.category != "E",
        "owner_user_basis": x.owner_user_basis,
    }


class ThinningInspectionEffectiveness(Model):
    damage_type: Literal["general", "local"]
    inspection_mode: Literal["intrusive", "non_intrusive"]
    visual_coverage_percent: NonNegative = Field(default=0, le=100)
    spot_thickness_coverage_percent: NonNegative = Field(default=0, le=100)
    advanced_scan_coverage_percent: NonNegative = Field(default=0, le=100)
    profile_radiography_coverage_percent: NonNegative = Field(default=0, le=100)
    follow_up_coverage_percent: NonNegative = Field(default=0, le=100)
    inspection_quality_high: bool = True
    locations_qualified: bool = True
    technique_effective: bool = True


@calculation(
    "inspection/thinning-effectiveness",
    "API 581 Annex 2.C.8 thinning inspection effectiveness category",
    ThinningInspectionEffectiveness,
    ["Part 2 Annex C §2.C.8.1-§2.C.8.2, Tables 2.C.8.1-2.C.8.2; PDF pp454-455"],
    origin="api581_annex_2c8_inspection_effectiveness",
    limitations=[
        "Implements the printed general/local thinning percentage examples only. It classifies inspection effectiveness; it does not calculate inspection uncertainty, PoF, damage factor or inspection credit.",
        "The caller must qualify inspection quality, CML/location selection and technique effectiveness. A failed qualification returns E rather than manufacturing credit. Thresholds follow the table's percentage bands; ambiguous technique descriptions are not inferred."
    ],
)
def thinning_effectiveness(x):
    qualified = x.inspection_quality_high and x.locations_qualified and x.technique_effective
    if not qualified:
        return {
            "effectiveness_category": "E",
            "damage_type": x.damage_type,
            "inspection_mode": x.inspection_mode,
            "qualification_status": "failed",
            "basis": "inspection_quality_or_location_or_technique_not_qualified",
        }

    visual = x.visual_coverage_percent
    spot = x.spot_thickness_coverage_percent
    scan = x.advanced_scan_coverage_percent
    profile = x.profile_radiography_coverage_percent
    follow = x.follow_up_coverage_percent

    if x.damage_type == "local":
        if x.inspection_mode == "intrusive":
            if visual >= 100 and follow >= 100:
                category, basis = "A", "100_percent_visual_and_follow_up"
            elif visual > 75 and follow >= 100:
                category, basis = "B", "over_75_percent_visual_and_follow_up"
            elif visual > 50 and follow >= 100:
                category, basis = "C", "over_50_percent_visual_and_follow_up"
            elif visual > 20 and follow >= 100:
                category, basis = "D", "over_20_percent_visual_and_follow_up"
            else:
                category, basis = "E", "local_intrusive_threshold_not_met"
        else:
            coverage = max(spot, scan, profile)
            if coverage >= 100:
                category, basis = "A", "100_percent_suspect_area_coverage"
            elif coverage > 75:
                category, basis = "B", "over_75_percent_suspect_area_coverage"
            elif coverage > 50:
                category, basis = "C", "over_50_percent_suspect_area_coverage"
            elif coverage > 20:
                category, basis = "D", "over_20_percent_suspect_area_coverage"
            else:
                category, basis = "E", "local_non_intrusive_threshold_not_met"
    elif x.inspection_mode == "intrusive":
        if (visual > 50 and spot > 50) or scan >= 10 or profile >= 10:
            category, basis = "A", "general_intrusive_high_coverage"
        elif (visual > 25 and spot > 25) or scan > 5 or profile > 5:
            category, basis = "B", "general_intrusive_usually_effective"
        elif visual > 5 and spot > 5 or profile > 0:
            category, basis = "C", "general_intrusive_fairly_effective"
        elif visual > 0:
            category, basis = "D", "general_intrusive_poorly_effective"
        else:
            category, basis = "E", "general_intrusive_threshold_not_met"
    else:
        if spot >= 100 or scan >= 10 or profile >= 10:
            category, basis = "A", "general_non_intrusive_high_coverage"
        elif spot > 75 or scan > 5 or profile > 5:
            category, basis = "B", "general_non_intrusive_usually_effective"
        elif spot > 50 or profile > 0:
            category, basis = "C", "general_non_intrusive_fairly_effective"
        elif spot > 25:
            category, basis = "D", "general_non_intrusive_poorly_effective"
        else:
            category, basis = "E", "general_non_intrusive_threshold_not_met"

    ensure(category in {"A", "B", "C", "D", "E"}, "Invalid inspection effectiveness category")
    return {
        "effectiveness_category": category,
        "damage_type": x.damage_type,
        "inspection_mode": x.inspection_mode,
        "qualification_status": "qualified",
        "basis": basis,
    }


class SccInspectionEffectiveness(Model):
    mechanism_family: Literal["weld_scc", "clscc_pta"]
    inspection_mode: Literal["intrusive", "non_intrusive"]
    targeted_coverage_percent: NonNegative = Field(default=0, le=100)
    ultrasonic_scan_percent: NonNegative = Field(default=0, le=100)
    radiography_percent: NonNegative = Field(default=0, le=100)
    acoustic_emission_follow_up_percent: NonNegative = Field(default=0, le=100)
    relevant_indication_follow_up_percent: NonNegative = Field(default=0, le=100)
    inspection_quality_high: bool = True
    locations_qualified: bool = True
    technique_effective: bool = True


@calculation(
    "inspection/scc-effectiveness",
    "API 581 Annex 2.C.9 stress-corrosion-cracking inspection effectiveness category",
    SccInspectionEffectiveness,
    ["Part 2 Annex C §2.C.9.1-§2.C.9.9, Tables 2.C.9.1-2.C.9.9; PDF pp456-464"],
    origin="api581_annex_2c9_inspection_effectiveness",
    limitations=[
        "Implements the common percentage bands in the SCC example tables. It classifies inspection effectiveness only; it does not calculate SCC susceptibility, inspection uncertainty, PoF or damage factor.",
        "For CLSCC/PTA the source provides no non-intrusive A-level technique; this API returns E unless a lower category threshold is met. Caller must qualify inspection quality, suspect-area definition and indication follow-up."
    ],
)
def scc_effectiveness(x):
    if not (x.inspection_quality_high and x.locations_qualified and x.technique_effective):
        return {"effectiveness_category": "E", "mechanism_family": x.mechanism_family,
                "inspection_mode": x.inspection_mode, "qualification_status": "failed",
                "basis": "inspection_quality_or_location_or_technique_not_qualified"}

    targeted = x.targeted_coverage_percent
    scan = x.ultrasonic_scan_percent
    radiography = x.radiography_percent
    follow = x.relevant_indication_follow_up_percent
    ae_follow = x.acoustic_emission_follow_up_percent

    if x.mechanism_family == "weld_scc":
        if x.inspection_mode == "intrusive":
            if targeted >= 100 and follow >= 100:
                category, basis = "A", "100_percent_targeted_and_indication_follow_up"
            elif (targeted > 75 or ae_follow >= 100) and follow >= 100:
                category, basis = "B", "over_75_percent_targeted_or_AE_with_follow_up"
            elif targeted > 35 and follow >= 100 or radiography > 35:
                category, basis = "C", "over_35_percent_targeted_or_radiography"
            elif targeted > 10 and follow >= 100 or radiography > 10:
                category, basis = "D", "over_10_percent_targeted_or_radiography"
            else:
                category, basis = "E", "weld_intrusive_threshold_not_met"
        else:
            if scan >= 100:
                category, basis = "A", "100_percent_ultrasonic_scan"
            elif scan > 75:
                category, basis = "B", "over_75_percent_ultrasonic_scan"
            elif scan > 35:
                category, basis = "C", "over_35_percent_ultrasonic_scan"
            elif scan > 10:
                category, basis = "D", "over_10_percent_ultrasonic_scan"
            else:
                category, basis = "E", "weld_non_intrusive_threshold_not_met"
    elif x.inspection_mode == "intrusive":
        if targeted >= 100 and follow >= 100:
            category, basis = "A", "100_percent_targeted_and_indication_follow_up"
        elif (targeted > 65 or ae_follow >= 100) and follow >= 100:
            category, basis = "B", "over_65_percent_targeted_or_AE_with_follow_up"
        elif targeted > 35 and follow >= 100 or radiography > 65:
            category, basis = "C", "over_35_percent_targeted_or_over_65_percent_radiography"
        elif targeted > 10 and follow >= 100 or radiography > 35:
            category, basis = "D", "over_10_percent_targeted_or_over_35_percent_radiography"
        else:
            category, basis = "E", "CLSCC_PTA_intrusive_threshold_not_met"
    else:
        if scan >= 100 and x.mechanism_family == "weld_scc":
            category, basis = "A", "100_percent_ultrasonic_scan"
        elif scan > 65:
            category, basis = "B", "over_65_percent_ultrasonic_scan"
        elif scan > 35:
            category, basis = "C", "over_35_percent_ultrasonic_scan"
        elif scan > 10:
            category, basis = "D", "over_10_percent_ultrasonic_scan"
        else:
            category, basis = "E", "SCC_non_intrusive_threshold_not_met_or_A_unavailable"
    return {"effectiveness_category": category, "mechanism_family": x.mechanism_family,
            "inspection_mode": x.inspection_mode, "qualification_status": "qualified",
            "basis": basis}


class ExternalInspectionEffectiveness(Model):
    mechanism_family: Literal["external_corrosion", "external_clscc", "cui", "cui_clscc"]
    insulation_status: Literal["not_applicable", "removed", "not_removed"] = "not_applicable"
    visual_coverage_percent: NonNegative = Field(default=0, le=100)
    targeted_ndt_coverage_percent: NonNegative = Field(default=0, le=100)
    insulation_removed_percent: NonNegative = Field(default=0, le=100)
    follow_up_coverage_percent: NonNegative = Field(default=0, le=100)
    inspection_quality_high: bool = True
    locations_qualified: bool = True
    technique_effective: bool = True


@calculation(
    "inspection/external-effectiveness",
    "API 581 Annex 2.C.10 external-damage inspection effectiveness category",
    ExternalInspectionEffectiveness,
    ["Part 2 Annex C §2.C.10.1-§2.C.10.2, Tables 2.C.10.1-2.C.10.4; PDF pp463-465"],
    origin="api581_annex_2c10_inspection_effectiveness",
    limitations=[
        "Implements the printed external-corrosion, external CLSCC, CUI and CUI-CLSCC percentage examples. It classifies inspection effectiveness only and does not calculate external damage factor or inspection uncertainty.",
        "CUI-CLSCC/non-removed insulation has no source technique for A-D and therefore remains E. Caller must qualify exposed/suspect area definition, inspection quality and follow-up."
    ],
)
def external_effectiveness(x):
    if not (x.inspection_quality_high and x.locations_qualified and x.technique_effective):
        return {"effectiveness_category": "E", "mechanism_family": x.mechanism_family,
                "insulation_status": x.insulation_status, "qualification_status": "failed",
                "basis": "inspection_quality_or_location_or_technique_not_qualified"}

    visual = x.visual_coverage_percent
    ndt = x.targeted_ndt_coverage_percent
    removed = x.insulation_removed_percent
    follow = x.follow_up_coverage_percent
    if x.mechanism_family == "external_corrosion":
        if visual > 95 and follow >= 100: category, basis = "A", "over_95_percent_visual_with_follow_up"
        elif visual > 60 and follow >= 100: category, basis = "B", "over_60_percent_visual_with_follow_up"
        elif visual > 30 and follow >= 100: category, basis = "C", "over_30_percent_visual_with_follow_up"
        elif visual > 5 and follow >= 100: category, basis = "D", "over_5_percent_visual_with_follow_up"
        else: category, basis = "E", "external_corrosion_threshold_not_met"
    elif x.mechanism_family == "external_clscc":
        if ndt >= 100 and follow >= 100: category, basis = "A", "100_percent_dye_or_eddy_with_follow_up"
        elif ndt > 60 and follow >= 100: category, basis = "B", "over_60_percent_dye_or_eddy_with_follow_up"
        elif ndt > 30 and follow >= 100: category, basis = "C", "over_30_percent_dye_or_eddy_with_follow_up"
        elif ndt > 5 and follow >= 100: category, basis = "D", "over_5_percent_dye_or_eddy_with_follow_up"
        else: category, basis = "E", "external_clscc_threshold_not_met"
    elif x.mechanism_family == "cui":
        if visual < 100 or follow < 100:
            category, basis = "E", "cui_requires_full_visual_and_follow_up"
        elif x.insulation_status == "removed":
            if removed >= 100: category, basis = "A", "cui_removed_100_percent_suspect_area"
            elif removed > 50: category, basis = "B", "cui_removed_over_50_percent_suspect_area"
            elif removed > 25: category, basis = "C", "cui_removed_over_25_percent_suspect_area"
            elif removed > 5: category, basis = "D", "cui_removed_over_5_percent_total_area"
            else: category, basis = "E", "cui_removed_threshold_not_met"
        elif x.insulation_status == "not_removed":
            if ndt >= 100: category, basis = "A", "cui_not_removed_100_percent_profile_radiography"
            elif ndt > 65: category, basis = "B", "cui_not_removed_over_65_percent_profile_radiography"
            elif ndt > 35: category, basis = "C", "cui_not_removed_over_35_percent_profile_radiography"
            elif ndt > 5: category, basis = "D", "cui_not_removed_over_5_percent_profile_radiography"
            else: category, basis = "E", "cui_not_removed_threshold_not_met"
        else: category, basis = "E", "cui_insulation_status_required"
    elif x.insulation_status == "removed" and visual >= 100 and follow >= 100:
        if ndt >= 100: category, basis = "A", "cui_clscc_removed_100_percent_targeted_ndt"
        elif ndt > 60: category, basis = "B", "cui_clscc_removed_over_60_percent_targeted_ndt"
        elif ndt > 30: category, basis = "C", "cui_clscc_removed_over_30_percent_targeted_ndt"
        elif ndt > 5: category, basis = "D", "cui_clscc_removed_over_5_percent_targeted_ndt"
        else: category, basis = "E", "cui_clscc_removed_threshold_not_met"
    else:
        category, basis = "E", "cui_clscc_non_removed_or_qualification_not_met"
    return {"effectiveness_category": category, "mechanism_family": x.mechanism_family,
            "insulation_status": x.insulation_status, "qualification_status": "qualified",
            "basis": basis}


class BuriedInspectionEffectiveness(Model):
    inspection_mode: Literal["intrusive", "non_intrusive"]
    coverage_percent: NonNegative = Field(default=0, le=100)
    state_of_art_internal_technology: bool = False
    selected_internal_technology: bool = False
    statistical_or_extreme_value_analysis: bool = False
    partial_smart_pig_or_specialized_crawler: bool = False
    hydrostatic_test: bool = False
    full_excavation_visual_ndt: bool = False
    external_ndt_crawler: bool = False
    cathodic_protection_managed: bool = False
    close_interval_survey: bool = False
    soil_water_sampling: bool = False
    dcvg_coating_survey: bool = False
    guided_wave_and_corrosion_management: bool = False
    spot_check_exposed_areas: bool = False
    inspection_quality_high: bool = True
    qualification_basis: str = Field(min_length=1, max_length=1000)


@calculation(
    "inspection/buried-effectiveness",
    "API 581 Annex 2.C.7 buried-component inspection effectiveness category",
    BuriedInspectionEffectiveness,
    ["Part 2 Annex C §2.C.7.1-§2.C.7.2, Table 2.C.7.1; PDF pp452-453"],
    origin="api581_annex_2c7_buried_inspection_effectiveness",
    limitations=[
        "Classifies the example intrusive/non-intrusive evidence bundles in Table 2.C.7.1. It does not infer corrosion rate, cathodic-protection adequacy, soil corrosivity, PoF or damage factor.",
        "The caller must qualify the evidence flags and coverage. A missing qualification basis or low inspection quality returns E; partial excavation and non-intrusive evidence are not silently promoted to full coverage."
    ],
)
def buried_effectiveness(x):
    if not x.inspection_quality_high or not x.qualification_basis.strip():
        return {"effectiveness_category": "E", "inspection_mode": x.inspection_mode,
                "qualification_status": "failed", "basis": "inspection_quality_or_basis_not_qualified"}
    if x.inspection_mode == "intrusive":
        if x.state_of_art_internal_technology and x.coverage_percent >= 100:
            category, basis = "A", "100_percent_state_of_art_internal_inspection"
        elif x.selected_internal_technology and x.statistical_or_extreme_value_analysis:
            category, basis = "B", "selected_internal_inspection_with_statistical_analysis"
        elif x.partial_smart_pig_or_specialized_crawler:
            category, basis = "C", "partial_smart_pig_or_specialized_crawler"
        elif x.hydrostatic_test:
            category, basis = "D", "hydrostatic_test"
        else:
            category, basis = "E", "intrusive_evidence_bundle_not_met"
    elif (
        x.full_excavation_visual_ndt and x.coverage_percent >= 100
        and x.soil_water_sampling and x.cathodic_protection_managed
    ) or (
        x.external_ndt_crawler and x.coverage_percent >= 100
        and x.cathodic_protection_managed
    ):
        category, basis = "A", "qualified_full_external_inspection_and_CP_controls"
    elif (
        x.external_ndt_crawler and x.statistical_or_extreme_value_analysis
    ) or (
        x.close_interval_survey and x.full_excavation_visual_ndt
        and x.cathodic_protection_managed
    ):
        category, basis = "B", "selected_external_inspection_with_statistics_or_CP_guided_excavation"
    elif x.guided_wave_and_corrosion_management and x.spot_check_exposed_areas:
        category, basis = "C", "guided_wave_with_corrosion_management_and_spot_check"
    elif x.coverage_percent > 5 and (x.full_excavation_visual_ndt or x.external_ndt_crawler):
        category, basis = "D", "limited_external_visual_or_NDE_inspection"
    else:
        category, basis = "E", "non_intrusive_evidence_bundle_not_met"
    return {"effectiveness_category": category, "inspection_mode": x.inspection_mode,
            "qualification_status": "qualified", "basis": basis}


class PrdInspectionEffectiveness(Model):
    component_type: Literal["pressure_relief_device", "rupture_disk"]
    as_received_bench_test: bool = False
    leak_pressure_documented: bool = False
    opening_pressure_documented: bool = False
    reseat_pressure_documented: bool = False
    inlet_outlet_examined: bool = False
    cleaned_or_steamed_before_test: bool = False
    detailed_internal_visual: bool = False
    in_situ_actual_process_fluid: bool = False
    removed_and_visually_inspected: bool = False
    in_situ_non_process_fluid: bool = False
    leakage_monitoring: bool = False
    overhaul_without_pop_test: bool = False
    internal_details_documented: bool = False
    qualification_basis: str = Field(min_length=1, max_length=1000)


@calculation(
    "inspection/prd-effectiveness",
    "API 581 Annex 2.C.3 pressure-relief-device inspection effectiveness category",
    PrdInspectionEffectiveness,
    ["Part 2 Annex C §2.C.3-§2.C.3.1, Table 2.C.3.1; PDF pp445-446"],
    origin="api581_annex_2c3_prd_inspection_effectiveness",
    limitations=[
        "Implements the Table 2.C.3.1 evidence examples. It classifies inspection effectiveness only and does not calculate PRD failure frequency, service-age factor, set-pressure factor or leak consequence.",
        "Rupture-disk A-level inspection is explicitly unavailable in the source table. Missing qualification basis or incomplete evidence returns E rather than an optimistic category."
    ],
)
def prd_effectiveness(x):
    if not x.qualification_basis.strip():
        return {"effectiveness_category": "E", "component_type": x.component_type,
                "qualification_status": "failed", "basis": "qualification_basis_missing"}
    if x.component_type == "pressure_relief_device":
        if (x.as_received_bench_test and x.leak_pressure_documented
                and x.opening_pressure_documented and x.reseat_pressure_documented
                and x.inlet_outlet_examined):
            category, basis = "A", "as_received_bench_test_pressures_and_piping_exam"
        elif ((x.as_received_bench_test and x.cleaned_or_steamed_before_test and x.detailed_internal_visual)
              or x.in_situ_actual_process_fluid):
            category, basis = "B", "cleaned_bench_test_with_visual_or_actual_fluid_in_situ_test"
        elif x.detailed_internal_visual or x.in_situ_non_process_fluid:
            category, basis = "C", "documented_visual_or_non_process_fluid_in_situ_test"
        elif x.overhaul_without_pop_test:
            category, basis = "D", "overhaul_without_pop_test"
        else:
            category, basis = "E", "PRD_evidence_bundle_not_met"
    else:
        if x.removed_and_visually_inspected:
            category, basis = "B", "rupture_disk_removed_and_visually_inspected"
        elif x.leakage_monitoring:
            category, basis = "C", "rupture_disk_leakage_monitoring"
        elif x.internal_details_documented:
            category, basis = "D", "rupture_disk_internal_details_only"
        else:
            category, basis = "E", "rupture_disk_no_effective_method"
    return {"effectiveness_category": category, "component_type": x.component_type,
            "qualification_status": "qualified", "basis": basis}


class LiningInspectionEffectiveness(Model):
    inspection_mode: Literal["intrusive", "non_intrusive"]
    visual_coverage_percent: NonNegative = Field(default=0, le=100)
    holiday_test_coverage_percent: NonNegative = Field(default=0, le=100)
    disbonding_test_coverage_percent: NonNegative = Field(default=0, le=100)
    ultrasonic_scan_coverage_percent: NonNegative = Field(default=0, le=100)
    inspection_quality_high: bool = True
    locations_qualified: bool = True
    qualification_basis: str = Field(min_length=1, max_length=1000)


@calculation(
    "inspection/lining-effectiveness",
    "API 581 Annex 2.C.6 non-metallic lining inspection effectiveness category",
    LiningInspectionEffectiveness,
    ["Part 2 Annex C §2.C.6.1-§2.C.6.2, Table 2.C.6.1; PDF pp451-452"],
    origin="api581_annex_2c6_lining_inspection_effectiveness",
    limitations=[
        "Implements the example percentage bands for corrosion-resistant non-metallic liners. The source states this inspection effectiveness is not currently used in the lining damage factor calculation; this API does not change that rule.",
        "Non-intrusive A-level inspection is explicitly unavailable in the source table. Inspection quality, suspect-area definition and test suitability remain owner-qualified inputs."
    ],
)
def lining_effectiveness(x):
    if not (x.inspection_quality_high and x.locations_qualified and x.qualification_basis.strip()):
        return {"effectiveness_category": "E", "inspection_mode": x.inspection_mode,
                "qualification_status": "failed", "basis": "inspection_quality_location_or_basis_not_qualified"}
    visual = x.visual_coverage_percent
    holiday = x.holiday_test_coverage_percent
    disbonding = x.disbonding_test_coverage_percent
    scan = x.ultrasonic_scan_coverage_percent
    if x.inspection_mode == "intrusive":
        if visual >= 100 and holiday >= 100 and disbonding >= 100:
            category, basis = "A", "100_percent_visual_holiday_and_disbonding_tests"
        elif visual > 65 and holiday > 65 and disbonding > 65:
            category, basis = "B", "over_65_percent_visual_holiday_and_disbonding_tests"
        elif max(visual, holiday, disbonding) > 35:
            category, basis = "C", "over_35_percent_intrusive_liner_test"
        elif max(visual, holiday, disbonding) > 5:
            category, basis = "D", "over_5_percent_intrusive_liner_test"
        else:
            category, basis = "E", "intrusive_liner_threshold_not_met"
    else:
        if scan >= 100:
            category, basis = "B", "100_percent_automated_or_manual_ultrasonic_scan"
        elif scan > 65:
            category, basis = "C", "over_65_percent_ultrasonic_scan"
        elif scan > 35:
            category, basis = "D", "over_35_percent_ultrasonic_scan"
        else:
            category, basis = "E", "non_intrusive_liner_threshold_or_A_unavailable"
    return {"effectiveness_category": category, "inspection_mode": x.inspection_mode,
            "qualification_status": "qualified", "basis": basis}


class TubeBundleInspectionUncertainty(Model):
    inspection_effectiveness: Literal["A", "B", "C", "D", "E"]
    owner_user_basis: str = Field(min_length=1, max_length=1000)


@calculation(
    "inspection/tube-bundle-uncertainty",
    "API 581 Annex 2.C.4.1 default tube-bundle inspection uncertainty",
    TubeBundleInspectionUncertainty,
    ["Part 2 Annex C §2.C.4.1.1-§2.C.4.1.3, Table 2.C.4.1; PDF pp446-448"],
    origin="api581_annex_2c4_tube_bundle_uncertainty",
    limitations=[
        "Returns the recommended additional-uncertainty percentage only: A=5%, B=10%, C=20%, D=30%, E=50%. It does not shift a Weibull curve or calculate tube-bundle PoF by itself.",
        "The source says tube-bundle LoIE tables are owner-user defined; the category and basis remain caller-qualified and must not be inferred from an NDE name alone."
    ],
)
def tube_bundle_uncertainty(x):
    values = {"A": 5.0, "B": 10.0, "C": 20.0, "D": 30.0, "E": 50.0}
    percent = values[x.inspection_effectiveness]
    return {"inspection_effectiveness": x.inspection_effectiveness,
            "uncertainty_percent": percent,
            "uncertainty_fraction": percent / 100.0,
            "baseline_no_history_percent": 50.0,
            "owner_user_basis": x.owner_user_basis}


class AstInspectionEffectiveness(Model):
    component_type: Literal["shell_internal", "shell_external", "tank_bottom"]
    inspection_side: Literal["internal", "external", "soil_side", "product_side"]
    insulated: bool = False
    visual_coverage_percent: NonNegative = Field(default=0, le=100)
    internal_video_or_visual: bool = False
    pit_depth_measurement: bool = False
    ut_scan_percent: NonNegative = Field(default=0, le=100)
    ut_follow_up: bool = False
    insulation_removed_percent: NonNegative = Field(default=0, le=100)
    pulse_eddy_percent: NonNegative = Field(default=0, le=100)
    floor_scan_percent: NonNegative = Field(default=0, le=100)
    vacuum_box_percent: NonNegative = Field(default=0, le=100)
    sponge_test_percent: NonNegative = Field(default=0, le=100)
    statistical_floor_analysis: bool = False
    qualification_basis: str = Field(min_length=1, max_length=1000)
    inspection_quality_high: bool = True


@calculation(
    "inspection/ast-effectiveness",
    "API 581 Annex 2.C.5 atmospheric storage tank inspection effectiveness category",
    AstInspectionEffectiveness,
    ["Part 2 Annex C §2.C.5.1-§2.C.5.2, Tables 2.C.5.1-2.C.5.3; PDF pp449-451"],
    origin="api581_annex_2c5_ast_inspection_effectiveness",
    limitations=[
        "Implements the example AST shell-internal, shell-external and tank-bottom evidence bands. It does not calculate tank corrosion rate, minimum thickness, PoF or financial consequence.",
        "The caller must select the correct side and qualify inspection quality, exposed/suspect area and API 653/NDE interpretation. Inputs from multiple sides are not silently combined into a higher category."
    ],
)
def ast_effectiveness(x):
    if not (x.inspection_quality_high and x.qualification_basis.strip()):
        return {"effectiveness_category": "E", "component_type": x.component_type,
                "inspection_side": x.inspection_side, "qualification_status": "failed",
                "basis": "inspection_quality_or_basis_not_qualified"}
    if x.component_type == "shell_internal":
        if x.internal_video_or_visual and x.pit_depth_measurement and x.ut_scan_percent >= 100 and x.ut_follow_up:
            category, basis = "A", "internal_visual_pit_and_full_UT_confirmation"
        elif x.ut_scan_percent > 0 and x.internal_video_or_visual and x.ut_follow_up:
            category, basis = "B", "internal_video_with_external_UT_follow_up"
        elif x.ut_scan_percent > 0 and x.internal_video_or_visual:
            category, basis = "C", "external_spot_UT_with_internal_information"
        elif x.ut_scan_percent > 0:
            category, basis = "D", "external_spot_UT_without_internal_information"
        else:
            category, basis = "E", "shell_internal_evidence_bundle_not_met"
    elif x.component_type == "shell_external":
        if x.insulated:
            if x.visual_coverage_percent > 95 and x.insulation_removed_percent > 90 and x.pulse_eddy_percent > 90:
                category, basis = "A", "insulated_shell_full_visual_removal_and_pulse_eddy"
            elif x.visual_coverage_percent > 95 and x.insulation_removed_percent > 50 and x.pulse_eddy_percent > 50:
                category, basis = "B", "insulated_shell_over_50_percent_suspect_inspection"
            elif x.visual_coverage_percent > 95 and x.insulation_removed_percent > 30 and x.pulse_eddy_percent > 30:
                category, basis = "C", "insulated_shell_over_30_percent_suspect_inspection"
            elif x.visual_coverage_percent > 95 and x.insulation_removed_percent > 10 and x.pulse_eddy_percent > 10:
                category, basis = "D", "insulated_shell_over_10_percent_suspect_inspection"
            else:
                category, basis = "E", "insulated_shell_threshold_not_met"
        elif x.visual_coverage_percent > 95 and x.ut_follow_up:
            category, basis = "A", "uninsulated_shell_over_95_percent_visual_with_follow_up"
        elif x.visual_coverage_percent > 50 and x.ut_follow_up:
            category, basis = "B", "uninsulated_shell_over_50_percent_visual_with_follow_up"
        elif x.visual_coverage_percent > 25 and x.ut_follow_up:
            category, basis = "C", "uninsulated_shell_over_25_percent_visual_with_follow_up"
        elif x.visual_coverage_percent > 10 and x.ut_follow_up:
            category, basis = "D", "uninsulated_shell_over_10_percent_visual_with_follow_up"
        else:
            category, basis = "E", "uninsulated_shell_threshold_not_met"
    elif x.inspection_side == "soil_side":
        if x.floor_scan_percent > 90 and x.ut_follow_up:
            category, basis = "A", "soil_side_over_90_percent_floor_scan_and_UT_follow_up"
        elif (x.floor_scan_percent > 50 and x.ut_follow_up) or x.statistical_floor_analysis:
            category, basis = "B", "soil_side_over_50_percent_scan_or_statistical_analysis"
        elif x.floor_scan_percent > 5 and x.ut_follow_up:
            category, basis = "C", "soil_side_partial_floor_scan_and_UT_follow_up"
        elif x.ut_scan_percent > 0 or x.visual_coverage_percent > 50:
            category, basis = "D", "soil_side_spot_or_limited_visual_inspection"
        else:
            category, basis = "E", "soil_side_threshold_not_met"
    else:
        if x.visual_coverage_percent >= 100 and x.vacuum_box_percent >= 100:
            category, basis = "A", "product_side_full_visual_and_vacuum_box"
        elif x.sponge_test_percent > 75 or x.visual_coverage_percent >= 100:
            category, basis = "B", "product_side_full_visual_or_over_75_percent_sponge"
        elif 50 <= x.sponge_test_percent <= 75 or x.visual_coverage_percent > 50:
            category, basis = "C", "product_side_intermediate_liner_or_visual_inspection"
        elif x.sponge_test_percent > 0 or x.visual_coverage_percent > 0:
            category, basis = "D", "product_side_limited_inspection"
        else:
            category, basis = "E", "product_side_threshold_not_met"
    return {"effectiveness_category": category, "component_type": x.component_type,
            "inspection_side": x.inspection_side, "qualification_status": "qualified",
            "basis": basis}
