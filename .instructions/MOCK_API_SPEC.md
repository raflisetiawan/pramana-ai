# MOCK_API_SPEC.md — Spesifikasi Mock API VClaim 2.0

> Mock server ini mensimulasikan perilaku **VClaim Versi 2.0 BPJS Kesehatan**  
> untuk keperluan development dan testing tanpa menggunakan data/server produksi.  
> Semua data yang dikembalikan adalah **data sintetis fiktif**.

---

## 1. Overview

### Tujuan Mock Server
- Memungkinkan development berlangsung **tanpa akses ke environment BPJS**
- Mensimulasikan **semua skenario UAT** sesuai dokumen checklist resmi VClaim 2.0
- Menyediakan data referensi yang konsisten (diagnosa, dokter, poli, faskes)
- Dapat diatur untuk **mensimulasikan error** (untuk testing error handling)

### Base URL
```
Development: http://localhost:8001/vclaim/v2
Docker:      http://mock-vclaim:8001/vclaim/v2
```

### Endpoint Docs
```
Swagger UI:  http://localhost:8001/docs
ReDoc:       http://localhost:8001/redoc
```

---

## 2. Mekanisme Autentikasi

Setiap request ke VClaim 2.0 harus menyertakan tiga header berikut.  
Mock server akan **memvalidasi** header ini (bukan skip), agar SIMRS terbiasa mengirim header yang benar.

### Headers yang Wajib Ada
```
X-cons-id:    {VCLAIM_CONS_ID dari .env}
X-timestamp:  {Unix timestamp saat ini, format: YYYY-MM-DD HH:MM:SS}
X-signature:  {HMAC-SHA256 signature}
```

### Cara Membuat Signature
```python
import hmac
import hashlib
import base64
from datetime import datetime

def generate_signature(cons_id: str, secret_key: str) -> tuple[str, str]:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{cons_id}&{timestamp}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode("utf-8")
    return timestamp, signature_b64

# Contoh penggunaan:
timestamp, signature = generate_signature(
    cons_id="pramana_dev_cons_id",
    secret_key="pramana_dev_secret_key_32chars_min"
)

headers = {
    "X-cons-id": "pramana_dev_cons_id",
    "X-timestamp": timestamp,
    "X-signature": signature,
    "Content-Type": "application/json"
}
```

### Response jika Auth Gagal
```json
HTTP 401
{
  "metaData": {
    "code": "401",
    "message": "Unauthorized - Invalid signature"
  }
}
```

---

## 3. Format Response Standar

Semua response mengikuti format envelope berikut:

```json
{
  "metaData": {
    "code": "200",
    "message": "OK"
  },
  "response": { ... }
}
```

### Kode Status yang Digunakan
| Code | Arti |
|---|---|
| `200` | Sukses |
| `201` | Data tidak ditemukan (bukan error, tapi kosong) |
| `400` | Request tidak valid / validasi gagal |
| `401` | Auth gagal |
| `500` | Internal server error (simulasi) |

---

## 4. Endpoint: Pencarian Peserta

### 4.1 Cari Peserta by Nomor Kartu

```
GET /vclaim/v2/Peserta/nokartu/{noKartu}/tglSEP/{tglSEP}
```

**Path Parameters:**
| Parameter | Format | Contoh |
|---|---|---|
| `noKartu` | 13 digit numerik | `0001234567890` |
| `tglSEP` | YYYY-MM-DD | `2024-01-15` |

**Response Sukses (Peserta Aktif):**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "peserta": {
      "noKartu": "0001234567890",
      "nik": "3578010101900001",
      "nama": "BUDI SANTOSO",
      "pisa": "L",
      "tglLahir": "1990-01-01",
      "tglMulaiAktif": "2020-01-01",
      "tglAkhirBerlaku": "2024-12-31",
      "kdProvUmum": "35",
      "nmProvUmum": "Jawa Timur",
      "kdKabKotaUmum": "3578",
      "nmKabKotaUmum": "Kota Surabaya",
      "kdKecUmum": "357801",
      "nmKecUmum": "Tegalsari",
      "alamat": "Jl. Pemuda No. 10, Surabaya",
      "kdRtRw": "001/002",
      "kdKelurahan": "3578010001",
      "nmKelurahan": "Tegalsari",
      "kdPropinsi": "35",
      "nmPropinsi": "Jawa Timur",
      "kdKabKota": "3578",
      "nmKabKota": "Kota Surabaya",
      "kdKecamatan": "357801",
      "nmKecamatan": "Tegalsari",
      "jenisPeserta": {
        "kode": "1",
        "nama": "PBPU"
      },
      "hakKelas": {
        "kode": "2",
        "keterangan": "KELAS II"
      },
      "pjPeserta": {
        "kodePj": "07",
        "namaPj": "Peserta Mandiri"
      },
      "aktif": true,
      "statusPeserta": {
        "kode": "1",
        "keterangan": "AKTIF"
      },
      "noMR": null,
      "misteriumPesertaList": []
    }
  }
}
```

**Response Peserta Non-Aktif:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "peserta": {
      "noKartu": "0001234567891",
      "nama": "SITI RAHAYU",
      "aktif": false,
      "statusPeserta": {
        "kode": "3",
        "keterangan": "NON AKTIF - Premi Tunggak"
      }
    }
  }
}
```

