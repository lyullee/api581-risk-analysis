"""Optional, process-isolated native SLABx pool adapter; no fallback physics."""
import json
import importlib.metadata
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from typing import Literal
from pydantic import Field, model_validator, ValidationError
from .core import Model, Positive, NonNegative, Fraction, DomainError, REGISTRY, calculation, ensure


class NativeSubstance(Model):
    fluid_id: str = Field(min_length=1,max_length=100)
    molecular_weight_kg_kmol: Positive
    vapor_heat_capacity_j_kg_k: Positive
    liquid_heat_capacity_j_kg_k: Positive
    latent_heat_j_kg: Positive
    normal_boiling_point_k: Positive
    liquid_density_kg_m3: Positive
    property_source: str = Field(min_length=1,max_length=1000)


class NativeEngineCapabilityRequest(Model):
    requested_engines: list[Literal["slabx", "slabx-lh2"]] = Field(
        default_factory=lambda: ["slabx", "slabx-lh2"], min_length=1, max_length=2
    )


@calculation("dispersion/native-engine-capabilities", "Inspect optional SLABx engine capabilities", NativeEngineCapabilityRequest,
    ["Native adapter deployment contract; tested mappings SLABx1.0.8 and SLABx-LH2 0.2.0"],
    origin="optional_native_engine_capability_probe", limitations=[
        "Deployment probe only; it performs no dispersion calculation and does not validate a native engine scientifically. Missing or mismatched packages are reported as status values rather than silently replaced. Available operations are the adapter's supported constant pool/jet boundaries, not a claim that every source domain is implemented."])
def native_engine_capabilities(x):
    required = {"slabx": "1.0.8", "slabx-lh2": "0.2.0"}
    requested = list(dict.fromkeys(x.requested_engines))
    if "slabx-lh2" in requested and "slabx" not in requested:
        requested.insert(0, "slabx")
    installed: dict[str, str | None] = {}
    status: dict[str, str] = {}
    module_import_status: dict[str, str] = {}
    module_names = {"slabx": "slabx", "slabx-lh2": "slabx_lh2"}
    for name in requested:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = None
        installed[name] = version
        status[name] = "missing" if version is None else "available" if version == required[name] else "version_mismatch"
        if version is None:
            module_import_status[name] = "not_installed"
        else:
            try:
                module_import_status[name] = (
                    "importable" if importlib.util.find_spec(module_names[name]) is not None
                    else "not_importable"
                )
            except (ImportError, ModuleNotFoundError, ValueError):
                module_import_status[name] = "not_importable"
        if status[name] == "available" and module_import_status[name] != "importable":
            status[name] = "not_importable"
    return {"requested_engines": requested, "required_versions": {name: required[name] for name in requested},
        "installed_versions": installed, "engine_status": status,
        "module_import_status": module_import_status,
        "worker_isolation": "subprocess",
        "supported_operations": ["pool_centreline", "pool_footprint", "pool_flash_fire", "jet_centreline", "jet_footprint"],
        "probe_scope": "package_presence_version_and_importability"}


class NativeAtmosphere(Model):
    wind_speed_m_s: Positive
    wind_reference_height_m: Positive
    temperature_k: Positive
    pressure_pa_abs: Literal[101325.0]
    relative_humidity_fraction: Fraction
    roughness_length_m: Positive
    stability: Literal["A","B","C","D","E","F"]

    @model_validator(mode="after")
    def wind_reference(self):
        if self.wind_reference_height_m <= self.roughness_length_m:
            raise ValueError("Wind reference height must exceed roughness length")
        if self.pressure_pa_abs != 101325.:
            raise ValueError("Verified constant-property native mapping requires 101325 Pa")
        return self


