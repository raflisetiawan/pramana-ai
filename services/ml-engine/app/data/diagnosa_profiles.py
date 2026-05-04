"""
Pramana AI — Profil Diagnosa untuk Generasi Data Sintetis

Menyediakan profil medis realistis per kode ICD-10 yang digunakan
sebagai dasar untuk membangkitkan data klaim sintetis.
Setiap profil mencakup:
- Rata-rata dan standar deviasi Length of Stay (LOS)
- Tarif INA-CBGs rata-rata per tipe RS
- Prosedur yang lazim dilakukan
- Diagnosa sekunder yang biasa menyertai
- Severity score (1-5) berdasarkan kompleksitas klinis
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DiagnosaProfile:
    """Profil medis per kode diagnosa ICD-10."""

    kode: str
    nama: str
    chapter: str  # e.g., "I" for cardiovascular

    # LOS parameters (dalam hari)
    los_mean: float
    los_std: float
    los_min: int = 1
    los_max: int = 60

    # Tarif INA-CBGs rata-rata per tipe RS (dalam Rupiah)
    tarif_ina_cbgs_a: float = 0.0  # RS Tipe A
    tarif_ina_cbgs_b: float = 0.0  # RS Tipe B
    tarif_ina_cbgs_c: float = 0.0  # RS Tipe C
    tarif_ina_cbgs_d: float = 0.0  # RS Tipe D

    # Severity score (1-5)
    severity_score: int = 3

    # Prosedur ICD-9 yang lazim
    common_procedures: list[str] = field(default_factory=list)

    # Diagnosa sekunder yang biasa menyertai
    common_secondary: list[str] = field(default_factory=list)

    # Apakah ini termasuk diagnosa "berat" (untuk rule LOS < 1)
    is_severe: bool = False

    # Frekuensi kemunculan (bobot probabilitas)
    frequency_weight: float = 1.0


# ============================================================================
# Profil Diagnosa yang Mencerminkan Klaim BPJS Umum
# ============================================================================

DIAGNOSA_PROFILES: dict[str, DiagnosaProfile] = {
    # --- CARDIOVASCULAR (Chapter I) ---
    "I50.0": DiagnosaProfile(
        kode="I50.0",
        nama="Congestive Heart Failure",
        chapter="I",
        los_mean=7.0,
        los_std=3.0,
        los_min=3,
        los_max=30,
        tarif_ina_cbgs_a=12_000_000,
        tarif_ina_cbgs_b=10_500_000,
        tarif_ina_cbgs_c=8_500_000,
        tarif_ina_cbgs_d=7_000_000,
        severity_score=4,
        common_procedures=["88.72", "99.04", "96.04"],
        common_secondary=["I10", "E11.9", "N18.3", "J18.9", "E78.0"],
        is_severe=True,
        frequency_weight=3.0,
    ),
    "I21.9": DiagnosaProfile(
        kode="I21.9",
        nama="Acute Myocardial Infarction, Unspecified",
        chapter="I",
        los_mean=8.0,
        los_std=3.5,
        los_min=3,
        los_max=30,
        tarif_ina_cbgs_a=18_000_000,
        tarif_ina_cbgs_b=15_500_000,
        tarif_ina_cbgs_c=12_000_000,
        tarif_ina_cbgs_d=10_000_000,
        severity_score=5,
        common_procedures=["36.06", "36.07", "88.72", "99.04"],
        common_secondary=["I10", "I25.1", "E11.9", "E78.0", "I48"],
        is_severe=True,
        frequency_weight=2.0,
    ),
    "I10": DiagnosaProfile(
        kode="I10",
        nama="Essential (Primary) Hypertension",
        chapter="I",
        los_mean=3.0,
        los_std=1.5,
        los_min=1,
        los_max=10,
        tarif_ina_cbgs_a=5_000_000,
        tarif_ina_cbgs_b=4_200_000,
        tarif_ina_cbgs_c=3_500_000,
        tarif_ina_cbgs_d=3_000_000,
        severity_score=2,
        common_procedures=["88.72"],
        common_secondary=["E78.0", "E11.9"],
        is_severe=False,
        frequency_weight=5.0,
    ),
    "I20.0": DiagnosaProfile(
        kode="I20.0",
        nama="Unstable Angina",
        chapter="I",
        los_mean=5.0,
        los_std=2.0,
        los_min=2,
        los_max=15,
        tarif_ina_cbgs_a=10_000_000,
        tarif_ina_cbgs_b=8_500_000,
        tarif_ina_cbgs_c=7_000_000,
        tarif_ina_cbgs_d=5_500_000,
        severity_score=4,
        common_procedures=["88.72", "36.06"],
        common_secondary=["I10", "E78.0", "I25.1"],
        is_severe=True,
        frequency_weight=2.0,
    ),
    "I63.9": DiagnosaProfile(
        kode="I63.9",
        nama="Cerebral Infarction, Unspecified",
        chapter="I",
        los_mean=10.0,
        los_std=5.0,
        los_min=3,
        los_max=45,
        tarif_ina_cbgs_a=14_000_000,
        tarif_ina_cbgs_b=11_500_000,
        tarif_ina_cbgs_c=9_500_000,
        tarif_ina_cbgs_d=8_000_000,
        severity_score=5,
        common_procedures=["96.04", "96.71", "99.15"],
        common_secondary=["I10", "E11.9", "I48", "E78.0"],
        is_severe=True,
        frequency_weight=2.5,
    ),

    # --- ENDOCRINE (Chapter E) ---
    "E11.9": DiagnosaProfile(
        kode="E11.9",
        nama="Type 2 Diabetes Mellitus Without Complications",
        chapter="E",
        los_mean=4.0,
        los_std=2.0,
        los_min=1,
        los_max=14,
        tarif_ina_cbgs_a=5_500_000,
        tarif_ina_cbgs_b=4_800_000,
        tarif_ina_cbgs_c=4_000_000,
        tarif_ina_cbgs_d=3_200_000,
        severity_score=2,
        common_procedures=["99.15"],
        common_secondary=["I10", "E78.0", "N18.3"],
        is_severe=False,
        frequency_weight=5.0,
    ),

    # --- RESPIRATORY (Chapter J) ---
    "J18.9": DiagnosaProfile(
        kode="J18.9",
        nama="Pneumonia, Unspecified Organism",
        chapter="J",
        los_mean=6.0,
        los_std=3.0,
        los_min=2,
        los_max=21,
        tarif_ina_cbgs_a=8_000_000,
        tarif_ina_cbgs_b=6_800_000,
        tarif_ina_cbgs_c=5_500_000,
        tarif_ina_cbgs_d=4_500_000,
        severity_score=3,
        common_procedures=["96.04", "99.04", "33.24"],
        common_secondary=["J96.0", "D50.9", "A09"],
        is_severe=False,
        frequency_weight=4.0,
    ),
    "J44.1": DiagnosaProfile(
        kode="J44.1",
        nama="COPD with Acute Exacerbation",
        chapter="J",
        los_mean=6.0,
        los_std=2.5,
        los_min=2,
        los_max=20,
        tarif_ina_cbgs_a=7_500_000,
        tarif_ina_cbgs_b=6_500_000,
        tarif_ina_cbgs_c=5_200_000,
        tarif_ina_cbgs_d=4_200_000,
        severity_score=3,
        common_procedures=["96.04", "96.71"],
        common_secondary=["I10", "J96.0", "I50.0"],
        is_severe=False,
        frequency_weight=3.0,
    ),
    "J96.0": DiagnosaProfile(
        kode="J96.0",
        nama="Acute Respiratory Failure",
        chapter="J",
        los_mean=10.0,
        los_std=5.0,
        los_min=3,
        los_max=45,
        tarif_ina_cbgs_a=16_000_000,
        tarif_ina_cbgs_b=13_500_000,
        tarif_ina_cbgs_c=11_000_000,
        tarif_ina_cbgs_d=9_000_000,
        severity_score=5,
        common_procedures=["96.04", "96.71", "99.04"],
        common_secondary=["J18.9", "J44.1", "I50.0"],
        is_severe=True,
        frequency_weight=1.5,
    ),

    # --- RENAL (Chapter N) ---
    "N18.5": DiagnosaProfile(
        kode="N18.5",
        nama="Chronic Kidney Disease, Stage 5",
        chapter="N",
        los_mean=5.0,
        los_std=2.5,
        los_min=1,
        los_max=21,
        tarif_ina_cbgs_a=9_000_000,
        tarif_ina_cbgs_b=7_500_000,
        tarif_ina_cbgs_c=6_000_000,
        tarif_ina_cbgs_d=5_000_000,
        severity_score=4,
        common_procedures=["39.95", "99.04", "99.15"],
        common_secondary=["I10", "E11.9", "D50.9"],
        is_severe=True,
        frequency_weight=3.0,
    ),
    "N39.0": DiagnosaProfile(
        kode="N39.0",
        nama="Urinary Tract Infection, Site Not Specified",
        chapter="N",
        los_mean=3.0,
        los_std=1.5,
        los_min=1,
        los_max=10,
        tarif_ina_cbgs_a=4_000_000,
        tarif_ina_cbgs_b=3_400_000,
        tarif_ina_cbgs_c=2_800_000,
        tarif_ina_cbgs_d=2_200_000,
        severity_score=1,
        common_procedures=[],
        common_secondary=["E11.9", "N18.3"],
        is_severe=False,
        frequency_weight=3.0,
    ),

    # --- GASTROINTESTINAL (Chapter K) ---
    "K35.9": DiagnosaProfile(
        kode="K35.9",
        nama="Acute Appendicitis, Unspecified",
        chapter="K",
        los_mean=4.0,
        los_std=1.5,
        los_min=2,
        los_max=14,
        tarif_ina_cbgs_a=8_500_000,
        tarif_ina_cbgs_b=7_200_000,
        tarif_ina_cbgs_c=5_800_000,
        tarif_ina_cbgs_d=4_800_000,
        severity_score=3,
        common_procedures=["47.09"],
        common_secondary=["R50.9"],
        is_severe=False,
        frequency_weight=3.0,
    ),
    "K80.2": DiagnosaProfile(
        kode="K80.2",
        nama="Calculus of Gallbladder Without Cholecystitis",
        chapter="K",
        los_mean=4.0,
        los_std=1.5,
        los_min=2,
        los_max=14,
        tarif_ina_cbgs_a=9_000_000,
        tarif_ina_cbgs_b=7_800_000,
        tarif_ina_cbgs_c=6_200_000,
        tarif_ina_cbgs_d=5_000_000,
        severity_score=3,
        common_procedures=["51.23"],
        common_secondary=["K25.9"],
        is_severe=False,
        frequency_weight=2.5,
    ),

    # --- MUSCULOSKELETAL (Chapter M/S) ---
    "S72.0": DiagnosaProfile(
        kode="S72.0",
        nama="Fracture of Neck of Femur",
        chapter="S",
        los_mean=7.0,
        los_std=3.0,
        los_min=3,
        los_max=30,
        tarif_ina_cbgs_a=15_000_000,
        tarif_ina_cbgs_b=13_000_000,
        tarif_ina_cbgs_c=10_500_000,
        tarif_ina_cbgs_d=8_500_000,
        severity_score=3,
        common_procedures=["79.35", "81.54"],
        common_secondary=["D50.9", "M54.5"],
        is_severe=False,
        frequency_weight=2.0,
    ),
    "M54.5": DiagnosaProfile(
        kode="M54.5",
        nama="Low Back Pain",
        chapter="M",
        los_mean=3.0,
        los_std=1.5,
        los_min=1,
        los_max=10,
        tarif_ina_cbgs_a=4_500_000,
        tarif_ina_cbgs_b=3_800_000,
        tarif_ina_cbgs_c=3_000_000,
        tarif_ina_cbgs_d=2_500_000,
        severity_score=1,
        common_procedures=[],
        common_secondary=["M17.9"],
        is_severe=False,
        frequency_weight=4.0,
    ),

    # --- ONCOLOGY (Chapter C) ---
    "C34.9": DiagnosaProfile(
        kode="C34.9",
        nama="Malignant Neoplasm of Bronchus and Lung",
        chapter="C",
        los_mean=8.0,
        los_std=4.0,
        los_min=2,
        los_max=30,
        tarif_ina_cbgs_a=15_000_000,
        tarif_ina_cbgs_b=13_000_000,
        tarif_ina_cbgs_c=10_000_000,
        tarif_ina_cbgs_d=8_000_000,
        severity_score=5,
        common_procedures=["33.24", "96.04"],
        common_secondary=["J18.9", "D50.9", "R04.2"],
        is_severe=True,
        frequency_weight=1.5,
    ),

    # --- INFECTIOUS (Chapter A) ---
    "A09": DiagnosaProfile(
        kode="A09",
        nama="Other and Unspecified Gastroenteritis and Colitis",
        chapter="A",
        los_mean=3.0,
        los_std=1.0,
        los_min=1,
        los_max=7,
        tarif_ina_cbgs_a=3_500_000,
        tarif_ina_cbgs_b=3_000_000,
        tarif_ina_cbgs_c=2_500_000,
        tarif_ina_cbgs_d=2_000_000,
        severity_score=1,
        common_procedures=["99.15"],
        common_secondary=["R50.9"],
        is_severe=False,
        frequency_weight=5.0,
    ),
    "A15.0": DiagnosaProfile(
        kode="A15.0",
        nama="Tuberculosis of Lung, Confirmed by Sputum Microscopy",
        chapter="A",
        los_mean=10.0,
        los_std=5.0,
        los_min=3,
        los_max=30,
        tarif_ina_cbgs_a=7_000_000,
        tarif_ina_cbgs_b=6_000_000,
        tarif_ina_cbgs_c=5_000_000,
        tarif_ina_cbgs_d=4_000_000,
        severity_score=3,
        common_procedures=["33.24"],
        common_secondary=["D50.9", "J18.9", "R04.2"],
        is_severe=False,
        frequency_weight=2.5,
    ),

    # --- NEUROLOGICAL (Chapter G) ---
    "G40.9": DiagnosaProfile(
        kode="G40.9",
        nama="Epilepsy, Unspecified",
        chapter="G",
        los_mean=4.0,
        los_std=2.0,
        los_min=1,
        los_max=14,
        tarif_ina_cbgs_a=6_000_000,
        tarif_ina_cbgs_b=5_000_000,
        tarif_ina_cbgs_c=4_200_000,
        tarif_ina_cbgs_d=3_500_000,
        severity_score=3,
        common_procedures=["96.04"],
        common_secondary=["R50.9"],
        is_severe=False,
        frequency_weight=2.0,
    ),

    # --- OBSTETRIC (Chapter O) ---
    "O82": DiagnosaProfile(
        kode="O82",
        nama="Single Delivery by Caesarean Section",
        chapter="O",
        los_mean=4.0,
        los_std=1.5,
        los_min=3,
        los_max=10,
        tarif_ina_cbgs_a=9_500_000,
        tarif_ina_cbgs_b=8_000_000,
        tarif_ina_cbgs_c=6_500_000,
        tarif_ina_cbgs_d=5_500_000,
        severity_score=2,
        common_procedures=["74.1", "99.04"],
        common_secondary=["D50.9"],
        is_severe=False,
        frequency_weight=3.0,
    ),
}


# ============================================================================
# Mapping ICD-10 Chapter ke Ordinal Encoding
# ============================================================================

ICD_CHAPTER_ENCODING: dict[str, int] = {
    "A": 1,   # Infectious diseases
    "B": 2,   # Other infectious diseases
    "C": 3,   # Neoplasms
    "D": 4,   # Blood diseases
    "E": 5,   # Endocrine
    "F": 6,   # Mental disorders
    "G": 7,   # Nervous system
    "H": 8,   # Eye and ear
    "I": 9,   # Cardiovascular
    "J": 10,  # Respiratory
    "K": 11,  # Digestive
    "L": 12,  # Skin
    "M": 13,  # Musculoskeletal
    "N": 14,  # Genitourinary
    "O": 15,  # Pregnancy
    "P": 16,  # Perinatal
    "Q": 17,  # Congenital
    "R": 18,  # Symptoms
    "S": 19,  # Injury
    "T": 20,  # Injury (continued)
}


# ============================================================================
# Daftar Prosedur ICD-9 yang Tersedia
# ============================================================================

AVAILABLE_PROCEDURES: dict[str, str] = {
    "36.06": "Insertion of Non-Drug-Eluting Coronary Artery Stent",
    "36.07": "Insertion of Drug-Eluting Coronary Artery Stent",
    "39.95": "Hemodialisis",
    "39.99": "Other Operations on Vessels",
    "47.09": "Other Appendectomy",
    "51.23": "Laparoscopic Cholecystectomy",
    "79.35": "Open Reduction of Fracture with Internal Fixation, Femur",
    "81.54": "Total Knee Replacement",
    "88.72": "Diagnostik Ultrasonografi Jantung (Echocardiography)",
    "96.04": "Insertion of Endotracheal Tube",
    "96.71": "Continuous Invasive Mechanical Ventilation < 96 Hours",
    "99.04": "Transfusi Whole Blood",
    "99.15": "Parenteral Infusion of Concentrated Nutritional Substances",
    "33.24": "Closed Biopsy of Bronchus",
    "74.1": "Low Cervical Caesarean Section",
}


# ============================================================================
# Mapping Diagnosa → Prosedur yang TIDAK LAZIM (untuk anomali detection)
# ============================================================================

# Prosedur yang tidak masuk akal untuk diagnosa tertentu
UNUSUAL_PROCEDURE_MAP: dict[str, list[str]] = {
    # Diagnosa ringan tapi dapat prosedur berat
    "A09": ["36.06", "36.07", "79.35", "81.54", "74.1", "96.71"],
    "M54.5": ["36.06", "36.07", "39.95", "74.1", "96.71", "33.24"],
    "N39.0": ["36.06", "36.07", "79.35", "81.54", "74.1", "96.71"],
    "I10": ["36.06", "36.07", "79.35", "81.54", "74.1", "96.71", "39.95"],
    "E11.9": ["36.06", "36.07", "79.35", "81.54", "74.1", "96.71"],
    "G40.9": ["36.06", "36.07", "79.35", "81.54", "74.1", "39.95"],
    # Diagnosa spesifik tapi prosedur untuk organ lain
    "K35.9": ["36.06", "36.07", "39.95", "79.35", "81.54", "74.1"],
    "K80.2": ["36.06", "36.07", "39.95", "79.35", "81.54", "74.1"],
    "O82": ["36.06", "36.07", "39.95", "79.35", "81.54", "47.09"],
    "S72.0": ["36.06", "36.07", "39.95", "51.23", "74.1", "47.09"],
}


# ============================================================================
# Data Rumah Sakit Sintetis (diperluas dari faskes.json)
# ============================================================================

HOSPITAL_PROFILES: list[dict] = [
    # Tipe A
    {"kode_rs": "RS-A-001", "nama_rs": "RSUD Dr. Soetomo", "tipe_rs": "A", "provinsi": "Jawa Timur", "kabupaten": "Kota Surabaya"},
    {"kode_rs": "RS-A-002", "nama_rs": "RSUP Dr. Sardjito", "tipe_rs": "A", "provinsi": "DI Yogyakarta", "kabupaten": "Kota Yogyakarta"},
    # Tipe B
    {"kode_rs": "RS-B-001", "nama_rs": "RS Dr. Saiful Anwar", "tipe_rs": "B", "provinsi": "Jawa Timur", "kabupaten": "Kota Malang"},
    {"kode_rs": "RS-B-002", "nama_rs": "RSU Haji Surabaya", "tipe_rs": "B", "provinsi": "Jawa Timur", "kabupaten": "Kota Surabaya"},
    {"kode_rs": "RS-B-003", "nama_rs": "RSUD Kanjuruhan", "tipe_rs": "B", "provinsi": "Jawa Timur", "kabupaten": "Kab. Malang"},
    {"kode_rs": "RS-B-004", "nama_rs": "RSUD Dr. Moewardi", "tipe_rs": "B", "provinsi": "Jawa Tengah", "kabupaten": "Kota Surakarta"},
    {"kode_rs": "RS-B-005", "nama_rs": "RSUD Margono Soekarjo", "tipe_rs": "B", "provinsi": "Jawa Tengah", "kabupaten": "Kab. Banyumas"},
    # Tipe C
    {"kode_rs": "RS-C-001", "nama_rs": "RSU Aminah", "tipe_rs": "C", "provinsi": "Jawa Timur", "kabupaten": "Kab. Blitar"},
    {"kode_rs": "RS-C-002", "nama_rs": "RSU Muhammadiyah Lamongan", "tipe_rs": "C", "provinsi": "Jawa Timur", "kabupaten": "Kab. Lamongan"},
    {"kode_rs": "RS-C-003", "nama_rs": "RSU Permata Bunda", "tipe_rs": "C", "provinsi": "Jawa Tengah", "kabupaten": "Kab. Purwokerto"},
    # Tipe D
    {"kode_rs": "RS-D-001", "nama_rs": "RSU Bhakti Husada", "tipe_rs": "D", "provinsi": "Jawa Timur", "kabupaten": "Kab. Pacitan"},
    {"kode_rs": "RS-D-002", "nama_rs": "RSU Aisyiyah Ponorogo", "tipe_rs": "D", "provinsi": "Jawa Timur", "kabupaten": "Kab. Ponorogo"},
]


# Regional cost index — multiplier biaya berdasarkan provinsi
REGIONAL_COST_INDEX: dict[str, float] = {
    "DKI Jakarta": 1.20,
    "Jawa Barat": 1.05,
    "Jawa Tengah": 0.95,
    "DI Yogyakarta": 0.93,
    "Jawa Timur": 1.00,
    "Bali": 1.08,
    "Sumatera Utara": 1.10,
    "Sumatera Barat": 1.05,
    "Kalimantan Timur": 1.15,
    "Sulawesi Selatan": 1.05,
}
