"""Explicit historical toxic-criterion priority with exposure-duration matching."""
import math
from typing import Literal
from pydantic import Field, model_validator
from .core import Model, Positive, Fraction, calculation, ensure, finite_tree
from .toxic_level2 import ToxicFluid, SpeciesThreshold, impact_table, species_threshold, MixtureLimit, mixture_limit, _ROWS, _TABLE_LIMIT

Kind = Literal["probit50","lc50","erpg3","aegl3","teel3","idlh","epa_endpoint"]
_TIER = dict(probit50=1,lc50=1,erpg3=2,aegl3=2,teel3=2,idlh=3,epa_endpoint=3)


class CriterionCandidate(Model):
    criterion_id: str = Field(min_length=1,max_length=100)
    kind: Kind
    concentration_ppm: Positive = Field(le=1e6)
    exposure_duration_s: Positive
    source: str = Field(min_length=1,max_length=1000)

    @model_validator(mode="after")
    def source_basis(self):
        if not self.criterion_id.strip() or not self.source.strip():
            raise ValueError("Criterion id and source must be nonblank")
        windows = {"idlh":{1800.},"erpg3":{3600.},"teel3":{900.},"aegl3":{600.,1800.,3600.}}
        if self.kind in windows and self.exposure_duration_s not in windows[self.kind]:
            raise ValueError("Criterion duration conflicts with API5812016 exposure windows")
        return self


class ToxicCriterion(Model):
    fluid_id: str = Field(min_length=1,max_length=100)
    exposure_duration_s: Positive
    use_printed_table: bool = True
    additional_candidates: list[CriterionCandidate] = Field(default_factory=list,max_length=50)
    excluded_candidate_ids: dict[str,str] = Field(default_factory=dict)
    selected_criterion_id: str | None = Field(default=None,min_length=1,max_length=100)
    toxic_mole_fraction: Fraction = 1.
    candidate_availability_basis: str = Field(min_length=1,max_length=1000)


@calculation("consequence/select-toxic-criterion", "Select duration-matched toxic criterion by API581 priority", ToxicCriterion,
    ["Part3 §5.9.2,Table4.14,eqs(3.189)-(3.190); PDF pp531,565-567"],
    origin="api581_explicit_toxic_criterion_selection",limitations=[_TABLE_LIMIT,
        "Only provided candidates and the enabled historical table snapshot are considered, not an external literature/current-limit search. Caller declares candidate availability/applicability; named exclusions require a nonblank basis. Printed probit uses50% fatality and supplied exposure seconds. Same-priority ties require explicit selection, not minimum/maximum of incomparable limits.",
        "Exposure durations match exactly. Printed IDLH uses1800s, ERPG3600s, AEGL600/1800/3600 only where available. LC50/TEEL/EPA ppm must be owner-qualified candidates; EPA mg/L is not silently converted. A lower-priority selection cannot override an eligible higher-priority candidate without explicit exclusion.",
        "Mixture threshold divides pure-component ppm by toxic MOLE fraction once. Zero fraction means absent component; mathematically above1e6ppm is unattainable, not capped. Returned threshold is a criterion, not a field exposure duration or validated damage footprint."])
