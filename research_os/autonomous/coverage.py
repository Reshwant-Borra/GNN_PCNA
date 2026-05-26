"""Coverage estimator.

Counts items per named category and scores how complete coverage is.

Used by literature/corpus building agents to answer "have I collected
enough sources across the major scientific and engineering categories?"
rather than the much weaker "is source count >= N?".
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from research_os.autonomous.schemas import CoverageCategory, CoverageResult


class CoverageEstimator:
    """Score how well a set of items covers a list of named categories.

    Each item is matched against each category by keyword presence in a
    derived text representation (title + abstract + tags, by default).
    """

    def __init__(self, categories: Iterable[CoverageCategory]):
        self.categories: List[CoverageCategory] = list(categories)
        if not self.categories:
            raise ValueError("CoverageEstimator needs at least one category")

    def evaluate(
        self,
        items: List[Dict[str, Any]],
        *,
        text_fields: Iterable[str] = ("title", "abstract", "summary", "topics"),
    ) -> CoverageResult:
        per_cat_counts: Dict[str, int] = {c.name: 0 for c in self.categories}
        for item in items:
            text = self._item_text(item, list(text_fields))
            for cat in self.categories:
                if cat.matches(text):
                    per_cat_counts[cat.name] += 1

        per_cat_score: Dict[str, float] = {}
        weighted_score_sum = 0.0
        weight_sum = 0.0
        gaps: List[str] = []
        suggested: List[str] = []
        for cat in self.categories:
            count = per_cat_counts[cat.name]
            score = min(1.0, count / max(1, cat.min_items))
            per_cat_score[cat.name] = score
            weighted_score_sum += score * cat.weight
            weight_sum += cat.weight
            if count < cat.min_items:
                gaps.append(cat.name)
                # Suggest a search query built from the most distinctive keywords.
                if cat.keywords:
                    suggested.append(" ".join(cat.keywords[:4]))
        overall = (weighted_score_sum / weight_sum) if weight_sum else 0.0
        return CoverageResult(
            score=round(overall, 3),
            per_category_counts=per_cat_counts,
            per_category_score={k: round(v, 3) for k, v in per_cat_score.items()},
            gaps=gaps,
            suggested_queries=suggested,
            total_items=len(items),
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _item_text(item: Dict[str, Any], fields: List[str]) -> str:
        parts: List[str] = []
        for f in fields:
            v = item.get(f)
            if v is None:
                continue
            if isinstance(v, (list, tuple)):
                parts.append(" ".join(str(x) for x in v))
            else:
                parts.append(str(v))
        return " \n ".join(parts)


__all__ = ["CoverageEstimator"]
