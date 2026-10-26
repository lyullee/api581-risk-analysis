"""CLSCC potential wet-chloride and printed-temperature screening."""
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, calculation, ensure
from .scc_mechanisms import ClsccSusceptibility, clscc_susceptibility, Assessment, InspectionCounts, assess

class ClsccScreen(Model):
    material: Literal['austenitic_stainless_steel','other_material']
    actual_or_potential_wet_chloride_exposure: bool
    operating_temperature_k: Positive
    temperature_basis: Literal['printed_si','printed_us_converted']
    exposure_basis: str = Field(min_length=1)


@calculation('damage/clscc-screening','CLSCC material/potential wet-chloride and operating-temperature screen',ClsccScreen,
    ['Part2 §12.3; PDF p207'],limitations=[
        'Austenitic stainless steel, actual/potential chlorides AND water and operating temperature strictly above selected38C or100F threshold. Paired source thresholds differ; unit basis explicit. Exposure qualification includes upsets, retained hydrotest water, cooling tower drift and insulation/process conditions. No concentration cutoff, bulk-to-local enrichment, nickel-content exemption, material immunity or DF0 inferred. A negative screen does not invalidate observed cracks or replace FFS.'])
def clscc_screening(x):
    ensure(bool(x.exposure_basis.strip()),'Qualified material and actual/potential wet-chloride exposure review required')
    threshold=311.15 if x.temperature_basis=='printed_si' else (100.-32)*5/9+273.15
    material=x.material=='austenitic_stainless_steel'
    hot=x.operating_temperature_k>threshold
    return {'evaluate_clscc':material and x.actual_or_potential_wet_chloride_exposure and hot,
        'material_in_scope':material,'temperature_screen_passed':hot,'screening_temperature_threshold_k':threshold,
        'selected_temperature_basis':x.temperature_basis}


class QualifiedClsccAssessment(Model):
    screening: ClsccScreen
    ph_over_10: bool
    chloride_band_ppm: Literal['1-10','11-100','101-1000','>1000']
    chemistry_basis: str = Field(min_length=1)
    confirmed_cracking: bool
    unrepaired_cracks: bool
    years_since_qualifying_inspection: NonNegative
    inspections: InspectionCounts
    inspection_basis: str = Field(min_length=1)


@calculation('damage/clscc-qualified-assessment','CLSCC wet-chloride screen through SI susceptibility and inspection DF',QualifiedClsccAssessment,
    ['Part2 §§12.3,12.6.3,Tables12.2M/12.3,Table6.3; eq(2.31); PDF pp207-211'],
    origin='qualified_clscc_screen_si_table_to_df',limitations=[
    'Uses the selected printed SI Table12.2M or US Table12.2 and the same operating temperature for susceptibility. Qualified chloride ion band and pH>10 classification supplied; no bulk-to-local chloride enrichment or interpolation through concentration gaps. No synthetic DF0 on screen-out. Confirmed cracking forces high; unrepaired cracks require FFS. Inspection period/coverage are mechanism-specific external qualifications. Source pH>10/93C overlap in the SI table and existing equivalent count support are retained; no whole-asset risk.'])
def clscc_qualified_assessment(x):
    ensure(not x.unrepaired_cracks,'Unrepaired CLSCC requires separate FFS evaluation','ffs_required')
    ensure(bool(x.chemistry_basis.strip()) and bool(x.inspection_basis.strip()),'Qualified local chloride/pH and CLSCC inspection bases required')
    screen=clscc_screening(x.screening)
    ensure(screen['evaluate_clscc'],'CLSCC material/wet-chloride/temperature screen not met','clscc_outside_screen')
    selected=clscc_susceptibility(ClsccSusceptibility(
        temperature_k=x.screening.operating_temperature_k,
        temperature_basis=x.screening.temperature_basis,
        ph_over_10=x.ph_over_10, chloride_band_ppm=x.chloride_band_ppm))
    result=assess('clscc',Assessment(susceptibility=selected['susceptibility'],confirmed_cracking=x.confirmed_cracking,
        unrepaired_cracks=False,years_since_qualifying_inspection=x.years_since_qualifying_inspection,inspections=x.inspections))
    return {**screen,**selected,**result}
