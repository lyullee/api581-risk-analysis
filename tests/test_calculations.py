"""Numerical boundary tests and independent physical invariants, not certification."""
import math
import pytest
from api581 import pof, release, effects, risk, thinning
from api581.core import evaluate, DomainError


def calc(id, **inputs):
    return evaluate(id, inputs)["outputs"]


@pytest.mark.parametrize("score,expected", [(0, 10), (500, 1), (1000, .1)])
def test_management_anchors(score, expected):
    assert calc("frequency/management-factor", score=score)["management_factor"] == pytest.approx(expected)


@pytest.mark.parametrize("component", sorted(pof.GFF))
def test_gff_balance(component):
    result = calc("frequency/generic", component_type=component)
    assert result["total_per_year"] == pytest.approx(math.fsum(result["by_hole_per_year"].values()))


def test_gff_does_not_silently_use_2008_hextube():
    with pytest.raises(DomainError):
        calc("frequency/generic", component_type="HEXTUBE")


def test_frequency_can_exceed_one_not_clipped():
    result = calc("frequency/adjusted", generic_frequency_per_year=.1, total_damage_factor=100, management_factor=2)
    assert result["annual_failure_frequency"] == 20
    assert calc("reliability/poisson-probability", annual_failure_frequency=20, duration_years=1)["period_failure_probability"] < 1


def test_damage_combination_local_general_and_lining():
    data = dict(thinning=8, lining=3, external=[2, 5], scc=[1, 7], htha=2, fatigue=4,
                brittle_fracture=1, temper_embrittlement=3, embrittlement_885f=2, sigma_embrittlement=1)
    local = calc("damage/combine", **data, thinning_external_distribution="local")
    general = calc("damage/combine", **data, thinning_external_distribution="general")
    assert local["governing_brittle"] == 3
    assert local["total_damage_factor"] == 21
    assert general["total_damage_factor"] == 24


def test_weibull_characteristic_life_and_inverse():
    result = calc("reliability/weibull", shape=3, characteristic_life_years=10, age_years=10)
    assert result["cumulative_failure_probability"] == pytest.approx(.6321205588285577)
    inverse = calc("reliability/weibull-quantile", shape=3, characteristic_life_years=10,
                   probability=result["cumulative_failure_probability"])
    assert inverse["age_years"] == pytest.approx(10)


def test_weibull_singular_origin_is_not_json_infinity():
    out = calc("reliability/weibull", shape=.5, characteristic_life_years=10, age_years=0)
    assert out["hazard_per_year"] is None
    assert out["hazard_singular_at_origin"]


def test_liquid_zero_pressure_difference_and_area_scaling():
    data = dict(diameter_m=.01, upstream_pressure_pa_abs=201325, density_kg_m3=1000)
    rate = calc("release/liquid", **data)["mass_rate_kg_s"]
    assert rate == pytest.approx(.677539648074, rel=1e-9)
    assert calc("release/liquid", **{**data, "diameter_m": .02})["mass_rate_kg_s"] == pytest.approx(4 * rate)
    assert calc("release/liquid", **{**data, "upstream_pressure_pa_abs": 101325})["mass_rate_kg_s"] == 0


def test_reverse_pressure_rejected():
    with pytest.raises(DomainError):
        calc("release/liquid", diameter_m=.01, upstream_pressure_pa_abs=90000, density_kg_m3=1000)


def test_gas_continuity_at_choking_boundary_and_zero_differential():
    k = 1.4
    transition = 101325 * ((k + 1) / 2) ** (k / (k - 1))
    data = dict(diameter_m=.01, temperature_k=300, molecular_weight_kg_kmol=28.0134, heat_capacity_ratio=k)
    low = calc("release/gas", **data, upstream_pressure_pa_abs=transition * (1 - 1e-8))
    high = calc("release/gas", **data, upstream_pressure_pa_abs=transition * (1 + 1e-8))
    assert low["regime"] == "subsonic" and high["regime"] == "sonic"
    assert low["mass_rate_kg_s"] == pytest.approx(high["mass_rate_kg_s"], rel=1e-6)
    assert calc("release/gas", **data, upstream_pressure_pa_abs=101325)["mass_rate_kg_s"] == 0


