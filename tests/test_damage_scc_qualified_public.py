import runpy

from api581 import evaluate


def test_amine_figure_assessment_public_boundary():
    result = evaluate("damage/amine-figure-assessment", {
        "screening": {"material": "carbon_steel", "acid_gas_treating_amine_present": True,
                      "screening_basis": "qualified amine exposure"},
        "service": {"confirmed_cracking": False, "unrepaired_cracks": False,
                    "stress_relieved": False, "solution": "lean", "amine_group": "mea_or_dipa",
                    "maximum_metal_temperature_k": 380.0, "heat_traced": False,
                    "steamed_out_before_water_flush": False, "applicability_basis": "qualified figure inputs"},
        "years_since_qualifying_inspection": 2.0,
        "inspections": {"a": 1, "b": 0, "c": 0, "d": 0},
        "inspection_basis": "qualified amine inspection history",
    })
    assert result["outputs"]["susceptibility"] in {"low", "medium", "high"}


def test_hic_h2s_qualified_susceptibility_public_boundary():
    result = evaluate("damage/hic-h2s-qualified-susceptibility", {
        "environment": {"water_ph": 8.5, "h2s_in_water_ppm": 2000, "cyanides_present": True},
        "steel_sulfur_weight_percent": 0.02, "product_form": "plate_or_welded", "pwht": True,
        "confirmed_cracking": False, "service_basis": "qualified HIC material and chemistry",
    })
    assert result["outputs"]["susceptibility"] in {"low", "medium", "high"}


def test_acscc_water_susceptibility_public_boundary():
    result = evaluate("damage/acscc-water-susceptibility", {
        "water_ph": 7.5, "carbonate_ppm": 100, "pwht": False,
        "carbonate_measurement_basis": "qualified carbonate analysis",
        "traditional_alkalinity_only": False,
        "service_fabrication_basis": "qualified ACSCC service",
    })
    assert result["outputs"]["susceptibility"] == "medium"


def test_pascc_figure_susceptibility_public_boundary():
    result = evaluate("damage/pascc-figure-susceptibility", {
        "alloy": {"operating_temperature_k": 700.15, "material_group": "l_grade_300ss",
                  "heat_treatment": "solution_annealed"},
        "sulfur_oxygen_water_during_operation": True,
        "sulfur_oxygen_water_during_shutdown": False,
        "qualified_rp0170_downtime_protection": False,
        "confirmed_cracking": False, "unrepaired_cracks": False,
        "service_alloy_basis": "qualified PASCC alloy and exposure",
    })
    assert result["outputs"]["susceptibility"] == "medium"


def test_clscc_qualified_assessment_public_boundary():
    result = evaluate("damage/clscc-qualified-assessment", {
        "screening": {"material": "austenitic_stainless_steel",
                      "actual_or_potential_wet_chloride_exposure": True,
                      "operating_temperature_k": 350.0, "temperature_basis": "printed_si",
                      "exposure_basis": "qualified wet chloride exposure"},
        "ph_over_10": False, "chloride_band_ppm": "101-1000",
        "chemistry_basis": "qualified local chloride and pH",
        "confirmed_cracking": False, "unrepaired_cracks": False,
        "years_since_qualifying_inspection": 2.0,
        "inspections": {"a": 1, "b": 0, "c": 0, "d": 0},
        "inspection_basis": "qualified CLSCC inspection history",
    })
    assert result["outputs"]["susceptibility"] in {"low", "medium", "high"}


def test_ssc_qualified_assessment_public_boundary():
    result = evaluate("damage/ssc-qualified-assessment", {
        "screening": {"material": "carbon_steel", "water_present": True, "h2s_present": True,
                      "exposure_basis": "qualified wet H2S exposure"},
        "service": {"environment": {"water_ph": 8.5, "h2s_in_water_ppm": 2000, "cyanides_present": True},
                    "measured_brinnell_hardness": 180.0, "pwht": True,
                    "service_basis": "qualified SSC chemistry and hardness"},
        "confirmed_cracking": False, "unrepaired_cracks": False,
        "years_since_qualifying_inspection": 2.0,
        "inspections": {"a": 1, "b": 0, "c": 0, "d": 0},
        "inspection_basis": "qualified SSC inspection history",
    })
    assert result["outputs"]["damage_factor"] > 0


