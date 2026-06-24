"""Tests for context extraction (Function 1)."""
from __future__ import annotations

import pytest

from llm_core.harness.context_evaluator import ContextEvalResult, evaluate_context
from llm_core.harness.context_extractor import (
    ContextExtractionResult,
    _extract_json_block,
    _normalize,
    _parse_extraction_response,
)
from llm_core.harness.context_schema import format_schema_hint, get_schema


# ---------------------------------------------------------------------------
# context_schema
# ---------------------------------------------------------------------------

class TestContextSchema:
    def test_variant_analysis_keys(self):
        schema = get_schema("variant_analysis")
        assert "sequencer" in schema
        assert "analysis_type" in schema
        assert "n_samples" in schema

    def test_unknown_domain_returns_empty(self):
        assert get_schema("unknown_domain") == {}

    def test_format_schema_hint_nonempty(self):
        hint = format_schema_hint("transcriptomics")
        assert "data_type" in hint
        assert "short_read" in hint

    def test_format_schema_hint_unknown_domain(self):
        hint = format_schema_hint("nonexistent")
        assert "no structured" in hint


# ---------------------------------------------------------------------------
# context_extractor — JSON parsing
# ---------------------------------------------------------------------------

class TestExtractJsonBlock:
    def test_bare_json(self):
        text = '{"sequencer": "illumina"}'
        assert _extract_json_block(text) == '{"sequencer": "illumina"}'

    def test_fenced_json(self):
        text = '```json\n{"sequencer": "nanopore"}\n```'
        result = _extract_json_block(text)
        assert result is not None
        assert "nanopore" in result

    def test_prose_with_embedded_json(self):
        text = 'Here is my answer: {"analysis_type": "germline"} done.'
        result = _extract_json_block(text)
        assert result is not None
        assert "germline" in result

    def test_no_json_returns_none(self):
        assert _extract_json_block("no json here at all") is None


class TestNormalize:
    def test_string_enum_accepted(self):
        schema = get_schema("variant_analysis")
        out = _normalize({"sequencer": "illumina"}, schema)
        assert out["sequencer"] == "illumina"

    def test_case_insensitive_string(self):
        schema = get_schema("variant_analysis")
        out = _normalize({"sequencer": "Illumina"}, schema)
        assert out["sequencer"] == "illumina"

    def test_unknown_enum_value_dropped(self):
        schema = get_schema("variant_analysis")
        out = _normalize({"sequencer": "unknown_platform"}, schema)
        assert "sequencer" not in out

    def test_null_values_dropped(self):
        schema = get_schema("variant_analysis")
        out = _normalize({"sequencer": None, "analysis_type": "germline"}, schema)
        assert "sequencer" not in out
        assert out["analysis_type"] == "germline"

    def test_integer_field(self):
        schema = get_schema("variant_analysis")
        out = _normalize({"n_samples": "50"}, schema)
        assert out["n_samples"] == 50

    def test_invalid_integer_dropped(self):
        schema = get_schema("variant_analysis")
        out = _normalize({"n_samples": "not_a_number"}, schema)
        assert "n_samples" not in out

    def test_unknown_keys_ignored(self):
        schema = get_schema("variant_analysis")
        out = _normalize({"unknown_key": "value", "sequencer": "illumina"}, schema)
        assert "unknown_key" not in out
        assert out["sequencer"] == "illumina"


class TestParseExtractionResponse:
    def test_valid_json_response(self):
        raw = '{"sequencer": "illumina", "analysis_type": "germline"}'
        schema = get_schema("variant_analysis")
        result = _parse_extraction_response(raw, schema)
        assert result.parse_error is None
        assert result.extracted["sequencer"] == "illumina"
        assert result.extracted["analysis_type"] == "germline"

    def test_no_json_sets_parse_error(self):
        result = _parse_extraction_response("I cannot determine the context.", get_schema("variant_analysis"))
        assert result.parse_error == "no_json_found"
        assert result.extracted == {}

    def test_null_fields_excluded(self):
        raw = '{"sequencer": "illumina", "analysis_type": null}'
        schema = get_schema("variant_analysis")
        result = _parse_extraction_response(raw, schema)
        assert "analysis_type" not in result.extracted
        assert result.extracted["sequencer"] == "illumina"


# ---------------------------------------------------------------------------
# context_evaluator
# ---------------------------------------------------------------------------

class TestEvaluateContext:
    def test_exact_match(self):
        result = evaluate_context(
            extracted={"sequencer": "illumina", "analysis_type": "germline"},
            gold={"sequencer": "illumina", "analysis_type": "germline"},
        )
        assert result.exact_match is True
        assert result.recall == 1.0
        assert result.precision == 1.0

    def test_partial_match(self):
        result = evaluate_context(
            extracted={"sequencer": "illumina"},
            gold={"sequencer": "illumina", "analysis_type": "germline"},
        )
        assert result.exact_match is False
        assert result.recall == pytest.approx(0.5)
        assert result.field_scores["sequencer"] is True
        assert result.field_scores["analysis_type"] is False

    def test_wrong_value(self):
        result = evaluate_context(
            extracted={"sequencer": "nanopore"},
            gold={"sequencer": "illumina"},
        )
        assert result.exact_match is False
        assert result.recall == 0.0
        assert result.field_scores["sequencer"] is False

    def test_empty_gold_skips(self):
        result = evaluate_context(extracted={"sequencer": "illumina"}, gold={})
        assert result.skipped is True
        assert result.exact_match is None

    def test_extra_extracted_keys_not_penalised(self):
        result = evaluate_context(
            extracted={"sequencer": "illumina", "extra_key": "value"},
            gold={"sequencer": "illumina"},
        )
        assert result.exact_match is True
        assert result.recall == 1.0

    def test_case_insensitive_string_match(self):
        result = evaluate_context(
            extracted={"sequencer": "Illumina"},
            gold={"sequencer": "illumina"},
        )
        assert result.field_scores["sequencer"] is True

    def test_integer_field_match(self):
        result = evaluate_context(
            extracted={"n_samples": 30},
            gold={"n_samples": 30},
        )
        assert result.field_scores["n_samples"] is True

    def test_none_extracted_counts_as_wrong(self):
        result = evaluate_context(
            extracted={},
            gold={"sequencer": "illumina"},
        )
        assert result.field_scores["sequencer"] is False
        assert result.recall == 0.0