def test_inventory_is_limited_by_group_and_8inch_supply():
    out = calc("release/available-inventory", component_mass_kg=100, inventory_group_mass_kg=1000,
               release_rate_kg_s=10, eight_inch_rate_kg_s=2)
    assert out == {"added_mass_kg": 360, "available_mass_kg": 460}


@pytest.mark.parametrize("diameter,mass,rate,expected", [(.00635, 10000, 100, "continuous"),
    (.01, 4536, 100, "continuous"), (.01, 5000, 25.2, "instantaneous"), (.01, 5000, 0, "continuous")])
def test_release_type_edges(diameter, mass, rate, expected):
    assert calc("release/type", diameter_m=diameter, available_mass_kg=mass, theoretical_rate_kg_s=rate)["release_type"] == expected


def test_magnitude_mass_conservation_and_seconds():
    out = calc("release/magnitude", theoretical_rate_kg_s=10, reduction_fraction=.2, available_mass_kg=100, maximum_duration_s=20)
    assert out == {"adjusted_rate_kg_s": 8, "duration_s": 12.5, "released_mass_kg": 100}


def test_transient_triangle_integral_and_inventory_rejection():
    points = [{"time_s": 0, "rate_kg_s": 0}, {"time_s": 10, "rate_kg_s": 10}, {"time_s": 20, "rate_kg_s": 0}]
    assert calc("release/integrate-profile", points=points, available_mass_kg=100)["released_mass_kg"] == 100
    with pytest.raises(DomainError):
        calc("release/integrate-profile", points=points, available_mass_kg=99)


def test_jet_energy_threshold_and_inverse_square():
    power = calc("effects/jet-fire-power", mass_rate_kg_s=10, heat_of_combustion_j_kg=46e6)["radiated_power_w"]
    assert power == 161e6
    result = calc("effects/jet-fire-distance", radiated_power_w=power, threshold_w_m2=12600,
                  transmissivity_model="constant", atmospheric_transmissivity=.8)
    assert result["consequence_area_m2"] == pytest.approx(2555.555555555556)
    flux = calc("effects/jet-fire-flux", radiated_power_w=power, distance_m=result["threshold_distance_m"], atmospheric_transmissivity=.8)
    assert flux["received_flux_w_m2"] == pytest.approx(12600)


def test_jet_distance_water_vapor_root_residual():
    out = calc("effects/jet-fire-distance", radiated_power_w=1e8, threshold_w_m2=12600,
               transmissivity_model="api_water_vapor", water_partial_pressure_pa=1500)
    flux = out["transmissivity_at_distance"] * 1e8 / (4 * math.pi * out["threshold_distance_m"] ** 2)
    assert flux == pytest.approx(12600)


@pytest.mark.parametrize("phase,kind,event", [("vapor", "continuous", "jet_fire"),
    ("vapor", "instantaneous", "fireball"), ("liquid", "continuous", "pool_fire")])
def test_event_tree_conserves_probability(phase, kind, event):
    out = calc("events/leakage-tree", phase=phase, release_type=kind, ignition_probability=.4,
               immediate_given_ignition=.25, vce_given_delayed=.2)
    assert out["probability_sum"] == pytest.approx(1)
    assert out["terminal_probabilities"][event] == pytest.approx(.1)
    assert out["terminal_probabilities"]["vce"] == pytest.approx(.06)


def test_bayesian_posterior_matches_hand_calculation():
    # Low prior * A likelihood = (.45, .027, .002), normalization = .479.
    out = calc("damage/thinning-posterior", confidence="low", inspections_a=1)
    assert out["posterior_probabilities"] == pytest.approx([.45 / .479, .027 / .479, .002 / .479])
    large = calc("damage/thinning-posterior", confidence="low", inspections_a=10000)
    assert sum(large["posterior_probabilities"]) == pytest.approx(1)


