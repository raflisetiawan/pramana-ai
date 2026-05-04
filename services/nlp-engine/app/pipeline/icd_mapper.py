"""ICD mapper for Indonesian clinical text.

Phase 3.2 combines three deliberately transparent signals:
- manual Indonesian aliases for common diagnoses/procedures,
- fuzzy string matching with RapidFuzz,
- optional IndoBERT embedding similarity for re-ranking.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Literal

from rapidfuzz import fuzz, process

ICDSystem = Literal["icd10", "icd9", "all"]

BASE_DIR = Path(__file__).resolve().parents[1]       # .../app/
SERVICE_DIR = BASE_DIR.parent                         # .../nlp-engine/ (or /app in Docker)
# REPO_ROOT: two levels above the service dir (dev), or fallback to SERVICE_DIR (Docker)
try:
    REPO_ROOT = SERVICE_DIR.parents[1]
except IndexError:
    REPO_ROOT = SERVICE_DIR
DEFAULT_MODEL_NAME = "indobenchmark/indobert-base-p1"
DEFAULT_MODEL_CACHE_DIR = BASE_DIR / "saved_models"

COMMON_MAPPINGS: dict[str, str] = {
    "gagal jantung": "I50.0",
    "gagal jantung kongestif": "I50.0",
    "chf": "I50.0",
    "congestive heart failure": "I50.0",
    "hipertensi": "I10",
    "darah tinggi": "I10",
    "diabetes": "E11.9",
    "diabetes melitus": "E11.9",
    "diabetes melitus tipe 2": "E11.9",
    "dm tipe 2": "E11.9",
    "pneumonia": "J18.9",
    "bronkopneumonia": "J18.0",
    "gagal ginjal kronis": "N18.5",
    "ckd": "N18.5",
    "chronic kidney disease": "N18.5",
    "serangan jantung": "I21.9",
    "infark miokard akut": "I21.9",
    "ami": "I21.9",
    "stroke": "I64",
    "asma": "J45.9",
    "sesak napas": "R06.0",
    "dyspnea": "R06.0",
    "demam": "R50.9",
    "kejang": "G40.9",
    "tuberkulosis paru": "A16.2",
    "tb paru": "A16.2",
    "anemia": "D50.9",
    "diare": "A09",
    "nyeri punggung bawah": "M54.5",
    "low back pain": "M54.5",
    "fraktur femur": "S72.0",
    "infeksi saluran kemih": "N39.0",
    "isk": "N39.0",
    "apendisitis": "K35.9",
    "apendisitis akut": "K35.9",
    "appendicitis": "K35.9",
    # Obstetric
    "persalinan sc": "O82",
    "persalinan sectio caesarea": "O82",
    "kehamilan dengan sc": "O82",
    "kehamilan bekas sc": "O82",
    "delivery by caesarean section": "O82",
    # Procedures (ICD-9-CM)
    "hemodialisis": "39.95",
    "cuci darah": "39.95",
    "transfusi darah": "99.04",
    "transfusi whole blood": "99.04",
    "echocardiography": "88.72",
    "ekokardiografi": "88.72",
    "usg jantung": "88.72",
    "appendectomy": "47.09",
    "apendektomi": "47.09",
    "sectio caesarea": "74.1",
    "operasi sesar": "74.1",
    "pemasangan stent": "36.07",
    "stent koroner": "36.07",
    "orif femur": "79.35",
    "ventilasi mekanik": "96.71",
    "intubasi": "96.04",
}


@dataclass(frozen=True, slots=True)
class ICDEntry:
    """One ICD master-data row plus searchable aliases."""

    kode: str
    nama: str
    system: Literal["icd10", "icd9"]
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def searchable_terms(self) -> tuple[str, ...]:
        """Return normalized terms used by fuzzy and embedding search."""
        terms = [self.nama, self.kode, *self.aliases]
        return tuple(dict.fromkeys(_normalize_text(term) for term in terms if term))


@dataclass(frozen=True, slots=True)
class ICDCandidate:
    """Candidate ICD match returned to callers."""

    kode: str
    nama: str
    score: float
    system: Literal["icd10", "icd9"]
    fuzzy_score: float
    embedding_score: float | None
    source: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable candidate."""
        return asdict(self)


