"""High-precision source polynomial, scaling laws and bounded inversion."""
import math
from decimal import Decimal, localcontext
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import effects


def domain(first=1.5,last=1000,basis="Illustrative numerical interval; engineering applicability not validated"):
    return effects.BlastFitDomainInput(minimum_scaled_distance_m_kg13=first,
        maximum_scaled_distance_m_kg13=last,engineering_basis=basis)


def decimal_source_pressure(scaled):
    # Independent direct sum at80 digits, including natural logarithm and SI conversion.
    values=['-.059965896','1.1288697','-7.9625216','25.106738','-30.396707',
            '19.399862','-6.8853477','1.2825511','-.097705789']
    with localcontext() as ctx:
        ctx.prec=80
        logarithm=Decimal(str(scaled)).ln()
        return float(Decimal(100000)*sum(Decimal(value)/logarithm**i for i,value in enumerate(values)))


@pytest.mark.parametrize("scaled",[1.5,2,5,10,100,1000])
def test_pressure_matches_high_precision_printed_inverse_log_polynomial(scaled):
    result=effects.vce_scaled_overpressure(effects.VceScaledOverpressureInput(
        scaled_distance_m_kg13=scaled,fit_domain=domain())).outputs
    assert result.side_on_overpressure_pa == pytest.approx(decimal_source_pressure(scaled),rel=1e-9)
    assert result.slope_pa_per_scaled_distance < 0
    if scaled == 10:
        assert result.side_on_overpressure_pa == pytest.approx(16083.410137,abs=.001)


def test_hopkinson_mass_scaling_and_physical_distance_composition():
    for mass,distance in [(1,10),(8,20),(125,50)]:
        scaled=effects.vce_scaled_distance(effects.VceScaledDistanceInput(distance_m=distance,tnt_equivalent_mass_kg=mass)).outputs
        result=effects.vce_blast_overpressure(effects.VceBlastOverpressureInput(distance_m=distance,
            tnt_equivalent_mass_kg=mass,fit_domain=domain())).outputs
        assert scaled.scaled_distance_m_kg13 == pytest.approx(10)
        assert result.scaled_distance_m_kg13 == pytest.approx(10)
        assert result.side_on_overpressure_pa == pytest.approx(decimal_source_pressure(10))


@pytest.mark.parametrize("first,last",[(1,100),(.5,100),(5,2),(2,2),(1.2,100),(1.32,100),(1.35,100),(2,10000)])
def test_singular_negative_nonmonotone_or_reversed_fit_domains_rejected(first,last):
    with pytest.raises(DomainError) as exc:
        effects.vce_scaled_overpressure(effects.VceScaledOverpressureInput(
            scaled_distance_m_kg13=5,fit_domain=domain(first,last)))
    assert exc.value.code == "invalid_blast_fit_domain"


@pytest.mark.parametrize("scaled",[1.4,1001])
def test_outside_caller_fit_domain_rejected(scaled):
    with pytest.raises(DomainError) as exc:
        effects.vce_scaled_overpressure(effects.VceScaledOverpressureInput(
            scaled_distance_m_kg13=scaled,fit_domain=domain()))
    assert exc.value.code == "outside_blast_fit_domain"


def test_caller_domain_and_nonblank_basis_are_required():
    with pytest.raises(ValidationError):
        effects.VceScaledOverpressureInput(scaled_distance_m_kg13=5)
    with pytest.raises(DomainError):
        effects.vce_scaled_overpressure(effects.VceScaledOverpressureInput(scaled_distance_m_kg13=5,fit_domain=domain(basis="  ")))


@pytest.mark.parametrize("target",[.01,.5,.99])
def test_building_probit_and_inverse_probability(target):
    pressure=effects.blast_building_pressure_threshold(effects.BlastBuildingPressureThresholdInput(
        building_collapse_probability=target)).outputs
    result=effects.blast_building_probit(effects.BlastBuildingProbitInput(
        side_on_overpressure_pa=pressure.side_on_overpressure_pa)).outputs
    assert result.building_collapse_probability == pytest.approx(target,abs=1e-14)
    assert result.probit == pytest.approx(pressure.probit)
    if target == .5:
        assert pressure.probit == 5
        assert pressure.side_on_overpressure_pa == pytest.approx(math.exp(28.8/2.92))


@pytest.mark.parametrize("target",[0,1])
def test_finite_pressure_threshold_requires_probability_strictly_inside_unit_interval(target):
    with pytest.raises(DomainError):
        effects.blast_building_pressure_threshold(effects.BlastBuildingPressureThresholdInput(building_collapse_probability=target))


def test_blast_inverse_distance_is_safe_and_matches_high_precision_target():
    threshold=decimal_source_pressure(10)
    answer=effects.vce_blast_distance(effects.VceBlastDistanceInput(tnt_equivalent_mass_kg=125,
        threshold_overpressure_pa=threshold,fit_domain=domain(),distance_tolerance_m=1e-7)).outputs
    assert answer.safe_distance_m == pytest.approx(50,abs=1e-7)
    assert answer.consequence_area_m2 == pytest.approx(math.pi*50**2,rel=1e-8)
    assert answer.status == "threshold_solved"
    assert answer.pressure_residual_pa <= 0
    result=effects.vce_blast_overpressure(effects.VceBlastOverpressureInput(tnt_equivalent_mass_kg=125,
        distance_m=answer.safe_distance_m,fit_domain=domain())).outputs
    assert result.side_on_overpressure_pa <= threshold


