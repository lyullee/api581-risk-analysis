"""Independent planar-area anchors and sampled-Gaussian convergence."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import dispersion


def grid(x=None,y=None,c=None,**changes):
    return dispersion.ThresholdGridAreaInput(**(dict(downwind_coordinates_m=x if x is not None else [0.,1.],
        crosswind_coordinates_m=y if y is not None else [0.,1.],
        volume_fraction_by_crosswind_then_downwind=c if c is not None else [[0.,1.],[0.,1.]],
        threshold_volume_fraction=.5,sampling_basis="Qualified analytic test field")|changes))


def test_linear_half_plane_has_exact_half_rectangle_area():
    r = dispersion.threshold_grid_area(grid()).outputs
    assert r.sampled_exceedance_area_m2 == .5
    assert r.threshold_area_m2 is None and r.footprint_status == "boundary_censored"
    assert set(r.boundary_sides) == {"downwind","negative_crosswind","positive_crosswind"}


def test_closed_six_vertex_threshold_polygon_area():
    # For the specified main diagonals, threshold vertices are
    # (.5,.5),(1,.5),(1.5,1),(1.5,1.5),(1,1.5),(.5,1): shoelace area.75.
    r = dispersion.threshold_grid_area(grid([0.,1.,2.],[0.,1.,2.],[[0,0,0],[0,1,0],[0,0,0]])).outputs
    assert r.threshold_area_m2 == pytest.approx(.75)
    assert r.footprint_status == "closed_on_supplied_grid" and not r.boundary_sides


def test_uniform_threshold_plateau_fills_rectangle_and_is_censored():
    r = dispersion.threshold_grid_area(grid([0.,2.],[-3.,3.],[[.5,.5],[.5,.5]])).outputs
    assert r.sampled_exceedance_area_m2 == 12
    assert len(r.boundary_sides) == 4


def test_no_threshold_reached_is_zero_not_missing_engine_result():
    r = dispersion.threshold_grid_area(grid(c=[[0.,.1],[.1,0.]])).outputs
    assert r.sampled_exceedance_area_m2 == r.threshold_area_m2 == 0
    assert r.footprint_status == "not_reached"


def gaussian(n):
    x = [-12.+24.*i/(n-1) for i in range(n)]
    y = [-18.+36.*i/(n-1) for i in range(n)]
    return dispersion.threshold_grid_area(grid(x,y,[[.8*math.exp(-.5*((a/2)**2+(b/3)**2)) for a in x] for b in y],
        threshold_volume_fraction=.2)).outputs


def test_gaussian_ellipse_converges_to_independent_analytic_area():
    exact = 2*math.pi*2*3*math.log(.8/.2)
    coarse,fine = gaussian(21),gaussian(81)
    assert fine.threshold_area_m2 == pytest.approx(exact,rel=.003)
    assert abs(fine.threshold_area_m2-exact) < abs(coarse.threshold_area_m2-exact)


def test_coordinate_translation_and_area_scale_invariance():
    c = [[0,0,0],[0,1,0],[0,0,0]]
    a = dispersion.threshold_grid_area(grid([0.,1.,2.],[0.,1.,2.],c)).outputs
    b = dispersion.threshold_grid_area(grid([1e9,1e9+2,1e9+4],[-1e9,-1e9+3,-1e9+6],c)).outputs
    assert b.threshold_area_m2 == pytest.approx(a.threshold_area_m2*6)


@pytest.mark.parametrize("x,y,c",[
    ([0.,0.],[0.,1.],[[0.,1.],[0.,1.]]),
    ([1.,0.],[0.,1.],[[0.,1.],[0.,1.]]),
    ([0.,float("inf")],[0.,1.],[[0.,1.],[0.,1.]]),
    ([0.,1.],[0.,1.],[[0.,1.]]),
    ([0.,1.],[0.,1.],[[0.,2.],[0.,1.]]),
    ([False,1.],[0.,1.],[[0.,1.],[0.,1.]])])
def test_invalid_or_unqualified_spatial_grid_rejected(x,y,c):
    with pytest.raises(ValidationError):
        grid(x,y,c)


def test_coordinate_area_overflow_is_explicit():
    with pytest.raises(DomainError) as exc:
        dispersion.threshold_grid_area(grid([-1e308,1e308],[-1e308,1e308],[[1,1],[1,1]]))
    assert exc.value.code == "numerical_failure"
