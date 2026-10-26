import api581


def test_pof_method_selection_combined_route():
    result = api581.evaluate(
        "frequency/pof-method-selection",
        {
            "method": "combined",
            "qualification_basis": "Qualified plant reliability program and generic API 581 data",
            "uncertainty_quantified": True,
        },
    )
    assert result["outputs"] == {
        "method": "combined",
        "qualification_basis": "Qualified plant reliability program and generic API 581 data",
        "uncertainty_quantified": True,
        "numeric_pof_route": "gff_df_fms",
    }

