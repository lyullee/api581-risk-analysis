import pytest

from api581.api import inspection


@pytest.mark.parametrize(
    ("category", "ordinal", "credit"),
    [("A", 1, True), ("B", 2, True), ("C", 3, True), ("D", 4, True), ("E", 5, False)],
)
def test_common_effectiveness_category_metadata(category, ordinal, credit):
    result = inspection.effectiveness_category(
        inspection.EffectivenessCategoryInput(
            category=category, owner_user_basis="qualified owner-user category basis"
        )
    ).outputs
    assert result.ordinal == ordinal
    assert result.inspection_credit_allowed is credit


def test_effectiveness_summary_combines_lower_categories_without_crediting_e():
    result = inspection.effectiveness_summary(
        inspection.EffectivenessSummaryInput(
            mechanism="scc", categories=["C", "C", "D", "E"]
        )
    ).outputs
    assert result.highest_effectiveness_category == "C"
    assert result.inspection_count == 4
    assert result.creditable_inspection_count == 3
    assert result.e_inspection_count == 1
    assert result.equivalent_counts == {"a": 0, "b": 1, "c": 0, "d": 1}


def test_general_non_intrusive_thinning_category_a_uses_table_threshold():
    result = inspection.thinning_effectiveness(
        inspection.ThinningEffectivenessInput(
            damage_type="general",
            inspection_mode="non_intrusive",
            spot_thickness_coverage_percent=100,
        )
    ).outputs
    assert result.effectiveness_category == "A"
    assert result.qualification_status == "qualified"


@pytest.mark.parametrize(
    ("coverage", "expected"),
    [(80, "B"), (60, "C"), (30, "D"), (10, "E")],
)
def test_general_non_intrusive_thinning_uses_strict_percentage_bands(coverage, expected):
    result = inspection.thinning_effectiveness(
        inspection.ThinningEffectivenessInput(
            damage_type="general",
            inspection_mode="non_intrusive",
            spot_thickness_coverage_percent=coverage,
        )
    ).outputs
    assert result.effectiveness_category == expected


def test_local_intrusive_requires_follow_up_to_receive_credit():
    result = inspection.thinning_effectiveness(
        inspection.ThinningEffectivenessInput(
            damage_type="local",
            inspection_mode="intrusive",
            visual_coverage_percent=100,
            follow_up_coverage_percent=50,
        )
    ).outputs
    assert result.effectiveness_category == "E"


def test_failed_qualification_is_explicitly_ineffective():
    result = inspection.thinning_effectiveness(
        inspection.ThinningEffectivenessInput(
            damage_type="general",
            inspection_mode="non_intrusive",
            spot_thickness_coverage_percent=100,
            inspection_quality_high=False,
        )
    ).outputs
    assert result.effectiveness_category == "E"
    assert result.qualification_status == "failed"


def test_weld_scc_non_intrusive_ultrasonic_scan_category_a():
    result = inspection.scc_effectiveness(
        inspection.SccEffectivenessInput(
            mechanism_family="weld_scc",
            inspection_mode="non_intrusive",
            ultrasonic_scan_percent=100,
        )
    ).outputs
    assert result.effectiveness_category == "A"


def test_clscc_non_intrusive_does_not_claim_unavailable_category_a():
    result = inspection.scc_effectiveness(
        inspection.SccEffectivenessInput(
            mechanism_family="clscc_pta",
            inspection_mode="non_intrusive",
            ultrasonic_scan_percent=100,
        )
    ).outputs
    assert result.effectiveness_category == "B"


def test_scc_intrusive_requires_relevant_indication_follow_up():
    result = inspection.scc_effectiveness(
        inspection.SccEffectivenessInput(
            mechanism_family="weld_scc",
            inspection_mode="intrusive",
            targeted_coverage_percent=100,
            relevant_indication_follow_up_percent=50,
        )
    ).outputs
    assert result.effectiveness_category == "E"


def test_external_corrosion_uses_visual_exposure_bands():
    result = inspection.external_effectiveness(
        inspection.ExternalEffectivenessInput(
            mechanism_family="external_corrosion",
            visual_coverage_percent=96,
            follow_up_coverage_percent=100,
        )
    ).outputs
    assert result.effectiveness_category == "A"


def test_cui_without_insulation_removal_can_use_profile_radiography():
    result = inspection.external_effectiveness(
        inspection.ExternalEffectivenessInput(
            mechanism_family="cui",
            insulation_status="not_removed",
            visual_coverage_percent=100,
            targeted_ndt_coverage_percent=70,
            follow_up_coverage_percent=100,
        )
    ).outputs
    assert result.effectiveness_category == "B"


def test_cui_clscc_non_removed_has_no_claimed_effective_category():
    result = inspection.external_effectiveness(
        inspection.ExternalEffectivenessInput(
            mechanism_family="cui_clscc",
            insulation_status="not_removed",
            visual_coverage_percent=100,
            targeted_ndt_coverage_percent=100,
            follow_up_coverage_percent=100,
        )
    ).outputs
    assert result.effectiveness_category == "E"