class ICDMapper:
    """In-memory ICD mapper with fuzzy search and optional IndoBERT re-ranking."""

    def __init__(
        self,
        icd10_path: Path | None = None,
        icd9_path: Path | None = None,
        *,
        use_embeddings: bool = True,
        model_name: str = DEFAULT_MODEL_NAME,
        model_cache_dir: Path = DEFAULT_MODEL_CACHE_DIR,
    ) -> None:
        self.icd10_path = icd10_path or _resolve_data_path("icd10.json")
        self.icd9_path = icd9_path or _resolve_data_path("icd9.json")
        self.entries = _load_entries(self.icd10_path, self.icd9_path)
        self.entries_by_code = {entry.kode: entry for entry in self.entries}
        self._choices = _build_choices(self.entries)
        self._use_embeddings = use_embeddings
        self._model_name = model_name
        self._model_cache_dir = model_cache_dir
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._entry_embeddings: dict[str, list[float]] = {}

        if use_embeddings:
            self._initialize_embeddings()

    def map_diagnosis(
        self,
        diagnosis_name: str,
        *,
        system: ICDSystem = "icd10",
        top_k: int = 5,
    ) -> list[dict[str, object]]:
        """Map diagnosis/procedure text to ICD candidates.

        Args:
            diagnosis_name: Plain diagnosis or procedure text.
            system: ``icd10`` for diagnoses, ``icd9`` for procedures, or ``all``.
            top_k: Maximum candidates to return.

        Returns:
            Candidate dictionaries sorted by descending score.
        """
        return [
            candidate.to_dict()
            for candidate in self.search(diagnosis_name, system=system, top_k=top_k)
        ]

    def search(
        self,
        query: str,
        *,
        system: ICDSystem = "icd10",
        top_k: int = 5,
    ) -> list[ICDCandidate]:
        """Return ranked ICD candidates for a query."""
        normalized_query = _normalize_text(query)
        if not normalized_query:
            return []

        raw_matches = self._fuzzy_matches(normalized_query, system=system, limit=max(top_k * 4, 10))
        manual_code = COMMON_MAPPINGS.get(normalized_query)
        manual_candidate: tuple[ICDEntry, float] | None = None
        if manual_code:
            entry = self.entries_by_code.get(manual_code)
            if entry and (system == "all" or entry.system == system):
                manual_candidate = (entry, 100.0)

        candidate_scores: dict[str, tuple[ICDEntry, float, str]] = {}
        if manual_candidate:
            entry, score = manual_candidate
            candidate_scores[entry.kode] = (entry, score, "manual")

        for entry, fuzzy_score in raw_matches:
            existing = candidate_scores.get(entry.kode)
            if not existing or fuzzy_score > existing[1]:
                candidate_scores[entry.kode] = (entry, fuzzy_score, "fuzzy")

        query_embedding = self._embed_text(normalized_query)
        candidates: list[ICDCandidate] = []
        for entry, fuzzy_score, source in candidate_scores.values():
            embedding_score = self._embedding_score(query_embedding, entry)
            combined_score = _combine_scores(fuzzy_score, embedding_score, source)
            candidates.append(
                ICDCandidate(
                    kode=entry.kode,
                    nama=entry.nama,
                    score=combined_score,
                    system=entry.system,
                    fuzzy_score=round(fuzzy_score / 100.0, 4),
                    embedding_score=embedding_score,
                    source=source if embedding_score is None else f"{source}+embedding",
                )
            )

        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        return candidates[:top_k]

    def _fuzzy_matches(
        self,
        normalized_query: str,
        *,
        system: ICDSystem,
        limit: int,
    ) -> list[tuple[ICDEntry, float]]:
        choices = [
            choice
            for choice in self._choices
            if system == "all" or choice["entry"].system == system
        ]
        terms = [str(choice["term"]) for choice in choices]
        extracted = process.extract(
            normalized_query,
            terms,
            scorer=fuzz.WRatio,
            limit=limit,
        )

        best_by_code: dict[str, tuple[ICDEntry, float]] = {}
        for _choice, score, index in extracted:
            entry = choices[index]["entry"]
            existing = best_by_code.get(entry.kode)
            if not existing or score > existing[1]:
                best_by_code[entry.kode] = (entry, float(score))

        return sorted(best_by_code.values(), key=lambda item: item[1], reverse=True)

    def _initialize_embeddings(self) -> None:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            self._torch = torch
            self._tokenizer = AutoTokenizer.from_pretrained(
                self._model_name,
                cache_dir=str(self._model_cache_dir),
                local_files_only=True,
            )
            self._model = AutoModel.from_pretrained(
                self._model_name,
                cache_dir=str(self._model_cache_dir),
                local_files_only=True,
            )
            self._model.eval()
            for entry in self.entries:
                text = " ".join(entry.searchable_terms)
                self._entry_embeddings[entry.kode] = self._embed_text(text) or []
        except Exception:
            self._use_embeddings = False
            self._tokenizer = None
            self._model = None
            self._torch = None
            self._entry_embeddings = {}

    def _embed_text(self, text: str) -> list[float] | None:
        if not self._use_embeddings or not self._tokenizer or not self._model or not self._torch:
            return None
        with self._torch.no_grad():
            inputs = self._tokenizer(
                text,
                truncation=True,
                max_length=128,
                padding=True,
                return_tensors="pt",
            )
            outputs = self._model(**inputs)
            attention_mask = inputs["attention_mask"].unsqueeze(-1)
            token_embeddings = outputs.last_hidden_state * attention_mask
            summed = token_embeddings.sum(dim=1)
            counts = attention_mask.sum(dim=1).clamp(min=1)
            vector = (summed / counts).squeeze(0)
            norm = vector.norm(p=2).clamp(min=1e-12)
            return (vector / norm).cpu().tolist()

    def _embedding_score(self, query_embedding: list[float] | None, entry: ICDEntry) -> float | None:
        if query_embedding is None:
            return None
        entry_embedding = self._entry_embeddings.get(entry.kode)
        if not entry_embedding:
            return None
        cosine = sum(left * right for left, right in zip(query_embedding, entry_embedding))
        return round(max(0.0, min(1.0, (cosine + 1.0) / 2.0)), 4)


