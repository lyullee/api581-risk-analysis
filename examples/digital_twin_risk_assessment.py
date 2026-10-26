"""Run a damage-composed API 581 risk assessment through the twin envelope."""
import _bootstrap  # noqa: F401
from datetime import datetime, timezone

from api581.digital_twin import TwinCalculationRequest, execute_request


request = TwinCalculationRequest(
    request_id="req-risk-001",
    calculation_id="risk/assessment-from-damage",
    asset_id="asset-demo",
    component_id="pipe-8-demo",
    observed_at=datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc),
    source_revision="demo-revision-1",
    correlation_id="demo-correlation-1",
    inputs={
        "component_type": "PIPE-8",
        "management_score": 20,
        "damage": {
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
        },
        "damage_factor_source": "qualified mechanism outputs",
        "consequences": [
            {"hole": "small", "equipment_area_m2": 1.0, "personnel_area_m2": 2.0, "financial_consequence": 10.0},
            {"hole": "medium", "equipment_area_m2": 2.0, "personnel_area_m2": 3.0, "financial_consequence": 20.0},
            {"hole": "large", "equipment_area_m2": 3.0, "personnel_area_m2": 4.0, "financial_consequence": 30.0},
            {"hole": "rupture", "equipment_area_m2": 4.0, "personnel_area_m2": 5.0, "financial_consequence": 40.0},
        ],
        "consequence_source": "qualified four-hole consequence outputs",
        "currency": "USD",
    },
)

response = execute_request(request)
print("risk scope:", response.outputs["integration_scope"])
print("financial risk/year:", response.outputs["risk"]["financial_risk_per_year"])
