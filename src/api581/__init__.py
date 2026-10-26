"""API 581 calculation engine. No implicit standard-compliance certification."""

from .core import VERSION as __version__, Context, DomainError, REGISTRY, evaluate
from . import pof, release, effects, risk, thinning, cracking, level1, consequences, level1_summary, cost_tables, scc_mechanisms, external_corrosion, external_cracking, fatigue, htha, brittle, temper, bundle, prd, prd_consequences, prd_history, level1_type1, level1_toxic, pool_fire, inspection_effectiveness
from .result import CalculationResult
from . import fireball
from . import blast
from . import physical_explosion
from . import toxic_level2
from . import level2_summary
from . import evaporation
from . import source_partition
from . import ignition
from . import two_phase_events
from . import tank
from . import tank_environment
from . import tank_financial
from . import tank_source
from . import tank_integrated
from . import tank_shell
from . import slabx_adapter
from . import spatial
from . import jet_handoff
from . import toxic_criteria
from . import native_toxic
from . import soil_corrosion
from . import tank_corrosion
from . import tank_thinning
from . import clad_thinning
from . import thinning_conditions
from . import lining
from . import cooling_water
from . import cooling_selection
from . import co2_corrosion
from . import co2_screening
from . import oxidation
from . import acid_sour_water
from . import alkaline_sour_water
from . import hydrochloric_acid
from . import hydrofluoric_acid
from . import amine_corrosion
from . import sulfuric_acid
from . import h2sh2_corrosion
from . import sulfidic_corrosion
from . import flash_solver
from . import saturation
from . import flash_pool
from . import area_contribution
from . import groundwater
from . import thinning_selection
from . import thinning_history
from . import caustic_screening
from . import amine_screening
from . import ssc_screening
from . import hic_screened
from . import acscc_screening
from . import pascc_screening
from . import clscc_screening
from .workflow import Step, Workflow, run_workflow
from . import digital_twin
from . import api520
from . import schema
from . import evidence
from .evidence import ValidationEvidence
from . import standard
from . import portfolio
from . import representative_fluids
from . import corrosion_rate
from . import thinning_type
from .catalog import describe, list_calculations, coverage, coverage_summary, clause_evidence, review_queue, calculation_evidence, validation_queue, ScopeBoundary, scope_boundaries, audit_coverage

__all__ = ["api", "Context", "DomainError", "CalculationResult", "evaluate",
           "Step", "Workflow", "run_workflow", "describe", "list_calculations", "coverage", "coverage_summary", "clause_evidence", "review_queue", "calculation_evidence", "validation_queue", "ScopeBoundary", "scope_boundaries", "audit_coverage", "digital_twin", "schema", "evidence", "ValidationEvidence", "standard", "__version__"]


def __getattr__(name):
    if name == "api":
        from importlib import import_module
        return import_module(".api", __name__)
    raise AttributeError(name)
