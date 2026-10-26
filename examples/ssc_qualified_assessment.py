"""Wet-H2S screen -> environment -> Brinnell/PWHT -> cyanide -> SSC DF."""
from api581 import Context
from api581.api import damage


def main():
    result=damage.ssc_qualified_assessment(damage.SscQualifiedAssessmentInput(
        screening=dict(material='carbon_steel',water_present=True,h2s_present=True,
            exposure_basis='Qualified wet-H2S steel service demonstration'),
        service=dict(environment=dict(water_ph=8.5,h2s_in_water_ppm=2000.,cyanides_present=True),
            measured_brinnell_hardness=237.,pwht=False,
            service_basis='Actually measured maximum weldment Brinnell and current chemistry/PWHT fixture'),
        confirmed_cracking=False,unrepaired_cracks=False,years_since_qualifying_inspection=2.,
        inspections=dict(a=1,b=0,c=0,d=0),inspection_basis='Qualified SSC-specific A inspection coverage and elapsed period'),
        context=Context(asset_id='ssc-qualified-demo',source_revision='wet-h2s-hardness-cyanide-v1'))
    output=result.outputs
    assert output.environmental_severity=='moderate'
    assert output.unadjusted_susceptibility=='medium' and output.susceptibility=='high'
    assert output.base_damage_factor==5. and abs(output.damage_factor-5*2**1.1)<1e-12
    print('Environment / raw / cyanide-adjusted:',output.environmental_severity,output.unadjusted_susceptibility,output.susceptibility)
    print('SVI / base / SSC DF:',output.severity_index,output.base_damage_factor,output.damage_factor)
    return output


if __name__=='__main__':
    main()
