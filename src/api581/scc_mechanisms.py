"""SCC mechanism-specific severity, inspection and age calculations (Part 2 §§6-14)."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure
from .pof import InspectionEquivalent, inspection_equivalent
from .cracking import SccBase, scc_base

Susceptibility = Literal["none","low","medium","high"]
Mechanism = Literal["caustic","amine","ssc","hic-sohic-h2s","acscc","pascc","clscc","hsc-hf","hic-sohic-hf"]
PROFILES = {
    "caustic":(6,"6.2",25,(0,50,500,5000)),
    "amine":(7,"7.2",26,(0,10,100,1000)),
    "ssc":(8,"8.4",27,(0,1,10,100)),
    "hic-sohic-h2s":(9,"9.4",28,(0,1,10,100)),
    "acscc":(10,"10.3",29,(0,10,100,1000)),
    "pascc":(11,"11.3",30,(0,50,500,5000)),
    "clscc":(12,"12.3",31,(0,50,500,5000)),
    "hsc-hf":(13,"13.3",32,(0,1,10,100)),
    "hic-sohic-hf":(14,"14.3",33,(0,1,10,100))}


class Severity(Model):
    mechanism: Mechanism
    susceptibility: Susceptibility


@calculation("damage/scc-severity", "Mechanism-specific SCC severity index", Severity,
             ["Part 2 Tables 6.2,7.2,8.4,9.4,10.3,11.3,12.3,13.3,14.3"],
             limitations=["Caller must complete material/service susceptibility screening before selecting a severity."])
def severity(x):
    return {"severity_index":PROFILES[x.mechanism][3][("none","low","medium","high").index(x.susceptibility)]}


class InspectionCounts(Model):
    a: int = Field(ge=0,le=100000,strict=True)
    b: int = Field(ge=0,le=100000,strict=True)
    c: int = Field(ge=0,le=100000,strict=True)
    d: int = Field(ge=0,le=100000,strict=True)


class Assessment(Model):
    susceptibility: Susceptibility
    confirmed_cracking: bool
    unrepaired_cracks: bool
    years_since_qualifying_inspection: NonNegative
    inspections: InspectionCounts


class Monitoring(Model):
    monitoring: Literal["none","process_variables","hydrogen_probes","both"]


@calculation("damage/hic-monitoring-factor", "HIC/SOHIC monitoring adjustment factor", Monitoring,
             ["Part 2 Tables 9.5,14.4; PDF pp193,221"])
def monitoring_factor(x):
    return {"monitoring_factor":{"none":1,"process_variables":2,"hydrogen_probes":2,"both":4}[x.monitoring]}


class HicAssessment(Assessment):
    monitoring: Literal["none","process_variables","hydrogen_probes","both"]


def assess(mechanism,x):
    ensure(not x.unrepaired_cracks,"Detected unrepaired cracks require an FFS-based evaluation", "ffs_required")
    susceptibility="high" if x.confirmed_cracking else x.susceptibility
    svi=severity(Severity(mechanism=mechanism,susceptibility=susceptibility))["severity_index"]
    counts=inspection_equivalent(InspectionEquivalent(mechanism="scc",**x.inspections.model_dump()))
    grade,count="E",0
    for candidate in "abcd":
        if counts[candidate]:
            grade,count=candidate.upper(),counts[candidate]
            break
    ensure(count<=6,"Equivalent inspection count exceeds Table 6.3 support; no extrapolation")
    base=scc_base(SccBase(severity_index=svi,inspection_grade=grade,inspection_count=count))["base_damage_factor"]
    monitoring=monitoring_factor(Monitoring(monitoring=x.monitoring))["monitoring_factor"] if isinstance(x,HicAssessment) else 1
    age_factor=max(x.years_since_qualifying_inspection,1)**1.1
    return {"effective_susceptibility":susceptibility,"severity_index":svi,"equivalent_inspection_grade":grade,
            "equivalent_inspection_count":count,"base_damage_factor":base,"age_factor":age_factor,
            "monitoring_factor":monitoring,"damage_factor":base*age_factor/monitoring}


def register_mechanism(mechanism):
    section,table,eq,_=PROFILES[mechanism]
    model=HicAssessment if mechanism.startswith("hic-sohic") else Assessment
    def calculate(x):
        return assess(mechanism,x)
    calculate.__name__=mechanism.replace("-","_")
    return calculation("damage/"+mechanism,f"{mechanism} damage factor from qualified susceptibility and inspections",model,
        [f"Part 2 §{section}.6, Table {table}, eq (2.{eq}), §3.4.3 and Table 6.3"],
        limitations=["Material/service screening and susceptibility must be independently established. Inspection counts and age must follow the mechanism-specific qualifying period. Confirmed cracking forces High; unrepaired cracks are rejected for separate FFS. Ambiguous Table 6.3 E/500 cell remains unsupported."])(calculate)


for _mechanism in PROFILES:
    globals()[_mechanism.replace("-","_")]=register_mechanism(_mechanism)


class HscSusceptibility(Model):
    measured_brinnell_hardness: Positive
    pwht: bool


@calculation("damage/hsc-hf-susceptibility", "HSC-HF susceptibility of eligible steel weldments", HscSusceptibility,
             ["Part 2 Table 13.2; PDF p215"], limitations=["Eligible material and HF exposure must be screened separately. Brinnell must be measured as Brinnell, not converted from microhardness."])
def hsc_susceptibility(x):
    column=0 if x.measured_brinnell_hardness<200 else (1 if x.measured_brinnell_hardness<=237 else 2)
    return {"susceptibility":(("none","low","high") if x.pwht else ("low","medium","high"))[column]}


class SscSusceptibility(HscSusceptibility):
    environmental_severity: Literal["low","moderate","high"]


@calculation("damage/ssc-susceptibility", "SSC hardness/heat-treatment susceptibility", SscSusceptibility,
             ["Part 2 Table 8.3; PDF p187"], limitations=["Environmental severity and cyanide-related susceptibility upgrade must be established separately. Table 'Not' is normalized to none."])
def ssc_susceptibility(x):
    column=0 if x.measured_brinnell_hardness<200 else (1 if x.measured_brinnell_hardness<=237 else 2)
    rows={False:{"high":("low","medium","high"),"moderate":("low","medium","high"),"low":("low","low","medium")},
          True:{"high":("none","low","medium"),"moderate":("none","none","low"),"low":("none","none","none")}}
    return {"susceptibility":rows[x.pwht][x.environmental_severity][column]}


class HicMaterial(Model):
    steel_sulfur_weight_percent: NonNegative = Field(le=100)
    product_form: Literal["plate_or_welded","seamless_or_extruded_pipe"]
    pwht: bool


@calculation("damage/hic-hf-susceptibility", "HIC/SOHIC-HF steel/product susceptibility", HicMaterial,
             ["Part 2 Table 14.2; PDF p220"], limitations=["Eligible steel with HF exposure only; material/service screening remains separate."])
def hic_hf_susceptibility(x):
    if x.product_form=="seamless_or_extruded_pipe": level="low"
    elif x.steel_sulfur_weight_percent>.01: level="high"
    else: level="medium" if x.pwht else "high"
    return {"susceptibility":level}


class HicH2sMaterial(HicMaterial):
    environmental_severity: Literal["low","moderate","high"]


@calculation("damage/hic-h2s-susceptibility", "HIC/SOHIC-H2S steel/product susceptibility", HicH2sMaterial,
             ["Part 2 Table 9.3; PDF p193"], limitations=["Environmental severity, existing-crack rule and cyanide upgrade must be established separately."])
def hic_h2s_susceptibility(x):
    if x.product_form=="seamless_or_extruded_pipe":
        level="medium" if x.environmental_severity=="high" and not x.pwht else "low"
    elif x.steel_sulfur_weight_percent>.01:
        level={"high":("high","high"),"moderate":("high","medium"),"low":("medium","low")}[x.environmental_severity][x.pwht]
    else:
        level={"high":("high","medium"),"moderate":("medium","low"),"low":("low","low")}[x.environmental_severity][x.pwht]
    return {"susceptibility":level}


class ClsccSusceptibility(Model):
    temperature_k: Positive
    temperature_basis: Literal["printed_si", "printed_us_converted"] = "printed_si"
    ph_over_10: bool
    chloride_band_ppm: Literal["1-10","11-100","101-1000",">1000"]


@calculation("damage/clscc-susceptibility", "CLSCC SI/US temperature/chloride susceptibility", ClsccSusceptibility,
             ["Part 2 Tables 12.2M/12.2; PDF pp210-211"], limitations=["Eligible material and chloride band selected by caller; no interpolation across concentration gaps. Temperature basis is explicit. For pH>10 at exactly 93 C in the SI table, overlapping source rows require manual resolution."])
def clscc_susceptibility(x):
    t=x.temperature_k-273.15
    column=("1-10","11-100","101-1000",">1000").index(x.chloride_band_ppm)
    if x.temperature_basis == "printed_si":
        if x.ph_over_10:
            ensure(abs(t-93)>1e-9,"Source rows overlap at pH>10 and 93 C", "ambiguous_source")
            row=0 if t<=38 else (1 if t<93 else (2 if t<=149 else 3))
            rows=[("none",)*4,("low",)*4,("low","low","low","medium"),("medium","medium","medium","high")]
        else:
            row=0 if t<=38 else (1 if t<=66 else (2 if t<=93 else (3 if t<=149 else 4)))
            rows=[("low","low","low","medium"),("low","medium","medium","high"),("medium","medium","high","high"),("medium","high","high","high"),("high",)*4]
    else:
        tf=t*9/5+32
        if x.ph_over_10:
            row=0 if tf<=100 else (1 if tf<=200 else (2 if tf<=300 else 3))
            rows=[("none",)*4,("low",)*4,("low","low","low","medium"),("medium","medium","medium","high")]
        else:
            row=0 if tf<=100 else (1 if tf<=150 else (2 if tf<=200 else (3 if tf<=300 else 4)))
            rows=[("low","low","low","medium"),("low","medium","medium","high"),("medium","medium","high","high"),("medium","high","high","high"),("high",)*4]
    return {"susceptibility":rows[row][column]}


class WetH2sEnvironment(Model):
    water_ph: float = Field(allow_inf_nan=False,strict=True)
    h2s_in_water_ppm: NonNegative
    cyanides_present: bool


@calculation("damage/wet-h2s-environment", "Wet H2S environmental severity and cyanide flag", WetH2sEnvironment,
             ["Part 2 Tables 8.2,9.2; PDF pp187,193"],
             limitations=["The source pH rows leave gaps and the H2S columns overlap at 1000 ppm; these inputs require manual classification and are rejected. Cyanide flag requires upgrading the subsequent susceptibility, not the environmental-severity row."])
def wet_h2s_environment(x):
    p=x.water_ph
    if p<5.5: row=0
    elif p<=7.5: row=1
    elif 7.6<=p<=8.3: row=2
    elif 8.4<=p<=8.9: row=3
    elif p>9: row=4
    else: ensure(False,"Water pH falls in a source-table gap", "ambiguous_source")
    concentration=x.h2s_in_water_ppm
    ensure(concentration!=1000,"Source H2S columns overlap at 1000 ppm", "ambiguous_source")
    column=0 if concentration<50 else (1 if concentration<1000 else (2 if concentration<=10000 else 3))
    rows=[("low","moderate","high","high"),("low","low","low","moderate"),
          ("low","moderate","moderate","moderate"),("low","moderate","moderate","high"),("low","moderate","high","high")]
    return {"environmental_severity":rows[row][column],"susceptibility_upgrade_required":x.cyanides_present and p>8.3 and concentration>1000}


class AcsccSusceptibility(Model):
    water_ph_band: Literal["below_7.5","7.5_to_8","8_to_9","at_least_9"]
    carbonate_ppm: NonNegative
    pwht: bool


@calculation("damage/acscc-susceptibility", "ACSCC carbonate/PWHT susceptibility", AcsccSusceptibility,
             ["Part 2 Table 10.2; PDF p199"], limitations=["Caller selects source pH band and establishes eligible material/service. Band endpoint interpretation is not silently inferred from rounded pH readings."])
def acscc_susceptibility(x):
    if x.pwht or x.water_ph_band=="below_7.5": result="none"
    elif x.water_ph_band=="at_least_9": result="high"
    elif x.carbonate_ppm<100: result="low"
    else: result="medium" if x.water_ph_band=="7.5_to_8" else "high"
    return {"susceptibility":result}


class PasccSusceptibility(Model):
    operating_temperature_k: Positive
    material_group: Literal["regular_300ss_or_alloy600_800","h_grade_300ss","l_grade_300ss","321ss","347ss_alloy20_625_or_austenitic_overlay"]
    heat_treatment: Literal["solution_annealed","stabilized_before_welding","stabilized_after_welding"]


@calculation("damage/pascc-susceptibility", "PASCC temperature/material/heat-treatment susceptibility", PasccSusceptibility,
             ["Part 2 Table 11.2; PDF p205"], limitations=["Eligible material/service must be established separately. Blank heat-treatment cells are unsupported; SI threshold is 427 C."])
def pascc_susceptibility(x):
    hot=x.operating_temperature_k>=700.15
    if x.material_group in ("regular_300ss_or_alloy600_800","h_grade_300ss","l_grade_300ss"):
        ensure(x.heat_treatment=="solution_annealed","Selected PASCC heat-treatment cell is blank", "unsupported_table_cell")
        result={"regular_300ss_or_alloy600_800":("medium","high"),"h_grade_300ss":("high","high"),"l_grade_300ss":("low","medium")}[x.material_group][hot]
    elif x.material_group=="321ss":
        result="low" if x.heat_treatment=="stabilized_after_welding" else ("high" if hot else "medium")
    else:
        result="medium" if hot and x.heat_treatment=="solution_annealed" else "low"
    return {"susceptibility":result}
