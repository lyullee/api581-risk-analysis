from __future__ import annotations

import hashlib

from scripts.nurion_pbs_submit import ROOT, stage_reference_sources


def test_nurion_payload_stages_canonical_supporting_pdf(tmp_path):
    staged = stage_reference_sources(tmp_path)
    source = ROOT / "API-581-2016.pdf"
    assert source.is_file()
    assert staged == (source.name,)
    staged_bytes = (tmp_path / source.name).read_bytes()
    assert staged_bytes == source.read_bytes()
    assert hashlib.sha256(staged_bytes).hexdigest() == hashlib.sha256(source.read_bytes()).hexdigest()
