import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import level1


def hf_area(**changes):
    data=dict(fluid="h2s",release_type="continuous",duration_s=300,toxic_rate_kg_s=1/2.205,
        toxic_mass_kg=100,nonignition_probability=1)
    return level1.hf_h2s_toxic_area(level1.HfH2sToxicAreaInput(**{**data,**changes}))


@pytest.mark.parametrize("fluid,seconds,d", [("hf",300,3.5683),("hf",3600,4.4576),
    ("h2s",300,3.9686),("h2s",1200,4.238),("h2s",3600,4.4365)])
def test_hf_h2s_native_unit_rate_log_intercepts(fluid,seconds,d):
    assert hf_area(fluid=fluid,duration_s=seconds).outputs.personnel_area_m2 == pytest.approx(.0929*10**d)


def test_h2s_instantaneous_uses_mass_not_rate_and_nonignition_once():
    out=hf_area(release_type="instantaneous",toxic_rate_kg_s=1e6,toxic_mass_kg=1/2.205,
        nonignition_probability=.6).outputs
    assert out.unweighted_personnel_area_m2 == pytest.approx(.0929*10**2.7840)
    assert out.personnel_area_m2 == pytest.approx(.6*out.unweighted_personnel_area_m2)


def test_hf_continuous_interpolates_curves_not_log_coefficients():
    out=hf_area(fluid="hf",duration_s=450,toxic_rate_kg_s=2.4).outputs
    lower=.0929*10**(1.1401*math.log10(2.205*2.4)+3.5683)
    upper=.0929*10**(1.1031*math.log10(2.205*2.4)+3.8431)
    assert out.personnel_area_m2 == pytest.approx((lower+upper)/2)
    with pytest.raises(DomainError) as error:
        level1.hf_h2s_toxic_coefficients(level1.HfH2sToxicCoefficientsInput(fluid="hf",release_type="continuous",duration_s=450))
    assert error.value.code == "interpolation_required"


def test_hf_ambiguous_print_is_visible_and_never_implicitly_corrected():
    raw=level1.hf_h2s_toxic_coefficients(level1.HfH2sToxicCoefficientsInput(fluid="hf",release_type="instantaneous")).outputs
    assert raw.d == 33606 and raw.source_cell_status == "ambiguous_print"
    with pytest.raises(DomainError) as error:
        hf_area(fluid="hf",release_type="instantaneous")
    assert error.value.code == "unsupported_table_cell"
    qualified=hf_area(fluid="hf",release_type="instantaneous",hf_instantaneous_intercept=3.3606,
        intercept_qualification="Synthetic test fixture; not a claimed source correction")
    assert qualified.outputs.personnel_area_m2 == pytest.approx(.0929*10**(1.4056*math.log10(2.205*100)+3.3606))
    assert qualified.normalized_inputs["intercept_qualification"]
    with pytest.raises(DomainError):
        hf_area(fluid="hf",release_type="instantaneous",hf_instantaneous_intercept=3.3606)
    with pytest.raises(DomainError):
        hf_area(fluid="h2s",release_type="instantaneous",hf_instantaneous_intercept=3.3606,intercept_qualification="not applicable")


@pytest.mark.parametrize("duration", [299,3601])
def test_hf_h2s_continuous_does_not_extrapolate(duration):
    with pytest.raises(DomainError):
        hf_area(duration_s=duration)
    assert hf_area(duration_s=duration,toxic_rate_kg_s=0).outputs.personnel_area_m2 == 0


def misc(fluid,phase,seconds,rate=1,probability=1):
    return level1.misc_toxic_area(level1.MiscToxicAreaInput(fluid=fluid,release_phase=phase,duration_s=seconds,
        toxic_rate_kg_s=rate,nonignition_probability=probability)).outputs


@pytest.mark.parametrize("fluid,phase,seconds,coefficient", [
    ("alcl3","powder",300,3.4531),("co","gas",180,9.55),("hcl","gas",300,123.67),
    ("nitric_acid","gas",600,23851.3),("nitric_acid","liquid",600,2674.47),
    ("no2","gas",1200,2338.76),("no2","liquid",180,430),
    ("phosgene","gas",3600,96274.2),("phosgene","liquid",1200,14727.5),
    ("tdi","liquid",180,793.04),("ee","gas",90,.8954),("ee","liquid",600,.6857),
    ("eo","gas",600,47.69),("po","gas",180,.0008),("po","liquid",3600,367.06)])