**Response Nomor Kartu Tidak Ditemukan:**
```json
{
  "metaData": { "code": "201", "message": "Peserta tidak ditemukan" },
  "response": null
}
```

### Skenario Test yang Harus Bisa Disimulasikan
| Nomor Kartu | Skenario |
|---|---|
| `0001234567890` | Peserta aktif, kelas II |
| `0001234567891` | Peserta non-aktif (premi) |
| `0001234567892` | Peserta aktif, kelas I |
| `0001234567893` | Peserta aktif, kelas III |
| `9999999999999` | Nomor kartu tidak ditemukan |

---

## 5. Endpoint: Referensi

### 5.1 Referensi Diagnosa (ICD-10)
```
GET /vclaim/v2/referensi/diagnosa/{keyword}
```

**Contoh Request:** `/vclaim/v2/referensi/diagnosa/jantung`

**Response:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "diagnosa": [
      { "kode": "I50.0", "nama": "Congestive Heart Failure" },
      { "kode": "I20.0", "nama": "Unstable Angina" },
      { "kode": "I21.9", "nama": "Acute Myocardial Infarction, Unspecified" }
    ]
  }
}
```

### 5.2 Referensi Dokter
```
GET /vclaim/v2/referensi/dokter/{keyword}
GET /vclaim/v2/referensi/dokter/pelayanan/{kdPoli}/tglPelayanan/{tgl}/Spesialis/{kdSpesialis}
```

**Response:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "dokter": [
      {
        "kodeDokter": "DR001",
        "namaDokter": "dr. Ahmad Fauzi, Sp.JP",
        "spesialistik": "Jantung dan Pembuluh Darah"
      }
    ]
  }
}
```

### 5.3 Referensi Poli
```
GET /vclaim/v2/referensi/poli/{keyword}
```

**Response:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "poli": [
      { "kode": "INT", "nama": "Poli Interne" },
      { "kode": "JPD", "nama": "Poli Jantung dan Pembuluh Darah" },
      { "kode": "SAR", "nama": "Poli Saraf" },
      { "kode": "ORT", "nama": "Poli Ortopedi" },
      { "kode": "MAT", "nama": "Poli Mata" },
      { "kode": "THT", "nama": "Poli THT" },
      { "kode": "KUL", "nama": "Poli Kulit dan Kelamin" },
      { "kode": "PAR", "nama": "Poli Paru" },
      { "kode": "GIN", "nama": "Poli Ginekologi" },
      { "kode": "URO", "nama": "Poli Urologi" },
      { "kode": "HDL", "nama": "Poli Hemodialisa" },
      { "kode": "IRM", "nama": "Poli Rehabilitasi Medik" },
      { "kode": "GIG", "nama": "Poli Gigi dan Mulut" },
      { "kode": "ANK", "nama": "Poli Anak" },
      { "kode": "IGD", "nama": "Instalasi Gawat Darurat" }
    ]
  }
}
```

### 5.4 Referensi Prosedur (ICD-9-CM)
```
GET /vclaim/v2/referensi/procedure/{keyword}
```

**Response:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "procedure": [
      { "kode": "39.95", "nama": "Hemodialisis" },
      { "kode": "99.04", "nama": "Transfusi Whole Blood" },
      { "kode": "88.72", "nama": "Diagnostik Ultrasonografi Jantung" }
    ]
  }
}
```

### 5.5 Referensi Fasilitas Kesehatan
```
GET /vclaim/v2/referensi/faskes/{tipe}/{keyword}
```
Tipe: `1` = Faskes Tingkat I, `2` = Faskes Tingkat II (RS)

