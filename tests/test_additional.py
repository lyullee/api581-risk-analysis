import math
import pytest
from api581 import evaluate, DomainError


def c(id, **kwargs):
    return evaluate(id, kwargs)["outputs"]


def test_inspection_equivalence_does_not_discard_lower_grades():
    out = c("inspection/equivalent", mechanism="scc", a=0, b=1, c=1, d=3)
    assert out == {"a": 1, "b": 0, "c": 0, "d": 1}


def test_mttf_conversion_exponential_anchor():
    assert c("reliability/weibull-from-mttf", shape=1, mean_life_years=10)["characteristic_life_years"] == 10


def test_orifice_and_heat_capacity():
    assert c("release/orifice-area", diameter_m=2)["area_m2"] == pytest.approx(math.pi)
    assert c("properties/heat-capacity-ratio", cp_j_mol_k=3.5 * 8.31446261815324)["heat_capacity_ratio"] == pytest.approx(1.4)
    assert 0 < c("release/viscosity-factor", reynolds_number=100)["viscosity_factor"] < 1


def test_mixture_mass_fraction_balance():
    out = c("properties/mixture-molecular-weight", components=[{"mole_fraction": .5, "molecular_weight_kg_kmol": 2},
                                                               {"mole_fraction": .5, "molecular_weight_kg_kmol": 18}])
    assert out["molecular_weight_kg_kmol"] == 10
    assert out["mass_fractions"] == pytest.approx([.1, .9])


def test_flash_fire_criteria():
    assert c("effects/flash-fire", area_within_lfl_m2=400) == {"personnel_area_m2": 400, "equipment_area_m2": 100}


def test_pool_site_limit_and_burning_rate():
    rate = c("effects/pool-burning-rate", heat_of_combustion_j_kg=40e6, latent_heat_j_kg=400000, boiling=True)
    assert rate["burning_rate_kg_m2_s"] == pytest.approx(.1481)
    out = c("effects/pool-fire-area", liquid_rate_kg_s=1, burning_rate_kg_m2_s=.1,
            available_liquid_mass_kg=1000, density_kg_m3=1000, site_maximum_area_m2=5)
    assert out["pool_area_m2"] == 5
    assert math.pi * out["pool_radius_m"] ** 2 == pytest.approx(5)


def test_pool_nonboiling_sensible_heat_reduces_burning_rate():
    out = c("effects/pool-burning-rate", heat_of_combustion_j_kg=40e6, latent_heat_j_kg=400000, boiling=False,
            specific_heat_j_kg_k=2000, boiling_temperature_k=400, ambient_temperature_k=300)
    assert out["burning_rate_kg_m2_s"] == pytest.approx(.001481 * 40e6 / 600000)


def test_fireball_branch_and_energy_balance():
    out = c("effects/fireball-geometry", flammable_mass_kg=1)
    assert out == {"diameter_m": 5.8, "center_height_m": 4.35, "duration_s": .45}
    large = c("effects/fireball-geometry", flammable_mass_kg=30000)
    assert large["duration_s"] == pytest.approx(2.6 * 30000 ** .167)
    emissive = c("effects/fireball-emissive-power", flammable_mass_kg=1, heat_of_combustion_j_kg=40e6,
                 radiative_fraction=.3, diameter_m=5.8, duration_s=.45)["surface_emissive_power_w_m2"]
    assert emissive * math.pi * 5.8 ** 2 * .45 == pytest.approx(12e6)
    assert c("effects/fireball-radiative-fraction", burst_pressure_pa_abs=1e6)["radiative_fraction"] == pytest.approx(.0296 * 1000 ** .32)


def test_tnt_mass_energy_equivalence_without_implicit_heat_constant():
    out = c("effects/vce-tnt-equivalence", flammable_cloud_mass_kg=100, combustion_heat_j_kg=46e6,
            explosion_yield=.03, tnt_heat_j_kg=4.648e6, tnt_heat_source="independent test basis")
    assert out["tnt_equivalent_mass_kg"] * 4.648e6 == pytest.approx(138e6)