def test_blast_distance_and_area_mass_scaling_laws():
    values=[]
    for mass in [1,8]:
        values.append(effects.vce_blast_distance(effects.VceBlastDistanceInput(tnt_equivalent_mass_kg=mass,
            threshold_overpressure_pa=34500,fit_domain=domain(),distance_tolerance_m=1e-8)).outputs)
    assert values[1].safe_distance_m == pytest.approx(2*values[0].safe_distance_m,abs=2e-8)
    assert values[1].consequence_area_m2 == pytest.approx(4*values[0].consequence_area_m2,rel=1e-8)


@pytest.mark.parametrize("threshold",[1,1e7])
def test_out_of_bracket_pressure_does_not_extrapolate(threshold):
    with pytest.raises(DomainError) as exc:
        effects.vce_blast_distance(effects.VceBlastDistanceInput(tnt_equivalent_mass_kg=10,
            threshold_overpressure_pa=threshold,fit_domain=domain()))
    assert exc.value.code == "unbracketed_threshold"


def test_inverse_iteration_failure_is_explicit():
    with pytest.raises(DomainError) as exc:
        effects.vce_blast_distance(effects.VceBlastDistanceInput(tnt_equivalent_mass_kg=10,
            threshold_overpressure_pa=34500,fit_domain=domain(),maximum_iterations=10,distance_tolerance_m=1e-12))
    assert exc.value.code == "nonconvergent_threshold"


@pytest.mark.parametrize("scaled",[1.5,1000])
def test_exact_endpoint_thresholds_are_accepted(scaled):
    pressure=effects.vce_scaled_overpressure(effects.VceScaledOverpressureInput(scaled_distance_m_kg13=scaled,fit_domain=domain())).outputs.side_on_overpressure_pa
    result=effects.vce_blast_distance(effects.VceBlastDistanceInput(tnt_equivalent_mass_kg=1,
        threshold_overpressure_pa=pressure,fit_domain=domain())).outputs
    assert result.safe_distance_m == scaled
    assert result.iterations == 0
    assert result.pressure_residual_pa == 0


def request(**updates):
    values=dict(flammable_cloud_mass_kg=1000,combustion_heat_j_kg=46e6,explosion_yield=.03,
        tnt_heat_j_kg=4.648e6,tnt_heat_source="Caller-qualified illustrative4.648MJ/kg; not silently copied from inconsistent SI text",
        mass_basis="total_released_flammable",yield_engineering_basis="Illustrative hydrocarbon total-release basis, source5.8.5.4",
        personnel_building_collapse_probability=.5,fit_domain=domain())
    return effects.VceBlastConsequenceInput(**(values|updates))


def test_consequence_composes_tnt_equivalence_probit_and_both_distances():
    result=effects.vce_blast_consequence(request()).outputs
    assert result.tnt_equivalent_mass_kg == pytest.approx(.03*1000*46e6/4.648e6)
    for label,pressure in [("personnel",result.personnel_threshold_overpressure_pa),("equipment",34500)]:
        distance=effects.vce_blast_distance(effects.VceBlastDistanceInput(tnt_equivalent_mass_kg=result.tnt_equivalent_mass_kg,
            threshold_overpressure_pa=pressure,fit_domain=domain())).outputs
        assert getattr(result,label+"_area_m2") == distance.consequence_area_m2
        assert getattr(result,label+"_safe_distance_m") == distance.safe_distance_m
    assert result.personnel_area_m2 > result.equipment_area_m2 > 0
    assert result.mass_basis == "total_released_flammable"


@pytest.mark.parametrize("updates",[{"flammable_cloud_mass_kg":0},{"explosion_yield":0}])
def test_zero_mass_or_yield_returns_no_explosion(updates):
    result=effects.vce_blast_consequence(request(**updates)).outputs
    assert result.personnel_status == result.equipment_status == "no_explosion"
    assert result.personnel_area_m2 == result.equipment_area_m2 == 0


def test_underflow_is_not_reported_as_absent_explosion():
    with pytest.raises(DomainError) as exc:
        effects.vce_blast_consequence(request(flammable_cloud_mass_kg=1e-300,explosion_yield=1e-300))
    assert exc.value.code == "numerical_failure"


def test_scaled_distance_rejects_numerical_overflow():
    with pytest.raises(DomainError) as exc:
        effects.vce_scaled_distance(effects.VceScaledDistanceInput(distance_m=1e308,tnt_equivalent_mass_kg=1e-300))
    assert exc.value.code == "numerical_failure"


def test_vce_default_personnel_target_matches_step8_14_probit5():
    inputs=effects.VceBlastConsequenceInput(**request().model_dump(exclude={"personnel_building_collapse_probability"}))
    result=effects.vce_blast_consequence(inputs).outputs
    assert result.personnel_building_collapse_probability == .5
    assert result.personnel_threshold_overpressure_pa == pytest.approx(math.exp(28.8/2.92))
