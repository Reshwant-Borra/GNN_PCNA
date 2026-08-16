# Benchmark Limitations

## Purpose

Audit whether a benchmark such as CryptoBench is fit for Phase 2 conclusions. A bad benchmark creates fake rigor.

## Hard Rules

- No benchmark may be adopted before its limitations are documented.
- Benchmark labels must be traced to their generation method.
- Benchmark quality issues must be carried into claim limitations.
- A benchmark being public, named, or cited is not enough.

## Required Checks

- How were labels generated?
- Are labels curated, proxy, computational, experimental, or mixed?
- How noisy are labels?
- Are cryptic-pocket definitions consistent across proteins?
- Is there protein-family bias?
- Is there ligand-count, ligand-size, ligand-class, or ligand-source bias?
- Is there resolution or structure-quality bias?
- Is there publication bias toward well-studied proteins?
- Are apo/holo pairs grouped?
- Are homologs controlled?
- Does the benchmark include PCNA or close PCNA homologs?
- Does benchmark evaluation align with residue-level top-k recovery?

## Forbidden Actions

- Assuming CryptoBench is good enough without audit.
- Treating auxiliary ligand-proximity datasets as cryptic-pocket benchmarks.
- Hiding benchmark limitations because they weaken the story.
- Comparing metrics across benchmarks with different label definitions without caveats.

## Examples Of Failure

- Benchmark positives are derived from ligand proximity, but the report calls them experimentally validated cryptic pockets.
- Proteins from the same family appear across train and test.
- Low-resolution structures dominate positives.

## Prevention

Create benchmark limitation notes before dataset adoption and include them in every evaluation report.

## Compliance Artifact

`reports/phase2/benchmark_limitations.md`.

## If The Rule Fails

Do not use the benchmark for training, evaluation, or claims until limitations are documented and accepted.
