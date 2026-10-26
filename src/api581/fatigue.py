"""Mechanical fatigue of piping, Part 2 §24; category choices are explicit."""
from typing import Literal
from pydantic import Field
from .core import Model, calculation


class FatigueBase(Model):
    previous_failure_count: int = Field(ge=0,strict=True)
    shaking_severity: Literal["minor","moderate","severe"]
    shaking_duration_band: Literal["less_than_2_weeks","2_to_13_weeks","13_to_52_weeks"]
    cyclic_loading: Literal["reciprocating_machinery","prv_chatter","high_pressure_drop_valve","none"]


@calculation("damage/fatigue-base", "Piping mechanical fatigue base factor", FatigueBase,
             ["Part 2 §24.6.3 STEP 1-5, eq (2.92); PDF p289"], limitations=["Piping only; caller selects vibration/duration band. Source gives no explicit duration factor above 52 weeks or unique numeric classification at 13 weeks."])
def fatigue_base(x):
    previous=1 if x.previous_failure_count==0 else (50 if x.previous_failure_count==1 else 500)
    shaking={"minor":1,"moderate":50,"severe":500}[x.shaking_severity]
    duration={"less_than_2_weeks":1,"2_to_13_weeks":.2,"13_to_52_weeks":.02}[x.shaking_duration_band]
    cyclic={"reciprocating_machinery":50,"prv_chatter":25,"high_pressure_drop_valve":10,"none":1}[x.cyclic_loading]
    return {"previous_failure_factor":previous,"shaking_factor":shaking,"shaking_duration_factor":duration,
            "cyclic_loading_factor":cyclic,"base_damage_factor":max(previous,shaking*duration,cyclic)}


class FatigueAdjustments(Model):
    corrective_action: Literal["complete_engineering_analysis","experience_based_modification","none"]
    total_pipe_fittings: int = Field(ge=0,strict=True)
    damaged_or_improper_supports: bool
    broken_or_directly_welded_gussets: bool
    branch_design: Literal["threaded_socketweld_saddle_on","saddle_in","tee_or_weldolet","sweepolet"]
    any_branch_above_nps_2: bool


@calculation("damage/fatigue-adjustments", "Piping mechanical fatigue adjustment factors", FatigueAdjustments,
             ["Part 2 §24.6.3 STEP 6, eq (2.93); PDF p290"])
def fatigue_adjustments(x):
    factors={"corrective_action_factor":{"complete_engineering_analysis":.002,"experience_based_modification":.2,"none":2}[x.corrective_action],
             "complexity_factor":.5 if x.total_pipe_fittings<=5 else (1 if x.total_pipe_fittings<=10 else 2),
             "pipe_condition_factor":2 if x.damaged_or_improper_supports or x.broken_or_directly_welded_gussets else 1,
             "joint_branch_factor":{"threaded_socketweld_saddle_on":2,"saddle_in":1,"tee_or_weldolet":.2,"sweepolet":.02}[x.branch_design],
             "branch_diameter_factor":.02 if x.any_branch_above_nps_2 else 1}
    import math
    return {**factors,"combined_adjustment_factor":math.prod(factors.values())}


class FatigueAssessment(Model):
    base: FatigueBase
    adjustments: FatigueAdjustments


@calculation("damage/mechanical-fatigue", "Piping mechanical fatigue damage factor", FatigueAssessment,
             ["Part 2 eqs (2.92)-(2.93)"], limitations=["Piping only; qualitative categories supplied by caller. Not a stress-range/cycle-count fatigue life or FFS calculation."])
def mechanical_fatigue(x):
    base=fatigue_base(x.base)
    factors=fatigue_adjustments(x.adjustments)
    return {**base,**factors,"damage_factor":base["base_damage_factor"]*factors["combined_adjustment_factor"]}