def test_hic_h2s_qualified_assessment_public_boundary():
    result = evaluate("damage/hic-h2s-qualified-assessment", {
        "screening": {"material": "carbon_steel", "water_present": True, "h2s_present": True,
                      "exposure_basis": "qualified wet H2S exposure"},
        "service": {"environment": {"water_ph": 8.5, "h2s_in_water_ppm": 2000, "cyanides_present": True},
                    "steel_sulfur_weight_percent": 0.02, "product_form": "plate_or_welded", "pwht": True,
                    "confirmed_cracking": False, "service_basis": "qualified HIC chemistry and material"},
        "known_blisters_or_cracks": False, "ffs_disposition": "not_required", "ffs_basis": None,
        "years_since_qualifying_inspection": 2.0,
        "inspections": {"a": 1, "b": 0, "c": 0, "d": 0},
        "monitoring": "process_variables", "experience_factor": None, "experience_basis": None,
        "inspection_monitoring_basis": "qualified HIC inspection and monitoring",
    })
    assert result["outputs"]["damage_factor"] > 0


def test_hic_h2s_monitoring_selection_public_boundary():
    result = evaluate("damage/hic-h2s-monitoring-selection", {
        "monitoring": "both", "experience_factor": None, "experience_basis": None,
    })
    assert result["outputs"]["monitoring_factor"] == 4.0


def test_acscc_qualified_assessment_public_boundary():
    result = evaluate("damage/acscc-qualified-assessment", {
        "screening": {"material": "carbon_steel", "water_present": True, "water_ph": 7.6,
                      "fccu_feed_sulfur_reduced": False, "fccu_feed_nitrogen_increased": False,
                      "screening_basis": "qualified ACSCC screening"},
        "water": {"water_ph": 7.6, "carbonate_ppm": 100, "pwht": False,
                  "shared_ph_boundary_policy": None, "carbonate_measurement_basis": "qualified carbonate",
                  "traditional_alkalinity_only": False, "service_fabrication_basis": "qualified ACSCC service"},
        "confirmed_cracking": False, "unrepaired_cracks": False,
        "years_since_qualifying_inspection": 2.0,
        "inspections": {"a": 1, "b": 0, "c": 0, "d": 0},
        "inspection_basis": "qualified ACSCC inspection history",
    })
    assert result["outputs"]["damage_factor"] > 0


def test_pascc_qualified_assessment_public_boundary():
    result = evaluate("damage/pascc-qualified-assessment", {
        "screening": {"material": "austenitic_stainless_steel", "sulfur_bearing_compounds_exposure": True,
                      "exposure_basis": "qualified PASCC exposure"},
        "service": {"alloy": {"operating_temperature_k": 700.15, "material_group": "l_grade_300ss",
                                "heat_treatment": "solution_annealed"},
                    "sulfur_oxygen_water_during_operation": True,
                    "sulfur_oxygen_water_during_shutdown": False,
                    "qualified_rp0170_downtime_protection": False,
                    "protection_basis": None, "confirmed_cracking": False, "unrepaired_cracks": False,
                    "service_alloy_basis": "qualified PASCC alloy"},
        "years_since_qualifying_inspection": 2.0,
        "inspections": {"a": 1, "b": 0, "c": 0, "d": 0},
        "inspection_basis": "qualified PASCC inspection history",
    })
    assert result["outputs"]["damage_factor"] > 0


def test_amine_rate_primitives_public_boundaries():
    carbon = evaluate("damage/amine-carbon-base-rate", {
        "table_family": "mea_dea",
        "loading": {"acid_gas_loading_mol_mol": 0.35, "loading_gap_policy": "reject_unassigned_0p10_to_0p15"},
        "contaminant_row": "low", "maximum_temperature_k": 389.15, "velocity_m_s": 2.0,
        "unit_basis": "printed_si", "lookup_policy": "exact_nodes_only",
    })
    stainless = evaluate("damage/amine-stainless-rate", {
        "acid_gas_loading_mol_mol": 0.35, "maximum_temperature_k": 400.0,
        "unit_basis": "printed_si", "lookup_policy": "exact_nodes_only",
        "low_loading_policy": "reject_below_0p1", "normal_service_conditions_qualified": True,
        "qualification_basis": "qualified Type300 normal service",
    })
    assert carbon["outputs"]["base_corrosion_rate_m_year"] >= 0
    assert stainless["outputs"]["corrosion_rate_m_year"] >= 0


