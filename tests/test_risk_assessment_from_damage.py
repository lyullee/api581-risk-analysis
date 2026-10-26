from api581.api import risk


def damage():
    return {
        "thinning": 2.0,
        "lining": None,
        "external": [1.5],
        "scc": [0.0],
        "htha": 0.0,
        "fatigue": 0.0,
        "brittle_fracture": 0.0,
        "temper_embrittlement": 0.0,
        "embrittlement_885f": 0.0,
        "sigma_embrittlement": 0.0,
        "thinning_external_distribution": "local",
    }


def consequences():
    return [
        {"hole": "small", "equipment_area_m2": 1.0, "personnel_area_m2": 2.0, "financial_consequence": 10.0},
        {"hole": "medium", "equipment_area_m2": 2.0, "personnel_area_m2": 3.0, "financial_consequence": 20.0},
        {"hole": "large", "equipment_area_m2": 3.0, "personnel_area_m2": 4.0, "financial_consequence": 30.0},
        {"hole": "rupture", "equipment_area_m2": 4.0, "personnel_area_m2": 5.0, "financial_consequence": 40.0},
    ]


def test_assessment_from_damage_combines_mechanisms_before_risk():
    result = risk.assessment_from_damage(
        risk.AssessmentFromDamageInput(
            component_type="PIPE-8",
            management_score=20,
            damage=damage(),
            damage_factor_source="qualified mechanism outputs",
            consequences=consequences(),
            consequence_source="qualified four-hole consequence outputs",
            currency="USD",
        )
    ).outputs
    assert result.integration_scope == "combined_damage_and_supplied_consequences"
    assert result.damage_factor.total_damage_factor == 2.0
    assert result.risk.financial_risk_per_year > 0
    assert len(result.scenarios) == 4
