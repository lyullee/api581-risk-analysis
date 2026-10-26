import pytest

from api581.api import properties
from api581.representative_fluids import (
    AcidCausticSelection,
    MixtureRepresentativeFluid,
    RepresentativeFluid,
)
from api581.release import Gas, Liquid


def test_table_42m_note1_polynomial_and_static_properties():
    result = properties.representative_fluid(
        RepresentativeFluid(fluid="H2", temperature_k=300)
    ).outputs
    assert result.molecular_weight_kg_kmol == 2
    assert result.liquid_density_kg_m3 == pytest.approx(71.010)
    assert result.normal_boiling_point_k == pytest.approx(20.15)
    assert result.ambient_state == "Gas"
    assert result.cp_basis == "table_note_1_polynomial"
    assert result.cp_value_table_units == pytest.approx(28.84555)
    assert result.autoignition_temperature_k == pytest.approx(673.15)


def test_table_42m_note3_fourth_degree_polynomial():
    result = properties.representative_fluid(
        RepresentativeFluid(fluid="Water", temperature_k=400)
    ).outputs
    expected = 2.76e5 - 2.09e3 * 400 + 8.125 * 400**2 - 1.41e-2 * 400**3 + 9.37e-6 * 400**4
    assert result.cp_value_table_units == pytest.approx(expected)
    assert result.cp_basis == "table_note_3_polynomial"


def test_table_42m_note2_hyperbolic_form_is_evaluated():
    result = properties.representative_fluid(
        RepresentativeFluid(fluid="Methanol", temperature_k=300)
    ).outputs
    assert result.cp_value_table_units is not None
    assert result.cp_value_table_units > 0
    assert result.cp_basis == "table_note_2_hyperbolic"


def test_table_42m_rows_without_properties_return_nulls():
    result = properties.representative_fluid(
        RepresentativeFluid(fluid="HCL", temperature_k=300)
    ).outputs
    assert result.cp_value_table_units is None
    assert result.cp_basis == "not_available"
    assert result.autoignition_temperature_k is None


def test_mixture_representative_fluid_weights_properties_and_selects_table_row():
    result = properties.mixture_representative_fluid(
        MixtureRepresentativeFluid(
            components=[
                {"fluid": "C5", "mole_fraction": 0.5},
                {"fluid": "C6-C8", "mole_fraction": 0.5},
            ]
        )
    ).outputs
    assert result.molecular_weight_kg_kmol == pytest.approx(86.0)
    assert result.normal_boiling_point_k == pytest.approx(340.65)
    assert result.liquid_density_kg_m3 == pytest.approx(654.6085)
    assert result.selected_fluid == "C5"
    assert result.relevant_mole_fraction == pytest.approx(1.0)
    assert result.level2_recommended is False


def test_mixture_representative_fluid_excludes_inert_fraction_from_consequence_rule():
    result = properties.mixture_representative_fluid(
        MixtureRepresentativeFluid(
            components=[
                {"fluid": "Water", "mole_fraction": 0.9, "consequence_relevant": False},
                {"fluid": "C25+", "mole_fraction": 0.1},
            ]
        )
    ).outputs
    assert result.relevant_mole_fraction == pytest.approx(0.1)
    assert result.selected_fluid == "C25+"


def test_mixture_representative_fluid_requires_normalized_mole_fractions():
    with pytest.raises(Exception, match="mole fractions must sum"):
        properties.mixture_representative_fluid(
            MixtureRepresentativeFluid(
                components=[{"fluid": "C5", "mole_fraction": 0.4}]
            )
        )


def test_acid_caustic_rule_selects_acid_liquid_reference():
    result = properties.acid_caustic_representative_fluid(
        AcidCausticSelection(
            is_acid_or_caustic=True,
            is_flammable=False,
            is_toxic=False,
            personnel_contact_hazard=True,
        )
    ).outputs
    assert result.selection == "acid_reference"
    assert result.representative_fluid == "Acid"
    assert result.release_phase == "liquid"
    assert result.consequence_model == "acid_splash"


@pytest.mark.parametrize(
    "changes",
    [
        {"is_acid_or_caustic": False},
        {"is_flammable": True},
        {"is_toxic": True},
        {"personnel_contact_hazard": False},
    ],
)
def test_acid_caustic_rule_does_not_override_other_routes(changes):
    values = dict(
        is_acid_or_caustic=True,
        is_flammable=False,
        is_toxic=False,
        personnel_contact_hazard=True,
    )
    values.update(changes)
    result = properties.acid_caustic_representative_fluid(
        AcidCausticSelection(**values)
    ).outputs
    assert result.selection == "not_applicable"
    assert result.representative_fluid is None


