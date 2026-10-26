"""Submit API-581 integration gates through the existing shared Nurion SSH master."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
WSL = ["wsl.exe", "-d", "Fusion-Local-22.04", "-u", "root", "--exec"]
SOCKET = "/root/.cache/nbcp-nurion/master.sock"
HOST = "r1021a02@nurion.ksc.re.kr"
SSH_OPTIONS = [
    "-o", "ControlMaster=no", "-o", "ControlPath=" + SOCKET,
    "-o", "BatchMode=yes", "-o", "NumberOfPasswordPrompts=0",
    "-o", "ConnectTimeout=15", "-o", "ConnectionAttempts=1",
    "-o", "StrictHostKeyChecking=yes",
    "-o", "UserKnownHostsFile=/mnt/c/Users/lyul/.ssh/known_hosts",
]


def run_wsl(args: list[str], *, timeout: int = 300) -> str:
    completed = subprocess.run(WSL + args, text=True, capture_output=True, timeout=timeout)
    if completed.returncode:
        raise RuntimeError((completed.stdout + "\n" + completed.stderr).strip())
    return completed.stdout.strip()


def ssh(command: str, *, timeout: int = 300) -> str:
    return run_wsl(["ssh", *SSH_OPTIONS, HOST, command], timeout=timeout)


def scp(local: Path, remote: str, *, timeout: int = 600) -> None:
    linux_local = run_wsl(["wslpath", "-u", str(local.resolve())], timeout=30)
    run_wsl(["scp", "-o", "ControlPath=" + SOCKET, *SSH_OPTIONS[0:2], *SSH_OPTIONS[2:],
             linux_local, HOST + ":" + remote], timeout=timeout)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_reference_sources(stage: Path) -> tuple[str, ...]:
    """Stage documentary source files needed by clean remote workers."""
    staged: list[str] = []
    for name in ("API-581-2016.pdf",):
        source = ROOT / name
        if source.is_file():
            shutil.copy2(source, stage / source.name)
            staged.append(source.name)
    return tuple(staged)


def make_payload(run_id: str, wheel_dir: Path) -> Path:
    stage = ROOT / "tmp" / ("nurion-api581-" + run_id)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    for name in ("src", "tests", "scripts", "examples", "docs"):
        shutil.copytree(ROOT / name, stage / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("pyproject.toml", "requirements.lock.txt", "README.md"):
        shutil.copy2(ROOT / name, stage / name)
    # The supporting-text regression rebuilds and fingerprints the canonical
    # source PDF.  Stage that source explicitly; it is intentionally not part
    # of the release-manifest artifact list because it is reference material,
    # not a distributable package artifact.
    stage_reference_sources(stage)
    # Keep only the small, hash-pinned release receipts needed by the remote
    # provenance gate; never archive the large local native virtualenv or all
    # historical PBS tarballs under tmp/.
    manifest = json.loads((ROOT / "docs" / "release-manifest.json").read_text(encoding="utf-8"))
    manifest_paths = [item["path"] for group in ("package_artifacts", "evidence_artifacts")
                      for item in manifest.get(group, [])]
    for relative in manifest_paths:
        if not relative.startswith("tmp/"):
            continue
        source = ROOT / Path(relative)
        target = stage / Path(relative)
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif source.is_dir():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, target)
    deps = stage / "deps"
    deps.mkdir()
    for wheel in wheel_dir.glob("*.whl"):
        shutil.copy2(wheel, deps / wheel.name)
    archive = ROOT / "tmp" / ("nurion-api581-" + run_id + ".tar.gz")
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(stage, arcname=stage.name)
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote-root", default="/scratch/r1021a02/api581_integration")
    parser.add_argument("--wheel-dir", type=Path, default=ROOT / "tmp" / "linux-wheels")
    args = parser.parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    archive = make_payload(run_id, args.wheel_dir)
    remote = f"{args.remote_root}/{run_id}"
    remote_archive = f"{remote}/{archive.name}"
    print("Checking shared SSH master…", flush=True)
    run_wsl(["ssh", "-S", SOCKET, "-O", "check", HOST], timeout=30)
    ssh(f"mkdir -p {shlex.quote(remote)}", timeout=30)
    print(f"Uploading {archive.name}…", flush=True)
    scp(archive, remote + "/", timeout=900)
    digest = sha256(archive)
    command = (
        f"cd {shlex.quote(remote)} && "
        f"printf '%s  %s\\n' {digest} {shlex.quote(archive.name)} | sha256sum -c - && "
        f"tar -xzf {shlex.quote(archive.name)} && "
        f"cd {shlex.quote('nurion-api581-' + run_id)} && "
        "printf '%s  %s\\n' " + sha256(ROOT / "scripts" / "nurion_api581.pbs") +
        " scripts/nurion_api581.pbs | sha256sum -c - && "
        "qsub scripts/nurion_api581.pbs"
    )
    # The payload is self-contained; qsub output is the authoritative receipt.
    receipt = ssh(command, timeout=120)
    print(receipt)
    print(f"run_id={run_id}")
    print(f"remote_root={remote}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
