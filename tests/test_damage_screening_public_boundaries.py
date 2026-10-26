"""Direct public evaluate() checks for selected damage screening primitives."""

from api581 import evaluate
from test_amine_figure import request as amine_figure_request
from test_caustic_screening import susceptibility as caustic_figure_request


def test_damage_figure_susceptibility_public_boundaries():
    amine = evaluate("damage/amine-figure-susceptibility", amine_figure_request().model_dump())
    caustic = evaluate("damage/caustic-figure-susceptibility", caustic_figure_request().model_dump())
    assert amine["outputs"]["susceptibility"] in {"none", "low", "medium", "high"}
    assert caustic["outputs"]["susceptibility"] in {"none", "low", "medium", "high"}


def test_damage_contaminant_and_ssc_public_boundaries():
    contaminant = evaluate("damage/amine-contaminant-row", {
        "amine_type": "mea",
        "contaminant_mass_fraction": 0.03,
        "mdea_scale_policy": "not_mdea",
    })
    ssc = evaluate("damage/ssc-qualified-susceptibility", {
        "environment": {"water_ph": 8.5, "h2s_in_water_ppm": 2000.0, "cyanides_present": False},
        "measured_brinnell_hardness": 220.0,
        "pwht": True,
        "service_basis": "Qualified SSC service screening fixture",
    })
    assert contaminant["outputs"]["contaminant_row"]
    assert ssc["outputs"]["susceptibility"] in {"none", "low", "medium", "high"}

