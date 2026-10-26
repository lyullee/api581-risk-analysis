"""AST per-hole normalization, financial composition and uniform-DF risk anchors."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import tank, frequency


def common(component):
    gff = tank.generic_frequency(tank.GenericFrequencyInput(component_type=component)).outputs
    return dict(generic_frequency_by_hole_per_year=gff.by_hole_per_year,
        generic_frequency_source="Part2 Table3.1; total eq3.208",
        cost_by_location_per_bbl=dict(in_dike=10.,surface_on_site=50.,surface_off_site=250.,
            subsoil=1500.,groundwater=5000.,surface_water=1500.),
        fraction_leaving_dike=.8,fraction_on_site=.25,fraction_off_site=.5,
        currency="USD",cost_basis="Qualified fixture valuation in 2026 USD; illustrative prices",
        repair=dict(material_id="carbon_steel",price_factor_since_2001=2.,usd_to_output_currency=1.,cost_basis_year=2026),
        outage_multiplier=1.,production_cost_per_day=1000.)


def bottom():
    return tank.BottomFinancialConsequenceInput(**common("TANKBOTTOM"),tank_diameter_m=61,
        leaked_volume_by_hole_bbl=dict(small=100.,medium=0.,large=0.),
        total_tank_volume_bbl=1000.,detection_time_days=10.,groundwater_arrival_time_days=3.)


def shell():
    return tank.ShellFinancialConsequenceInput(**common("COURSE-1-10"),
        released_volume_by_hole_bbl=dict(small=100.,medium=200.,large=300.,rupture=1000.),
        equipment_area_m2=50.,personnel_area_m2=80.,equipment_cost_per_m2=100.,
        population_density_per_m2=.01,cost_per_injury=100000.)


@pytest.mark.parametrize("component,values,printed,total",[
    ("TANKBOTTOM",[7.2e-4,0,0,2e-6],7.2e-4,7.22e-4),
    ("COURSE-1-10",[7e-5,2.5e-5,5e-6,1e-7],1e-4,1.001e-4)])
def test_source_rows_and_equation_sum(component,values,printed,total):
    r = tank.generic_frequency(tank.GenericFrequencyInput(component_type=component)).outputs
    assert list(r.by_hole_per_year.values()) == values
    assert r.printed_total_per_year == printed
    assert r.total_per_year == pytest.approx(total)
    assert r.sum_minus_printed_per_year == pytest.approx(total-printed)
    assert r.total_basis == "hole_sum_eq3_208"


def test_non_tank_lookup_does_not_silently_change_existing_contract():
    with pytest.raises(DomainError):
        frequency.generic(frequency.GenericInput(component_type="TANKBOTTOM"))


def test_bottom_outage_na_remains_none_when_zero_frequency():
    x = bottom()
    r = tank.component_outage(tank.ComponentOutageInput(component_type="TANKBOTTOM",
        generic_frequency_by_hole_per_year=x.generic_frequency_by_hole_per_year,outage_multiplier=2)).outputs
    assert r.component_outage_days == pytest.approx((7.2e-4*5+2e-6*50)/7.22e-4*2)
    assert r.effective_days_by_hole == dict(small=5,medium=None,large=None,rupture=50)


def test_nonzero_na_requires_override_and_propagates_to_composition():
    x = bottom().model_dump()
    x["generic_frequency_by_hole_per_year"]["medium"] = 1e-6
    with pytest.raises(DomainError) as exc:
        tank.bottom_financial_consequence(tank.BottomFinancialConsequenceInput(**x))
    assert exc.value.code == "missing_outage_override"
    x["override_outage_days"] = {"medium":8.}
    r = tank.bottom_financial_consequence(tank.BottomFinancialConsequenceInput(**x)).outputs
    assert r.component_outage_days == pytest.approx((7.2e-4*5+1e-6*8+2e-6*50)/7.23e-4)


def test_bottom_financial_independent_hand_anchor():
    r = tank.bottom_financial_consequence(bottom()).outputs
    # GFF-summed total, rupture-only D/30.5 squared=4, USD2001 escalation2.
    repair = (7.2e-4*5000+2e-6*120000*4)/7.22e-4*2
    production = (7.2e-4*5+2e-6*50)/7.22e-4*1000
    # 70% of leakage reaches groundwater, 30% subsoil; surface cost537/bbl.
    leak = 7.2e-4/7.22e-4*100*(.7*5000+.3*1500)
    rupture = 2e-6/7.22e-4*1000*537
    assert r.component_repair_cost == pytest.approx(repair)
    assert r.business_interruption_cost == pytest.approx(production)
    assert r.environmental_cost == pytest.approx(leak+rupture)
    assert r.financial_consequence == pytest.approx(repair+production+leak+rupture)
    assert r.surrounding_equipment_cost == r.surrounding_outage_days == r.injury_cost == 0


def test_shell_five_categories_and_reference_currency_hand_anchor():
    x = shell()
    r = tank.shell_financial_consequence(x).outputs
    rates = [7e-5,2.5e-5,5e-6,1e-7]
    total = 1.001e-4
    repair = sum(g*c for g,c in zip(rates,[5000,12000,20000,40000]))/total*2
    outage = sum(g*d for g,d in zip(rates,[2,3,3,14]))/total
    surrounding = 5000.
    surrounding_days = 10**1.242*(2500./1e6)**.585
    production = (outage+surrounding_days)*1000
    injury = 80*.01*100000
    environment = sum(g*v for g,v in zip(rates,[100,200,300,1000]))/total*537
    assert r.component_repair_cost == pytest.approx(repair)
    assert r.component_outage_days == pytest.approx(outage)
    assert r.surrounding_cost_reference_usd_2001 == 2500
    assert r.surrounding_outage_days == pytest.approx(surrounding_days)
    assert r.financial_consequence == pytest.approx(repair+surrounding+production+injury+environment)


def test_shell_fx_conversion_preserves_all_outage_times():
    x = shell()
    r = tank.shell_financial_consequence(x).outputs
    converted = x.model_dump()
    converted["currency"] = "KRW"
    converted["cost_basis"] = "Qualified fixture valuation in 2026 KRW; FX1300"
    converted["repair"]["usd_to_output_currency"] = 1300.
    for name in ["equipment_cost_per_m2","cost_per_injury","production_cost_per_day"]:
        converted[name] *= 1300
    converted["cost_by_location_per_bbl"] = {k:v*1300 for k,v in converted["cost_by_location_per_bbl"].items()}
    other = tank.shell_financial_consequence(tank.ShellFinancialConsequenceInput(**converted)).outputs
    assert other.financial_consequence == pytest.approx(r.financial_consequence*1300)
    assert other.component_outage_days == r.component_outage_days
    assert other.surrounding_outage_days == r.surrounding_outage_days


@pytest.mark.parametrize("kind",["bottom","shell"])
def test_uniform_df_risk_matches_conditional_average_once(kind):
    source = bottom() if kind == "bottom" else shell()
    fn = tank.bottom_risk_assessment if kind == "bottom" else tank.shell_risk_assessment
    model = tank.BottomRiskAssessmentInput if kind == "bottom" else tank.ShellRiskAssessmentInput
    r = fn(model(financial=source,management_score=500,total_damage_factor=3,
        damage_factor_source="Qualified fixture DF")).outputs
    total = math.fsum(source.generic_frequency_by_hole_per_year.values())
    assert r.management_factor == 1
    assert r.annual_failure_frequency == pytest.approx(total*3)
    assert r.financial_risk_per_year == pytest.approx(total*3*r.financial_consequence)
    assert math.fsum(r.annual_frequency_by_hole.values()) == pytest.approx(r.annual_failure_frequency)
    if kind == "shell":
        assert r.equipment_area_risk_m2_per_year == pytest.approx(total*3*50)
        assert r.personnel_area_risk_m2_per_year == pytest.approx(total*3*80)
    else:
        assert "equipment_area_risk_m2_per_year" not in r.model_dump()


@pytest.mark.parametrize("score,expected",[(0,10),(500,1),(1000,.1)])
def test_management_score_scales_annual_risk_only(score,expected):
    r = tank.bottom_risk_assessment(tank.BottomRiskAssessmentInput(financial=bottom(),management_score=score,
        total_damage_factor=1,damage_factor_source="fixture")).outputs
    assert r.management_factor == expected
    assert r.financial_risk_per_year == pytest.approx(7.22e-4*expected*r.financial_consequence)


def test_zero_df_has_zero_risk_but_retains_financial_consequence():
    r = tank.bottom_risk_assessment(tank.BottomRiskAssessmentInput(financial=bottom(),management_score=500,
        total_damage_factor=0,damage_factor_source="explicit no active damage fixture")).outputs
    assert r.annual_failure_frequency == r.financial_risk_per_year == 0
    assert r.financial_consequence > 0


@pytest.mark.parametrize("field",["generic_frequency_source","cost_basis"])
def test_blank_sources_rejected(field):
    x = bottom().model_dump()
    x[field] = "   "
    with pytest.raises(DomainError):
        tank.bottom_financial_consequence(tank.BottomFinancialConsequenceInput(**x))


def test_incomplete_frequency_and_zero_total_rejected():
    for rates in [dict(small=1.),dict(small=0.,medium=0.,large=0.,rupture=0.)]:
        x = bottom().model_dump()
        x["generic_frequency_by_hole_per_year"] = rates
        with pytest.raises(DomainError):
            tank.bottom_financial_consequence(tank.BottomFinancialConsequenceInput(**x))


def test_numerical_overflow_is_domain_failure():
    x = shell().model_dump()
    x["equipment_cost_per_m2"] = 1e308
    with pytest.raises(DomainError) as exc:
        tank.shell_financial_consequence(tank.ShellFinancialConsequenceInput(**x))
    assert exc.value.code == "numerical_failure"


def test_exact_component_ids_and_finite_strict_fields():
    with pytest.raises(ValidationError):
        tank.GenericFrequencyInput(component_type="COURSE-11")
    with pytest.raises(ValidationError):
        tank.BottomRiskAssessmentInput(financial=bottom(),management_score=500,
            total_damage_factor=True,damage_factor_source="fixture")


def test_positive_frequency_underflow_rejected():
    with pytest.raises(DomainError) as exc:
        tank.bottom_risk_assessment(tank.BottomRiskAssessmentInput(financial=bottom(),management_score=1000,
            total_damage_factor=5e-324,damage_factor_source="numerical boundary fixture"))
    assert exc.value.code == "numerical_failure"


def test_blank_damage_source_rejected():
    with pytest.raises(DomainError):
        tank.bottom_risk_assessment(tank.BottomRiskAssessmentInput(financial=bottom(),management_score=500,
            total_damage_factor=1,damage_factor_source="   "))


def test_shell_zero_area_keeps_component_outage_and_repair():
    x = shell().model_dump()
    x.update(equipment_area_m2=0.,personnel_area_m2=0.)
    r = tank.shell_financial_consequence(tank.ShellFinancialConsequenceInput(**x)).outputs
    assert r.component_repair_cost > 0 and r.component_outage_days > 0
    assert r.surrounding_equipment_cost == r.injury_cost == r.surrounding_outage_days == 0
    assert r.business_interruption_cost == pytest.approx(r.component_outage_days*x["production_cost_per_day"])