class NativeRun(Model):
    engine: Literal["slabx","slabx-lh2"]
    substance: NativeSubstance
    atmosphere: NativeAtmosphere
    receptor_height_m: NonNegative
    averaging_time_s: Positive
    plume_distance_limit_m: Positive = Field(le=1e6)
    puff_time_limit_s: Positive | None = None
    puff_steps: int = Field(default=40,ge=10,le=1000,strict=True)
    threshold_volume_fraction: Positive = Field(le=1)
    threshold_source: str = Field(min_length=1,max_length=1000)
    source_qualification: str = Field(min_length=1,max_length=1000)
    meander_closure: Literal["ermak","sigma_theta"]
    lh2_plume_width_coupling: bool
    timeout_s: Positive = Field(default=120,le=600)

    @model_validator(mode="after")
    def qualifications(self):
        if not all(v.strip() for v in (self.threshold_source,self.source_qualification,self.substance.property_source)):
            raise ValueError("Source, property and threshold qualifications must be nonblank")
        if self.engine == "slabx" and self.lh2_plume_width_coupling:
            raise ValueError("LH2 correction cannot be selected for slabx baseline")
        if self.engine == "slabx-lh2" and (self.substance.fluid_id != "hydrogen" or not 2.0 <= self.substance.molecular_weight_kg_kmol <= 2.02):
            raise ValueError("LH2 adapter requires explicitly identified hydrogen and qualified hydrogen properties")
        return self


class NativePool(NativeRun):
    vapor_source_rate_kg_s: Positive
    source_area_m2: Positive
    release_duration_s: Positive


class NativePoolFootprint(NativePool):
    crosswind_half_span_m: Positive
    crosswind_points_per_side: int = Field(default=65,ge=3,le=501,strict=True)


@calculation("dispersion/native-pool-centreline", "Run native SLABx/SLABx-LH2 constant vapor pool in an isolated process", NativePool,
    ["Part3 §§5.8.5-5.8.6,5.9: external dispersion boundary",
     "SLABx1.0.8 core.source.EvaporatingPool/core.plume.run_dispersion/post.concentration.concentration_field",
     "SLABx-LH2 0.2.0 water_ice.with_sublimation/plume_width_coupling/diagnostics.premise_summary"],
    origin="optional_native_dispersion_adapter",
    limitations=["Optional native packages required: tested mapping slabx1.0.8 and slabx-lh2 0.2.0. Each run uses a fresh Python subprocess so LH2 module-global corrections cannot alter host calculations. No silent alternate engine/version or fallback model.",
        "Only constant finite-duration ground-level pure-vapor evaporating pool at normal boiling temperature and101325Pa. Required rate is evaporated vapor, not liquid feed/orifice rate. Caller qualifies physical source, material properties, threshold, wind/stability and averaging. No automatic conversion from draft SourcePoint profiles, jets, droplets, mixtures, growing pools or source-ledger transitions.",
        "Native x_max limits the plume grid, not the final puff extent. plume_distance_limit_m maps exactly to that parameter; puff_time_limit_s maps to native t_max, or null preserves native automatic puff duration. Actual grid extent is reported. Threshold censoring uses the final returned native grid, not an assumed x_max cutoff.",
        "Returns time-averaged native centreline volume fractions and native endpoint interpolation, not a 2D contour area or flammable cloud mass. Last-node exceedance is boundary-censored, not a solved separation distance. No distance-to-circle area substitution. No LH2 safety factor is applied.",
        "LH2 premise violation makes threshold_distance_m null while native_threshold_distance_m and centreline remain diagnostics. A passing premise check is not experimental/site validation. Baseline slabx applicability remains not_evaluated. External package versions/source fingerprints accompany result; API581 software-test status is not native model certification."])
def native_pool(x):
    return _execute_worker(x,"dispersion/native-pool-centreline","centreline")


