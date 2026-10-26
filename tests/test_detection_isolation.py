import pytest
from api581.api import release


def inp(**changes):
    return release.DetectionIsolationInput(**({
        'detection_rating': 'A', 'isolation_rating': 'A', 'hole_size': 'small',
        'theoretical_rate_kg_s': 10., 'available_mass_kg': 10000.
    } | changes))


@pytest.mark.parametrize('detection,isolation,reduction', [
    ('A','A',.25), ('A','B',.20), ('A','C',.10),
    ('B','A',.10), ('B','B',.15), ('B','C',.10),
    ('C','A',0.), ('C','B',0.), ('C','C',0.)])
def test_table_46_all_printed_rating_pairs(detection, isolation, reduction):
    result = release.detection_isolation(inp(
        detection_rating=detection, isolation_rating=isolation)).outputs
    assert result.release_reduction_fraction == reduction


@pytest.mark.parametrize('hole,seconds', [
    ('small', 20*60), ('medium', 10*60), ('large', 5*60)])
def test_table_47m_duration_and_mass(hole, seconds):
    result = release.detection_isolation(inp(hole_size=hole)).outputs
    assert result.maximum_leak_duration_s == seconds
    assert result.adjusted_rate_kg_s == 7.5
    assert result.duration_s == seconds
    assert result.released_mass_kg == 7.5 * seconds


def test_rupture_has_no_table_duration_and_uses_available_mass():
    result = release.detection_isolation(inp(hole_size='rupture')).outputs
    assert result.maximum_leak_duration_s is None
    assert result.duration_s is None
    assert result.released_mass_kg == 10000.


@pytest.mark.parametrize('detection_type,detection_rating', [
    ('process_instrumentation', 'A'),
    ('outside_envelope_detector', 'B'),
    ('visual_or_marginal', 'C')])
@pytest.mark.parametrize('isolation_type,isolation_rating', [
    ('automatic_instrument_or_detector', 'A'),
    ('remote_operator', 'B'),
    ('manual_valve', 'C')])
def test_table_45_qualitative_rating_map(detection_type, detection_rating,
                                         isolation_type, isolation_rating):
    result = release.detection_isolation_rating(
        release.DetectionIsolationRatingInput(
            detection_type=detection_type, isolation_type=isolation_type,
            qualification_basis='Owner evidence and coverage review')).outputs
    assert result.detection_rating == detection_rating
    assert result.isolation_rating == isolation_rating


def test_table_45_qualification_basis_required():
    with pytest.raises(Exception):
        release.detection_isolation_rating(release.DetectionIsolationRatingInput(
            detection_type='process_instrumentation', isolation_type='remote_operator',
            qualification_basis=' '))


@pytest.mark.parametrize('basis,diameter,hole,representative', [
    ('printed_si', 0., 'small', .0064),
    ('printed_si', .0064, 'small', .0064),
    ('printed_si', .006400001, 'medium', .025),
    ('printed_si', .051, 'medium', .025),
    ('printed_si', .051000001, 'large', .102),
    ('printed_si', .152, 'large', .102),
    ('printed_si', .152000001, 'rupture', .4064),
    ('printed_us_converted', .00635, 'small', .00635),
    ('printed_us_converted', .0508, 'medium', .0254),
    ('printed_us_converted', .1524, 'large', .1016),
])
def test_table_44_hole_boundaries_and_representatives(basis, diameter, hole, representative):
    result = release.hole_size_selection(release.HoleSizeSelectionInput(
        hole_diameter_m=diameter, component_diameter_m=.8,
        diameter_basis=basis)).outputs
    assert result.selected_hole == hole
    assert result.representative_diameter_m == pytest.approx(representative)


def test_table_44_rupture_representative_is_capped_by_component_diameter():
    result = release.hole_size_selection(release.HoleSizeSelectionInput(
        hole_diameter_m=.3, component_diameter_m=.2,
        diameter_basis='printed_si')).outputs
    assert result.selected_hole == 'rupture'
    assert result.representative_diameter_m == .2
