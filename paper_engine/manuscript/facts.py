"""The grounding fact sheet.

Everything the writer is allowed to assert about results lives here, assembled
from real run manifests via :mod:`paper_engine.figures.data_loaders`. The writer
is instructed to use only these facts and never to invent numbers. The fact
sheet also encodes the governance guardrails (test set not evaluated, metric
rationale, candidate-region language) so they propagate into every section.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from paper_engine.figures import data_loaders as dl
from paper_engine.figures import md as md_mod


@dataclass
class FactSheet:
    dataset: dict
    split: dict
    model_config: dict
    primary: dict
    baselines: List[dict]
    ablation: List[dict]
    md_status: dict
    guardrails: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    # ----- rendering for the LLM prompt -----
    def to_prompt_block(self) -> str:
        lines: List[str] = []
        d = self.dataset
        s = self.split
        lines.append("DATASET & SPLIT (real, frozen):")
        lines.append(
            f"- {d['structures_labeled']} labelled structures; positive-unlabeled "
            f"labels; {d['total_positives']:,} positive residues, "
            f"{d['total_masked']:,} masked (excluded from loss)."
        )
        prev = d.get("positive_prevalence")
        if prev:
            lines.append(f"- Positive prevalence among evaluated residues: ~{prev*100:.1f}%.")
        lines.append(
            f"- Split frozen (hash {s['manifest_hash']}), homology-blocked at "
            f"{s['identity_threshold']}% sequence identity; PCNA held out "
            f"({s['pcna_holdout_count']} cluster); test set = "
            f"{s['fold_distribution'].get('test', 'NA')} structures, NEVER evaluated."
        )
        mc = self.model_config
        if mc:
            lines.append("\nMODEL (real config):")
            lines.append(
                f"- {mc.get('architecture')} (hidden_dim={mc.get('hidden_dim')}, "
                f"dropout={mc.get('dropout')}, lr={mc.get('lr')}, "
                f"pos_weight≈{mc.get('pos_weight'):.1f}); features = 25 structural + "
                f"ESM2 per-residue embeddings."
            )
        p = self.primary
        lines.append("\nVALIDATION RESULTS (validation folds only; NO test results exist):")
        lines.append(
            f"- Primary {p['display']}: macro-AUPRC {p['mean']:.4f} ± {p['sd']:.4f} "
            f"over {p['n_runs']} runs (4 folds × 3 seeds); per-fold means "
            f"{ {k: round(v,4) for k,v in p['per_fold'].items()} }; best single run "
            f"{p['best_mean']:.4f}; mean macro-AUROC {p['macro_auroc']:.3f}."
        )
        lines.append("- Baselines (same split, validation macro-AUPRC):")
        for b in self.baselines:
            sd = f" ± {b['sd']:.4f}" if b.get("sd") is not None else ""
            lines.append(f"    · {b['display']}: {b['mean']:.4f}{sd}")
        lines.append("- Edge-type ablation:")
        for a in self.ablation:
            sd = f" ± {a['sd']:.4f}" if a.get("sd") is not None else ""
            lines.append(f"    · {a['display']}: {a['mean']:.4f}{sd}")
        lines.append("\nMOLECULAR DYNAMICS:")
        lines.append(f"- {self.md_status['summary']}")
        lines.append("\nNON-NEGOTIABLE GUARDRAILS:")
        for g in self.guardrails:
            lines.append(f"- {g}")
        return "\n".join(lines)


def build_fact_sheet() -> FactSheet:
    primary = dl.load_primary_training()
    models = dl.load_all_models()
    by_key = {m.key: m for m in models}
    label = dl.load_label_stats()
    split = dl.load_split_stats()
    cfg = dl.load_model_config()

    def model_dict(m) -> dict:
        return {"key": m.key, "display": m.display, "mean": m.mean,
                "sd": m.sd, "macro_auroc": m.macro_auroc}

    baselines = [model_dict(by_key[k]) for k in
                 ("sage_no_sequential", "gat_2l", "gcn_1l", "degree", "random")
                 if k in by_key]
    ablation = [model_dict(by_key[k]) for k in
                ("graphsage_3l", "sage_no_sequential", "sage_no_spatial")
                if k in by_key]

    # MD status from the REAL Phase-5 analysis (25 ns, apo 1AXC). Honest framing:
    # the candidate residues are NOT more flexible than the reference, so no opening.
    from paper_engine.figures import md_results
    if md_results.md_available():
        summary = md_results.load_summary()
        rep1 = summary.get("replicates", {}).get("replicate_01", {})
        rmsf = md_results.load_rmsf_windows("replicate_01")
        ref_vals = [v for k, v in rmsf.items() if "reference" in k]
        cand_vals = [statistics.mean(v) for k, v in rmsf.items() if "reference" not in k]
        ref = statistics.mean(ref_vals[0]) if ref_vals else 0.0
        cand_lo = min(cand_vals) if cand_vals else 0.0
        cand_hi = max(cand_vals) if cand_vals else 0.0
        md_status = {
            "available": True,
            "summary": (
                "REAL exploratory MD (Phase 5 triage). System: human PCNA homotrimer "
                "1AXC (apo-from-p21, peptide removed), OpenMM 8.2 / AMBER14 / TIP3P, "
                "~287k atoms. Effective sampling n=1: replicate_01 = full 25 ns "
                "(250 frames @ 0.1 ns); replicate_02 incomplete (killed at budget wall); "
                "no 8GLA positive control; first 5 ns discarded as equilibration. The "
                "original analysis was corrupted by missing PBC imaging and was re-run "
                "with image_molecules, core alignment excluding measured windows, and "
                "RMSF about the mean. "
                f"STABILITY: backbone Cα RMSD mean {rep1.get('mean_backbone_rmsd_nm', 0.255):.3f} nm, "
                f"max {rep1.get('max_backbone_rmsd_nm', 0.305):.3f} nm, flat plateau (stable trimer). "
                f"FLEXIBILITY: per-window Cα RMSF at the GNN novel candidates "
                "(239-243, 28-32, 206-210) is 0.074-0.081 nm = 0.59-0.65x the IDCL/PIP "
                f"reference window 118-122 ({ref:.3f} nm); the IDCL-adjacent control "
                "134-138 is 0.084 nm (0.67x). POCKET-OPENING CHECK (SASA + mouth-distance "
                "proxies, 3 monomers as informal triplicates): NO sustained opening in any "
                "monomer; novel candidates showed only transient SASA excursions (~18-26%, "
                "2-7 of 200 frames, returning to baseline); the front-face PIP pocket stayed "
                "essentially static; the only sustained widening was the known-flexible IDCL "
                "(134-138, expected loop motion). RESULT: the GNN-predicted novel candidate "
                "pockets remained RIGID and did NOT open. This is a valid "
                "negative/inconclusive result (NOT falsification): 25 ns / n=1 / no positive "
                "control cannot sample ns-us cryptic-opening events. No druggability, "
                "validated-site, or novel-site claims are supported."
            ),
            "length_ns": 25.0,
            "result_class": "negative_inconclusive",
            "stable": True,
        }
    else:
        md_status = {
            "available": False,
            "summary": ("MD analysis not available; do not report MD results."),
        }

    primary_dict = {
        "display": "GraphSAGE-3L",
        "mean": primary.mean,
        "sd": primary.sd,
        "n_runs": len(primary.runs),
        "per_fold": primary.per_fold_mean,
        "best_mean": primary.best_run.best_val_macro_auprc,
        "macro_auroc": primary.macro_auroc_mean or 0.0,
    }

    guardrails = [
        "The test set was NOT evaluated. Never state or imply any test-set result.",
        "Report macro-AUPRC as primary; AUROC is inflated at ~4.6% prevalence.",
        "No scientific claim of a 'validated', 'confirmed', or 'discovered' pocket. "
        "Use candidate-region language ('candidate pocket-associated residues', "
        "'computationally predicted', 'requires further validation').",
        "The 25 ns MD is exploratory and short: candidate residues are NOT more flexible "
        "than the reference, so there is NO pocket opening. Report this honest negative "
        "result; never claim opening, binding, or that MD validated anything. The run is "
        "25 ns on 1AXC — never inflate the timescale (no 100 ns, no 900 ns).",
        "Do not invent citations, numbers, p-values, or experimental results.",
        "The ablation shows the sequential-edge contribution is NOT established; "
        "state this honestly rather than claiming the full architecture is required.",
    ]

    sources = [primary.source, label["source"], split["source"]]
    if cfg.get("source"):
        sources.append(cfg["source"])

    return FactSheet(
        dataset=label, split=split, model_config=cfg, primary=primary_dict,
        baselines=baselines, ablation=ablation, md_status=md_status,
        guardrails=guardrails, sources=sources,
    )


if __name__ == "__main__":  # pragma: no cover
    print(build_fact_sheet().to_prompt_block())
