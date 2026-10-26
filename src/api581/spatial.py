"""Bounded planar threshold area on an explicitly triangulated sampled grid."""
import math
from typing import Annotated
from pydantic import Field, model_validator
from .core import Model, Positive, Fraction, calculation, ensure


Coordinate = Annotated[float,Field(strict=True,allow_inf_nan=False)]


class ConcentrationGrid(Model):
    downwind_coordinates_m: list[Coordinate] = Field(min_length=2,max_length=4000)
    crosswind_coordinates_m: list[Coordinate] = Field(min_length=2,max_length=4000)
    volume_fraction_by_crosswind_then_downwind: list[list[Fraction]]
    threshold_volume_fraction: Positive = Field(le=1)
    sampling_basis: str = Field(min_length=1,max_length=1000)

    @model_validator(mode="after")
    def grid(self):
        x,y = self.downwind_coordinates_m,self.crosswind_coordinates_m
        if len(x)*len(y) > 1000000:
            raise ValueError("Spatial grid limited to1000000 nodes")
        if not all(math.isfinite(v) for v in x+y) or any(b <= a for axis in (x,y) for a,b in zip(axis,axis[1:])):
            raise ValueError("Coordinates must be finite and strictly increasing")
        if len(self.volume_fraction_by_crosswind_then_downwind) != len(y) or any(
            len(row) != len(x) for row in self.volume_fraction_by_crosswind_then_downwind):
            raise ValueError("Concentrations must have shape[crosswind][downwind]")
        if not self.sampling_basis.strip():
            raise ValueError("Sampling basis must be nonblank")
        return self


def _triangle_area(vertices,threshold):
    """Clip a linear concentration triangle in a local unit-square frame."""
    clipped = []
    previous = vertices[-1]
    for current in vertices:
        a,b = previous[2] >= threshold,current[2] >= threshold
        if a != b:
            fraction = (threshold-previous[2])/(current[2]-previous[2])
            clipped.append((previous[0]+fraction*(current[0]-previous[0]),
                            previous[1]+fraction*(current[1]-previous[1])))
        if b:
            clipped.append(current[:2])
        previous = current
    if len(clipped) < 3:
        return 0.
    return abs(math.fsum(a[0]*b[1]-b[0]*a[1] for a,b in zip(clipped,clipped[1:]+clipped[:1])))/2


@calculation("dispersion/threshold-grid-area", "Planar concentration exceedance area on a sampled triangulated grid", ConcentrationGrid,
    ["Part3 §§5.8.5-5.8.6,5.9: external spatial concentration footprint boundary"],origin="engineering_spatial_postprocessing",
    limitations=["Numerical postprocessing, not a printed API581 correlation. Each rectangular cell is split along lower-left to upper-right diagonal; concentration is linear on each triangle and the threshold polygon is clipped exactly on that interpolant. Results depend on supplied sampling, not an exact continuous-model contour.",
        "Field is at one common receptor height/time-averaging/source basis. No circular area from centreline distance, vertical cloud mass or multi-weather/event union. Any edge reaching threshold censors the footprint: threshold_area_m2 is null; sampled_exceedance_area_m2 remains the within-grid diagnostic. Below-threshold nodes do not rule out unresolved subgrid peaks; caller must establish resolution/convergence."])
def threshold_grid_area(x):
    xs,ys,c = x.downwind_coordinates_m,x.crosswind_coordinates_m,x.volume_fraction_by_crosswind_then_downwind
    threshold = x.threshold_volume_fraction
    boundaries = []
    for side,values in (("upwind",[r[0] for r in c]),("downwind",[r[-1] for r in c]),
                        ("negative_crosswind",c[0]),("positive_crosswind",c[-1])):
        if any(v >= threshold for v in values):
            boundaries.append(side)
    terms,count = [],0
    for j in range(len(ys)-1):
        dy = ys[j+1]-ys[j]
        for i in range(len(xs)-1):
            dx = xs[i+1]-xs[i]
            cell = dx*dy
            ensure(math.isfinite(cell) and cell > 0,"Spatial cell area outside numerical range","numerical_failure")
            v00,v10,v11,v01 = c[j][i],c[j][i+1],c[j+1][i+1],c[j+1][i]
            if max(v00,v10,v11,v01) < threshold:
                continue
            fraction = 1. if min(v00,v10,v11,v01) >= threshold else (
                _triangle_area([(0.,0.,v00),(1.,0.,v10),(1.,1.,v11)],threshold)
                +_triangle_area([(0.,0.,v00),(1.,1.,v11),(0.,1.,v01)],threshold))
            ensure(0 <= fraction <= 1+1e-12,"Invalid interpolated area fraction","numerical_failure")
            value = min(fraction,1.)*cell
            ensure(value > 0 or fraction == 0,"Positive spatial area underflow","numerical_failure")
            terms.append(value)
            count += value > 0
    area = math.fsum(terms)
    reached = any(v >= threshold for row in c for v in row)
    return {"sampled_exceedance_area_m2":area,"threshold_area_m2":None if boundaries else area,
        "footprint_status":"boundary_censored" if boundaries else "closed_on_supplied_grid" if reached else "not_reached",
        "boundary_sides":boundaries,"positive_area_cell_count":count,
        "downwind_node_count":len(xs),"crosswind_node_count":len(ys),
        "interpolation_basis":"piecewise_linear_main_diagonal_triangles"}
