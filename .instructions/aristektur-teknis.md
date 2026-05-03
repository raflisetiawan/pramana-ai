# Arsitektur Solusi & Pendekatan Teknis

## Nama Solusi: Smart-Claim Co-Pilot

Smart-Claim Co-Pilot adalah sistem berbasis AI yang berperan sebagai *"co-pilot"* bagi manusia — bukan pengganti verifikator, melainkan asisten cerdas yang secara dramatis meningkatkan kecepatan dan akurasi mereka. Sistem ini beroperasi di dua sisi secara bersamaan: di sisi Rumah Sakit (hulu) dan di sisi BPJS (hilir).

---

## Alur Sistem End-to-End

Berikut adalah gambaran alur kerja sistem dari hulu ke hilir:

```
[Hulu - RS]                [Transmisi]           [Hilir - BPJS]
     │                          │                      │
     ▼                          ▼                      ▼
AI Pindai RME Harian  →  Kirim via EClaim   →  Risk Scoring Instan
Saran Koding Otomatis      Gateway Harian        per Dokumen Klaim
Validasi Kelengkapan    (tanpa cutoff bulanan)        │
     │                                               ▼
     └──────────────────────────────────► Dashboard Triage
                                         Hijau (Low Risk) → Proses Cepat
                                         Merah (High Risk) → Audit Mendalam
```

### Penjelasan Setiap Tahap

**Tahap 1 — Hulu (Sisi Rumah Sakit)**

AI memindai Rekam Medis Elektronik (RME) secara harian, bukan menunggu akhir bulan. Di tahap ini, AI melakukan tiga fungsi:
- Memberikan **saran koding** ICD-10 dan ICD-9 berdasarkan teks resume medis
- Memberikan **peringatan dini** jika terdapat ketidaksesuaian antara diagnosa dan prosedur
- Memvalidasi **kelengkapan administratif** berkas secara otomatis sebelum pengiriman

Manfaatnya: RS dapat memperbaiki kesalahan *sebelum* klaim dikirim, sehingga angka *pending claim* turun signifikan.

**Tahap 2 — Transmisi Data**

Klaim dikirimkan melalui **EClaim Gateway** secara harian. Ini adalah perubahan paradigma dari sistem *batch* bulanan yang selama ini menjadi salah satu penyebab penumpukan verifikasi di akhir periode.

**Tahap 3 — Hilir (Sisi BPJS)**

Setiap klaim yang masuk langsung mendapat **Risk Score** dari model AI secara instan. Tidak ada antrian menunggu giliran diverifikasi manual satu per satu.

**Tahap 4 — Dashboard Triage**

Verifikator BPJS melihat dashboard yang sudah mengelompokkan klaim:
- **Klaim Hijau (Low Risk):** Dapat diproses dan disetujui dalam hitungan menit dengan validasi minimal
- **Klaim Merah (High Risk):** Memerlukan audit mendalam oleh verifikator berpengalaman

---

## Tiga Pilar Teknologi AI

### Pilar 1: Generative AI (NLP/LLM) — Ekstraksi Koding Otomatis

**Masalah yang diselesaikan:** Resume medis ditulis dalam bahasa alami (naratif), sementara sistem klaim membutuhkan kode numerik yang sangat spesifik (ICD-10/ICD-9). Proses konversi manual ini membutuhkan keahlian khusus dan rawan kesalahan.

**Cara kerja:**

```
Resume Medis (Teks)
"Pasien datang dengan keluhan sesak napas progresif selama 3 hari.
 Pemeriksaan fisik menunjukkan ronkhi basal bilateral. Didiagnosa
 Congestive Heart Failure (CHF) eksaserbasi akut..."
        │
        ▼ [LLM / NLP Pipeline]
        │
Koding Terstruktur:
- Diagnosa Utama: I50.0 (Congestive Heart Failure)
- Diagnosa Sekunder: J18.9 (Pneumonia, tidak spesifik)  ← flagged for review
- Prosedur: 99.04 (Transfusi Whole Blood)
- Skor Keyakinan: 92% untuk diagnosa utama, 67% untuk sekunder
```

**Komponen teknis:**
- Model bahasa yang di-*fine-tune* dengan korpus dokumen medis Indonesia
- Sistem *confidence scoring* — kode dengan skor rendah otomatis di-*flag* untuk direview manusia
- Mapping ke tarif INA-CBGs yang berlaku

---

### Pilar 2: Supervised Machine Learning — Deteksi Anomali & Upcoding

**Masalah yang diselesaikan:** Mendeteksi klaim yang memiliki pola tidak wajar secara statistik, bahkan jika secara dokumen terlihat lengkap dan benar.

**Cara kerja:**

Model dilatih menggunakan data historis klaim dengan label "wajar" / "anomali". Variabel yang digunakan sebagai fitur input:

| Kelompok Variabel | Contoh Fitur |
| :--- | :--- |
| **Biaya** | Total tagihan, biaya per hari, biaya per komponen (obat, tindakan, akomodasi) |
| **Klinis** | Diagnosa utama + sekunder, prosedur, *Length of Stay* (LOS) |
| **Geografis** | Lokasi RS, tipe RS (A/B/C/D), kapasitas |
| **Temporal** | Bulan pengajuan, pola pengajuan historis RS tersebut |
| **Komparasi** | Perbandingan biaya dengan RS setipe di wilayah yang sama untuk diagnosa yang sama |

**Algoritma yang digunakan:**
- **Random Forest:** Robust terhadap data tidak seimbang (*imbalanced dataset*), mudah diinterpretasi via *feature importance*
- **XGBoost:** Performa lebih tinggi, terutama untuk menangkap interaksi antar-variabel yang kompleks
- **Ensemble:** Kombinasi keduanya untuk hasil prediksi yang lebih stabil

**Output model:** Risk Score 0–100 untuk setiap berkas klaim, beserta penjelasan variabel mana yang paling berkontribusi terhadap skor tersebut (menggunakan SHAP values).

---

### Pilar 3: Graph Neural Networks (GNN) — Deteksi Fraud Kolusif

**Masalah yang diselesaikan:** Kecurangan yang melibatkan banyak pihak (*fraud rings*) tidak dapat terdeteksi dengan menganalisis setiap klaim secara terpisah. Kuncinya adalah mendeteksi pola tidak wajar dalam *relasi antar-transaksi*.

**Cara kerja:**

Data klaim dimodelkan sebagai *graph* (jaringan):
- **Node (Simpul):** RS, Dokter, Pasien, Diagnosis, Prosedur
- **Edge (Sisi):** Relasi antar-entitas (dokter X melayani pasien Y dengan diagnosa Z di RS A)

GNN mendeteksi kluster anomali dalam jaringan ini — misalnya, satu dokter yang menggunakan kode diagnosa yang sama persis untuk ratusan pasien yang berbeda dalam periode singkat, atau jaringan RS berbeda yang mengajukan klaim dengan pola biaya yang sangat mirip.

---

## Prinsip Arsitektur: Human-in-the-Loop

Sistem ini **tidak pernah** menolak atau menyetujui klaim secara otomatis. Semua output AI bersifat rekomendasi dan membutuhkan konfirmasi manusia. Ini bukan kelemahan — ini adalah desain yang disengaja untuk:

1. Memenuhi aspek hukum: keputusan yang berdampak finansial pada RS harus dapat dipertanggungjawabkan oleh manusia yang bertanggung jawab
2. Menghindari dampak kesalahan *false positive* yang merugikan RS yang jujur
3. Membangun kepercayaan secara bertahap dari para pengguna