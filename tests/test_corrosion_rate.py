import pytest

from api581.api import damage
from api581.core import DomainError


def test_measured_corrosion_rate_uses_direct_thickness_difference():
    result = damage.measured_corrosion_rate(
        damage.MeasuredCorrosionRateInput(
            initial_thickness_m=0.012,
            current_thickness_m=0.010,
            elapsed_years=4,
            measurement_basis="same CML, comparable UT method",
        )
    ).outputs
    assert result.metal_loss_m == pytest.approx(0.002)
    assert result.corrosion_rate_m_year == pytest.approx(0.0005)
    assert result.rate_basis == "direct_two_thickness_difference"


def test_measured_corrosion_rate_rejects_thickness_gain():
    with pytest.raises(DomainError, match="cannot exceed"):
        damage.measured_corrosion_rate(
            damage.MeasuredCorrosionRateInput(
                initial_thickness_m=0.010,
                current_thickness_m=0.011,
                elapsed_years=4,
                measurement_basis="inconsistent baseline",
            )
        )


def test_thinning_type_prefers_effective_localized_inspection_result():
    result = damage.thinning_type(
        damage.ThinningTypeInput(
            effective_inspection_types=["general", "localized"],
            applicable_mechanism_types=["general"],
            qualification_basis="qualified inspection history",
        )
    ).outputs
    assert result.thinning_type == "localized"
    assert result.selection_source == "effective_inspection_results"


def test_thinning_type_defaults_conservatively_to_localized_mechanism():
    result = damage.thinning_type(
        damage.ThinningTypeInput(
            applicable_mechanism_types=["general", "localized"],
            qualification_basis="qualified mechanism screening",
        )
    ).outputs
    assert result.thinning_type == "localized"
    assert result.selection_source == "applicable_mechanism_conservative_default"
