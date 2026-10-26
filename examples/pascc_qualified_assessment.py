"""Qualified shutdown protection changes susceptibility once before SCC DF."""
from api581 import Context
from api581.api import damage


def request(**changes):
    return damage.PasccQualifiedAssessmentInput(**(dict(screening=dict(material='austenitic_stainless_steel',
        sulfur_bearing_compounds_exposure=True,exposure_basis='Qualified sulfur exposure history'),
        service=dict(alloy=dict(operating_temperature_k=650.,material_group='regular_300ss_or_alloy600_800',
            heat_treatment='solution_annealed'),sulfur_oxygen_water_during_operation=False,
            sulfur_oxygen_water_during_shutdown=True,qualified_rp0170_downtime_protection=True,
            protection_basis='Owner-qualified RP0170 shutdown protection fixture, not verified by software',
            confirmed_cracking=False,unrepaired_cracks=False,
            service_alloy_basis='Qualified regular300SS alloy group, thermal and shutdown exposure history'),
        years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0),
        inspection_basis='Qualified PASCC-specific inspection1A coverage and2year age')|changes))


def main():
    output=damage.pascc_qualified_assessment(request(),context=Context(asset_id='pascc-protection-demo',
        source_revision='qualified-alloy-shutdown-protection-v1')).outputs
    assert output.table_or_override_susceptibility=='medium' and output.susceptibility=='low'
    assert output.severity_index==50 and output.base_damage_factor==3.
    assert abs(output.damage_factor-3*2**1.1)<1e-12
    print('Raw / protected susceptibility:',output.table_or_override_susceptibility,output.susceptibility)
    print('SVI / base / PASCC DF:',output.severity_index,output.base_damage_factor,output.damage_factor)
    return output


if __name__=='__main__':
    main()