def test_amine_corrosion_assessment_public_boundary():
    result = evaluate("damage/amine-corrosion-assessment", {
        "amine_service_present": True,
        "applicability_basis": "qualified chemical gas treating amine service",
        "rate_model": {
            "method": "carbon_table", "material": "carbon_steel",
            "low_alloy_qualification_basis": None,
            "solution": {"amine_type": "mea", "amine_mass_fraction": 0.25},
            "contaminants": {"amine_type": "mea", "contaminant_mass_fraction": 0.03,
                            "mdea_scale_policy": "not_mdea", "mdea_scale_qualification_basis": None,
                            "four_percent_boundary_policy": None, "four_percent_qualification_basis": None},
            "loading": {"acid_gas_loading_mol_mol": 0.35, "loading_gap_policy": "reject_unassigned_0p10_to_0p15"},
            "maximum_temperature_k": 389.15, "velocity_m_s": 2.0, "unit_basis": "printed_si",
            "lookup_policy": "exact_nodes_only",
            "classification_qualification_basis": "qualified rate-table velocity classification",
            "qualification_basis": "qualified local temperature and concentration",
        },
    })
    assert result["outputs"]["corrosion_rate_m_year"] > 0


def test_sour_water_assessment_public_boundary():
    result = evaluate("damage/sour-water-assessment", {
        "screening": {"free_water_present": False, "qualification_basis": "qualified dry service"},
        "acid_model": None, "alkaline_model": None,
    })
    assert result["outputs"]["corrosion_rate_m_year"] == 0


def test_thinning_composition_public_boundaries():
    selected = runpy.run_path("examples/multiple_thinning_mechanisms.py")["request"]().model_dump()
    history = runpy.run_path("examples/thinning_history_assessment.py")["request"]().model_dump()
    selected_result = evaluate("damage/thinning-selected-mechanisms", selected)
    history_result = evaluate("damage/thinning-history-assessment", history)
    assert selected_result["outputs"]["thinning_damage_factor"] > 0
    assert history_result["outputs"]["thinning_damage_factor"] > 0


def test_thinning_workflow_examples_public_boundaries():
    soil = runpy.run_path("examples/soil_corrosion_to_thinning.py")["result"].normalized_inputs
    cooling = runpy.run_path("examples/cooling_water_to_thinning.py")["result"].normalized_inputs
    co2 = runpy.run_path("examples/co2_corrosion_to_thinning.py")["result"].normalized_inputs
    co2_screened = runpy.run_path("examples/co2_screened_to_thinning.py")["result"].normalized_inputs
    acid = runpy.run_path("examples/acid_sour_water_to_thinning.py")["result"].normalized_inputs
    alkaline = runpy.run_path("examples/alkaline_sour_water_to_thinning.py")["result"].normalized_inputs
    hcl = runpy.run_path("examples/hcl_to_thinning.py")["result"].normalized_inputs
    hf = runpy.run_path("examples/hf_to_thinning.py")["result"].normalized_inputs
    sulfuric = runpy.run_path("examples/sulfuric_to_thinning.py")["result"].normalized_inputs
    sulfidic = runpy.run_path("examples/sulfidic_to_thinning.py")["result"].normalized_inputs
    assert evaluate("damage/soil-thinning-assessment", soil)["outputs"]
    assert evaluate("damage/cooling-water-thinning-assessment", cooling)["outputs"]
    assert evaluate("damage/co2-thinning-assessment", co2)["outputs"]
    assert evaluate("damage/co2-screened-thinning", co2_screened)["outputs"]
    assert evaluate("damage/acid-sour-water-thinning-assessment", acid)["outputs"]
    assert evaluate("damage/alkaline-sour-water-thinning-assessment", alkaline)["outputs"]
    assert evaluate("damage/hcl-thinning-assessment", hcl)["outputs"]
    assert evaluate("damage/hf-thinning-assessment", hf)["outputs"]
    assert evaluate("damage/sulfuric-thinning-assessment", sulfuric)["outputs"]
    assert evaluate("damage/sulfidic-thinning-assessment", sulfidic)["outputs"]


