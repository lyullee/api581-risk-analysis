import api581


def test_effectiveness_summary_promotes_two_category_b_inspections():
    result = api581.evaluate(
        "inspection/effectiveness-summary",
        {"mechanism": "scc", "categories": ["A", "B", "B", "E"]},
    )
    assert result["outputs"] == {
        "mechanism": "scc",
        "highest_effectiveness_category": "A",
        "inspection_count": 4,
        "creditable_inspection_count": 3,
        "counts": {"a": 1, "b": 2, "c": 0, "d": 0, "e": 1},
        "equivalent_counts": {"a": 2, "b": 0, "c": 0, "d": 0},
        "e_inspection_count": 1,
        "qualification_status": "caller_qualified_categories",
    }

