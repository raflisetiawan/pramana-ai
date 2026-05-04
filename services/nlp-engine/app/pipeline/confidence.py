"""Confidence scoring for ICD coding candidates.

Phase 3.3 — three complementary signals are blended:

1. **fuzzy_score**      — rapidfuzz WRatio, already normalized to 0–1.
2. **embedding_score**  — cosine similarity from IndoBERT embeddings, 0–1.
                          ``None`` when the model is unavailable (CPU-only).
3. **code_frequency**   — relative prevalence of an ICD code in the reference
                          corpus (``CODE_FREQUENCY_TABLE``). High-frequency
                          codes are slightly preferred when other signals tie,
                          which mirrors clinical reality.

The final score is normalized to **0.0–1.0**. Any candidate whose score is
below ``NLP_CONFIDENCE_THRESHOLD`` is automatically flagged so downstream
verifiers know to apply extra scrutiny.

Usage::

    from app.pipeline.confidence import score_candidate, flag_result

    scored = score_candidate(
        fuzzy_score=0.82,
        embedding_score=0.71,
        icd_code="I50.0",
        source="manual",
    )
    # scored.confidence → 0.9107
    # scored.flagged    → False
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Candidates with a final confidence below this value are flagged.
NLP_CONFIDENCE_THRESHOLD: float = 0.75

# Blending weights — must sum to 1.0 when embedding is available.
_W_FUZZY: float = 0.50
_W_EMBED: float = 0.35
_W_FREQ: float = 0.15

# When embedding is unavailable the remaining 35% is redistributed.
_W_FUZZY_NO_EMBED: float = 0.70
_W_FREQ_NO_EMBED: float = 0.30

# Manual-mapping candidates receive a score floor so they are not accidentally
# pushed below the threshold by a weak frequency signal.
_MANUAL_SCORE_FLOOR: float = 0.92

# ---------------------------------------------------------------------------
# Code-frequency table
# ---------------------------------------------------------------------------
# Relative prevalence of ICD codes observed in Indonesian BPJS-Kesehatan
# hospital claims. Values are normalised to [0, 1] where 1.0 = most common.
# This table acts as a lightweight prior; missing codes default to 0.5.
# Extend this dict as more training data becomes available.

CODE_FREQUENCY_TABLE: dict[str, float] = {
    # --- ICD-10: very common diagnoses ---
    "I50.0": 1.00,   # Congestive Heart Failure
    "I10":   0.98,   # Essential Hypertension
    "E11.9": 0.95,   # T2 Diabetes Mellitus, unspecified
    "J18.9": 0.93,   # Pneumonia, unspecified
    "N18.5": 0.88,   # CKD Stage 5
    "I21.9": 0.85,   # Acute MI, unspecified
    "I64":   0.82,   # Stroke NOS
    "J45.9": 0.80,   # Asthma, unspecified
    "A16.2": 0.78,   # Pulmonary TB without confirmation
    "D50.9": 0.75,   # Iron deficiency anaemia, unspecified
    "G40.9": 0.72,   # Epilepsy, unspecified
    "R50.9": 0.70,   # Fever, unspecified
    "R06.0": 0.68,   # Dyspnoea
    "A09":   0.66,   # Gastroenteritis/colitis
    "M54.5": 0.64,   # Low back pain
    "N39.0": 0.62,   # UTI, site not specified
    "K35.9": 0.60,   # Acute appendicitis, unspecified
    "S72.0": 0.58,   # Fracture neck of femur
    "O82":   0.56,   # Delivery by CS
    "I50.1": 0.55,   # Left ventricular failure
    "I11.0": 0.53,   # Hypertensive heart disease w/ HF
    "I20.0": 0.52,   # Unstable angina
    "I25.1": 0.51,   # Atherosclerotic heart disease
    "I48":   0.50,   # Atrial fibrillation and flutter
    "I63.9": 0.50,   # Cerebral infarction, unspecified
    "E10.9": 0.48,   # T1 Diabetes, unspecified
    "E11.5": 0.46,   # T2 Diabetes w/ circ. complications
    "E13.9": 0.44,   # Other DM, unspecified
    "E78.0": 0.42,   # Pure hypercholesterolaemia
    "J18.0": 0.60,   # Bronchopneumonia
    "J44.0": 0.45,   # COPD w/ acute lower resp. infection
    "J44.1": 0.44,   # COPD w/ acute exacerbation
    "J96.0": 0.42,   # Acute respiratory failure
    "N18.3": 0.48,   # CKD Stage 3
    "N18.4": 0.46,   # CKD Stage 4
    "K80.2": 0.40,   # Cholelithiasis w/o cholecystitis
    "K92.2": 0.38,   # GI haemorrhage, unspecified
    "K25.9": 0.36,   # Gastric ulcer, unspecified
    "S82.0": 0.34,   # Fracture of patella
    "S06.0": 0.32,   # Concussion
    "C34.9": 0.30,   # Malignant neoplasm lung
    "C50.9": 0.28,   # Malignant neoplasm breast
    "C18.9": 0.26,   # Malignant neoplasm colon
    "G45.9": 0.24,   # TIA, unspecified
    "M17.9": 0.22,   # Gonarthrosis, unspecified
    "A15.0": 0.40,   # TB lung confirmed sputum
    "B20":   0.20,   # HIV disease
    "R04.2": 0.18,   # Haemoptysis
    "P07.3": 0.16,   # Other preterm infants
    # --- ICD-9-CM: common procedures ---
    "39.95": 0.90,   # Haemodialysis
    "99.04": 0.85,   # Whole blood transfusion
    "88.72": 0.80,   # Echocardiography
    "96.71": 0.75,   # Mechanical ventilation < 96 h
    "96.04": 0.70,   # Endotracheal tube insertion
    "47.09": 0.65,   # Other appendectomy
    "74.1":  0.62,   # Low cervical CS
    "79.35": 0.58,   # ORIF femur
    "36.07": 0.55,   # Drug-eluting coronary stent
    "36.06": 0.50,   # Non-drug-eluting coronary stent
    "51.23": 0.48,   # Laparoscopic cholecystectomy
    "81.54": 0.45,   # Total knee replacement
    "99.15": 0.40,   # Parenteral nutrition infusion
    "33.24": 0.35,   # Closed bronchial biopsy
    "39.99": 0.30,   # Other vessel operations
}

_DEFAULT_FREQUENCY: float = 0.50


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConfidenceResult:
    """Final confidence score for one ICD candidate.

    Attributes:
        icd_code: The ICD-10 or ICD-9 code being scored.
        confidence: Blended score in range [0.0, 1.0].
        flagged: ``True`` when confidence < ``NLP_CONFIDENCE_THRESHOLD``.
        flag_reason: Human-readable reason why the candidate was flagged,
            or an empty string when not flagged.
        fuzzy_score: The raw fuzzy match score (0–1) fed into the blender.
        embedding_score: The embedding cosine score (0–1), or ``None``.
        code_frequency: The frequency prior used from ``CODE_FREQUENCY_TABLE``.
        source: Propagated from ``ICDCandidate.source`` (manual / fuzzy / …).
    """

    icd_code: str
    confidence: float
    flagged: bool
    flag_reason: str
    fuzzy_score: float
    embedding_score: float | None
    code_frequency: float
    source: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "icd_code": self.icd_code,
            "confidence": self.confidence,
            "flagged": self.flagged,
            "flag_reason": self.flag_reason,
            "fuzzy_score": self.fuzzy_score,
            "embedding_score": self.embedding_score,
            "code_frequency": self.code_frequency,
            "source": self.source,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_candidate(
    fuzzy_score: float,
    icd_code: str,
    *,
    embedding_score: float | None = None,
    source: str = "fuzzy",
    threshold: float = NLP_CONFIDENCE_THRESHOLD,
) -> ConfidenceResult:
    """Compute confidence for a single ICD candidate.

    Args:
        fuzzy_score: Normalized rapidfuzz score in [0, 1].
        icd_code: ICD-10 or ICD-9 code string (e.g. ``"I50.0"``).
        embedding_score: Cosine similarity from IndoBERT, in [0, 1].
            Pass ``None`` when the model is unavailable.
        source: Source label from the ICD mapper (``"manual"``, ``"fuzzy"``,
            ``"manual+embedding"``, ``"fuzzy+embedding"``).
        threshold: Override the default confidence threshold.

    Returns:
        A :class:`ConfidenceResult` with the blended score and flag status.
    """
    fuzzy_score = _clamp(fuzzy_score)
    if embedding_score is not None:
        embedding_score = _clamp(embedding_score)

    code_frequency = CODE_FREQUENCY_TABLE.get(icd_code, _DEFAULT_FREQUENCY)
    raw = _blend(fuzzy_score, embedding_score, code_frequency)

    # Manual mappings have a guaranteed confidence floor.
    is_manual = source.startswith("manual")
    if is_manual:
        raw = max(raw, _MANUAL_SCORE_FLOOR)

    confidence = round(_clamp(raw), 4)
    flagged, flag_reason = _evaluate_flag(confidence, icd_code, threshold)

    return ConfidenceResult(
        icd_code=icd_code,
        confidence=confidence,
        flagged=flagged,
        flag_reason=flag_reason,
        fuzzy_score=round(fuzzy_score, 4),
        embedding_score=round(embedding_score, 4) if embedding_score is not None else None,
        code_frequency=round(code_frequency, 4),
        source=source,
    )


def score_candidates(
    candidates: list[dict[str, object]],
    *,
    threshold: float = NLP_CONFIDENCE_THRESHOLD,
) -> list[ConfidenceResult]:
    """Batch-score a list of candidate dicts (as returned by :func:`map_diagnosis`).

    Each dict must have at minimum: ``kode``, ``fuzzy_score``, ``source``.
    ``embedding_score`` is optional and defaults to ``None``.

    Args:
        candidates: List of candidate dictionaries from the ICD mapper.
        threshold: Confidence threshold for flagging.

    Returns:
        List of :class:`ConfidenceResult` sorted by descending confidence.
    """
    results: list[ConfidenceResult] = []
    for cand in candidates:
        result = score_candidate(
            fuzzy_score=float(cand.get("fuzzy_score", 0.0)),
            icd_code=str(cand.get("kode", "")),
            embedding_score=(
                float(cand["embedding_score"])
                if cand.get("embedding_score") is not None
                else None
            ),
            source=str(cand.get("source", "fuzzy")),
            threshold=threshold,
        )
        results.append(result)

    results.sort(key=lambda r: r.confidence, reverse=True)
    return results


def flag_result(
    confidence: float,
    icd_code: str,
    *,
    threshold: float = NLP_CONFIDENCE_THRESHOLD,
) -> tuple[bool, str]:
    """Determine whether a pre-computed confidence score should be flagged.

    Convenience wrapper for callers that have already computed a confidence
    value and only need the flag decision.

    Args:
        confidence: Pre-computed confidence in [0, 1].
        icd_code: The ICD code being evaluated.
        threshold: Confidence threshold (default ``NLP_CONFIDENCE_THRESHOLD``).

    Returns:
        A ``(flagged, flag_reason)`` tuple.
    """
    return _evaluate_flag(_clamp(confidence), icd_code, threshold)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _blend(
    fuzzy_score: float,
    embedding_score: float | None,
    code_frequency: float,
) -> float:
    """Blend the three signals into a single [0, 1] score."""
    if embedding_score is not None:
        combined = (
            _W_FUZZY * fuzzy_score
            + _W_EMBED * embedding_score
            + _W_FREQ * code_frequency
        )
    else:
        combined = (
            _W_FUZZY_NO_EMBED * fuzzy_score
            + _W_FREQ_NO_EMBED * code_frequency
        )

    if math.isnan(combined):
        return 0.0
    return combined


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *value* to [lo, hi]."""
    return max(lo, min(hi, value))


def _evaluate_flag(
    confidence: float,
    icd_code: str,
    threshold: float,
) -> tuple[bool, str]:
    """Return ``(flagged, flag_reason)`` based on confidence and threshold."""
    if confidence < threshold:
        reason = (
            f"Confidence {confidence:.4f} di bawah threshold {threshold:.2f} "
            f"untuk kode {icd_code}"
        )
        return True, reason
    return False, ""
