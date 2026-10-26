import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import level1, release


def area(**changes):
    data=dict(fluid="CO",release_phase="gas",effect="equipment",release_type="continuous",
        autoignition="not_likely",adjusted_rate_kg_s=10,released_mass_kg=1000,mitigation_fraction=0)
    return level1.type1_flammable_area(level1.Type1FlammableAreaInput(**{**data,**changes})).outputs


@pytest.mark.parametrize("fluid,equipment_a,personnel_a", [("Aromatics",3.952,12.76),("Styrene",3.952,12.76),
    ("CO",.040,5.491),("DEE",9.072,26.76),("Methanol",.005,0),("PO",3.277,8.239),
    ("EEA",0,0),("EE",2.595,7.107),("EG",1.548,5.042),("EO",6.712,11)])
def test_all_ten_type1_continuous_gas_si_anchors(fluid,equipment_a,personnel_a):
    assert area(fluid=fluid,adjusted_rate_kg_s=1).area_m2 == equipment_a
    assert area(fluid=fluid,adjusted_rate_kg_s=1,effect="personnel").area_m2 == personnel_a


def test_type1_high_continuous_rate_does_not_blend_to_instantaneous():
    result=area(adjusted_rate_kg_s=100,released_mass_kg=1e6)
    assert result.area_m2 == pytest.approx(.040*100**1.752)
    assert result.energy_efficiency_factor == 1
    # The distinct instantaneous relation must not enter the continuous value.
    assert result.area_m2 != pytest.approx(10.97*1e6**.667)


def test_type1_instantaneous_energy_correction_and_mitigation_applied_once():
    result=area(release_type="instantaneous",released_mass_kg=10000,mitigation_fraction=.2)
    correction=4*math.log10(2.205*10000)-15
    assert result.area_m2 == pytest.approx(10.97*10000**.667*.8/correction)
    assert result.energy_efficiency_factor == pytest.approx(correction)


def test_blank_equipment_cell_does_not_disable_valid_personnel_calculation():
    with pytest.raises(DomainError) as error:
        area(fluid="Aromatics",release_phase="liquid",autoignition="likely")
    assert error.value.code == "unsupported_table_cell"
    assert area(fluid="Aromatics",release_phase="liquid",autoignition="likely",effect="personnel").area_m2 == pytest.approx(56*10**.268)
    assert area(fluid="Methanol",effect="personnel").area_m2 == 0  # printed zero, not blank.


def test_type1_native_table_lookup_and_type0_separation():
    cell=level1.flammable_coefficients(level1.FlammableCoefficientsInput(fluid="DEE",release_phase="liquid",
        effect="equipment",release_type="instantaneous",autoignition="likely")).outputs
    assert cell.a == 1.090 and cell.b == .919
    with pytest.raises(DomainError):
        level1.flammable_area(level1.FlammableAreaInput(fluid="CO",release_phase="gas",release_type="continuous",
            adjusted_rate_kg_s=1,released_mass_kg=100,operating_temperature_k=300,autoignition_temperature_k=600,mitigation_fraction=0))
    with pytest.raises(ValidationError):
        level1.Type1FlammableAreaInput(fluid="CO",release_phase="gas",effect="equipment",release_type="continuous",
            autoignition="not_likely",adjusted_rate_kg_s=1,released_mass_kg=100,mitigation_fraction=0,instantaneous_weight=.5)


def test_pyrophoric_type0_lookup_is_available():
    result=level1.flammable_coefficients(level1.FlammableCoefficientsInput(fluid="Pyrophoric",release_phase="liquid",
        effect="equipment",release_type="continuous",autoignition="likely")).outputs
    assert result.a == 110.3 and result.b == .95


def test_controlled_source_to_type1_consequence_without_unused_ait_input():
    source=release.GasInput(diameter_m=.0254,upstream_pressure_pa_abs=1e6,temperature_k=300,
        molecular_weight_kg_kmol=28,heat_capacity_ratio=1.4)
    controls=dict(source=source,operating_temperature_k=300,component_mass_kg=1000,inventory_group_mass_kg=2000,
        detection="A",isolation="A",duration_hole="medium")
    controlled=release.controlled_scenario(release.ControlledScenarioInput(**controls)).outputs
    result=level1.release_to_type1_flammable(level1.ReleaseToType1FlammableInput(**controls,
        fluid="CO",final_release_phase="gas",autoignition="not_likely",mitigation_fraction=0)).outputs
    assert result.release_type == "continuous"
    assert result.adjusted_rate_kg_s == pytest.approx(.75*result.theoretical_rate_kg_s)
    assert result.adjusted_rate_kg_s == controlled.adjusted_rate_kg_s
    assert result.equipment_area_m2 == pytest.approx(.040*result.adjusted_rate_kg_s**1.752)
    assert result.personnel_area_m2 == pytest.approx(5.491*result.adjusted_rate_kg_s**.991)
    assert result.fluid_type == 1
