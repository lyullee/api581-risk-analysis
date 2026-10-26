"""ACSCC alkaline-water and FCCU feed-change screening, Part2 section10.3."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, calculation, ensure
from .scc_mechanisms import AcsccSusceptibility, acscc_susceptibility, Assessment, InspectionCounts, assess


class AcsccScreen(Model):
    material: Literal['carbon_steel','low_alloy_steel','other_material']
    water_present: bool
    water_ph: float | None = Field(default=None,strict=True,allow_inf_nan=False)
    fccu_feed_sulfur_reduced: bool
    fccu_feed_nitrogen_increased: bool
    screening_basis: str = Field(min_length=1)


@calculation('damage/acscc-screening','ACSCC alkaline-water and FCCU feed-change evaluation triggers',AcsccScreen,
    ['Part2 §10.3; PDF p196'],limitations=[
        'Carbon/low-alloy steel: alkaline water pH>7.5 or reduced-sulfur/increased-nitrogen FCCU feed changes trigger evaluation. Exactly7.5 does not pass the strict water trigger. Feed-change triggers are independent review flags, not proof of carbonate concentration or susceptibility. Water presence requires its qualified pH; absent water must omit pH. No H2S threshold, cyanide exclusion, carbonate estimate, PWHT credit or damage factor is inferred. Outside scope is not overall immunity or zero risk.'])
def acscc_screening(x):
    ensure(bool(x.screening_basis.strip()),'Qualified material/water chemistry and FCCU feed-change review basis required')
    ensure((x.water_ph is not None)==x.water_present,'Water pH required exactly when water is present')
    triggers=[]
    if x.water_present and x.water_ph>7.5:
        triggers.append('alkaline_water_ph_above_7_5')
    if x.fccu_feed_sulfur_reduced:
        triggers.append('fccu_feed_sulfur_reduced')
    if x.fccu_feed_nitrogen_increased:
        triggers.append('fccu_feed_nitrogen_increased')
    eligible=x.material!='other_material'
    return {'evaluate_acscc':eligible and bool(triggers),'material_in_scope':eligible,'evaluation_triggers':triggers}


class AcsccWaterSusceptibility(Model):
    water_ph: float = Field(strict=True,allow_inf_nan=False)
    carbonate_ppm: NonNegative
    pwht: bool
    shared_ph_boundary_policy: Literal['lower_ph_row','higher_ph_row'] | None = None
    carbonate_measurement_basis: str = Field(min_length=1)
    traditional_alkalinity_only: bool
    service_fabrication_basis: str = Field(min_length=1)


@calculation('damage/acscc-water-susceptibility','Qualified numeric water pH to ACSCC carbonate/PWHT susceptibility',AcsccWaterSusceptibility,
    ['Part2 Table10.2 and note1; PDF p199'],limitations=[
        'Numeric pH mapped to existing Table10.2 bands. Shared8.0/9.0 endpoints require explicit lower/higher-pH row selection; no automatic susceptibility-maximizing policy.7.5 enters7.5_to_8, independently of screening strict>7.5.100ppm carbonate belongs high-concentration column. Traditional P/M alkalinity alone is rejected per note1; caller supplies qualified carbonate method. No carbonate inference from total alkalinity, PWHT certification, numeric pH rounding allowance or material applicability.'])
def acscc_water_susceptibility(x):
    ensure(bool(x.carbonate_measurement_basis.strip()) and bool(x.service_fabrication_basis.strip()),
        'Qualified carbonate analysis and service/fabrication bases required')
    ensure(not x.traditional_alkalinity_only,'Traditional P/M alkalinity alone is ineffective for carbonate in sour water','unsupported_carbonate_measurement')
    ph=x.water_ph
    boundary=ph in (8.,9.)
    ensure((x.shared_ph_boundary_policy is not None)==boundary,
        'Shared pH8/9 endpoints require a row policy; unused policy must be omitted','ambiguous_acscc_ph_boundary')
    if boundary:
        bands=('7.5_to_8','8_to_9') if ph==8. else ('8_to_9','at_least_9')
        band=bands[x.shared_ph_boundary_policy=='higher_ph_row']
    else:
        band='below_7.5' if ph<7.5 else '7.5_to_8' if ph<8. else '8_to_9' if ph<9. else 'at_least_9'
    result=acscc_susceptibility(AcsccSusceptibility(water_ph_band=band,carbonate_ppm=x.carbonate_ppm,pwht=x.pwht))
    return {**result,'selected_ph_band':band,'shared_ph_boundary_encountered':boundary}


class AcsccQualifiedAssessment(Model):
    screening: AcsccScreen
    water: AcsccWaterSusceptibility
    confirmed_cracking: bool
    unrepaired_cracks: bool
    years_since_qualifying_inspection: NonNegative
    inspections: InspectionCounts
    inspection_basis: str = Field(min_length=1)


@calculation('damage/acscc-qualified-assessment','ACSCC screen and common water chemistry through inspection/age DF',AcsccQualifiedAssessment,
    ['Part2 §§10.3,10.6.3,Table10.2-10.3,Table6.3; eq(2.29); PDF pp196-199'],
    origin='qualified_acscc_water_to_existing_scc_df',limitations=[
        'Requires positive screening and water-present numeric pH consistent with susceptibility input. FCCU feed change can trigger review but cannot replace water/carbonate data needed by Table10.2. Shared pH8/9 policy, qualified carbonate measurement and PWHT remain explicit. Confirmed cracking forceshigh; unrepaired cracks requireFFS. Independent mechanism-specific inspection age/coverage required; existing six-equivalent-inspection support retained. No chemical speciation, automatic damage detection, FFS or whole-asset risk.'])
def acscc_qualified_assessment(x):
    ensure(not x.unrepaired_cracks,'Unrepaired ACSCC requires separate FFS evaluation','ffs_required')
    ensure(bool(x.inspection_basis.strip()),'ACSCC-specific inspection age and effectiveness basis required')
    screen=acscc_screening(x.screening)
    ensure(screen['evaluate_acscc'],'ACSCC material/environment review screen not met','acscc_outside_screen')
    ensure(x.screening.water_present,'ACSCC table requires qualified aqueous carbonate conditions','acscc_water_required')
    ensure(x.screening.water_ph==x.water.water_ph,'Screening and susceptibility water pH must agree','acscc_ph_mismatch')
    water=acscc_water_susceptibility(x.water)
    result=assess('acscc',Assessment(susceptibility=water['susceptibility'],confirmed_cracking=x.confirmed_cracking,
        unrepaired_cracks=False,years_since_qualifying_inspection=x.years_since_qualifying_inspection,inspections=x.inspections))
    return {**screen,**water,**result}