def _execute_worker(x,identifier,operation):
    try:
        serialized = json.dumps({**x.model_dump(mode="json"),"_operation":operation},allow_nan=False)
        # Keep the isolated worker usable from both an installed wheel and a
        # source checkout.  ``python -m`` otherwise cannot discover ``src/``
        # when the parent process was started by a repository test runner.
        worker_env = os.environ.copy()
        package_root = str(Path(__file__).resolve().parents[1])
        existing_pythonpath = worker_env.get("PYTHONPATH", "")
        worker_env["PYTHONPATH"] = (
            package_root if not existing_pythonpath
            else package_root + os.pathsep + existing_pythonpath
        )
        process = subprocess.run([sys.executable,"-m","api581._slabx_worker"],input=serialized,
            text=True,encoding="utf-8",capture_output=True,timeout=x.timeout_s,
            env=worker_env)
    except subprocess.TimeoutExpired as exc:
        raise DomainError("engine_timeout","Native dispersion worker exceeded timeout") from exc
    except OSError as exc:
        raise DomainError("engine_execution_failed","Native dispersion worker could not start") from exc
    try:
        payload = json.loads(process.stdout)
    except (ValueError,TypeError) as exc:
        diagnostic = (getattr(process, "stderr", "") or "").strip().replace("\n", " ")[:500]
        message = "Native dispersion worker returned no valid result"
        if diagnostic:
            message += f": {diagnostic}"
        raise DomainError("engine_protocol_failure", message) from exc
    if not isinstance(payload,dict):
        raise DomainError("engine_protocol_failure","Native dispersion worker result must be an object")
    if process.returncode or "error" in payload:
        diagnostic = (getattr(process, "stderr", "") or "").strip().replace("\n", " ")[:500]
        message = payload.get("error", "Native engine failed")
        if diagnostic and diagnostic not in message:
            message += f": {diagnostic}"
        raise DomainError(payload.get("code","engine_execution_failed"), message)
    from .outputs import OUTPUT_MODELS
    try:
        return OUTPUT_MODELS[identifier].model_validate(payload).model_dump()
    except ValidationError as exc:
        raise DomainError("engine_result_invalid","Native worker output violates the typed result contract") from exc


@calculation("dispersion/native-pool-footprint", "Native SLABx/SLABx-LH2 planar concentration threshold footprint", NativePoolFootprint,
    ["Part3 §§5.8.5-5.8.6,5.9: external dispersion footprint boundary",
     "SLABx1.0.8 post.concentration.ConcentrationField.at_y"],origin="optional_native_dispersion_spatial_postprocessing",
    limitations=["Same explicitly qualified finite ground-level vapor pool, package versions, property/atmosphere constraints and process isolation as native-pool-centreline. Uses native at_y on a symmetric crosswind grid at one receptor height/averaging time. No conversion from centreline distance to circular area.",
        "Area integrates a piecewise-linear triangular concentration interpolant on the native downwind grid and user crosswind grid. Not an exact continuous contour; supplied resolution and span require convergence checks. Plume x_max is not the final puff extent. Returned field includes negative/upwind positions, and source expansion remains native.",
        "Any threshold exceedance at a sampled grid edge or LH2 premise violation sets threshold_area_m2 to null. sampled_exceedance_area_m2 and native field remain diagnostics. No boundary truncation reported as a resolved footprint, no LH2 safety factor, mass integration or individual/societal-risk inference. Baseline native applicability remains not_evaluated."])
def native_pool_footprint(x):
    return _execute_worker(x,"dispersion/native-pool-footprint","footprint")


class NativePoolFlashFire(NativePoolFootprint):
    criterion_role: Literal["qualified_lfl"]
    receptor_height_m: Literal[0.0]


@calculation("dispersion/native-pool-flash-fire", "Native LFL footprint through API581 flash-fire consequence", NativePoolFlashFire,
    ["Part3 §§5.8.6,4.8.2.3", "Native ConcentrationField.at_y plus sampled triangular threshold area"],
    origin="native_dispersion_to_api581_flash_fire_composition",
    limitations=[*REGISTRY["dispersion/native-pool-footprint"].limitations,
        "Ground-level receptor height0 required by §5.8.6. Caller must declare threshold as a qualified fluid-specific LFL using criterion_role=qualified_lfl. A declaration does not validate thermodynamics, exposure averaging or field applicability. Censored/premise-violating footprints fail explicitly instead of becoming zero or valid fire consequence. Not-reached yields zero only on the supplied sampled interpolant. Personnel area=LFL footprint; equipment=.25*footprint. No ignition/event/GFF weighting."])
def native_pool_flash_fire(x):
    from .effects import FlashFire, flash_fire
    result = native_pool_footprint(NativePoolFootprint(**x.model_dump(exclude={"criterion_role"})))
    ensure(result["threshold_area_m2"] is not None,
        f"LFL footprint unusable for consequence: {result['footprint_status']}","dispersion_footprint_unusable")
    effect = flash_fire(FlashFire(area_within_lfl_m2=result["threshold_area_m2"]))
    return {**result,**effect,"criterion_role":x.criterion_role}


