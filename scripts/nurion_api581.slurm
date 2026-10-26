#!/bin/bash
# API 581 integration gates for a Nurion Slurm allocation.
# Site-specific account/partition/time must be supplied by the operator:
#   sbatch --account=<ACCOUNT> --partition=<PARTITION> --time=HH:MM:SS \
#          scripts/nurion_api581.slurm
# Do not commit credentials or site module names to this file.
#SBATCH --job-name=api581-int
#SBATCH --output=tmp/nurion-%j.out
#SBATCH --error=tmp/nurion-%j.err
#SBATCH --cpus-per-task=4
#SBATCH --ntasks=1

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"

# Load the Python/module environment approved for the target partition before
# submitting, or export API581_PYTHON and API581_NATIVE_PYTHON in the job.
PYTHON_BIN="${API581_PYTHON:-python3}"
REPORT="${API581_REPORT:-tmp/nurion-${SLURM_JOB_ID:-local}.json}"
ARGS=(scripts/nurion_integration.py --python "$PYTHON_BIN" --output "$REPORT")
if [[ -n "${API581_NATIVE_PYTHON:-}" ]]; then
  ARGS+=(--native-python "$API581_NATIVE_PYTHON")
else
  # Native dependencies are site-specific; pure-Python gates still run.
  ARGS+=(--skip-native)
fi
"$PYTHON_BIN" "${ARGS[@]}"
