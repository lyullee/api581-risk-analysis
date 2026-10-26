# Nurion integration test

The repository includes a site-neutral Slurm job. It runs the complete Python
test suite, release-contract checks, reference fixtures, and the digital-twin
example. If a Python environment containing `slabx`, `slabx-lh2`, and
`CoolProp` is supplied, it also runs the native verification suite.

## Submit from Nurion

Copy the repository to the login node using the institution-approved transfer
method, then from the checkout:

```bash
sbatch --account=<ACCOUNT> --partition=<PARTITION> --time=02:00:00 \
  scripts/nurion_api581.slurm
```

The account, partition, wall time, module names, and Python environment are
site-specific and are deliberately not hard-coded. To use a prepared native
environment, submit with `API581_NATIVE_PYTHON=/path/to/python` (and optionally
`API581_PYTHON=/path/to/python`). Without it, the job runs the dependency-free
gates and skips native bindings.

Monitor and collect the result with the normal Slurm commands:

```bash
squeue -j <JOB_ID>
sacct -j <JOB_ID> --format=JobID,State,Elapsed,MaxRSS,ExitCode
cat tmp/nurion-<JOB_ID>.out
cat tmp/nurion-<JOB_ID>.json
```

No SSH keys, tokens, or Nurion hostnames are stored in this repository. The
Windows checkout cannot submit directly unless an institutional SSH/Slurm
client and an approved Nurion endpoint are configured.

## Parallel PBS shards

For large validation runs, use the shared SSH master and the PBS array submitter
instead of one long pytest process:

```powershell
.\.venv\Scripts\python.exe scripts/nurion_parallel_submit.py
```

The default efficient profile creates only the 10 specialized shards (0-9).
Use `--profile exhaustive` only when a full duplicate regression and broad matrix
are explicitly required; it creates 64 isolated shards. Shards 0-9 run import, release
contracts, reference fixtures, digital-twin example, catalog tests,
adapter/contract tests, catalog performance, the complete Python regression
suite, a compatibility regression suite excluding the sqlite module, and a
1,000-request digital-twin stress benchmark. Shards 10-31 replay the full
regression on independent nodes; shards 32-63 run the broad input-invariant
matrix (16,000 generated cases). The array payload stages
`pysqlite3-binary` and `RunStore` falls back to it when the cluster Python lacks
`_sqlite3`, so the complete suite can run on the current Nurion image. Each
shard has its own local node work directory and writes `shard-<index>.status`,
`.out`, and `.err` receipts into the remote payload directory. Monitor the array
with `qstat -t <ARRAY_ID>` and collect the receipts from the reported remote
root. A slow or unavailable optional test shard must not invalidate the other
completed shards.

Collect a completed array into one local evidence report:

```powershell
.\.venv\Scripts\python.exe scripts/nurion_parallel_collect.py `
  20261025T074247Z-parallel `
  --output tmp/nurion-parallel-20261025T074247Z.json
```

For an efficient 0-9 run, pass `--shards 10` to the collector. Use
`--shards 64` only for an explicitly authorized exhaustive run.

The collector is read-only on Nurion and reports each shard's state, return
code, host, timeout, and output tails plus an aggregate pass/fail summary.

The latest reconciled expanded `20261025T083425Z-parallel-reconciled` run
(`24187724[].pbs`, retry arrays `24187805[].pbs`, package-gate
`24188076[].pbs`, and final stress/regression/package-gate arrays
`24188192[].pbs`/`24188271[].pbs`, package-provenance `24188317[].pbs`,
fingerprint-gate `24188347[].pbs`, review-packet gate `24188354[].pbs`, and
packaged-schema gate `24188384[].pbs`, and wheel-data provenance gate
`24188399[].pbs`)
completed 64/64 shards
with zero failures or timeouts. It included the release,
supporting-text, completion-matrix metadata gates, 16,000 generated invariant
cases, repeated full regression on independent nodes, and the 1,000-request
digital-twin stress test. The stress worker uses one process pool with
`max_workers=8` and `chunksize=16`, rather than creating a process pool per
shard, while preserving the immutable batch manifest and response order.
Receipt: `tmp/nurion-parallel-20261025T083425Z-reconciled-v11.json`.

## Full Python regression profiles

The package supports both dependency-free and qualified-native profiles. The
dependency-free profile must report optional engines as `missing`; it should
not claim native availability. For a qualified SlabX/SlabX-LH2 profile, add
the native environment's site-packages to `PYTHONPATH` while using the regular
pytest runner:

```powershell
$env:PYTHONPATH="src;tmp\dispersion-native\Lib\site-packages"
.\.venv\Scripts\python.exe -m pytest -q
```

The current qualified profile runs the full suite with native bindings and
then runs `scripts/verify_native_suite.py --timeout-seconds 300`. Native suite
reports distinguish `passed`, `failed`, and `timed_out` per verification
script.
