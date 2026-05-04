"""Rule-based Named Entity Recognition for Indonesian medical resumes.

The first NLP milestone intentionally avoids a trained clinical NER model. It
uses deterministic section parsing, regexes, and keyword matching so the output
is auditable while the IndoBERT/spaCy assets are being prepared for later tasks.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Iterable, Literal

EntityLabel = Literal["DIAGNOSA", "PROSEDUR", "OBAT", "DURASI"]


@dataclass(frozen=True, slots=True)
class MedicalEntity:
    """Entity extracted from a resume medis text."""

    label: EntityLabel
    text: str
    start: int
    end: int
    confidence: float
    source: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return asdict(self)


SECTION_HEADERS = (
    "alasan masuk dirawat",
    "ringkasan riwayat penyakit",
    "pemeriksaan fisik",
    "pemeriksaan penunjang diagnostik terpenting",
    "terapi pengobatan selama di rs",
    "hasil konsultasi",
    "diagnosis utama",
    "diagnosis sekunder",
    "diagnosa utama",
    "diagnosa sekunder",
    "tindakan",
    "prosedur",
    "alergi",
    "hasil laboratorium",
    "diet",
    "instruksi",
    "edukasi",
    "tanggal kontrol",
    "terapi pulang",
)

DIAGNOSIS_KEYWORDS = {
    "anemia",
    "asma",
    "bronkopneumonia",
    "chf",
    "ckd",
    "congestive heart failure",
    "diabetes melitus",
    "diare",
    "dispnea",
    "dyspnoea",
    "fraktur",
    "gagal ginjal",
    "gagal jantung",
    "gastritis",
    "hipertensi",
    "hipoglikemia",
    "infark miokard",
    "kejang",
    "kolik abdomen",
    "pneumonia",
    "stroke",
    "tuberkulosis",
    "ulkus",
    "uti",
}

PROCEDURE_KEYWORDS = {
    "appendectomy",
    "biopsi",
    "ct scan",
    "debridement",
    "echocardiography",
    "ekg",
    "endoskopi",
    "hemodialisis",
    "kateterisasi",
    "laparoskopi",
    "operasi",
    "orif",
    "pemasangan stent",
    "pemeriksaan darah",
    "rontgen",
    "sectio caesarea",
    "transfusi",
    "usg",
    "ventilasi mekanik",
}

MEDICATION_KEYWORDS = {
    "albendazol",
    "albuterol",
    "amlodipin",
    "antihistamin",
    "aspirin",
    "atorvastatin",
    "ceftriaxone",
    "cefuroxime",
    "cetirizine",
    "clopidogrel",
    "furosemide",
    "insulin",
    "metformin",
    "methylprednisolone",
    "omeprazole",
    "ondansetron",
    "paracetamol",
    "ranitidine",
    "salbutamol",
}

HEADER_TO_LABEL: tuple[tuple[str, EntityLabel], ...] = (
    ("diagnosis utama", "DIAGNOSA"),
    ("diagnosis sekunder", "DIAGNOSA"),
    ("diagnosa utama", "DIAGNOSA"),
    ("diagnosa sekunder", "DIAGNOSA"),
    ("alasan masuk dirawat", "DIAGNOSA"),
    ("ringkasan riwayat penyakit", "DIAGNOSA"),
    ("tindakan", "PROSEDUR"),
    ("prosedur", "PROSEDUR"),
    ("pemeriksaan penunjang", "PROSEDUR"),
    ("terapi pengobatan selama di rs", "OBAT"),
    ("terapi pulang", "OBAT"),
)

DATE_PATTERN = re.compile(
    r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b"
)
DURATION_PATTERN = re.compile(
    r"\b(?:selama\s+)?\d{1,3}\s*(?:hari|hr|minggu|bulan|tahun|jam)\b",
    flags=re.IGNORECASE,
)
DOSE_PATTERN = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|iu|tablet|tab|ampul|vial)\b",
    flags=re.IGNORECASE,
)
LINE_ITEM_PATTERN = re.compile(r"^\s*(?:[-*]|\d+[.)])\s*(?P<item>.+?)\s*$")


def extract_entities(resume_text: str) -> list[dict[str, object]]:
    """Extract medical entities from plain text.

    Args:
        resume_text: Raw text from a medical resume.

    Returns:
        A list of dictionaries with label, text, character offsets,
        confidence, and extraction source.
    """
    return [entity.to_dict() for entity in RuleBasedMedicalNER().extract(resume_text)]


class RuleBasedMedicalNER:
    """Regex and keyword based NER for phase 3.1."""

    def extract(self, resume_text: str) -> list[MedicalEntity]:
        """Extract diagnosis, procedure, medication, and duration entities."""
        if not resume_text or not resume_text.strip():
            return []

        text = _normalize_text(resume_text)
        entities: list[MedicalEntity] = []
        entities.extend(_extract_durations(text))
        entities.extend(_extract_keyword_entities(text, DIAGNOSIS_KEYWORDS, "DIAGNOSA"))
        entities.extend(_extract_keyword_entities(text, PROCEDURE_KEYWORDS, "PROSEDUR"))
        entities.extend(_extract_keyword_entities(text, MEDICATION_KEYWORDS, "OBAT"))
        entities.extend(_extract_section_entities(text))
        entities.extend(_extract_medication_doses(text))

        return _dedupe_entities(entities)


@lru_cache(maxsize=1)
def get_spacy_model():
    """Load spaCy multilingual model as an optional tokenizer fallback."""
    try:
        import spacy

        return spacy.load("xx_ent_wiki_sm")
    except Exception:
        try:
            import spacy

            return spacy.blank("xx")
        except Exception:
            return None


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _extract_durations(text: str) -> list[MedicalEntity]:
    entities: list[MedicalEntity] = []
    for pattern in (DATE_PATTERN, DURATION_PATTERN):
        for match in pattern.finditer(text):
            entities.append(
                MedicalEntity(
                    label="DURASI",
                    text=match.group(0).strip(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.92,
                    source="regex:duration",
                )
            )
    return entities


def _extract_keyword_entities(
    text: str,
    keywords: Iterable[str],
    label: EntityLabel,
) -> list[MedicalEntity]:
    entities: list[MedicalEntity] = []
    for keyword in sorted(keywords, key=len, reverse=True):
        pattern = re.compile(rf"(?<!\w){re.escape(keyword)}(?!\w)", re.IGNORECASE)
        for match in pattern.finditer(text):
            entities.append(
                MedicalEntity(
                    label=label,
                    text=match.group(0).strip(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.88,
                    source="keyword",
                )
            )
    return entities


def _extract_section_entities(text: str) -> list[MedicalEntity]:
    entities: list[MedicalEntity] = []
    lines = text.splitlines(keepends=True)
    offset = 0
    current_label: EntityLabel | None = None

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower().rstrip(":")
        label = _label_for_header(lower)
        if label:
            current_label = label
            after_colon = _text_after_colon(stripped)
            if after_colon:
                start = text.find(after_colon, offset)
                entities.append(_entity_from_section(label, after_colon, start))
            offset += len(line)
            continue

        if _is_header(lower):
            current_label = None
            offset += len(line)
            continue

        if current_label:
            item = _extract_line_item(stripped)
            if item:
                start = text.find(item, offset)
                entities.append(_entity_from_section(current_label, item, start))

        offset += len(line)

    return entities


def _label_for_header(header: str) -> EntityLabel | None:
    for header_prefix, label in HEADER_TO_LABEL:
        if header.startswith(header_prefix):
            return label
    return None


def _is_header(text: str) -> bool:
    return any(text.startswith(header) for header in SECTION_HEADERS)


def _text_after_colon(text: str) -> str:
    if ":" not in text:
        return ""
    return _clean_entity_text(text.split(":", 1)[1])


def _extract_line_item(text: str) -> str:
    if not text:
        return ""
    match = LINE_ITEM_PATTERN.match(text)
    candidate = match.group("item") if match else text
    return _clean_entity_text(candidate)


def _clean_entity_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" -:;,.")
    if len(text) < 2:
        return ""
    return text[:120]


def _entity_from_section(label: EntityLabel, entity_text: str, start: int) -> MedicalEntity:
    start = max(start, 0)
    return MedicalEntity(
        label=label,
        text=entity_text,
        start=start,
        end=start + len(entity_text),
        confidence=0.78,
        source="section",
    )


def _extract_medication_doses(text: str) -> list[MedicalEntity]:
    entities: list[MedicalEntity] = []
    for match in DOSE_PATTERN.finditer(text):
        start = _scan_left_for_token(text, match.start())
        if start < match.start():
            entity_text = _clean_entity_text(text[start : match.end()])
            entities.append(
                MedicalEntity(
                    label="OBAT",
                    text=entity_text,
                    start=start,
                    end=match.end(),
                    confidence=0.74,
                    source="regex:dose",
                )
            )
    return entities


def _scan_left_for_token(text: str, index: int) -> int:
    left = text[max(0, index - 40) : index]
    match = re.search(r"([A-Za-z][A-Za-z0-9-]{2,}\s*)$", left)
    if not match:
        return index
    return index - len(match.group(1))


def _dedupe_entities(entities: list[MedicalEntity]) -> list[MedicalEntity]:
    sorted_entities = sorted(
        entities,
        key=lambda entity: (entity.start, -(entity.end - entity.start), -entity.confidence),
    )
    selected: list[MedicalEntity] = []
    seen: set[tuple[EntityLabel, str]] = set()

    for entity in sorted_entities:
        normalized = re.sub(r"\s+", " ", entity.text.lower()).strip()
        key = (entity.label, normalized)
        if key in seen:
            continue
        if any(_overlaps(entity, existing) for existing in selected):
            continue
        seen.add(key)
        selected.append(entity)

    return sorted(selected, key=lambda entity: entity.start)


def _overlaps(left: MedicalEntity, right: MedicalEntity) -> bool:
    return left.start < right.end and right.start < left.end
