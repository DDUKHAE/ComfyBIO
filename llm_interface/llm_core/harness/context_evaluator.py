"""Evaluate LLM-extracted context against gold ground truth."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextEvalResult:
    field_scores: dict[str, bool] = field(default_factory=dict)
    # per-key match: True = correct, False = wrong/missing

    precision: float | None = None
    # correct non-null extractions / total non-null extractions

    recall: float | None = None
    # correct extractions / total gold keys

    exact_match: bool | None = None
    # True only when every gold key is correctly extracted

    skipped: bool = False
    # True when gold context is empty (nothing to evaluate)


def evaluate_context(extracted: dict, gold: dict) -> ContextEvalResult:
    """Compare LLM-extracted context against gold ground truth.

    Scoring rules:
    - Only gold keys are required; extra extracted keys are not penalised.
    - A key is "correct" when extracted value matches gold (case-insensitive
      for strings, within 0.01 for numbers).
    - null / missing extraction for a gold key counts as incorrect.
    """
    if not gold:
        return ContextEvalResult(skipped=True)

    field_scores: dict[str, bool] = {}
    for key, gold_val in gold.items():
        extracted_val = extracted.get(key)
        field_scores[key] = _values_match(extracted_val, gold_val)

    gold_count = len(gold)
    correct_count = sum(field_scores.values())

    # Recall: how many gold keys were correctly extracted
    recall = correct_count / gold_count

    # Precision: of the non-null extracted keys, how many are correct
    non_null_extracted = [
        k for k, v in extracted.items() if v is not None
    ]
    if non_null_extracted:
        correct_in_extracted = sum(
            1 for k in non_null_extracted
            if k in gold and _values_match(extracted[k], gold[k])
        )
        precision = correct_in_extracted / len(non_null_extracted)
    else:
        precision = 0.0 if gold else 1.0

    exact_match = recall == 1.0 and all(field_scores.values())

    return ContextEvalResult(
        field_scores=field_scores,
        precision=precision,
        recall=recall,
        exact_match=exact_match,
    )


_ALIASES: dict[str, str] = {
    # genome builds
    "hg38": "GRCh38",
    "hg19": "GRCh37",
    "grch38": "GRCh38",
    "grch37": "GRCh37",
    # organisms
    "human": "homo_sapiens",
    "mouse": "mus_musculus",
    # sequencers
    "ont": "nanopore",
    "oxford nanopore": "nanopore",
    "illumina ngs": "illumina",
    # data types
    "single-end": "short_read",
    "paired-end": "short_read",
}


def _values_match(extracted, gold) -> bool:
    if extracted is None:
        return False
    if isinstance(gold, bool):
        if isinstance(extracted, bool):
            return extracted == gold
        return str(extracted).lower() in ("true", "1") if gold else str(extracted).lower() in ("false", "0")
    if isinstance(gold, str):
        norm_e = _ALIASES.get(str(extracted).lower().strip(), str(extracted).lower().strip())
        norm_g = _ALIASES.get(gold.lower().strip(), gold.lower().strip())
        return norm_e == norm_g
    if isinstance(gold, (int, float)):
        try:
            return abs(float(extracted) - float(gold)) < 0.01
        except (TypeError, ValueError):
            return False
    return extracted == gold
