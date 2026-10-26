import pytest
from api581.core import DomainError

from api581.api import frequency


@pytest.mark.parametrize(
    "method,route",
    [
        ("structural_reliability", "external_method_result"),
        ("statistical_generic_data", "gff_df_fms"),
        ("expert_judgment", "external_method_result"),
        ("combined", "gff_df_fms"),
    ],
)
def test_pof_method_selection_preserves_api581_method_route(method, route):
    output = frequency.pof_method_selection(
        frequency.PofMethodSelectionInput(
            method=method,
            qualification_basis="qualified component reliability basis",
            uncertainty_quantified=True,
        )
    ).outputs
    assert output.method == method
    assert output.numeric_pof_route == route
    assert output.uncertainty_quantified is True


def test_pof_method_selection_rejects_blank_basis():
    with pytest.raises(DomainError):
        frequency.pof_method_selection(
            frequency.PofMethodSelectionInput(
                method="expert_judgment",
                qualification_basis=" ",
                uncertainty_quantified=False,
            )
        )
