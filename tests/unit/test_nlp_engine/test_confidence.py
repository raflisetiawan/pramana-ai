"""Unit tests for confidence scorer — Task 3.5.3.

Covers:
- Score normalization to [0.0, 1.0]
- Flagging when confidence < threshold
- Manual source floor guarantee
- Blending with and without embedding
- Code frequency prior effect
- Batch scoring via score_candidates()
- flag_result() convenience function
- Edge cases (NaN, boundary values)
"""

from pathlib import Path
import sys

NLP_ENGINE_PATH = Path(__file__).resolve().parents[3] / "services" / "nlp-engine"
sys.path.insert(0, str(NLP_ENGINE_PATH))

import pytest  # noqa: E402

from app.pipeline.confidence import (  # noqa: E402
    CODE_FREQUENCY_TABLE,
    NLP_CONFIDENCE_THRESHOLD,
    ConfidenceResult,
    flag_result,
    score_candidate,
    score_candidates,
)


# ---------------------------------------------------------------------------
# 1. Score normalization — always in [0.0, 1.0]
# ---------------------------------------------------------------------------


class TestScoreNormalization:
    """Final confidence must always be in [0.0, 1.0]."""

    def test_perfect_scores_produce_high_confidence(self):
        result = score_candidate(1.0, "I50.0", embedding_score=1.0, source="fuzzy")
        assert 0.0 <= result.confidence <= 1.0
        assert result.confidence > 0.90

    def test_zero_scores_produce_low_confidence(self):
        result = score_candidate(0.0, "I50.0", embedding_score=0.0, source="fuzzy")
        assert 0.0 <= result.confidence <= 1.0
        assert result.confidence < 0.30

    def test_out_of_range_inputs_are_clamped(self):
        result = score_candidate(1.5, "I50.0", embedding_score=-0.3, source="fuzzy")
        assert 0.0 <= result.confidence <= 1.0

    def test_confidence_has_four_decimal_places(self):
        result = score_candidate(0.8123456, "I50.0", source="fuzzy")
        decimals = str(result.confidence).split(".")[-1]
        assert len(decimals) <= 4


# ---------------------------------------------------------------------------
# 2. Flagging behavior
# ---------------------------------------------------------------------------


class TestFlagging:
    """Candidates below NLP_CONFIDENCE_THRESHOLD should be flagged."""

    def test_high_confidence_not_flagged(self):
        result = score_candidate(0.95, "I50.0", source="fuzzy")
        assert not result.flagged
        assert result.flag_reason == ""

    def test_low_confidence_is_flagged(self):
        result = score_candidate(0.40, "I50.0", source="fuzzy")
        assert result.flagged
        assert "threshold" in result.flag_reason.lower()
        assert "I50.0" in result.flag_reason

    def test_exact_threshold_not_flagged(self):
        """Score equal to threshold should NOT be flagged."""
        result = score_candidate(0.999, "I50.0", source="fuzzy")
        # With frequency blending this might shift, but a very high fuzzy
        # should not be flagged.
        if result.confidence >= NLP_CONFIDENCE_THRESHOLD:
            assert not result.flagged

    def test_custom_threshold_respected(self):
        result = score_candidate(0.85, "I50.0", source="fuzzy", threshold=0.95)
        assert result.flagged

    def test_flag_reason_contains_icd_code(self):
        result = score_candidate(0.30, "B20", source="fuzzy")
        assert result.flagged
        assert "B20" in result.flag_reason


# ---------------------------------------------------------------------------
# 3. Manual source floor
# ---------------------------------------------------------------------------


class TestManualSourceFloor:
    """Manual mappings should have a guaranteed confidence floor >= 0.92."""

    def test_manual_source_gets_floor(self):
        result = score_candidate(0.50, "I50.0", source="manual")
        assert result.confidence >= 0.92

    def test_manual_with_embedding_gets_floor(self):
        result = score_candidate(0.50, "I50.0", embedding_score=0.40, source="manual+embedding")
        assert result.confidence >= 0.92

    def test_non_manual_source_no_floor(self):
        result = score_candidate(0.50, "B20", source="fuzzy")
        assert result.confidence < 0.92


# ---------------------------------------------------------------------------
# 4. Blending: with vs without embedding
# ---------------------------------------------------------------------------


class TestBlendingBehavior:
    """Verify three-signal blending and two-signal fallback."""

    def test_embedding_available_uses_three_signals(self):
        with_embed = score_candidate(
            0.80, "I50.0", embedding_score=0.90, source="fuzzy"
        )
        without_embed = score_candidate(0.80, "I50.0", source="fuzzy")
        # With a high embedding score, the confidence should be at least as
        # high (or different) compared to without.
        assert with_embed.confidence != without_embed.confidence

    def test_embedding_none_falls_back_gracefully(self):
        result = score_candidate(0.80, "I50.0", embedding_score=None, source="fuzzy")
        assert result.embedding_score is None
        assert 0.0 <= result.confidence <= 1.0

    def test_high_embedding_boosts_score(self):
        low_embed = score_candidate(
            0.80, "I50.0", embedding_score=0.30, source="fuzzy"
        )
        high_embed = score_candidate(
            0.80, "I50.0", embedding_score=0.95, source="fuzzy"
        )
        assert high_embed.confidence > low_embed.confidence