def select_criterion(x):
    ensure(x.fluid_id.strip() and x.candidate_availability_basis.strip(),"Fluid and availability bases must be nonblank")
    external_ids = [c.criterion_id for c in x.additional_candidates]
    ensure(len(set(external_ids)) == len(external_ids),"Duplicate external criterion id")
    ensure(all(not key.startswith("printed:") for key in external_ids),"External ids must not use reserved printed: prefix")
    candidates,unavailable = [],{}
    def add(identifier,kind,value,source):
        candidates.append(dict(criterion_id=identifier,kind=kind,concentration_ppm=value,
            exposure_duration_s=x.exposure_duration_s,source=source))
    if x.use_printed_table:
        ensure(x.fluid_id in _ROWS,"Unknown2016 toxic fluid; disable printed table only with qualified external candidates","unsupported_toxic_fluid")
        row = impact_table(ToxicFluid(fluid=x.fluid_id))
        if row["probit_available"]:
            ppm = species_threshold(SpeciesThreshold(fluid=x.fluid_id,exposure_duration_s=x.exposure_duration_s,
                target_fatality_probability=.5))["concentration_ppm"]
            add("printed:probit50","probit50",ppm,"2016 Table4.14/Annex3.A probit50; time seconds")
        else:
            unavailable["printed:probit50"] = "No printed probit coefficients"
        for identifier,kind,value,required in (("printed:idlh","idlh",row["idlh_ppm"],1800.),
                                               ("printed:erpg3","erpg3",row["erpg3_ppm"],3600.)):
            if value is None:
                unavailable[identifier] = "No printed value"
            elif x.exposure_duration_s != required:
                unavailable[identifier] = f"Requires exposure{required:g}s"
            else:
                add(identifier,kind,value,"2016 Table4.14 historical "+kind)
        aegl = row["aegl3_ppm"].get(str(int(x.exposure_duration_s))) if x.exposure_duration_s.is_integer() else None
        if aegl is None:
            unavailable["printed:aegl3"] = "No printed value at selected exposure duration"
        else:
            add("printed:aegl3","aegl3",aegl,"2016 Table4.14 AEGL3 at selected duration")
        if row["epa_toxic_endpoint_mg_l"] is not None:
            unavailable["printed:epa_endpoint"] = "Published mg/L needs explicit qualified ppm conversion; provide external candidate"
    for candidate in x.additional_candidates:
        if candidate.exposure_duration_s == x.exposure_duration_s:
            candidates.append(candidate.model_dump())
        else:
            unavailable[candidate.criterion_id] = "Exposure duration mismatch"
    ids = [c["criterion_id"] for c in candidates]
    ensure(len(set(ids)) == len(ids),"Duplicate eligible criterion id")
    for identifier,basis in x.excluded_candidate_ids.items():
        ensure(identifier in ids,"Exclusion must name an eligible candidate")
        ensure(basis.strip(),"Criterion exclusion basis must be nonblank")
    eligible = [c for c in candidates if c["criterion_id"] not in x.excluded_candidate_ids]
    ensure(eligible,"No eligible duration-matched toxic criterion","toxic_criterion_unavailable")
    tier = min(_TIER[c["kind"]] for c in eligible)
    first = [c for c in eligible if _TIER[c["kind"]] == tier]
    if x.selected_criterion_id is None:
        ensure(len(first) == 1,"Same-priority criteria require explicit selected_criterion_id","ambiguous_toxic_criterion")
        selected = first[0]
    else:
        matching = [c for c in eligible if c["criterion_id"] == x.selected_criterion_id]
        ensure(matching,"Selected criterion must be eligible")
        selected = matching[0]
        ensure(_TIER[selected["kind"]] == tier,"Eligible higher-priority criterion must be excluded explicitly","toxic_criterion_priority_conflict")
    mixture = mixture_limit(MixtureLimit(pure_component_limit_ppm=selected["concentration_ppm"],toxic_mole_fraction=x.toxic_mole_fraction))
    finite_tree(mixture)
    fraction = mixture["modified_mixture_limit_ppm"]/1e6 if mixture["component_present"] and mixture["attainable_in_mixture"] else None
    ensure(fraction is None or fraction > 0,"Toxic volume fraction underflow","numerical_failure")
    return {"fluid_id":x.fluid_id,"selected_criterion_id":selected["criterion_id"],"selected_kind":selected["kind"],
        "priority_tier":tier,"pure_component_limit_ppm":selected["concentration_ppm"],
        "modified_mixture_limit_ppm":mixture["modified_mixture_limit_ppm"],"threshold_volume_fraction":fraction,
        "component_present":mixture["component_present"],"attainable_in_mixture":mixture["attainable_in_mixture"],
        "exposure_duration_s":x.exposure_duration_s,"criterion_source":selected["source"],
        "eligible_candidate_ids":[c["criterion_id"] for c in eligible],"excluded_candidate_ids":x.excluded_candidate_ids,
        "unavailable_candidate_reasons":unavailable}
