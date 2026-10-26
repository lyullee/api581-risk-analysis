"""Qualified API581 rainout/flash partition -> actual native jet source."""
import math
from pydantic import Field
from .core import Model, Positive, REGISTRY, calculation, ensure, finite_tree
from .source_partition import SourcePartition, source_partition
from .slabx_adapter import NativeJetGeometry, NativeJet, NativeJetFootprint, native_jet, native_jet_footprint


class PartitionedJet(Model):
    partition: SourcePartition
    jet: NativeJetGeometry


class JetFootprintGeometry(NativeJetGeometry):
    crosswind_half_span_m: Positive
    crosswind_points_per_side: int = Field(default=65,ge=3,le=501,strict=True)


class PartitionedJetFootprint(Model):
    partition: SourcePartition
    jet: JetFootprintGeometry


_LIMITS = [*["Source-partition stage only: "+item for item in REGISTRY["release/level2-source-partition"].limitations],
    *REGISTRY["dispersion/native-jet-centreline"].limitations,
    "Native q is partition jet-total vapor+droplet rate; liquid MASS fraction is partition entrained-liquid fraction. Duration is jet mass/rate from same partition. No independent duplicate source rate/composition/duration accepted. Pool rainout remains a separate source, not added to native jet. Empty/zero-duration jet and pure-liquid jet fail explicitly. Caller still qualifies effective atmospheric exit area, temperature, flash/rainout data and native source applicability."]


def _handoff(x,footprint):
    partition = source_partition(x.partition)
    finite_tree(partition)
    q,mass = partition["jet_total_rate_kg_s"],partition["jet_total_mass_kg"]
    ensure(q > 0 and mass > 0 and partition["jet_fraction_nonzero"],"Partition has no positive finite-duration jet source","empty_jet_source")
    liquid = partition["entrained_liquid_mass_fraction"]
    ensure(liquid is not None and 0 <= liquid < 1,"Native jet cannot accept pure liquid/no-vapor partition","unsupported_engine_source_domain")
    duration = mass/q
    ensure(math.isfinite(duration) and duration > 0,"Jet handoff duration outside numerical range","numerical_failure")
    if x.jet.temperature_basis == "require_consistent":
        boiling = x.jet.substance.normal_boiling_point_k
        ensure(x.jet.source_temperature_k >= boiling and (liquid == 0 or x.jet.source_temperature_k == boiling),
            "Partition composition conflicts with required native source temperature","native_source_state_inconsistent")
    model = NativeJetFootprint if footprint else NativeJet
    request = model(**x.jet.model_dump(),mass_source_rate_kg_s=q,release_duration_s=duration,jet_liquid_mass_fraction=liquid)
    output = (native_jet_footprint if footprint else native_jet)(request)
    return {**output,**partition,"release_duration_s":duration,"integration_scope":"qualified_partition_to_native_jet"}


@calculation("dispersion/partitioned-jet-centreline", "API581 source partition through native jet centreline", PartitionedJet,
    [*REGISTRY["release/level2-source-partition"].references,*REGISTRY["dispersion/native-jet-centreline"].references],
    origin="api581_partition_to_native_jet_composition",limitations=_LIMITS)
def partitioned_jet(x):
    return _handoff(x,False)


@calculation("dispersion/partitioned-jet-footprint", "API581 source partition through native planar jet footprint", PartitionedJetFootprint,
    [*REGISTRY["release/level2-source-partition"].references,*REGISTRY["dispersion/native-jet-footprint"].references],
    origin="api581_partition_to_native_jet_spatial_composition",limitations=_LIMITS+[
        "Area is sampled-grid triangular interpolation and needs spatial convergence. Source/handoff-edge concentration, outer-grid exceedance or LH2 premise violation censors usable area; diagnostic field/area preserved. No missing near-field completion or source-face extrapolation."])
def partitioned_jet_footprint(x):
    return _handoff(x,True)