def test_all_ten_chemicals_printed_si_table_anchors(fluid,phase,seconds,coefficient):
    # SI unit mass rate => area exactly printed e: detects erroneous extra US conversion.
    assert misc(fluid,phase,seconds).unweighted_personnel_area_m2 == coefficient


def test_miscellaneous_si_power_interpolation_and_weighting():
    out=misc("co","gas",240,rate=2,probability=.3)
    expected=(9.55*2**1.15+60.09*2**1.06)/2
    assert out.unweighted_personnel_area_m2 == pytest.approx(expected)
    assert out.personnel_area_m2 == pytest.approx(.3*expected)
    coefficients=level1.misc_toxic_coefficients(level1.MiscToxicCoefficientsInput(fluid="co",release_phase="gas",duration_s=180)).outputs
    assert coefficients.native_rate_unit == "kg/s" and coefficients.native_area_unit == "m2"
    assert coefficients.si_mass_multiplier == coefficients.si_area_multiplier == 1


def test_powder_alcl3_is_duration_independent_but_zero_duration_has_no_release():
    assert misc("alcl3","powder",1,rate=2).personnel_area_m2 == misc("alcl3","powder",3600,rate=2).personnel_area_m2
    assert misc("alcl3","powder",0,rate=2).personnel_area_m2 == 0
    with pytest.raises(DomainError):
        misc("alcl3","liquid",300)


@pytest.mark.parametrize("fluid,phase,time", [("ee","liquid",300),("po","liquid",180),("po","liquid",240),
    ("tdi","gas",300),("co","gas",60),("co","gas",3601)])
def test_na_cells_and_out_of_range_not_invented(fluid,phase,time):
    with pytest.raises(DomainError):
        misc(fluid,phase,time)


def test_instantaneous_miscellaneous_not_supported():
    with pytest.raises(ValidationError):
        level1.MiscToxicAreaInput(fluid="co",release_phase="gas",release_type="instantaneous",duration_s=300,
            toxic_rate_kg_s=1,nonignition_probability=1)


@pytest.mark.parametrize("fluid,cutoff", [("hf",30),("h2s",100),("ammonia",300),("chlorine",10)])
def test_historical_idlh_is_inclusive_and_not_mass_fraction_conversion(fluid,cutoff):
    for concentration,required in [(cutoff,False),(cutoff+.001,True)]:
        out=level1.toxic_cutoff(level1.ToxicCutoffInput(fluid=fluid,concentration_ppm_on_idlh_basis=concentration)).outputs
        assert out.idlh_ppm == cutoff and out.requires_toxic_evaluation is required


def component(**changes):
    data=dict(fluid="h2s",release_phase="gas",release_type="continuous",theoretical_rate_kg_s=10,
        released_mass_kg=1000,toxic_mass_fraction=.1,available_mass_kg=12000,
        detection_maximum_duration_s=1800,nonignition_probability=.7)
    return level1.toxic_component_consequence(level1.ToxicComponentConsequenceInput(**{**data,**changes}))


def test_component_uses_theoretical_rate_inventory_duration_and_explicit_mitigation():
    out=component(mitigation=level1.MitigationCreditsInput(rate_reduction_fraction=.2,duration_reduction_fraction=.5)).outputs
    assert out.toxic_rate_kg_s == .8  # 10*.1*(1-.2), no flammable DI reduction.
    assert out.unmitigated_duration_s == 1200  # total inventory / theoretical total rate.
    assert out.duration_s == 600
    assert out.toxic_mass_kg == 100
    expected=.7*.0929*10**(1.2410*math.log10(2.205*.8)+4.0948)
    assert out.personnel_area_m2 == pytest.approx(expected)


def test_component_can_dispatch_to_si_misc_and_ammonia_paths():
    misc_out=component(fluid="co").outputs
    assert misc_out.personnel_area_m2 == pytest.approx(.7*651.49)
    ammonia=component(fluid="ammonia").outputs
    assert ammonia.personnel_area_m2 == pytest.approx(.7*1256)


def test_cutoff_disables_area_and_unqualified_duration_credit_does_not_extrapolate():
    out=component(concentration_ppm_on_idlh_basis=100).outputs
    assert out.screening_applied and not out.requires_toxic_evaluation and out.personnel_area_m2 == 0
    with pytest.raises(DomainError):
        component(mitigation=level1.MitigationCreditsInput(duration_reduction_fraction=.9))
    with pytest.raises(DomainError):
        component(fluid="h2s",release_phase="liquid")