def test_buried_intrusive_state_of_art_full_coverage_is_category_a():
    result = inspection.buried_effectiveness(
        inspection.BuriedEffectivenessInput(
            inspection_mode="intrusive",
            coverage_percent=100,
            state_of_art_internal_technology=True,
            qualification_basis="qualified inline inspection record",
        )
    ).outputs
    assert result.effectiveness_category == "A"


def test_buried_non_intrusive_requires_explicit_cp_and_external_evidence():
    result = inspection.buried_effectiveness(
        inspection.BuriedEffectivenessInput(
            inspection_mode="non_intrusive",
            coverage_percent=100,
            external_ndt_crawler=True,
            cathodic_protection_managed=True,
            qualification_basis="NACE-qualified CP and crawler report",
        )
    ).outputs
    assert result.effectiveness_category == "A"


def test_buried_unqualified_basis_does_not_receive_inspection_credit():
    result = inspection.buried_effectiveness(
        inspection.BuriedEffectivenessInput(
            inspection_mode="intrusive",
            coverage_percent=100,
            state_of_art_internal_technology=True,
            qualification_basis=" ",
        )
    ).outputs
    assert result.effectiveness_category == "E"
    assert result.qualification_status == "failed"


def test_prd_as_received_bench_test_is_category_a():
    result = inspection.prd_effectiveness(
        inspection.PrdEffectivenessInput(
            component_type="pressure_relief_device",
            as_received_bench_test=True,
            leak_pressure_documented=True,
            opening_pressure_documented=True,
            reseat_pressure_documented=True,
            inlet_outlet_examined=True,
            qualification_basis="qualified PRD test form",
        )
    ).outputs
    assert result.effectiveness_category == "A"


def test_rupture_disk_a_level_is_not_invented():
    result = inspection.prd_effectiveness(
        inspection.PrdEffectivenessInput(
            component_type="rupture_disk",
            qualification_basis="qualified rupture disk record",
            removed_and_visually_inspected=True,
        )
    ).outputs
    assert result.effectiveness_category == "B"


def test_prd_missing_basis_is_explicit_failure():
    result = inspection.prd_effectiveness(
        inspection.PrdEffectivenessInput(component_type="pressure_relief_device", qualification_basis=" ")
    ).outputs
    assert result.effectiveness_category == "E"
    assert result.qualification_status == "failed"


def test_lining_intrusive_full_test_bundle_is_category_a():
    result = inspection.lining_effectiveness(
        inspection.LiningEffectivenessInput(
            inspection_mode="intrusive",
            visual_coverage_percent=100,
            holiday_test_coverage_percent=100,
            disbonding_test_coverage_percent=100,
            qualification_basis="qualified liner inspection plan",
        )
    ).outputs
    assert result.effectiveness_category == "A"


def test_lining_non_intrusive_ultrasonic_scan_has_no_a_level():
    result = inspection.lining_effectiveness(
        inspection.LiningEffectivenessInput(
            inspection_mode="non_intrusive",
            ultrasonic_scan_coverage_percent=100,
            qualification_basis="qualified scan plan",
        )
    ).outputs
    assert result.effectiveness_category == "B"


@pytest.mark.parametrize(
    ("category", "uncertainty"),
    [("A", 5.0), ("B", 10.0), ("C", 20.0), ("D", 30.0), ("E", 50.0)],
)
def test_tube_bundle_uncertainty_uses_annex_table(category, uncertainty):
    result = inspection.tube_bundle_uncertainty(
        inspection.TubeBundleUncertaintyInput(
            inspection_effectiveness=category,
            owner_user_basis="owner-user LoIE table qualification",
        )
    ).outputs
    assert result.uncertainty_percent == uncertainty
    assert result.uncertainty_fraction == pytest.approx(uncertainty / 100)


def test_ast_external_shell_uninsulated_category_a_requires_follow_up():
    result = inspection.ast_effectiveness(
        inspection.AstEffectivenessInput(
            component_type="shell_external",
            inspection_side="external",
            visual_coverage_percent=96,
            ut_follow_up=True,
            qualification_basis="qualified API 653 external inspection",
        )
    ).outputs
    assert result.effectiveness_category == "A"


def test_ast_bottom_soil_side_category_a_requires_floor_scan_and_follow_up():
    result = inspection.ast_effectiveness(
        inspection.AstEffectivenessInput(
            component_type="tank_bottom",
            inspection_side="soil_side",
            floor_scan_percent=95,
            ut_follow_up=True,
            qualification_basis="qualified floor scan record",
        )
    ).outputs
    assert result.effectiveness_category == "A"


def test_ast_internal_shell_without_internal_information_is_not_promoted():
    result = inspection.ast_effectiveness(
        inspection.AstEffectivenessInput(
            component_type="shell_internal",
            inspection_side="external",
            ut_scan_percent=20,
            qualification_basis="external spot UT only",
        )
    ).outputs
    assert result.effectiveness_category == "D"
