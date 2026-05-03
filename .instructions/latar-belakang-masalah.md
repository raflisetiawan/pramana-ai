# Latar Belakang Proyek & Pernyataan Masalah

## Tentang Pramana AI

**Pramana** (प्रमाण) adalah kata dalam filosofi Sanskerta yang berarti *"alat pembuktian"*, *"sumber pengetahuan yang benar"*, atau *"validasi"*. Nama ini dipilih secara sengaja untuk mencerminkan inti dari solusi yang dibangun: sebuah sistem yang memberikan dasar pembuktian yang valid dan terpercaya dalam proses verifikasi klaim kesehatan.

- **Nama Produk:** Pramana AI — Smart-Claim Co-Pilot
- **Dikembangkan oleh:** Siena Clinical
- **Domain:** Verifikasi Klaim BPJS Kesehatan
- **Konteks:** Program AI Incubation for Public Sector, bermitra dengan BPJS Kesehatan sebagai *Problem Owner*

---

## Gambaran Sistem Saat Ini

Proses verifikasi klaim BPJS Kesehatan saat ini sepenuhnya atau sebagian besar bersifat manual. Alur yang berlaku adalah sebagai berikut:

1. **Rumah Sakit (FKRTL)** menyiapkan berkas klaim, termasuk resume medis, lembar SEP (Surat Eligibilitas Peserta), dan dokumen pendukung lainnya.
2. **Tim Casemix RS** melakukan pengkodean diagnosa (ICD-10) dan prosedur (ICD-9-CM) secara manual berdasarkan resume medis.
3. Berkas klaim dikirimkan secara *batch* (biasanya bulanan) ke **Kantor Cabang BPJS** melalui sistem *e-Claim*.
4. **Verifikator BPJS** memeriksa setiap berkas secara manual — membandingkan kode, memeriksa kelengkapan dokumen, dan menilai kewajaran biaya.
5. Klaim yang lolos akan dibayarkan. Klaim yang bermasalah dikembalikan (*pending*) ke RS untuk diperbaiki.

---

## Metrik Masalah yang Terukur

Data berikut menggambarkan skala permasalahan yang dihadapi saat ini:

| Metrik | Nilai | Dampak |
| :--- | :--- | :--- |
| **Rata-rata waktu verifikasi** | **14 Hari Kerja** | Siklus pembayaran yang sangat panjang |
| **Persentase klaim tertunda** | **34%** | 1 dari 3 klaim dikembalikan dan harus diproses ulang |
| **Beban waktu per berkas** | **~2 Jam** | Habis hanya untuk pengecekan administrasi dasar |

---

## Akar Masalah (Root Cause Analysis)

Angka-angka di atas bukan sekadar masalah kapasitas SDM, melainkan bersumber dari dua akar masalah mendasar:

### Akar Masalah 1: Kesalahan dalam Validasi Klaim

Pengecekan berkas secara manual sangat rentan terhadap human error. Jenis kesalahan yang paling umum terjadi:

- **Upcoding:** Penggunaan kode diagnosa atau prosedur dengan tarif yang lebih tinggi dari kondisi klinis yang sebenarnya. Ini bisa terjadi secara tidak sengaja karena ambiguitas kode, atau secara disengaja sebagai bentuk kecurangan.
- **Cloning:** Penggunaan berkas klaim yang identik atau hampir identik untuk pasien berbeda, yang mengindikasikan dokumen tidak dibuat berdasarkan kondisi riil setiap pasien.
- **Ketidaklengkapan Dokumen:** Berkas klaim yang dikirimkan tidak memiliki semua dokumen pendukung yang disyaratkan, sehingga harus dikembalikan.
- **Inkonsistensi Koding:** Kode diagnosa di resume medis tidak sesuai dengan kode yang diinput ke sistem *e-Claim*.

### Akar Masalah 2: Krisis Arus Kas Rumah Sakit

Keterlambatan verifikasi dan tingginya angka klaim tertunda secara langsung memicu masalah likuiditas bagi rumah sakit:

- Rumah sakit harus menanggung biaya operasional (gaji, obat, alat habis pakai) di muka, sementara pembayaran dari BPJS tertunda berbulan-bulan.
- Kondisi ini sangat memberatkan RS dengan kapasitas finansial terbatas, terutama RSUD di daerah.
- Rumah sakit terpaksa mengalihkan sumber daya manajemen untuk menangani administrasi klaim, alih-alih fokus pada peningkatan layanan klinis.

---

## Dampak Jika Tidak Ditangani

Tanpa intervensi sistemik, situasi ini akan terus memburuk seiring bertambahnya jumlah peserta JKN (Jaminan Kesehatan Nasional), yang berarti volume klaim yang harus diproses juga meningkat secara linear, sementara kapasitas verifikasi manual tidak dapat ditingkatkan dengan kecepatan yang sama.