# BUG_LOG.md — Bug History

> Mirror of KNOWN_BUGS.md. Add new entries here AND in KNOWN_BUGS.md.
> Never delete resolved entries — mark as RESOLVED.

---

## Active Bugs

### BUG-011: Random CryptoSite split has homology leakage

**Date found:** 2026-05-22
**Date resolved:** 2026-05-22
**Status:** resolved
**Severity:** critical
**Affected file(s):** `data/splits/cryptosite_split.json`, benchmark reports
**Found by:** prior audit

**Description:**
The old random split placed homologous structures across train and held-out sets, invalidating headline benchmark claims.

**Fix:**
Added MMseqs2 30% homology-clean splitting, split integrity validation, clean-split ablation training, and clean evaluation scripts. Final four-condition, three-seed rerun completed in E004.

### BUG-012: Clean benchmark provenance was insufficient

**Date found:** 2026-05-22
**Date resolved:** 2026-05-22
**Status:** resolved
**Severity:** warning
**Affected file(s):** `src/training/train.py`
**Found by:** remediation plan

**Description:**
Checkpoints did not record enough provenance to defend split hash, graph hash, command, environment, condition, node dimension, seed, and git commit.

**Fix:**
New `best_meta.json` files record clean benchmark provenance fields.

---

## Resolved Bugs

_None yet._

---

## Template

```
### BUG-{NNN}: {short title}

**Date found:** YYYY-MM-DD
**Date resolved:** YYYY-MM-DD (or "Open")
**Status:** open | investigating | resolved
**Severity:** critical | warning | minor
**Affected file(s):** src/path/to/file.py
**Found by:** Claude | Gemini | ChatGPT | user | test

**Description:**
What goes wrong. One paragraph max.

**Reproduction:**
Minimal steps or code snippet.

**Root cause:**
(fill in when known)

**Fix:**
(fill in when resolved)

**Tests added:**
(link to test that covers this case)
```

---

## Related

[[KNOWN_BUGS]] · [[CHANGELOG]] · [[DECISIONS]] · [[EXPERIMENT_INDEX]]
