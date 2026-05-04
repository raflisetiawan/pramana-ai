from pathlib import Path
import sys


NLP_ENGINE_PATH = Path(__file__).resolve().parents[3] / "services" / "nlp-engine"
sys.path.insert(0, str(NLP_ENGINE_PATH))

from app.pipeline.ner import RuleBasedMedicalNER, extract_entities  # noqa: E402


def test_extract_entities_returns_expected_medical_labels():
    resume_text = """
    Tanggal Masuk: 27/09/2018
    Ringkasan Riwayat Penyakit:
    - Pasien sesak napas selama 3 hari, riwayat hipertensi dan gagal jantung.

    Diagnosis Utama:
    - Congestive Heart Failure
    Diagnosis Sekunder:
    - Pneumonia

    Tindakan/Prosedur:
    1. Echocardiography
    2. Transfusi whole blood

    Terapi Pulang:
    - Furosemide 40 mg
    - Amlodipin
    """

    entities = extract_entities(resume_text)
    labels = {entity["label"] for entity in entities}
    texts = {str(entity["text"]).lower() for entity in entities}

    assert {"DIAGNOSA", "PROSEDUR", "OBAT", "DURASI"}.issubset(labels)
    assert "congestive heart failure" in texts
    assert "echocardiography" in texts
    assert "amlodipin" in texts
    assert "27/09/2018" in texts


def test_rule_based_ner_handles_empty_text():
    assert RuleBasedMedicalNER().extract("") == []


def test_entities_have_valid_offsets():
    resume_text = "Diagnosis Utama: hipertensi\nTerapi Pulang: metformin 500 mg"

    entities = extract_entities(resume_text)

    assert entities
    for entity in entities:
        start = int(entity["start"])
        end = int(entity["end"])
        assert start >= 0
        assert end > start
        assert resume_text[start:end].strip()
