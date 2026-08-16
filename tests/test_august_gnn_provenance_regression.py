from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


EXPECTED = {
    42: "03d01eba42eb7f6da01c0147dea434b1e1797bd2302e8a178d6bbd9b19526ce5",
    43: "7f145d6f54d03744f71c0224df4f170ad4aab388387e242234ebffda1acae17b",
    44: "0a739dec47248651499942207b82139e5dea8bebfafe5ed50aabcbbdfd6aa3f6",
}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_august_three_seed_checkpoint_hashes_unchanged():
    for seed, digest in EXPECTED.items():
        path = REPO / "artifacts" / "go_prep" / f"seed_{seed}" / "best.ckpt"
        assert path.exists()
        assert _sha(path) == digest


def test_august_handoff_identity_records_exact_score_reproduction():
    identity = json.loads((REPO / "artifacts" / "provenance" / "AUGUST_HANDOFF_IDENTITY.json").read_text())
    per_seed = identity["per_seed_inference_identity"]
    for row in per_seed.values():
        assert row["rows_compared"] == 510
        assert row["max_abs_score_difference"] == 0.0
        assert row["mean_abs_score_difference"] == 0.0
        assert row["residue_order_mismatches"] == 0
    assert identity["historical_report_match"]["candidate_sets_match"] is True
    assert identity["historical_report_match"]["consensus_residues_match"] is True
    assert identity["scientific_content_identity"] is True
    assert identity["consensus_reconstruction"]["mean_pairwise_jaccard"] == 0.6791537667698658
    assert len(identity["consensus_reconstruction"]["union"]) == 20