class NativeJetGeometry(NativeRun):
    orientation: Literal["horizontal_downwind","vertical_up"]
    jet_exit_area_m2: Positive
    release_height_m: NonNegative
    source_temperature_k: Positive
    temperature_basis: Literal["require_consistent","allow_native_clamp"]


class NativeJet(NativeJetGeometry):
    mass_source_rate_kg_s: Positive
    release_duration_s: Positive
    jet_liquid_mass_fraction: Fraction = Field(lt=1)

    @model_validator(mode="after")
    def temperature(self):
        boiling = self.substance.normal_boiling_point_k
        if self.temperature_basis == "require_consistent" and (
            self.source_temperature_k < boiling or self.jet_liquid_mass_fraction > 0 and self.source_temperature_k != boiling):
            raise ValueError("Native source is at boiling point with droplets, or at/above boiling for pure vapor; select explicit native clamp basis otherwise")
        return self


class NativeJetFootprint(NativeJet):
    crosswind_half_span_m: Positive
    crosswind_points_per_side: int = Field(default=65,ge=3,le=501,strict=True)


_JET_LIMITS = [
    "Actual slabx1.0.8 HorizontalJet or VerticalJet at constant finite rate/duration, optional slabx-lh2 0.2.0 water/plume-width corrections in an isolated process. Direction is downwind horizontal or upward vertical only. No arbitrary yaw/downward/impinging jet, mixture carrier, physical-transition ledger or underexpanded-jet solver.",
    "Input total pure-material vapor+droplet mass rate, effective atmospheric exit area, source temperature and liquid MASS fraction, not gas volume fraction. Native velocity derives from q/(rho*A); this API does not substitute a vessel choked-orifice area for a qualified expanded area. Source liquid fraction must be below1. Equilibrium droplets use native default closures; kinetic evaporation/rainout flags are not implicitly enabled.",
    "Temperature basis is explicit: native clamps vapor below boiling to boiling and all droplet sources to boiling. require_consistent rejects a conflicting input; allow_native_clamp reports requested and used temperature. No EOS/flash reconciliation inferred.101325Pa ambient and supplied constant properties only.",
    "Vertical buoyant-source rise is delegated to the installed SLABx VerticalJet implementation and returned as native diagnostics. The adapter does not substitute a separate plume model or apply an empirical safety factor. LH2 premise diagnostics still gate distance/area; passing them does not validate near-field jets or field applicability.",
    "Native source/handoff may begin at x=1m or beyond the vertical rise. Full upstream/near-field extent is not reconstructed. A footprint touching first/last or lateral grid edge is censored, and threshold_area_m2 remains null. No source-boundary extrapolation or circle-area substitution. x_max limits plume, not full puff extent.",
]


@calculation("dispersion/native-jet-centreline", "Native horizontal/vertical jet centreline dispersion", NativeJet,
    ["Part3 §§5.3,5.7,5.8.5-5.8.6,5.9 external dispersion source boundary",
     "SLABx1.0.8 core.source.HorizontalJet/core.vertical_jet.VerticalJet"],origin="optional_native_jet_dispersion_adapter",limitations=_JET_LIMITS)
def native_jet(x):
    return _execute_worker(x,"dispersion/native-jet-centreline","jet_centreline")


@calculation("dispersion/native-jet-footprint", "Native horizontal/vertical jet sampled threshold footprint", NativeJetFootprint,
    ["Part3 §§5.8.6,5.9 external spatial footprint boundary", "SLABx1.0.8 ConcentrationField.at_y"],
    origin="optional_native_jet_spatial_postprocessing",limitations=_JET_LIMITS+[
        "Planar area uses the same explicit main-diagonal triangular interpolant as threshold-grid-area. Native x grid and user symmetric y grid require resolution checks. Raw field and within-grid diagnostic area remain available when censored/premise-violating; no valid full footprint is claimed."])
def native_jet_footprint(x):
    return _execute_worker(x,"dispersion/native-jet-footprint","jet_footprint")