---

## 6. Endpoint: SEP (Surat Eligibilitas Peserta)

### 6.1 Insert SEP 2.0
```
POST /vclaim/v2/SEP/2.0/insert
```

**Request Body:**
```json
{
  "noKartu": "0001234567890",
  "tglSep": "2024-01-15",
  "ppkPelayanan": "0101R001",
  "jnsPelayanan": "2",
  "noMrLocal": "MR-2024-001234",
  "noTelp": "08123456789",
  "klsRawat": {
    "klsRawatHak": "2",
    "klsRawatNaik": "",
    "pembiayaan": "",
    "penanggungJawab": ""
  },
  "catatan": "",
  "diagAwal": "I50.0",
  "poli": "JPD",
  "poli_eks": "",
  "kodeDPJP": "DR001",
  "noRujukan": "150100100120240115000001",
  "tujuanKunj": "0",
  "flagProcedure": "0",
  "flagKonsul": "0",
  "assesmentPel": "0",
  "skdp": {
    "noSurat": "",
    "kodeDPJP": ""
  },
  "kdSatuSehat": "",
  "user": "admin_rs"
}
```

**Field Penting:**
| Field | Nilai | Keterangan |
|---|---|---|
| `jnsPelayanan` | `1` = Rawat Inap, `2` = Rawat Jalan | |
| `klsRawat.klsRawatHak` | `1`, `2`, `3` | Kelas hak peserta |
| `tujuanKunj` | `0` = Kunjungan pertama, `1` = Kontrol, `2` = Prosedur berulang | |
| `assesmentPel` | `0` = Bukan KLL, `1` = KLL bukan JR, `2` = KLL JR | |

**Response Sukses:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "sep": {
      "noSep": "0101R00120240115000001",
      "noKartu": "0001234567890",
      "nama": "BUDI SANTOSO",
      "tglSep": "2024-01-15",
      "jnsPelayanan": "2",
      "poli": "JPD",
      "namaPoli": "Poli Jantung dan Pembuluh Darah",
      "klsRawat": "2",
      "namaDPJP": "dr. Ahmad Fauzi, Sp.JP",
      "noRujukan": "150100100120240115000001",
      "kdDiag": "I50.0",
      "nmDiag": "Congestive Heart Failure",
      "statusPeserta": "1",
      "pjPeserta": "Peserta Mandiri",
      "hakKelas": "KELAS II",
      "noMrLocal": "MR-2024-001234",
      "tglTerbit": "2024-01-15 09:30:00"
    }
  }
}
```

**Response Validasi Gagal (Contoh):**
```json
{
  "metaData": {
    "code": "400",
    "message": "DPJP tidak boleh kosong"
  },
  "response": null
}
```

### Skenario Error yang Harus Disimulasikan (sesuai checklist UAT)
| Kondisi | Error Message |
|---|---|
| `kodeDPJP` kosong | "DPJP tidak boleh kosong" |
| `tglSep` lebih besar dari hari ini | "Tanggal SEP tidak boleh lebih dari tanggal pembuatan SEP" |
| `tglSep` kurang dari tanggal TMT peserta | "Tanggal SEP kurang dari tanggal TMT peserta" |
| Tanggal rujukan lebih baru dari tgl SEP | "Tanggal rujukan lebih dari tanggal SEP" |
| Pasien sudah ada SEP RITL yang belum pulang | "Peserta masih dalam perawatan rawat inap" |
| Backdate lebih dari 1 hari (RJTL) | "SEP backdate harus mengajukan persetujuan backdate" |
| `klsRawatNaik` lebih dari 1 kelas di atas hak | "Naik kelas maksimal 1 tingkat di atas hak kelas peserta" |

### 6.2 Update SEP 2.0
```
PUT /vclaim/v2/SEP/2.0/update
```

**Request Body:**
```json
{
  "noSep": "0101R00120240115000001",
  "klsRawat": "2",
  "noMrLocal": "MR-2024-001234",
  "noTelp": "08123456789",
  "diagAwal": "I50.0",
  "poli": "JPD",
  "kodeDPJP": "DR001",
  "catatan": "Update diagnosa",
  "user": "admin_rs"
}
```

### 6.3 Delete SEP 2.0
```
DELETE /vclaim/v2/SEP/2.0/delete
```

**Request Body:**
```json
{
  "noSep": "0101R00120240115000001",
  "user": "admin_rs"
}
```

### 6.4 Get SEP by Nomor SEP
```
GET /vclaim/v2/SEP/{noSep}
```

---

## 7. Endpoint: Rujukan

### 7.1 Get Rujukan by Nomor Kartu
```
GET /vclaim/v2/Rujukan/Peserta/{noKartu}
```

**Response:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "rujukan": {
      "noKunjungan": "150100100120240115000001",
      "tglKunjungan": "2024-01-15",
      "ppkAsal": {
        "kode": "150100100",
        "nama": "Puskesmas Tegalsari"
      },
      "ppkTujuan": {
        "kode": "0101R001",
        "nama": "RSUD Dr. Soetomo"
      },
      "diagnosa": {
        "kode": "I50.0",
        "nama": "Congestive Heart Failure"
      },
      "poliRujukan": {
        "kode": "JPD",
        "nama": "Jantung dan Pembuluh Darah"
      },
      "tglAkhirBerlaku": "2024-04-15",
      "jnsPelayanan": "2",
      "masaBerlaku": 90
    }
  }
}
```

