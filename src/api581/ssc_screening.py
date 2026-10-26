"""SSC applicability screen kept separate from hydrogen severity and hardness."""
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, calculation, ensure
from .scc_mechanisms import WetH2sEnvironment, wet_h2s_environment, SscSusceptibility, ssc_susceptibility, Assessment, InspectionCounts, assess


class SscScreen(Model):
    material: Literal['carbon_steel','low_alloy_steel','other_material']
    water_present: bool
    h2s_present: bool
    exposure_basis: str = Field(min_length=1)


@calculation('damage/ssc-screening','SSC carbon/low-alloy steel wet-H2S any-concentration screen',SscScreen,
    ['Part2 §8.3; PDF p184'],limitations=[
        'Evaluate carbon/low-alloy steel whenever both water and H2S are present at any concentration. No1ppm, partial-pressure, pH, temperature, hardness or PWHT cutoff is used to exclude the mechanism at this screen. Presence flags require qualified local/process/upset exposure evidence. Environmental hydrogen severity, cyanide, weld/HAZ Brinnell hardness and heat treatment remain separate susceptibility inputs. Screen-out is outside this procedure, not DF0, FFS acceptance or immunity to other mechanisms.'])
def ssc_screening(x):
    ensure(bool(x.exposure_basis.strip()),'Qualified steel, water and H2S exposure basis required')
    material=x.material!='other_material'
    return {'evaluate_ssc':material and x.water_present and x.h2s_present,
        'screening_reason':'outside_material_scope' if not material else 'water_absent' if not x.water_present else
            'h2s_absent' if not x.h2s_present else 'evaluate'}


@calculation('damage/hic-h2s-screening','HIC/SOHIC-H2S steel and wet-H2S any-concentration screen',SscScreen,
    ['Part2 §9.3; PDF p189'],limitations=[
        'Source material/water/H2S screening criteria coincide with SSC, but this identifier explicitly evaluates HIC/SOHIC-H2S. Carbon and low-alloy steel both enter screening; downstream Table9.3 carbon-steel material/sulfur/product assumptions require independent qualification. PWHT, seamless pipe, low sulfur or low H2S concentration alone do not exclude screening. No automatic SSC/HIC equivalence, SOHIC immunity, blister/crack FFS acceptance or zero DF.'])
def hic_h2s_screening(x):
    screen=ssc_screening(x)
    return {'evaluate_hic_sohic_h2s':screen['evaluate_ssc'],'screening_reason':screen['screening_reason']}


class SscQualifiedService(Model):
    environment: WetH2sEnvironment
    measured_brinnell_hardness: Positive
    pwht: bool
    service_basis: str = Field(min_length=1)


@calculation('damage/ssc-qualified-susceptibility','SSC environment and measured hardness with cyanide susceptibility upgrade',SscQualifiedService,
    ['Part2 Tables8.2-8.3; PDF p187'],limitations=[
        'Cyanide note upgrades susceptibility, not environmental severity, one category none->low->medium->high, capped at high, only when pH>8.3 and water H2S>1000ppm. Brinnell must be actually measured, not converted microhardness; PWHT and process chemistry require qualification. Existing source pH gaps and overlapping1000ppm columns fail explicitly. No automatic material applicability or chemical speciation.'])
def ssc_qualified_susceptibility(x):
    ensure(bool(x.service_basis.strip()),'Qualified water chemistry, measured weldment Brinnell and PWHT basis required')
    environment=wet_h2s_environment(x.environment)
    base=ssc_susceptibility(SscSusceptibility(measured_brinnell_hardness=x.measured_brinnell_hardness,
        pwht=x.pwht,environmental_severity=environment['environmental_severity']))['susceptibility']
    levels=('none','low','medium','high')
    selected=levels[min(3,levels.index(base)+int(environment['susceptibility_upgrade_required']))]
    return {**environment,'unadjusted_susceptibility':base,'susceptibility':selected,
        'cyanide_upgrade_applied':environment['susceptibility_upgrade_required']}


class SscQualifiedAssessment(Model):
    screening: SscScreen
    service: SscQualifiedService
    confirmed_cracking: bool
    unrepaired_cracks: bool
    years_since_qualifying_inspection: NonNegative
    inspections: InspectionCounts
    inspection_basis: str = Field(min_length=1)


@calculation('damage/ssc-qualified-assessment','SSC material/exposure through environment/hardness/cyanide and DF',SscQualifiedAssessment,
    ['Part2 §§8.3,8.5-8.6,Tables8.2-8.4,Table6.3; eq(2.27); PDF pp184-188'],
    origin='qualified_ssc_environment_hardness_to_df',limitations=[
        'Selected material/wet-H2S screen must pass. Reuses existing Table8.2 gaps/overlap guards, Table8.3 actual Brinnell/PWHT susceptibility and one-category cyanide note before crack override. Confirmed cracking forces high; unrepaired cracks require FFS. Caller qualifies mechanism-specific inspection period and coverage. Existing equivalent-count support up to6, age escalation and table DF preserved. No generic thinning-history reuse, FFS or total asset risk.'])
def ssc_qualified_assessment(x):
    ensure(not x.unrepaired_cracks,'Unrepaired SSC cracks require separate FFS evaluation','ffs_required')
    ensure(bool(x.inspection_basis.strip()),'SSC-specific qualifying inspection age and coverage basis required')
    screen=ssc_screening(x.screening)
    ensure(screen['evaluate_ssc'],'SSC material/wet-H2S screen not met','ssc_outside_screen')
    service=ssc_qualified_susceptibility(x.service)
    result=assess('ssc',Assessment(susceptibility=service['susceptibility'],confirmed_cracking=x.confirmed_cracking,
        unrepaired_cracks=False,years_since_qualifying_inspection=x.years_since_qualifying_inspection,inspections=x.inspections))
    return {**screen,**service,**result}