def test_thinning_base_reference_at_equal_stress_capacity():
    # Art=0, SR=1 => all three limit-state means are zero: each Phi(0)=0.5.
    out = calc("damage/thinning-base", wall_loss_fraction=0, strength_ratio=1, posterior=[.5, .3, .2])
    assert out["reliability_indices"] == [0, 0, 0]
    assert out["base_damage_factor"] == pytest.approx(.5 / 1.56e-4)


def test_thinning_increases_with_wall_loss():
    data = dict(strength_ratio=.3, posterior=[.5, .3, .2])
    values = [calc("damage/thinning-base", **data, wall_loss_fraction=a)["base_damage_factor"] for a in [0, .1, .2, .3]]
    assert values == sorted(values)


def test_integrated_risk_matches_weighted_consequence_without_double_weight():
    holes = [dict(hole=h, equipment_area_m2=100, personnel_area_m2=200, financial_consequence=1e6) for h in pof.HOLES]
    out = calc("risk/assessment", component_type="PIPE-8", management_score=500, total_damage_factor=10,
               damage_factor_source="test", consequences=holes, consequence_source="test", currency="KRW")
    assert out["risk"]["annual_failure_frequency"] == pytest.approx(3.06e-4)
    assert out["risk"]["financial_risk_per_year"] == pytest.approx(306)
    assert out["risk"]["personnel_area_risk_m2_per_year"] == pytest.approx(.0612)


def test_missing_hole_and_duplicate_scenarios_rejected():
    scenarios = [dict(scenario_id="same", annual_failure_frequency=.1, equipment_area_m2=1, personnel_area_m2=1, financial_consequence=1)] * 2
    with pytest.raises(DomainError):
        calc("risk/aggregate", scenarios=scenarios, currency="KRW")


def test_risk_portfolio_aggregates_disjoint_component_rows():
    out = calc(
        "risk/portfolio",
        components=[
            {"component_id": "V-101", "annual_failure_frequency": 1e-4,
             "equipment_area_risk_m2_per_year": 0.2,
             "personnel_area_risk_m2_per_year": 0.3,
             "financial_risk_per_year": 1000.0},
            {"component_id": "P-201", "annual_failure_frequency": 2e-4,
             "equipment_area_risk_m2_per_year": 0.1,
             "personnel_area_risk_m2_per_year": 0.4,
             "financial_risk_per_year": 2000.0},
        ],
        currency="KRW",
        disjointness_basis="component release scenarios are partitioned by owner event IDs",
    )
    assert out["component_count"] == 2
    assert out["annual_failure_frequency"] == pytest.approx(3e-4)
    assert out["area_risk_m2_per_year"] == pytest.approx(0.7)
    assert out["financial_risk_per_year"] == pytest.approx(3000.0)
    assert out["component_contributions"]["P-201"]["financial_risk_per_year"] == pytest.approx(2000.0)


def test_risk_portfolio_rejects_duplicate_component_ids():
    with pytest.raises(DomainError, match="Duplicate component_id"):
        calc(
            "risk/portfolio",
            components=[
                {"component_id": "V-101", "annual_failure_frequency": 1e-4,
                 "equipment_area_risk_m2_per_year": 0.0,
                 "personnel_area_risk_m2_per_year": 0.0,
                 "financial_risk_per_year": 0.0},
                {"component_id": "V-101", "annual_failure_frequency": 1e-4,
                 "equipment_area_risk_m2_per_year": 0.0,
                 "personnel_area_risk_m2_per_year": 0.0,
                 "financial_risk_per_year": 0.0},
            ],
            currency="KRW",
            disjointness_basis="owner partition",
        )


def test_first_crossing_on_nonmonotone_curve():
    out = calc("planning/target-crossing", points=[{"time_years": t, "value": r} for t, r in [(0, 1), (1, 3), (2, 0)]],
               target=2, metric="financial_per_year")
    assert out["crossing_years"] == .5
