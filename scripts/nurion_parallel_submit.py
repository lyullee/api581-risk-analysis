"""Upload the API-581 payload and submit configurable PBS array shards.

The default array keeps the ten specialized checks, adds parallel replay
shards, and runs a broad input-invariant matrix. Replay is intentionally redundant: independent nodes expose flaky
imports, nondeterministic numerical paths, and filesystem/runtime issues much
faster than a single serial regression run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import sys
import uuid
from datetime import datetime, timezone

from nurion_pbs_submit import ROOT, make_payload, run_wsl, scp, sha256, ssh


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote-root", default="/scratch/r1021a02/api581_parallel")
    parser.add_argument("--wheel-dir", type=Path, default=ROOT / "tmp" / "linux-wheels")
    parser.add_argument(
        "--array",
        help="PBS array range; efficient profile defaults to 0-9",
    )
    parser.add_argument(
        "--profile",
        choices=("efficient", "exhaustive"),
        default="efficient",
        help="efficient runs specialized checks only; exhaustive enables redundant replays and matrix shards",
    )
    args = parser.parse_args()
    args.array = args.array or ("0-9" if args.profile == "efficient" else "0-63")
    import re
    if not re.fullmatch(r"\d+-(?:\d+)", args.array):
        parser.error("--array must be a simple PBS range such as 0-31")
    first, last = (int(value) for value in args.array.split("-"))
    if first < 0 or last < first or last > 63:
        parser.error("--array must satisfy 0 <= first <= last <= 63")
    if args.profile == "efficient" and last > 9:
        parser.error("efficient profile only permits specialized shards 0-9; use --profile exhaustive for redundant replays/matrix")
    # Include a short nonce so rapid retries never collide with a partially
    # staged payload left by an interrupted upload in the same second.
    run_id = (
        __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        .strftime("%Y%m%dT%H%M%SZ")
        + "-parallel-"
        + uuid.uuid4().hex[:8]
    )
    archive = make_payload(run_id, args.wheel_dir)
    remote = f"{args.remote_root}/{run_id}"
    run_wsl(["ssh", "-S", "/root/.cache/nbcp-nurion/master.sock", "-O", "check", "r1021a02@nurion.ksc.re.kr"], timeout=30)
    ssh(f"mkdir -p {shlex.quote(remote)}", timeout=30)
    scp(archive, remote + "/", timeout=900)
    digest = sha256(archive)
    command = (
        f"cd {shlex.quote(remote)} && "
        f"printf '%s  %s\\n' {digest} {shlex.quote(archive.name)} | sha256sum -c - && "
        f"tar -xzf {shlex.quote(archive.name)} && "
        f"cd {shlex.quote('nurion-api581-' + run_id)} && "
        f"qsub -J {shlex.quote(args.array)} scripts/nurion_api581_array.pbs"
    )
    receipt_path = ROOT / "tmp" / f"nurion-parallel-{run_id}.submission.json"
    try:
        receipt = ssh(command, timeout=120)
    except RuntimeError as exc:
        # Upload succeeded, but qsub may reject the array (for example when
        # the account queue limit is already saturated). Preserve that fact
        # as a machine-readable receipt instead of losing the remote payload.
        record = {
            "run_id": run_id,
            "pbs_job": None,
            "remote_root": remote,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "status": "rejected",
            "error": str(exc),
        }
        receipt_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, ensure_ascii=False))
        return 2
    print(receipt)
    print(f"run_id={run_id}")
    print(f"remote_root={remote}")
    pbs_job = receipt.strip().splitlines()[-1]
    receipt_path.write_text(
        json.dumps({"run_id": run_id, "pbs_job": pbs_job, "remote_root": remote,
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    "status": "submitted"}, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
