import api581


def test_effectiveness_category_a_metadata():
    result = api581.evaluate(
        "inspection/effectiveness-category",
        {"category": "A", "owner_user_basis": "Qualified NDE procedure"},
    )
    assert result["outputs"] == {
        "category": "A",
        "ordinal": 1,
        "label": "Highly Effective",
        "inspection_credit_allowed": True,
        "owner_user_basis": "Qualified NDE procedure",
    }


def test_thinning_effectiveness_local_intrusive_full_visual_follow_up():
    result = api581.evaluate(
        "inspection/thinning-effectiveness",
        {
            "damage_type": "local",
            "inspection_mode": "intrusive",
            "visual_coverage_percent": 100.0,
            "follow_up_coverage_percent": 100.0,
        },
    )
    assert result["outputs"] == {
        "effectiveness_category": "A",
        "damage_type": "local",
        "inspection_mode": "intrusive",
        "qualification_status": "qualified",
        "basis": "100_percent_visual_and_follow_up",
    }


def test_scc_effectiveness_weld_intrusive_full_targeted_follow_up():
    result = api581.evaluate(
        "inspection/scc-effectiveness",
        {
            "mechanism_family": "weld_scc",
            "inspection_mode": "intrusive",
            "targeted_coverage_percent": 100.0,
            "relevant_indication_follow_up_percent": 100.0,
        },
    )
    assert result["outputs"] == {
        "effectiveness_category": "A",
        "mechanism_family": "weld_scc",
        "inspection_mode": "intrusive",
        "qualification_status": "qualified",
        "basis": "100_percent_targeted_and_indication_follow_up",
    }


def test_tube_bundle_uncertainty_category_c():
    result = api581.evaluate(
        "inspection/tube-bundle-uncertainty",
        {"inspection_effectiveness": "C", "owner_user_basis": "Qualified tube bundle inspection history"},
    )
    assert result["outputs"] == {
        "inspection_effectiveness": "C",
        "uncertainty_percent": 20.0,
        "uncertainty_fraction": 0.2,
        "baseline_no_history_percent": 50.0,
        "owner_user_basis": "Qualified tube bundle inspection history",
    }


def test_external_corrosion_full_visual_follow_up():
    result = api581.evaluate(
        "inspection/external-effectiveness",
        {
            "mechanism_family": "external_corrosion",
            "visual_coverage_percent": 100.0,
            "follow_up_coverage_percent": 100.0,
        },
    )
    assert result["outputs"] == {
        "effectiveness_category": "A",
        "mechanism_family": "external_corrosion",
        "insulation_status": "not_applicable",
        "qualification_status": "qualified",
        "basis": "over_95_percent_visual_with_follow_up",
    }


def test_buried_intrusive_hydrostatic_test_category_d():
    result = api581.evaluate(
        "inspection/buried-effectiveness",
        {
            "inspection_mode": "intrusive",
            "hydrostatic_test": True,
            "qualification_basis": "Qualified buried-component inspection basis",
        },
    )
    assert result["outputs"] == {
        "effectiveness_category": "D",
        "inspection_mode": "intrusive",
        "qualification_status": "qualified",
        "basis": "hydrostatic_test",
    }


def test_prd_pressure_relief_device_as_received_bench_test_category_a():
    result = api581.evaluate(
        "inspection/prd-effectiveness",
        {
            "component_type": "pressure_relief_device",
            "as_received_bench_test": True,
            "leak_pressure_documented": True,
            "opening_pressure_documented": True,
            "reseat_pressure_documented": True,
            "inlet_outlet_examined": True,
            "qualification_basis": "Qualified PRD inspection procedure",
        },
    )
    assert result["outputs"] == {
        "effectiveness_category": "A",
        "component_type": "pressure_relief_device",
        "qualification_status": "qualified",
        "basis": "as_received_bench_test_pressures_and_piping_exam",
    }


def test_lining_intrusive_full_visual_holiday_disbonding_category_a():
    result = api581.evaluate(
        "inspection/lining-effectiveness",
        {
            "inspection_mode": "intrusive",
            "visual_coverage_percent": 100.0,
            "holiday_test_coverage_percent": 100.0,
            "disbonding_test_coverage_percent": 100.0,
            "qualification_basis": "Qualified lining inspection procedure",
        },
    )
    assert result["outputs"] == {
        "effectiveness_category": "A",
        "inspection_mode": "intrusive",
        "qualification_status": "qualified",
        "basis": "100_percent_visual_holiday_and_disbonding_tests",
    }


def test_ast_shell_internal_full_ut_confirmation_category_a():
    result = api581.evaluate(
        "inspection/ast-effectiveness",
        {
            "component_type": "shell_internal",
            "inspection_side": "internal",
            "internal_video_or_visual": True,
            "pit_depth_measurement": True,
            "ut_scan_percent": 100.0,
            "ut_follow_up": True,
            "qualification_basis": "Qualified API 653 inspection procedure",
        },
    )
    assert result["outputs"] == {
        "effectiveness_category": "A",
        "component_type": "shell_internal",
        "inspection_side": "internal",
        "qualification_status": "qualified",
        "basis": "internal_visual_pit_and_full_UT_confirmation",
    }