def test_cooling_water_public_boundaries():
    cooling_result = runpy.run_path("examples/cooling_water_to_thinning.py")["result"]
    selection_example = runpy.run_path("examples/cooling_rate_selection_to_thinning.py")
    fresh = evaluate("damage/cooling-water-fresh-assessment", cooling_result.normalized_inputs["cooling"])
    selected = evaluate("damage/cooling-water-selected-thinning",
                        {"selection": selection_example["selection"], **selection_example["args"]})
    assert fresh["outputs"]["corrosion_rate_m_year"] >= 0
    assert selected["outputs"]["thinning_damage_factor"] >= 0


def test_unclad_and_h2sh2_thinning_public_boundaries():
    source = runpy.run_path("examples/co2_corrosion_to_thinning.py")["result"].normalized_inputs
    generic = {"assessment_scope": "non_ast_unclad", "qualification_basis": "qualified common baseline",
               "wall": {"starting_thickness_m": source["starting_thickness_m"],
                        "corrosion_rate_m_year": source["corrosion"]["wet_model"]["ph"]["ph"] * 0.00001,
                        "elapsed_years": source["elapsed_years"]},
               "strength": source["strength"], "inspections": source["inspections"],
               "conditions": source["conditions"]}
    h2sh2 = {"corrosion": {"h2s_h2_service_present": True,
                            "applicability_basis": "qualified high-temperature hydrogen service",
                            "service_model": {"material": "cr5_0p5mo", "unit_basis": "printed_si",
                                              "h2s_mole_fraction": 0.003, "maximum_temperature_k": 686.15,
                                              "stream_case": "gas_oil", "lookup_policy": "exact_nodes_only",
                                              "hydrogen_sulfidation_environment_qualified": True,
                                              "material_and_stream_qualification_basis": "qualified service and material"}},
              "assessment_distribution": "general", "distribution_qualification_basis": "qualified general coverage",
              "starting_thickness_m": 0.02, "elapsed_years": 2.0,
              "strength": source["strength"], "inspections": source["inspections"],
              "conditions": {"monitoring": {"row": {"mechanism": "high_temperature_h2s_h2"}, "methods": [], "organized_monitoring_plan": False},
                             "injection": source["conditions"]["injection"], "deadleg": source["conditions"]["deadleg"]},
              "qualification_basis": "qualified common non-AST baseline"}
    assert evaluate("damage/thinning-unclad-qualified", generic)["outputs"]
    assert evaluate("damage/h2sh2-thinning-assessment", h2sh2)["outputs"]


def test_amine_thinning_assessment_public_boundary():
    source = runpy.run_path("examples/co2_corrosion_to_thinning.py")["result"].normalized_inputs
    corrosion = {
        "amine_service_present": True, "applicability_basis": "qualified chemical gas treating amine service",
        "rate_model": {"method": "carbon_table", "material": "carbon_steel", "low_alloy_qualification_basis": None,
                       "solution": {"amine_type": "mea", "amine_mass_fraction": 0.25},
                       "contaminants": {"amine_type": "mea", "contaminant_mass_fraction": 0.03,
                                       "mdea_scale_policy": "not_mdea", "mdea_scale_qualification_basis": None,
                                       "four_percent_boundary_policy": None, "four_percent_qualification_basis": None},
                       "loading": {"acid_gas_loading_mol_mol": 0.35, "loading_gap_policy": "reject_unassigned_0p10_to_0p15"},
                       "maximum_temperature_k": 389.15, "velocity_m_s": 2.0, "unit_basis": "printed_si",
                       "lookup_policy": "exact_nodes_only", "classification_qualification_basis": "qualified velocity classification",
                       "qualification_basis": "qualified local temperature and concentration"},
    }
    conditions = dict(source["conditions"])
    conditions["monitoring"] = {"row": {"mechanism": "amine", "amine_velocity_regime": "high",
                                         "amine_regime_basis": "qualified amine velocity regime"},
                                 "methods": [], "organized_monitoring_plan": False}
    inputs = {"corrosion": corrosion, "assessment_distribution": "local",
              "distribution_qualification_basis": "qualified local attack coverage", "starting_thickness_m": 0.02,
              "elapsed_years": 1.0, "strength": source["strength"], "inspections": source["inspections"],
              "conditions": conditions, "qualification_basis": "qualified non-AST amine baseline"}
    assert evaluate("damage/amine-thinning-assessment", inputs)["outputs"]["thinning_damage_factor"] >= 0