def test_toxic_probit_zero_and_median():
    kwargs = dict(intercept=5, slope=1, concentration_exponent=1, concentration=1,
                  exposure_duration=1, concentration_unit="test", duration_unit="test", coefficient_source="test")
    assert c("effects/toxic-probit", **kwargs)["effect_probability"] == pytest.approx(.5)
    assert c("effects/toxic-probit", **{**kwargs, "concentration": 0})["effect_probability"] == 0


def test_empirical_area_coefficient_source_preserved():
    out = c("consequence/power-law-area", coefficient_a=2, exponent_b=2, release_magnitude=3,
            magnitude_unit="kg/s", coefficient_source="test SI coefficients")
    assert out["area_m2"] == 18 and out["coefficient_source"] == "test SI coefficients"


def test_expected_consequence_and_financial_sum():
    out = c("consequence/expected", outcomes=[dict(event_id="fire", probability=.25, equipment_area_m2=400, personnel_area_m2=800, financial_consequence=100),
            dict(event_id="safe", probability=.75, equipment_area_m2=0, personnel_area_m2=0, financial_consequence=0)], currency="KRW")
    assert out["equipment_area_m2"] == 100 and out["financial_consequence"] == 25
    costs = c("consequence/financial-total", component_repair_cost=1, surrounding_equipment_cost=2, business_interruption_cost=3,
              injury_cost=4, environmental_cost=5, currency="KRW", cost_basis_year=2026)
    assert costs["financial_consequence"] == 15


def test_risk_matrix_boundary_policy_and_invalid_dimensions():
    data = dict(frequency_per_year=.1, consequence=10, frequency_boundaries=[.1], consequence_boundaries=[10],
                risk_cells=[["low", "medium"], ["medium", "high"]], policy_id="test")
    assert c("risk/matrix", **data)["risk_label"] == "high"
    with pytest.raises(DomainError):
        c("risk/matrix", **{**data, "risk_cells": [["low"]]})


def test_strength_and_thinning_composition():
    fs = c("damage/flow-stress", yield_strength_pa=200e6, tensile_strength_pa=400e6, weld_efficiency=1)["flow_stress_pa"]
    assert fs == pytest.approx(330e6)
    out = c("damage/thinning-unclad", wall=dict(starting_thickness_m=.01, corrosion_rate_m_year=.0001, elapsed_years=10),
            strength=dict(differential_pressure_pa=1e6, diameter_m=1, flow_stress_pa=fs, starting_thickness_m=.01, shape="cylinder"),
            inspections=dict(confidence="low", inspections_a=1), injection_point_factor=1, deadleg_factor=1, online_monitoring_factor=1)
    assert out["wall_loss_fraction"] == pytest.approx(.1)
    assert out["thinning_damage_factor"] >= .1
    assert len(out["reliability_indices"]) == 3


def test_scc_lookup_known_cells_and_monotonic_inspection_benefit():
    assert c("damage/scc-base", severity_index=5000, inspection_grade="A", inspection_count=6)["base_damage_factor"] == 1
    assert c("damage/scc-base", severity_index=5000, inspection_grade="C", inspection_count=1)["base_damage_factor"] == 1670
    values = [c("damage/scc-base", severity_index=1000, inspection_grade="B", inspection_count=n)["base_damage_factor"] for n in range(1, 7)]
    assert values == sorted(values, reverse=True)
    with pytest.raises(DomainError, match="ambiguous"):
        c("damage/scc-base", severity_index=500, inspection_grade="E", inspection_count=0)


def test_caustic_escalation_and_lining_adjustment():
    assert c("damage/caustic-severity", susceptibility="high")["severity_index"] == 5000
    assert c("damage/caustic-escalation", base_damage_factor=50, years_since_qualifying_inspection=.5)["damage_factor"] == 50
    assert c("damage/caustic-escalation", base_damage_factor=50, years_since_qualifying_inspection=10)["damage_factor"] == pytest.approx(629.4627058970838)
    out = c("damage/lining-adjust", base_damage_factor=10, condition="poor", effective_online_monitoring=True)
    assert out["lining_damage_factor"] == 10