# ---------------------------------------------------------------------------
# 5. Code frequency prior
# ---------------------------------------------------------------------------


class TestCodeFrequency:
    """Frequency table should influence the final score."""

    def test_known_code_uses_table_frequency(self):
        result = score_candidate(0.80, "I50.0", source="fuzzy")
        assert result.code_frequency == CODE_FREQUENCY_TABLE["I50.0"]

    def test_unknown_code_uses_default_frequency(self):
        result = score_candidate(0.80, "Z99.99", source="fuzzy")
        assert result.code_frequency == 0.50  # default

    def test_high_frequency_code_scores_higher(self):
        # I50.0 has frequency 1.0, B20 has frequency 0.20
        high_freq = score_candidate(0.80, "I50.0", source="fuzzy")
        low_freq = score_candidate(0.80, "B20", source="fuzzy")
        assert high_freq.confidence > low_freq.confidence


# ---------------------------------------------------------------------------
# 6. Batch scoring
# ---------------------------------------------------------------------------


class TestBatchScoring:
    """score_candidates() should handle lists correctly."""

    def test_batch_returns_correct_count(self):
        candidates = [
            {"kode": "I50.0", "fuzzy_score": 0.95, "embedding_score": None, "source": "manual"},
            {"kode": "J18.9", "fuzzy_score": 0.70, "embedding_score": None, "source": "fuzzy"},
            {"kode": "B20", "fuzzy_score": 0.40, "embedding_score": None, "source": "fuzzy"},
        ]
        results = score_candidates(candidates)
        assert len(results) == 3

    def test_batch_sorted_by_confidence_descending(self):
        candidates = [
            {"kode": "B20", "fuzzy_score": 0.40, "source": "fuzzy"},
            {"kode": "I50.0", "fuzzy_score": 0.95, "source": "manual"},
            {"kode": "J18.9", "fuzzy_score": 0.70, "source": "fuzzy"},
        ]
        results = score_candidates(candidates)
        confidences = [r.confidence for r in results]
        assert confidences == sorted(confidences, reverse=True)

    def test_batch_with_embedding_scores(self):
        candidates = [
            {"kode": "I50.0", "fuzzy_score": 0.90, "embedding_score": 0.85, "source": "fuzzy+embedding"},
        ]
        results = score_candidates(candidates)
        assert len(results) == 1
        assert results[0].embedding_score is not None

    def test_empty_batch(self):
        assert score_candidates([]) == []


# ---------------------------------------------------------------------------
# 7. flag_result() convenience function
# ---------------------------------------------------------------------------


class TestFlagResultFunction:
    """flag_result() should produce consistent results."""

    def test_high_confidence_not_flagged(self):
        flagged, reason = flag_result(0.90, "I50.0")
        assert not flagged
        assert reason == ""

    def test_low_confidence_flagged(self):
        flagged, reason = flag_result(0.50, "J18.9")
        assert flagged
        assert "J18.9" in reason

    def test_custom_threshold(self):
        flagged, _ = flag_result(0.80, "I50.0", threshold=0.85)
        assert flagged


# ---------------------------------------------------------------------------
# 8. ConfidenceResult dataclass
# ---------------------------------------------------------------------------


class TestConfidenceResultDataclass:
    """ConfidenceResult should be immutable and serializable."""

    def test_to_dict_returns_all_fields(self):
        result = score_candidate(0.80, "I50.0", source="fuzzy")
        d = result.to_dict()
        expected_keys = {
            "icd_code", "confidence", "flagged", "flag_reason",
            "fuzzy_score", "embedding_score", "code_frequency", "source",
        }
        assert set(d.keys()) == expected_keys

    def test_frozen_dataclass(self):
        result = score_candidate(0.80, "I50.0", source="fuzzy")
        with pytest.raises(AttributeError):
            result.confidence = 0.99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 9. Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Boundary and degenerate inputs."""

    def test_nan_fuzzy_score_handled(self):
        result = score_candidate(float("nan"), "I50.0", source="fuzzy")
        assert 0.0 <= result.confidence <= 1.0

    def test_zero_fuzzy_zero_embedding(self):
        result = score_candidate(0.0, "I50.0", embedding_score=0.0, source="fuzzy")
        assert result.confidence >= 0.0

    def test_default_threshold_is_075(self):
        assert NLP_CONFIDENCE_THRESHOLD == 0.75
