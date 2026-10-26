from scripts.build_inventory import attach_ancestor_evidence


def clause(key, ids=()):
    return dict(id=key, calculation_ids=list(ids), status='not_implemented')


def test_ancestor_evidence_is_partial_and_traceable_not_sibling_or_other_part():
    rows=[clause('Part 2 §4'),clause('Part 2 §4.1',['a']),clause('Part 2 §40.1',['b']),clause('Part 3 §4.1',['c'])]
    attach_ancestor_evidence(rows)
    assert rows[0]['calculation_ids']==['a']
    assert rows[0]['assigned_calculation_ids']==[]
    assert rows[0]['descendant_evidence_clause_ids']==['Part 2 §4.1']
    assert rows[0]['status']=='partial' and rows[0]['evidence_basis']=='descendant_links_only'


def test_existing_assignment_retained_and_nested_evidence_not_invented():
    rows=[clause('Part 2 §4',['a']),clause('Part 2 §4.1'),clause('Part 2 §4.1.1',['b','b'])]
    attach_ancestor_evidence(rows)
    assert rows[0]['assigned_calculation_ids']==['a'] and rows[0]['calculation_ids']==['a','b']
    assert rows[0]['descendant_evidence_clause_ids']==['Part 2 §4.1.1']
    assert rows[1]['assigned_calculation_ids']==[] and rows[1]['descendant_calculation_ids']==['b']
    assert all(r['status']=='partial' for r in rows)


def test_unlinked_clause_stays_unimplemented():
    rows=[clause('Part 2 §4'),clause('Part 2 §4.1')]
    attach_ancestor_evidence(rows)
    assert all(r['status']=='not_implemented' and r['evidence_basis']=='no_registered_link' for r in rows)


def test_repeated_aggregation_does_not_promote_inherited_links_to_assignments():
    from copy import deepcopy
    rows=[clause('Part 2 §4'),clause('Part 2 §4.1'),clause('Part 2 §4.1.1',['a'])]
    attach_ancestor_evidence(rows)
    once=deepcopy(rows)
    attach_ancestor_evidence(rows)
    assert rows==once
    assert rows[0]['assigned_calculation_ids']==rows[1]['assigned_calculation_ids']==[]
    assert rows[0]['descendant_evidence_clause_ids']==['Part 2 §4.1.1']


def test_removing_child_evidence_does_not_leave_stale_parent_claim():
    rows=[clause('Part 2 §4'),clause('Part 2 §4.1',['a'])]
    attach_ancestor_evidence(rows)
    rows.pop()
    attach_ancestor_evidence(rows)
    assert rows[0]['status']=='not_implemented'
    assert rows[0]['calculation_ids']==[]


def test_packaged_inventory_keeps_part1_prd_and_bundle_toc_pages():
    from api581 import coverage
    sections = coverage()['sections']
    ids = {item['id'] for item in sections}
    assert 'Part 1 §7' in ids
    assert 'Part 1 §7.1.2' in ids
    assert 'Part 1 §8' in ids
    assert 'Part 1 §8.3.2' in ids


def test_packaged_inventory_has_no_unimplemented_technical_scope_headings():
    from api581 import coverage
    technical_missing = [item for item in coverage()['sections']
                         if item['status'] == 'not_implemented'
                         and item['review_category'] == 'technical_scope_review']
    assert technical_missing == []
