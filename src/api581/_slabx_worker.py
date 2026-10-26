"""Internal JSON worker for process-isolated optional native engines."""
import contextlib
from decimal import Decimal
import hashlib
import importlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import sys
from .core import DomainError, ensure, finite_tree
from .slabx_adapter import NativePool, NativePoolFootprint, NativeJet, NativeJetFootprint


def _fingerprint(package):
    root = Path(importlib.import_module(package).__file__).parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_native(x):
    required = {"slabx":"1.0.8"}
    if x.engine == "slabx-lh2":
        required["slabx-lh2"] = "0.2.0"
    versions = {}
    for name,expected in required.items():
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise DomainError("engine_not_configured",f"Optional package {name} not installed") from exc
        ensure(versions[name] == expected,f"Native mapping requires {name}=={expected}; installed {versions[name]}","unsupported_engine_version")
    from slabx.core.plume import run_dispersion
    from slabx.core.source import EvaporatingPool, HorizontalJet
    from slabx.post.concentration import concentration_field
    from slabx.submodels.atmosphere import Atmosphere
    from slabx.thermo.base import Substance, LegacyThermo, water_backend
    s,a = x.substance,x.atmosphere
    # Canonical decimal SI-prefix conversion avoids a one-ULP difference from
    # a native kg/mol decimal literal changing the adaptive integration grid.
    molecular_weight = float(Decimal(str(s.molecular_weight_kg_kmol))/Decimal(1000))
    substance = Substance(name=s.fluid_id,mw=molecular_weight,
        cp_vapour=s.vapor_heat_capacity_j_kg_k,cp_liquid=s.liquid_heat_capacity_j_kg_k,
        dh_vap=s.latent_heat_j_kg,T_boil=s.normal_boiling_point_k,rho_liquid=s.liquid_density_kg_m3)
    atmosphere = Atmosphere(u_ref=a.wind_speed_m_s,z_ref=a.wind_reference_height_m,T=a.temperature_k,
        rh=a.relative_humidity_fraction*100,z0=a.roughness_length_m,stability=a.stability,p=a.pressure_pa_abs)
    jet = isinstance(x,NativeJet)
    buoyant_vertical = False
    native_exit_velocity = None
    if jet:
        from slabx.core.vertical_jet import VerticalJet
        source_type = HorizontalJet if x.orientation == "horizontal_downwind" else VerticalJet
        source = source_type(substance=substance,rate=x.mass_source_rate_kg_s,area=x.jet_exit_area_m2,
            duration=x.release_duration_s,liquid_fraction=x.jet_liquid_mass_fraction,T_source=x.source_temperature_k,height=x.release_height_m)
        native_exit_velocity = source.exit_velocity(atmosphere)
        if x.orientation == "vertical_up" and source.rho_source(atmosphere) <= atmosphere.rho:
            # SLAB User's Guide Eq. 46a-46d: use an effective horizontal
            # source at the Briggs buoyant rise height and neutralize source
            # temperature/cp for downstream dispersion.
            g = 9.80665
            rho_s = source.rho_source(atmosphere)
            ws = source.w_source(atmosphere)
            bs = source.half_width_geometric
            ua = atmosphere.wind_speed(max(x.release_height_m, 1.0))
            ustar = max(atmosphere.u_star, 1e-9)
            fb = (4.0 / math.pi) * g * (atmosphere.rho - rho_s) * ws * bs * bs / atmosphere.rho
            h_rise = 0.0
            for _ in range(30):
                next_h = 1.2 * (fb / (ua * ustar * ustar)) ** (3.0 / 5.0) * (x.release_height_m + h_rise) ** (2.0 / 5.0)
                h_rise = next_h
            neutral_temperature = (molecular_weight / atmosphere.mw_moist) * atmosphere.T
            neutral_cp = (atmosphere.mw_moist / molecular_weight) * atmosphere.cp_moist
            neutral = Substance(name=f"{s.fluid_id}-neutralized", mw=molecular_weight,
                cp_vapour=neutral_cp,cp_liquid=neutral_cp,dh_vap=s.latent_heat_j_kg,
                T_boil=s.normal_boiling_point_k,rho_liquid=s.liquid_density_kg_m3)
            source = HorizontalJet(substance=neutral,rate=x.mass_source_rate_kg_s,area=x.jet_exit_area_m2,
                duration=x.release_duration_s,liquid_fraction=0.0,T_source=neutral_temperature,
                height=x.release_height_m + h_rise)
            buoyant_vertical = True
    else:
        source = EvaporatingPool(substance=substance,rate=x.vapor_source_rate_kg_s,area=x.source_area_m2,duration=x.release_duration_s)
    water = water_backend()
    correction = contextlib.nullcontext()
    if x.engine == "slabx-lh2":
        from slabx_lh2.water_ice import with_sublimation
        from slabx_lh2.plume_width import plume_width_coupling
        water = with_sublimation(water,p_ambient=a.pressure_pa_abs)
        correction = plume_width_coupling(active=x.lh2_plume_width_coupling)
    with correction:
        trajectory,used = run_dispersion(source,atmosphere,LegacyThermo(source.substance),water,
            x_max=x.plume_distance_limit_m,t_max=x.puff_time_limit_s,n_puff_steps=x.puff_steps)
        field = concentration_field(trajectory,atmosphere,z=x.receptor_height_m,t_avg=x.averaging_time_s,
            t_release=x.release_duration_s,meander_closure=x.meander_closure)
    distance = [float(v) for v in field.x]
    concentration = [float(v) for v in field.peak]
    ensure(len(distance) == len(concentration) and 1 < len(distance) <= 100000,"Invalid native grid","engine_result_invalid")
    ensure(all(math.isfinite(v) for v in distance) and all(math.isfinite(v) and 0 <= v <= 1 for v in concentration),
        "Nonphysical native concentration/grid","engine_result_invalid")
    ensure(all(b >= a for a,b in zip(distance,distance[1:])),"Nonmonotonic native grid","engine_result_invalid")
    endpoint = float(field.distance_to(x.threshold_volume_fraction))
    reached = any(v >= x.threshold_volume_fraction for v in concentration)
    endpoint = endpoint if reached and math.isfinite(endpoint) else None
    censored = concentration[-1] >= x.threshold_volume_fraction
    premise,ratio = "not_evaluated",None
    if x.engine == "slabx-lh2":
        from slabx_lh2.diagnostics import premise_summary
        diagnostic = premise_summary(trajectory)
        ratio = diagnostic["max"]
        ensure(math.isfinite(ratio),"LH2 premise diagnostic not finite","engine_result_invalid")
        premise = "violated" if diagnostic["violated"] else "within_premise"
    status = "premise_violated" if premise == "violated" else "boundary_censored" if censored else "interpolated" if reached else "not_reached"
    output = {"engine":x.engine,"engine_versions":versions,"engine_source_fingerprints":{
        name:_fingerprint(name.replace("-","_")) for name in versions},
        "downwind_distance_m":distance,"centreline_volume_fraction":concentration,
        "native_grid_maximum_downwind_distance_m":max(distance),
        "native_threshold_distance_m":endpoint,"threshold_distance_m":endpoint if status == "interpolated" else None,
        "threshold_status":status,"premise_status":premise,"maximum_vertical_to_horizontal_velocity_ratio":ratio,
        "used_source_area_m2":float(used.area),"effective_source_half_width_m":float(used.half_width),
        "averaging_time_s":x.averaging_time_s,"receptor_height_m":x.receptor_height_m,
        "spatial_output_scope":"centreline_only_no_footprint_area"}
    finite_tree(output)
    if jet:
        output.pop("effective_source_half_width_m")
        output.update(orientation=x.orientation,jet_exit_area_m2=float(x.jet_exit_area_m2),
            geometric_exit_half_width_m=float(x.jet_exit_area_m2 ** 0.5 / 2.0),native_exit_velocity_m_s=float(native_exit_velocity if buoyant_vertical else used.exit_velocity(atmosphere)),
            requested_source_temperature_k=x.source_temperature_k,used_source_temperature_k=float(used.T),
            source_temperature_clamped=float(used.T) != x.source_temperature_k,
            native_jet_liquid_mass_fraction=float(used.liquid_fraction),native_initial_downwind_distance_m=distance[0],
            native_near_field_status="briggs_buoyant_effective_horizontal_source" if buoyant_vertical else "not_reconstructed_before_native_handoff")
    if isinstance(x,(NativePoolFootprint,NativeJetFootprint)):
        import numpy as np
        from .spatial import ConcentrationGrid, threshold_grid_area
        ny = 2*x.crosswind_points_per_side-1
        ensure(ny*len(distance) <= 1000000,"Native planar grid exceeds1000000 nodes","engine_result_invalid")
        y = np.linspace(-x.crosswind_half_span_m,x.crosswind_half_span_m,ny)
        values = np.asarray(field.at_y(y),dtype=float)
        ensure(values.shape == (ny,len(distance)),"Native crosswind field shape mismatch","engine_result_invalid")
        ensure(np.all(np.isfinite(values)) and np.all((values >= 0)&(values <= 1)),"Nonphysical native spatial concentrations","engine_result_invalid")
        grid = ConcentrationGrid(downwind_coordinates_m=distance,crosswind_coordinates_m=y.tolist(),
            volume_fraction_by_crosswind_then_downwind=values.tolist(),threshold_volume_fraction=x.threshold_volume_fraction,
            sampling_basis="Native ConcentrationField.at_y at common z/t_avg and source; main-diagonal triangular interpolation")
        footprint = threshold_grid_area(grid)
        if premise == "violated":
            footprint["threshold_area_m2"] = None
            footprint["footprint_status"] = "premise_violated"
        output.update(footprint)
        output.update(crosswind_distance_m=y.tolist(),volume_fraction_by_crosswind_then_downwind=values.tolist(),
            spatial_output_scope="planar_sampled_threshold_field")
    return output


def main():
    try:
        payload = json.loads(sys.stdin.read())
        operation = payload.pop("_operation","centreline")
        models = {"centreline":NativePool,"footprint":NativePoolFootprint,"jet_centreline":NativeJet,"jet_footprint":NativeJetFootprint}
        ensure(operation in models,"Unknown native worker operation","engine_protocol_failure")
        request = models[operation].model_validate(payload)
        diagnostics = io.StringIO()
        with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics):
            result = run_native(request)
        result["native_messages"] = diagnostics.getvalue()
        print(json.dumps(result,allow_nan=False))
    except Exception as exc:
        code = exc.code if isinstance(exc,DomainError) else "engine_execution_failed"
        print(json.dumps({"code":code,"error":str(exc)},ensure_ascii=True))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