### 7.2 Insert Rujukan Antar RS
```
POST /vclaim/v2/Rujukan/2.0/insert
```

**Request Body:**
```json
{
  "noSep": "0101R00120240115000001",
  "tglRujukan": "2024-01-15",
  "ppkRujukan": "0201R001",
  "diagRujukan": "I50.0",
  "poliRujukan": "JPD",
  "tipeRujukan": "1",
  "catatan": "Perlu penanganan lebih lanjut",
  "user": "admin_rs"
}
```

---

## 8. Endpoint: Rencana Kontrol (Surat Kontrol & SPRI)

### 8.1 Insert Rencana Kontrol
```
POST /vclaim/v2/RencanaKontrol/insert
```

**Request Body:**
```json
{
  "noSep": "0101R00120240115000001",
  "tglRencanaKontrol": "2024-02-15",
  "poliKontrol": "JPD",
  "kodeDokter": "DR001",
  "user": "admin_rs"
}
```

**Response Sukses:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "noSuratKontrol": "SRT-CTRL-20240115-0001",
    "tglRencanaKontrol": "2024-02-15",
    "poliKontrol": "JPD",
    "namaPoli": "Poli Jantung dan Pembuluh Darah",
    "namaDokter": "dr. Ahmad Fauzi, Sp.JP"
  }
}
```

### 8.2 Insert SPRI (Surat Perintah Rawat Inap)
```
POST /vclaim/v2/RencanaKontrol/InsertSPRI
```

**Request Body:**
```json
{
  "noKartu": "0001234567890",
  "tglRencanaRI": "2024-01-20",
  "poliRI": "JPD",
  "kodeDokter": "DR001",
  "user": "admin_rs"
}
```

---

## 9. Endpoint: Monitoring Kunjungan

### 9.1 Monitoring Klaim
```
GET /vclaim/v2/Monitoring/Kunjungan/Tanggal/{tgl}/JnsPelayanan/{jnsPel}
```

**Path Parameters:**
- `tgl`: YYYY-MM-DD
- `jnsPel`: `1` = Rawat Inap, `2` = Rawat Jalan

**Response:**
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": {
    "list": [
      {
        "noSep": "0101R00120240115000001",
        "noKartu": "0001234567890",
        "nama": "BUDI SANTOSO",
        "tglSep": "2024-01-15",
        "poli": "JPD",
        "dokter": "dr. Ahmad Fauzi, Sp.JP",
        "diagAwal": "I50.0",
        "statusKlaim": "1"
      }
    ]
  }
}
```

---

## 10. Data Dummy untuk Development

### Seed Data Peserta (simpan di `mock-vclaim/app/data/peserta.json`)
```json
[
  {
    "noKartu": "0001234567890",
    "nik": "3578010101900001",
    "nama": "BUDI SANTOSO",
    "pisa": "L",
    "tglLahir": "1990-01-01",
    "aktif": true,
    "hakKelas": "2",
    "statusPeserta": "AKTIF"
  },
  {
    "noKartu": "0001234567891",
    "nik": "3578010101850001",
    "nama": "SITI RAHAYU",
    "pisa": "P",
    "tglLahir": "1985-03-15",
    "aktif": false,
    "hakKelas": "3",
    "statusPeserta": "NON AKTIF - Premi Tunggak"
  },
  {
    "noKartu": "0001234567892",
    "nik": "3578010101750001",
    "nama": "HENDRA WIJAYA",
    "pisa": "L",
    "tglLahir": "1975-07-20",
    "aktif": true,
    "hakKelas": "1",
    "statusPeserta": "AKTIF"
  },
  {
    "noKartu": "0001234567893",
    "nik": "3578010101950001",
    "nama": "DEWI KUSUMA",
    "pisa": "P",
    "tglLahir": "1995-11-08",
    "aktif": true,
    "hakKelas": "3",
    "statusPeserta": "AKTIF"
  }
]
```

