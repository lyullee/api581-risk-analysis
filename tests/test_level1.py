import math
import pytest
from api581 import evaluate, DomainError
from api581.level1 import COEFFICIENTS


def c(id, **kwargs):
    return evaluate(id, kwargs)["outputs"]


@pytest.mark.parametrize("fluid", list(COEFFICIENTS))
def test_all_populated_table_cells_have_valid_contracts(fluid):
    for phase, row in COEFFICIENTS[fluid].items():
        for i, pair in enumerate(row):
            args = dict(fluid=fluid, release_phase=phase, effect="personnel" if i >= 4 else "equipment",
                        release_type="instantaneous" if i%4 >= 2 else "continuous", autoignition="likely" if i%2 else "not_likely")
            if pair is None:
                with pytest.raises(DomainError): c("level1/flammable-coefficients", **args)
            else:
                out = c("level1/flammable-coefficients", **args)
                assert (out["a"],out["b"]) == pair


@pytest.mark.parametrize("d,i,f", [("A","A",.25),("A","B",.2),("A","C",.1),("B","B",.15),("B","C",.1),("C","C",0)])
def test_detection_table_anchors(d,i,f):
    assert c("release/detection-reduction", detection=d,isolation=i)["reduction_fraction"] == f


def test_undefined_reduction_not_invented():
    assert c("release/detection-reduction", detection="B",isolation="A")["reduction_fraction"] == .10


def test_detection_minutes_are_converted_to_seconds():
    assert c("release/detection-duration",detection="A",isolation="A",hole="small")["maximum_duration_s"] == 1200
    assert c("release/detection-duration",detection="C",isolation="A",hole="medium")["maximum_duration_s"] == 2400


def test_phase_override_and_boiling_boundary():
    assert c("level1/release-phase",stored_phase="gas",ambient_phase="liquid",normal_boiling_point_k=400)["release_phase"] == "gas"
    assert c("level1/release-phase",stored_phase="liquid",ambient_phase="gas",normal_boiling_point_k=299)["release_phase"] == "gas"
    assert c("level1/release-phase",stored_phase="liquid",ambient_phase="gas",normal_boiling_point_k=301)["release_phase"] == "liquid"


@pytest.mark.parametrize("temperature,expected", [(744.4,0),(800,.5),(855.6,1),(900,1)])
def test_ait_blend_boundaries(temperature,expected):
    out=c("level1/blending-factors",release_type="continuous",adjusted_rate_kg_s=12.6,instantaneous_coefficients_available=True,
          operating_temperature_k=temperature,autoignition_temperature_k=800)
    assert out["instantaneous_weight"] == .5
    assert out["autoignition_likely_weight"] == pytest.approx(expected,abs=1e-14)


def test_energy_efficiency_threshold():
    assert c("level1/energy-efficiency",released_mass_kg=4536)["energy_efficiency_factor"] == 1
    assert c("level1/energy-efficiency",released_mass_kg=10000)["energy_efficiency_factor"] == pytest.approx(4*math.log10(22050)-15)


def test_blended_area_independent_arithmetic_anchor():
    # C3-C4 continuous rate 12.6: IC=0.5, AIT=0, mass=100 -> no efficiency correction.
    out=c("level1/flammable-area",fluid="C3-C4",release_phase="gas",release_type="continuous",adjusted_rate_kg_s=12.6,
          released_mass_kg=100,operating_temperature_k=300,autoignition_temperature_k=800,mitigation_fraction=.2)
    assert out["equipment_area_m2"] == pytest.approx(.8*(.5*10.13*12.6+.5*4.590*100**.72))
    assert out["personnel_area_m2"] == pytest.approx(.8*(.5*25.64*12.6+.5*9.702*100**.75))


def test_instantaneous_area_does_not_use_continuous_rate():
    kwargs=dict(fluid="H2",release_phase="gas",release_type="instantaneous",adjusted_rate_kg_s=10,
                released_mass_kg=10000,operating_temperature_k=1000,autoignition_temperature_k=800,mitigation_fraction=0)
    a=c("level1/flammable-area",**kwargs)
    b=c("level1/flammable-area",**{**kwargs,"adjusted_rate_kg_s":100})
    assert a==b
    assert a["equipment_area_m2"] == pytest.approx(216.5*10000**.618/(4*math.log10(22050)-15))


def test_zero_release_and_blank_required_cell():
    kwargs=dict(fluid="C5",release_phase="liquid",release_type="continuous",adjusted_rate_kg_s=0,
                released_mass_kg=0,operating_temperature_k=300,autoignition_temperature_k=800,mitigation_fraction=0)
    assert c("level1/flammable-area",**kwargs)["equipment_area_m2"]==0
    with pytest.raises(DomainError): c("level1/flammable-area",**{**kwargs,"operating_temperature_k":800})


def test_composed_source_to_cof_matches_independent_steps():
    data=dict(source=dict(diameter_m=.0254,upstream_pressure_pa_abs=1e6,temperature_k=300,molecular_weight_kg_kmol=23,heat_capacity_ratio=1.3),
              fluid="C1-C2",final_release_phase="gas",operating_temperature_k=300,autoignition_temperature_k=831.15,
              component_mass_kg=100,inventory_group_mass_kg=1000,detection="A",isolation="A",duration_hole="medium",mitigation_fraction=.2)
    result=c("level1/release-to-flammable",**data)
    source=c("release/gas",**data["source"])
    assert result["theoretical_rate_kg_s"]==source["mass_rate_kg_s"]
    assert result["adjusted_rate_kg_s"]==pytest.approx(source["mass_rate_kg_s"]*.75)
    assert result["maximum_duration_s"]==600
    assert result["released_mass_kg"]<=result["available_mass_kg"]<=1000
    direct=c("level1/flammable-area",fluid="C1-C2",release_phase="gas",release_type=result["release_type"],
             adjusted_rate_kg_s=result["adjusted_rate_kg_s"],released_mass_kg=result["released_mass_kg"],
             operating_temperature_k=300,autoignition_temperature_k=831.15,mitigation_fraction=.2)
    assert result["equipment_area_m2"]==direct["equipment_area_m2"]
    with pytest.raises(DomainError): c("level1/release-to-flammable",**{**data,"duration_hole":"small"})
