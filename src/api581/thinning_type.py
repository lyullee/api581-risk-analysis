"""API 581 Annex 2.B thinning-type designation."""

from typing import Literal
from pydantic import Field
from .core import Model, calculation, ensure


class ThinningTypeSelection(Model):
    effective_inspection_types: list[Literal["general", "localized"]] = Field(default_factory=list, max_length=100)
    applicable_mechanism_types: list[Literal["general", "localized"]] = Field(min_length=1, max_length=100)
    qualification_basis: str = Field(min_length=1, max_length=1000)


@calculation(
    "damage/thinning-type",
    "API 581 Annex 2.B.1.2 general versus localized thinning designation",
    ThinningTypeSelection,
    ["Part 2 Annex B §1.2; Part 2 §4.5.2, PDF p321"],
    origin="api581_annex_2b1_2_thinning_type_selection",
    limitations=[
        "Effective inspection designation takes precedence. If no effective inspection type is supplied, any applicable localized mechanism conservatively selects localized thinning. This API does not screen mechanisms or calculate corrosion rates.",
        "The caller must qualify the mechanism list and inspection effectiveness; an empty inspection list is treated as unknown, not as evidence of general thinning."
    ],
)
def thinning_type(x):
    ensure(x.qualification_basis.strip(), "Thinning-type qualification basis must be nonblank")
    observed = x.effective_inspection_types
    source = "effective_inspection_results" if observed else "applicable_mechanism_conservative_default"
    types = observed or x.applicable_mechanism_types
    selected = "localized" if "localized" in types else "general"
    return {"thinning_type": selected, "selection_source": source,
            "effective_inspection_types": observed,
            "applicable_mechanism_types": x.applicable_mechanism_types,
            "qualification_basis": x.qualification_basis}
