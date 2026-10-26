"""Figure7.1 service -> susceptibility -> inspection/age DF, distinct from corrosion."""
from api581 import Context
from api581.api import damage


def main():
    result=damage.amine_figure_assessment(damage.AmineFigureAssessmentInput(
        screening=dict(material='carbon_steel',acid_gas_treating_amine_present=True,
            screening_basis='Qualified carbon-steel acid-gas-treating service fixture'),
        service=dict(confirmed_cracking=False,unrepaired_cracks=False,stress_relieved=False,
            solution='lean_and_rich',amine_group='dea',maximum_metal_temperature_k=(180.-32)*5/9+273.15,
            heat_traced=False,steamed_out_before_water_flush=False,
            applicability_basis='Actual maximum metal temperature and both lean/rich exposure qualified for illustrative DEA service'),
        years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0),
        inspection_basis='Qualified amine-specific1A inspection and2year period'),
        context=Context(asset_id='amine-figure-dea-demo',source_revision='qualified-service-fixture-v1'))
    output=result.outputs
    assert output.lean_exposure_selected and output.susceptibility=='low'
    assert output.severity_index==10 and output.base_damage_factor==1.
    assert abs(output.damage_factor-2**1.1)<1e-12
    print('Figure branch / susceptibility:',output.decision_branch,output.susceptibility)
    print('SVI / base / DF:',output.severity_index,output.base_damage_factor,output.damage_factor)
    return output


if __name__=='__main__':
    main()