def map_diagnosis(
    diagnosis_name: str,
    *,
    system: ICDSystem = "icd10",
    top_k: int = 5,
) -> list[dict[str, object]]:
    """Convenience function using the shared in-memory mapper."""
    return get_icd_mapper().map_diagnosis(diagnosis_name, system=system, top_k=top_k)


@lru_cache(maxsize=1)
def get_icd_mapper() -> ICDMapper:
    """Return the singleton mapper loaded in memory."""
    return ICDMapper()


def warmup_icd_mapper() -> ICDMapper:
    """Load ICD master data and embeddings during application startup."""
    return get_icd_mapper()


def _load_entries(icd10_path: Path, icd9_path: Path) -> list[ICDEntry]:
    entries: list[ICDEntry] = []
    entries.extend(_read_icd_file(icd10_path, "icd10"))
    entries.extend(_read_icd_file(icd9_path, "icd9"))
    return _attach_aliases(entries)


def _read_icd_file(path: Path, system: Literal["icd10", "icd9"]) -> list[ICDEntry]:
    with path.open(encoding="utf-8") as file:
        rows = json.load(file)
    return [
        ICDEntry(kode=str(row["kode"]).strip(), nama=str(row["nama"]).strip(), system=system)
        for row in rows
    ]


def _attach_aliases(entries: list[ICDEntry]) -> list[ICDEntry]:
    aliases_by_code: dict[str, list[str]] = {}
    for alias, code in COMMON_MAPPINGS.items():
        aliases_by_code.setdefault(code, []).append(alias)

    enriched: list[ICDEntry] = []
    for entry in entries:
        aliases = tuple(sorted(set(aliases_by_code.get(entry.kode, []))))
        enriched.append(ICDEntry(kode=entry.kode, nama=entry.nama, system=entry.system, aliases=aliases))
    return enriched


def _build_choices(entries: Iterable[ICDEntry]) -> list[dict[str, object]]:
    choices: list[dict[str, object]] = []
    for entry in entries:
        for term in entry.searchable_terms:
            choices.append({"term": term, "entry": entry})
    return choices


def _resolve_data_path(filename: str) -> Path:
    candidates = (
        BASE_DIR / "data" / filename,
        SERVICE_DIR / "app" / "data" / filename,
        REPO_ROOT / "services" / "mock-vclaim" / "app" / "data" / filename,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"ICD master data not found: {filename}")


def _normalize_text(text: str) -> str:
    lowered = text.casefold()
    lowered = re.sub(r"[^a-z0-9.]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _combine_scores(fuzzy_score: float, embedding_score: float | None, source: str) -> float:
    fuzzy_normalized = fuzzy_score / 100.0
    if embedding_score is None:
        combined = fuzzy_normalized
    else:
        combined = (0.65 * fuzzy_normalized) + (0.35 * embedding_score)
    if source == "manual":
        combined = max(combined, 0.97)
    if math.isnan(combined):
        combined = 0.0
    return round(max(0.0, min(1.0, combined)), 4)