### Data ICD-10 Minimal untuk Development
Simpan di `mock-vclaim/app/data/icd10.json` — minimal 50 kode yang paling umum di klaim BPJS:

```json
[
  { "kode": "I50.0", "nama": "Congestive Heart Failure" },
  { "kode": "I10",   "nama": "Essential (Primary) Hypertension" },
  { "kode": "E11.9", "nama": "Type 2 Diabetes Mellitus Without Complications" },
  { "kode": "J18.9", "nama": "Pneumonia, Unspecified Organism" },
  { "kode": "N18.3", "nama": "Chronic Kidney Disease, Stage 3" },
  { "kode": "N18.4", "nama": "Chronic Kidney Disease, Stage 4" },
  { "kode": "N18.5", "nama": "Chronic Kidney Disease, Stage 5" },
  { "kode": "I21.9", "nama": "Acute Myocardial Infarction, Unspecified" },
  { "kode": "J44.1", "nama": "COPD with Acute Exacerbation" },
  { "kode": "K35.9", "nama": "Acute Appendicitis, Unspecified" },
  { "kode": "S72.0", "nama": "Fracture of Neck of Femur" },
  { "kode": "C34.9", "nama": "Malignant Neoplasm of Bronchus and Lung" },
  { "kode": "G40.9", "nama": "Epilepsy, Unspecified" },
  { "kode": "M54.5", "nama": "Low Back Pain" },
  { "kode": "A09",   "nama": "Other and Unspecified Gastroenteritis and Colitis" }
]
```

---

## 11. Cara Simulasi Error & Edge Cases

Mock server memiliki endpoint khusus untuk mengontrol perilaku simulasi:

### Toggle Error Mode
```
POST /vclaim/v2/_mock/config
```

**Request Body:**
```json
{
  "error_rate": 0.1,
  "response_delay_ms": 500,
  "force_error_on_noka": ["0001234567890"],
  "simulate_timeout": false
}
```

### Reset ke Default
```
POST /vclaim/v2/_mock/reset
```

### Cek Konfigurasi Saat Ini
```
GET /vclaim/v2/_mock/status
```

---

## 12. Checklist Implementasi Mock Server

Sebelum dianggap selesai, mock server harus bisa mensimulasikan semua skenario UAT berikut:

### Peserta
- [ ] 1.1.1 Peserta aktif
- [ ] 1.1.2 Peserta non-aktif
- [ ] 1.1.3 Nomor kartu tidak ditemukan
- [ ] 1.2.1 Pencarian by NIK — ditemukan
- [ ] 1.2.2 Pencarian by NIK — tidak terdaftar

### SEP
- [ ] 3.1 SEP RJTL rujukan online — kunjungan pertama
- [ ] 3.1.1.1 Validasi rujukan > 90 hari
- [ ] 4.1 SEP RJTL rujukan offline
- [ ] 5.1 SEP RITL rawat inap
- [ ] 6.1 SEP KLL (Kecelakaan Lalu Lintas)
- [ ] 7.1–7.9 Semua validasi umum SEP
- [ ] 8.1–8.14 Semua skenario update SEP
- [ ] 9.1–9.4 Semua skenario hapus SEP

### Rujukan
- [ ] 13.1.1 Rujukan penuh
- [ ] 13.1.2 Rujukan parsial
- [ ] 13.1.3 Rujuk balik
- [ ] 13.1.4–13.1.7 Semua validasi rujukan

### Surat Kontrol & SPRI
- [ ] 17.1 Insert rencana kontrol + semua validasi
- [ ] 17.2 Update rencana kontrol
- [ ] 17.3 Delete rencana kontrol
- [ ] 18.1 Insert SPRI + semua validasi

### Perpanjangan Rujukan Khusus
- [ ] 19.1 Perpanjangan rujukan HD
- [ ] 19.1.1–19.1.7 Semua validasi