def test_level1_release_to_acid_composes_source_controls_and_splash():
    from api581.api import level1
    output = level1.release_to_acid(
        level1.ReleaseToAcidInput(
            source=Liquid(
                diameter_m=0.0064,
                upstream_pressure_pa_abs=300000,
                downstream_pressure_pa_abs=101325,
                density_kg_m3=1000,
            ),
            operating_temperature_k=300,
            component_mass_kg=1000,
            inventory_group_mass_kg=2000,
            detection="A",
            isolation="A",
            duration_hole="small",
            differential_pressure_pa=200000,
        )
    ).outputs
    assert output.representative_fluid == "Acid"
    assert output.release_phase == "liquid"
    assert output.personnel_area_m2 >= 0
    assert output.released_mass_kg >= 0


def test_level1_release_to_toxic_uses_theoretical_source_rate():
    from api581.api import level1
    output = level1.release_to_toxic(
        level1.ReleaseToToxicInput(
            source=Gas(
                diameter_m=0.0064,
                upstream_pressure_pa_abs=500000,
                downstream_pressure_pa_abs=101325,
                temperature_k=300,
                molecular_weight_kg_kmol=34,
                heat_capacity_ratio=1.3,
            ),
            operating_temperature_k=300,
            component_mass_kg=1000,
            inventory_group_mass_kg=2000,
            detection="A",
            isolation="A",
            duration_hole="small",
            fluid="h2s",
            release_phase="gas",
            toxic_mass_fraction=0.5,
            nonignition_probability=1.0,
        )
    ).outputs
    assert output.theoretical_rate_kg_s > 0
    assert output.toxic_rate_kg_s == pytest.approx(output.theoretical_rate_kg_s * 0.5)
    assert output.personnel_area_m2 >= 0


def test_level1_toxic_mixture_uses_largest_component_not_sum():
    from api581.api import level1
    output = level1.toxic_mixture_consequence(
        level1.ToxicMixtureConsequenceInput(
            components=[
                {"component_id": "h2s", "personnel_area_m2": 120.0},
                {"component_id": "hf", "personnel_area_m2": 80.0},
            ]
        )
    ).outputs
    assert output.personnel_area_m2 == 120.0
    assert output.critical_component_id == "h2s"
    assert output.component_count == 2
    assert output.component_areas_m2 == {"h2s": 120.0, "hf": 80.0}


def test_level1_toxic_hole_summary_maxes_components_then_gff_weights():
    from api581.api import level1
    cases = []
    for hole, frequency, area in [
        ("small", 1.0, 10.0), ("medium", 2.0, 20.0),
        ("large", 3.0, 30.0), ("rupture", 4.0, 40.0),
    ]:
        cases.append({
            "hole": hole,
            "generic_frequency_per_year": frequency,
            "components": [
                {"component_id": "h2s", "personnel_area_m2": area},
                {"component_id": "hf", "personnel_area_m2": area / 2},
            ],
        })
    output = level1.toxic_hole_summary(
        level1.ToxicHoleSummaryInput(cases=cases)
    ).outputs
    assert output.total_generic_frequency_per_year == 10.0
    assert output.personnel_area_m2 == pytest.approx(30.0)
    assert output.by_hole_personnel_area_m2["rupture"] == 40.0


def test_level1_release_to_steam_composes_controlled_source_and_nfnt_area():
    from api581.api import level1
    output = level1.release_to_steam(
        level1.ReleaseToSteamInput(
            source=Gas(
                diameter_m=0.0064,
                upstream_pressure_pa_abs=500000,
                downstream_pressure_pa_abs=101325,
                temperature_k=450,
                molecular_weight_kg_kmol=18,
                heat_capacity_ratio=1.3,
            ),
            operating_temperature_k=450,
            component_mass_kg=1000,
            inventory_group_mass_kg=2000,
            detection="A",
            isolation="A",
            duration_hole="small",
        )
    ).outputs
    assert output.representative_fluid == "Steam"
    assert output.release_phase == "gas"
    assert output.equipment_area_m2 == 0
    assert output.personnel_area_m2 >= 0
