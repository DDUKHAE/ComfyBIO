import pytest
from llm_core.gold.schema import AdversarialOverride, AlternativeGold, CanonicalGold, TieredGold, Verdict
from llm_core.gold.evaluator import GoldEvaluator


@pytest.fixture
def de_gold():
    return TieredGold(
        query_id="TR_006",
        family="de_analysis",
        context={"n_samples_per_group": 4},
        canonical=CanonicalGold(
            tools=["edgeR"],
            expected_output_criteria={"top10_overlap_min": 1.0},
        ),
        alternatives=AlternativeGold(
            tools=["DESeq2", "limma_voom"],
            functional_equivalence_criteria={"top10_overlap_with_canonical": ">= 0.80"},
        ),
        invalid_tools=["kallisto", "STAR", "fastp"],
        adversarial_override=AdversarialOverride(
            bad_hint_tool="DESeq2",
            correct_behaviors=["use_edgeR", "warn_sample_size"],
        ),
    )


def test_correct_canonical(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {"top10_overlap_min": 1.0}
    verdict = evaluator.evaluate(["edgeR"], output)
    assert verdict == Verdict.CORRECT_CANONICAL


def test_correct_alternative_above_threshold(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {"top10_overlap_with_canonical": 0.90}
    verdict = evaluator.evaluate(["DESeq2"], output)
    assert verdict == Verdict.CORRECT_ALTERNATIVE


def test_correct_alternative_below_threshold(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {"top10_overlap_with_canonical": 0.70}
    verdict = evaluator.evaluate(["DESeq2"], output)
    assert verdict == Verdict.INCORRECT


def test_critical_error_invalid_tool(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {}
    verdict = evaluator.evaluate(["kallisto"], output)
    assert verdict == Verdict.CRITICAL_ERROR


def test_incorrect_unknown_tool(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {}
    verdict = evaluator.evaluate(["some_unknown_tool"], output)
    assert verdict == Verdict.INCORRECT
