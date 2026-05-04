# FRONTEND_DESIGN.md — Panduan Desain UI/UX Pramana AI

> **Proyek:** Pramana AI — Smart-Claim Co-Pilot  
> **Stack:** React 18 + TypeScript · Vite 5 · shadcn/ui · Tailwind CSS · Recharts · TanStack Table  
> **Target Pengguna:** Verifikator BPJS, Admin RS (bukan konsumen umum — ini alat kerja profesional)

---

## 1. Filosofi & Arah Desain

### Konsep Inti: "Clinical Command Center"

Pramana AI bukan aplikasi konsumer. Ini adalah **alat kerja profesional** yang digunakan oleh verifikator yang memproses ratusan klaim per hari, di bawah tekanan waktu dan tanggung jawab hukum yang besar. Desain harus mencerminkan **otoritas, kejelasan, dan kepercayaan** — bukan keindahan demi keindahan.

Arah estetika yang dipilih adalah: **Refined Dark Utility** — antarmuka bertensi tinggi ala command center, presisi seperti software medis, dengan sentuhan kehangatan yang menjaga agar tidak terasa dingin seperti software pemerintah pada umumnya.

### Tiga Kata Kunci Desain

| Kata Kunci | Makna dalam Konteks Pramana |
| :--- | :--- |
| **Trustworthy** | Warna dan layout yang stabil, tidak mencolok. Verifikator harus percaya data yang ditampilkan. |
| **Decisive** | Hirarki visual yang tajam. Satu klaim, satu keputusan. Tidak ada ambiguitas tentang apa yang perlu dilakukan. |
| **Focused** | Minimum dekorasi. Setiap piksel harus mendukung pengambilan keputusan, bukan menghibur. |

### Yang DILARANG dalam Desain Ini

- ❌ Gradient ungu/pink ala startup SaaS generik
- ❌ Rounded corners besar (border-radius > 8px untuk container utama)
- ❌ Font Inter atau Roboto sebagai pilihan utama
- ❌ Card dengan shadow besar dan padding berlebihan
- ❌ Ilustrasi dekoratif atau ikon yang tidak informatif
- ❌ Animasi yang lambat (> 300ms) atau bouncy

---

## 2. Sistem Warna

### Palet Utama

```css
/* Gunakan CSS variables di :root */
:root {
  /* Background — Dark slate dengan nuansa navy */
  --bg-base:        #0D1117;   /* Background aplikasi */
  --bg-surface:     #161B22;   /* Card / panel */
  --bg-elevated:    #1C2128;   /* Dropdown, modal, hover state */
  --bg-overlay:     #21262D;   /* Baris tabel aktif */

  /* Border */
  --border-subtle:  #30363D;   /* Border halus antar elemen */
  --border-default: #444C56;   /* Border yang terlihat */
  --border-strong:  #6E7681;   /* Border emphasis */

  /* Teks */
  --text-primary:   #E6EDF3;   /* Judul, data penting */
  --text-secondary: #8B949E;   /* Label, metadata */
  --text-muted:     #484F58;   /* Placeholder, disabled */
  --text-inverse:   #0D1117;   /* Teks di atas background terang */

  /* Aksen Utama — Teal/Cyan (warna medis, kepercayaan) */
  --accent-primary:   #2F81F7;  /* Tombol utama, link aktif */
  --accent-secondary: #0EA5E9;  /* Hover, secondary action */
  --accent-glow:      rgba(47, 129, 247, 0.15); /* Glow effect subtle */

  /* Risk Levels — Ini adalah warna kritis dalam sistem */
  --risk-low:         #1A7F37;  /* Klaim Hijau — aman */
  --risk-low-bg:      rgba(26, 127, 55, 0.12);
  --risk-low-border:  rgba(26, 127, 55, 0.4);

  --risk-medium:      #9A6700;  /* Klaim Kuning — perlu review */
  --risk-medium-bg:   rgba(154, 103, 0, 0.12);
  --risk-medium-border: rgba(154, 103, 0, 0.4);

  --risk-high:        #B91C1C;  /* Klaim Merah — audit mendalam */
  --risk-high-bg:     rgba(185, 28, 28, 0.12);
  --risk-high-border: rgba(185, 28, 28, 0.4);

  /* Warna Status Klaim */
  --status-pending:   #6366F1;  /* Dalam proses */
  --status-approved:  #22C55E;  /* Disetujui */
  --status-returned:  #F97316;  /* Dikembalikan ke RS */
  --status-escalated: #EC4899;  /* Dieskalasi */
}
```

### Prinsip Penggunaan Warna

1. **Background bukan putih.** Seluruh aplikasi menggunakan dark theme. Mata verifikator yang bekerja 8+ jam sehari akan lebih nyaman.
2. **Warna risk adalah bahasa.** Hijau/Kuning/Merah adalah satu-satunya warna yang "berteriak" — semua elemen lain harus lebih tenang agar warna risk tetap bermakna.
3. **Aksen biru hanya untuk aksi.** Warna `--accent-primary` hanya digunakan untuk tombol CTA, link aktif, dan elemen interaktif. Bukan untuk dekorasi.

---

## 3. Tipografi

### Font Stack

```css
/* Import di index.css atau via Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&family=Lora:wght@600&display=swap');

:root {
  /* Font data & angka — Mono untuk nomor SEP, kode ICD, nilai numerik */
  --font-mono: 'IBM Plex Mono', 'Cascadia Code', monospace;
  
  /* Font body & label — Sans-serif yang bersih tapi berkarakter */
  --font-sans: 'DM Sans', 'Helvetica Neue', sans-serif;
  
  /* Font untuk judul halaman & hero text — sedikit editorial */
  --font-display: 'Lora', Georgia, serif;
}
```

### Hierarki Teks

| Token | Font | Size | Weight | Penggunaan |
| :--- | :--- | :--- | :--- | :--- |
| `text-display` | Lora | 28px | 600 | Judul halaman utama |
| `text-heading` | DM Sans | 20px | 600 | Judul section, panel |
| `text-subheading` | DM Sans | 14px | 600 | Label kolom tabel, sub-judul |
| `text-body` | DM Sans | 14px | 400 | Konten paragraf |
| `text-small` | DM Sans | 12px | 400 | Metadata, timestamp |
| `text-code` | IBM Plex Mono | 13px | 400 | Kode ICD, No. SEP, nilai numerik |
| `text-data` | IBM Plex Mono | 22px | 500 | Angka statistik di header dashboard |

### Aturan Tipografi Kritis

- **Semua kode ICD-10, ICD-9, dan No. SEP wajib menggunakan `font-mono`.** Ini bukan pilihan estetika — ini fungsional. Verifikator harus bisa membedakan `I10` (huruf I) dari `l10` (huruf l) seketika.
- **Angka nominal (Rp) gunakan `font-mono`** dengan format `Rp 12.500.000`, bukan `Rp12500000`.
- **Jangan gunakan teks caps untuk label penting.** Verifikasi klinis tidak boleh terasa seperti shouting.

---

## 4. Sistem Spacing & Layout

### Grid Layout Aplikasi

```
┌─────────────────────────────────────────────────────────────┐
│  SIDEBAR (240px, fixed)  │  MAIN CONTENT (flex-grow)        │
│                          │                                   │
│  Logo (48px h)           │  TOP BAR (56px, sticky)          │
│  ─────────               │  ─────────────────────────────   │
│  Nav Items               │                                   │
│                          │  PAGE CONTENT (scrollable)        │
│                          │                                   │
│                          │                                   │
└─────────────────────────────────────────────────────────────┘
```

### Spacing Scale (gunakan Tailwind)

Gunakan spacing kelipatan 4px. Prioritaskan:

| Konteks | Nilai |
| :--- | :--- |
| Padding dalam cell tabel | `px-4 py-3` (16px / 12px) |
| Padding dalam card / panel | `p-5` atau `p-6` |
| Gap antar section | `gap-6` atau `gap-8` |
| Margin antar elemen dalam panel | `space-y-3` atau `space-y-4` |

### Border Radius

- **Container besar** (card, panel): `rounded-md` (6px)
- **Badge, chip**: `rounded` (4px)
- **Tombol**: `rounded-md` (6px)
- **Tombol kecil / icon button**: `rounded` (4px)
- **Input field**: `rounded-md` (6px)

> **Tidak ada `rounded-xl` atau `rounded-2xl`** di seluruh aplikasi. Sudut tajam = keputusan tegas.

---

## 5. Komponen Utama

### 5.1 `RiskBadge` — Komponen Terpenting

Badge ini adalah jantung dari seluruh antarmuka. Harus bisa dibaca dalam sepersekian detik.

```tsx
// Props
interface RiskBadgeProps {
  score: number;       // 0–100
  level: 'low' | 'medium' | 'high';
  showScore?: boolean; // default: true
  size?: 'sm' | 'md' | 'lg'; // default: 'md'
}
```

**Spesifikasi Visual:**

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  ● LOW RISK    23   │    │  ● MED RISK    58   │    │  ● HIGH RISK   84   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
  bg: risk-low-bg             bg: risk-medium-bg          bg: risk-high-bg
  border: risk-low-border     border: risk-medium-border  border: risk-high-border
  text: risk-low              text: risk-medium           text: risk-high
  dot: solid circle           dot: solid circle           dot: pulse animation
```

- **Klaim Merah (High Risk)**: dot menggunakan `animate-pulse` untuk menarik perhatian
- **Score ditampilkan dengan `font-mono`**
- **Teks label menggunakan `font-sans` uppercase tracking-wider**

```tsx
// Contoh implementasi Tailwind
const riskConfig = {
  low:    { label: 'LOW RISK',  bg: 'bg-[var(--risk-low-bg)]',    text: 'text-[var(--risk-low)]',    border: 'border-[var(--risk-low-border)]' },
  medium: { label: 'MED RISK',  bg: 'bg-[var(--risk-medium-bg)]', text: 'text-[var(--risk-medium)]', border: 'border-[var(--risk-medium-border)]' },
  high:   { label: 'HIGH RISK', bg: 'bg-[var(--risk-high-bg)]',   text: 'text-[var(--risk-high)]',   border: 'border-[var(--risk-high-border)]' },
};
```

---

### 5.2 `ClaimTable` — Tabel Triage

Tabel utama yang menampilkan daftar klaim. Verifikator menghabiskan 70% waktu di sini.

**Kolom & Urutan:**

| # | Kolom | Lebar | Catatan |
| :--- | :--- | :--- | :--- |
| 1 | Risk Badge | 140px | **Kolom pertama** — keputusan triage dimulai dari sini |
| 2 | No. SEP | 160px | `font-mono`, klik untuk copy |
| 3 | Nama Pasien | 160px | Disamarkan: `Budi S***` (3 karakter pertama + asterisk) |
| 4 | RS Pengaju | 200px | Nama RS disingkat jika > 25 char |
| 5 | Diagnosa Utama | 180px | Kode ICD-10 (`font-mono`) + tooltip nama lengkap |
| 6 | Total Tagihan | 130px | `font-mono`, right-aligned |
| 7 | Tgl Pengajuan | 110px | Format: `15 Jan 2025` |
| 8 | Status | 120px | Badge status klaim |
| 9 | Aksi | 80px | Tombol "Detail →" |

**Aturan Visual Tabel:**

- **Row striping: TIDAK.** Gunakan border horizontal saja (`border-b border-[--border-subtle]`)
- **Hover state**: `bg-[var(--bg-overlay)]` pada row yang di-hover
- **Klaim Merah**: tambahkan `border-l-2 border-[var(--risk-high)]` di sisi kiri row
- **Klaim yang sudah diverifikasi hari ini**: opacity 70% (`opacity-70`)
- **Sticky header** dengan background `--bg-surface` agar tidak transparan saat scroll

**Filter Bar di Atas Tabel:**

```
┌────────────────────────────────────────────────────────────────────┐
│  [● Semua ▾]  [Risk Level ▾]  [Nama RS ▾]  [Tanggal ▾]  [🔍 Cari] │
└────────────────────────────────────────────────────────────────────┘
```

- Filter aktif ditampilkan sebagai chip yang bisa di-dismiss (`× INA-CBGs > 150%`)
- Jumlah hasil ditampilkan: `Menampilkan 47 dari 312 klaim`

---

### 5.3 `StatsHeader` — Statistik Ringkas di Dashboard

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  312         │  │  89          │  │  147          │  │  76          │
│  Total Klaim │  │  HIGH RISK   │  │  Menunggu     │  │  Diproses    │
│  Hari Ini    │  │  ▲ 12 vs     │  │  Verifikasi   │  │  Hari Ini    │
│              │  │  kemarin     │  │               │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

- Angka utama: `text-data` (IBM Plex Mono 22px 500)
- Label: `text-small text-secondary`
- Tren (naik/turun): warna merah jika HIGH RISK naik, hijau jika turun
- Animasi: angka **count-up** saat pertama kali dimuat (0 → nilai aktual, durasi 800ms)

---

### 5.4 `ShapChart` — Visualisasi Faktor Risiko

Komponen ini menampilkan SHAP values dari ML Engine. Ini adalah fitur diferensiasi Pramana — harus jelas dan informatif.

**Layout:**

```
┌─ FAKTOR RISIKO ──────────────────────────────────────────────────┐
│                                                                   │
│  Risk Score          ████████████████░░░░░░   72.4 / 100        │
│                                                                   │
│  Faktor Pendorong (↑ Meningkatkan Risiko)                        │
│                                                                   │
│  Rasio vs INA-CBGs   ██████████████░░░░  +0.28  Tagihan 15% di  │
│                                                  atas standar    │
│  Tagihan/Hari        ████████░░░░░░░░░░  +0.19  Lebih tinggi    │
│                                                  dari RS setipe  │
│  Pola Historis RS    █████░░░░░░░░░░░░░  +0.11                   │
│                                                                   │
│  Faktor Penurun (↓ Menurunkan Risiko)                            │
│                                                                   │
│  Length of Stay      ░░░░░░░░░░░░░░████  -0.05  LOS wajar       │
│  Diagnosa Utama      ░░░░░░░░░░░░██████  -0.08  Kode tepat      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Spesifikasi Visual Bar Chart:**

- Bar positif (risiko naik): `var(--risk-high)` dengan opacity 80%
- Bar negatif (risiko turun): `var(--risk-low)` dengan opacity 80%
- Bar menggunakan horizontal layout dengan `Recharts BarChart`
- Nilai SHAP ditampilkan di kanan bar dengan `font-mono text-small`
- Label penjelasan (`top_risk_factors` dari API) ditampilkan di sebelah kanan nilai
- Animasi masuk: bar tumbuh dari kiri dengan `animationBegin={200}` di Recharts

---

### 5.5 `NLPCodingPanel` — Perbandingan Koding AI vs RS

Panel ini menampilkan perbedaan antara kode yang diajukan RS vs saran AI.

```
┌─ ANALISIS KODING ICD ────────────────────────────────────────────┐
│                                                                   │
│  Diagnosa Utama                                                   │
│  ┌─────────────────────────┐  ┌────────────────────────────┐    │
│  │ DIKLAIM RS               │  │ SARAN AI              ✓   │    │
│  │ I50.0                   │  │ I50.0                      │    │
│  │ Congestive Heart Failure│  │ Congestive Heart Failure   │    │
│  └─────────────────────────┘  └────────────────────────────┘    │
│                                 Confidence: ████████░░ 92%       │
│                                                                   │
│  Diagnosa Sekunder              ⚠ MISMATCH TERDETEKSI            │
│  ┌─────────────────────────┐  ┌────────────────────────────┐    │
│  │ DIKLAIM RS               │  │ SARAN AI           ⚠ FLAG │    │
│  │ J18.1                   │  │ J18.9                      │    │
│  │ Lobar Pneumonia         │  │ Pneumonia, tidak spesifik  │    │
│  └─────────────────────────┘  └────────────────────────────┘    │
│  ↑ Kode lebih spesifik, tarif  Confidence: █████░░░░░ 67%       │
│  lebih tinggi. Perlu verifikasi!  (Di bawah threshold 0.75)      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Aturan Visual:**

- **Match**: border hijau, ikon checkmark, background `risk-low-bg`
- **Mismatch**: border kuning/oranye, ikon warning, background `risk-medium-bg`
- **Confidence bar** menggunakan gradient: merah di kiri → hijau di kanan
- Kode ICD selalu `font-mono` dengan ukuran yang lebih besar dari teksnya

---

### 5.6 `AuditTrail` — History Aksi

Timeline vertikal sederhana di halaman detail klaim:

```
●── 15 Jan 2025, 14:32  ── Rina Kusuma (Verifikator BPJS)
│   Klaim dikembalikan ke RS.
│   Catatan: "Kode diagnosa sekunder perlu klarifikasi."
│
●── 16 Jan 2025, 09:15  ── Ahmad Fauzi (Admin RS)
│   Klaim diajukan ulang dengan revisi koding.
│
●── 16 Jan 2025, 11:48  ── Rina Kusuma (Verifikator BPJS)
    Klaim disetujui.
```

---

## 6. Halaman-Halaman Utama

### 6.1 Halaman Login (`Login.tsx`)

**Layout:** Split-screen. Kiri: branding. Kanan: form.

```
┌────────────────────────┬────────────────────────────────────────┐
│                        │                                         │
│  [Logo Pramana AI]     │         Selamat Datang Kembali          │
│                        │                                         │
│  "Validasi yang        │  ┌──────────────────────────────────┐  │
│   cerdas untuk         │  │ Email                            │  │
│   sistem               │  └──────────────────────────────────┘  │
│   kesehatan            │  ┌──────────────────────────────────┐  │
│   nasional."           │  │ Password                   [👁]  │  │
│                        │  └──────────────────────────────────┘  │
│  — Dikembangkan        │                                         │
│    oleh Siena Clinical │  [         Masuk         ]             │
│                        │                                         │
│  [Dekorasi abstrak     │  BPJS Kesehatan  ·  Verifikasi Klaim   │
│   geometric subtle]    │                                         │
└────────────────────────┴────────────────────────────────────────┘
```

**Detail:**

- Kiri: background `--bg-surface`, teks `--text-secondary`, logo berukuran 48px
- Elemen dekoratif kiri: subtle hexagonal grid pattern dengan `opacity-5` (CSS background-image)
- Form di kanan: background `--bg-base`, form container tanpa card (form langsung di atas bg)
- Tombol submit: full-width, background `--accent-primary`, animasi loading spinner saat submit
- Error message: muncul di bawah tombol, teks `--risk-high`

---

### 6.2 Dashboard Triage (`Dashboard.tsx`)

**Layout:** Sidebar + Main Content

```
┌───────────┬──────────────────────────────────────────────────────┐
│ SIDEBAR   │ TOP BAR: Pramana AI   •  Rina Kusuma   [🔔] [Avatar] │
│           ├──────────────────────────────────────────────────────┤
│ ◈ Dashboard│                                                      │
│ ≡ Klaim   │  [Stats Header: 4 kartu]                             │
│ 📊 Analitik│                                                      │
│           │  ┌────────────────────────────────────────────────┐  │
│           │  │ Filter Bar                                     │  │
│           │  ├────────────────────────────────────────────────┤  │
│ ─────     │  │ ClaimTable (scrollable, sticky header)        │  │
│ [Avatar]  │  │                                               │  │
│ Rina K.   │  │                                               │  │
│ Verifikator│  │                                               │  │
│ [Logout]  │  └────────────────────────────────────────────────┘  │
└───────────┴──────────────────────────────────────────────────────┘
```

**Sidebar:**

- Lebar: 240px (collapsible ke 64px — icon only)
- Background: `--bg-surface`
- Border kanan: `--border-subtle`
- Active nav item: background `--accent-glow`, border kiri `--accent-primary` 3px, teks `--accent-secondary`
- Avatar user di bawah: menampilkan nama, role, dan tombol logout

**Top Bar:**

- Height: 56px
- Background: `--bg-surface` dengan `border-b border-[--border-subtle]`
- Breadcrumb atau page title di kiri
- Notifikasi badge + avatar di kanan

---

### 6.3 Halaman Detail Klaim (`ClaimDetail.tsx`)

**Layout:** Full-width dengan dua kolom pada bagian bawah.

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Kembali ke Dashboard                                          │
├───────────────────────────────────┬─────────────────────────────┤
│ INFO KLAIM                        │ RISK SCORE                  │
│ No. SEP: 0301R00001230120250001   │ [RiskBadge besar]           │
│ RS: RSUD Dr. Soetomo              │ ShapChart                   │
│ Diagnosa: I50.0 — CHF             │                             │
│ Tagihan: Rp 12.500.000            │                             │
│ LOS: 5 hari                       │                             │
│ Tgl Masuk: 15 Jan 2025            │                             │
│ Tgl Pulang: 20 Jan 2025           │                             │
├───────────────────────────────────┴─────────────────────────────┤
│ ANALISIS KODING NLP                                             │
│ [NLPCodingPanel]                                                │
├─────────────────────────────────────────────────────────────────┤
│ AKSI VERIFIKATOR                                                │
│ [Form aksi: Setujui / Kembalikan / Eskalasi + catatan]         │
├─────────────────────────────────────────────────────────────────┤
│ HISTORY KLAIM                                                   │
│ [AuditTrail]                                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Panel Aksi Verifikator:**

```
┌─ AMBIL KEPUTUSAN ───────────────────────────────────────────────┐
│                                                                  │
│  [✓ Setujui Klaim]  [↩ Kembalikan ke RS]  [↑ Eskalasi]         │
│                                                                  │
│  Catatan (wajib jika Kembalikan/Eskalasi):                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Warna Tombol Aksi:**

- Setujui: background `--risk-low`, hover lebih terang
- Kembalikan: background `--risk-medium`, text putih
- Eskalasi: background `--bg-elevated`, border `--border-default`, text `--text-primary` (subtle/secondary)
- Tombol harus **disabled** jika klaim sudah pernah diverifikasi

---

## 7. Panduan Animasi & Motion

### Prinsip

- **Fungsional, bukan dekoratif.** Animasi harus menjelaskan perubahan state, bukan memperindah.
- **Durasi pendek.** Semua transisi halaman dan komponen: 150–250ms. Tidak ada yang > 300ms kecuali chart.
- **Jangan animasikan data.** Loading state menggunakan skeleton, bukan spinner yang berputar-putar.

### Implementasi yang Wajib

| Elemen | Animasi | Durasi |
| :--- | :--- | :--- |
| Halaman baru dimuat | `opacity: 0 → 1` + `translateY: 8px → 0` | 200ms ease-out |
| Row tabel di-hover | `background-color` transition | 100ms |
| Risk badge `high` | dot blink `animate-pulse` | continuous |
| Stats header angka | Count-up dari 0 | 800ms ease-out |
| ShapChart bars | Grow dari kiri | 600ms ease-out |
| Sidebar collapse | `width` transition | 200ms ease-in-out |
| Modal / dialog muncul | `scale: 0.95 → 1` + `opacity: 0 → 1` | 150ms |
| Toast notification | Slide in dari kanan | 250ms |

### Skeleton Loading

Gunakan skeleton untuk semua data yang diambil dari API. **Jangan gunakan spinner.**

```tsx
// Contoh skeleton untuk ClaimTable
<div className="animate-pulse">
  {Array.from({ length: 8 }).map((_, i) => (
    <div key={i} className="h-12 bg-[var(--bg-elevated)] rounded mb-1" />
  ))}
</div>
```

---

## 8. Feedback & State UI

### Toast Notifications

Muncul di pojok kanan bawah. Tidak lebih dari 2 toast sekaligus.

| Tipe | Warna | Contoh |
| :--- | :--- | :--- |
| Success | `--risk-low` | "Klaim #0301R... berhasil disetujui" |
| Warning | `--risk-medium` | "Sesi akan berakhir dalam 10 menit" |
| Error | `--risk-high` | "Gagal memuat data. Coba lagi." |
| Info | `--accent-primary` | "2 klaim baru masuk" |

### Empty State

Ketika tidak ada klaim yang sesuai filter:

```
        ≡ ≡ ≡
       ─── ─ ─
      ─────────
      
  Tidak ada klaim ditemukan
  Coba ubah filter atau tanggal pencarian.
  [Reset Filter]
```

### Error State

Ketika API gagal:

```
  ⚠

  Gagal memuat data klaim
  Periksa koneksi atau hubungi admin sistem.
  
  [Coba Lagi]
```

---

## 9. Aksesibilitas

- **Kontras warna**: Semua teks body harus memiliki rasio kontras minimal 4.5:1 terhadap background-nya.
- **Focus indicator**: Semua elemen interaktif harus memiliki `outline` yang terlihat saat difokus keyboard. Jangan pernah `outline: none` tanpa pengganti.
- **ARIA labels**: Semua tombol yang hanya berisi ikon harus memiliki `aria-label`.
- **Screen reader**: `RiskBadge` harus membaca "HIGH RISK, skor 84" bukan hanya angka.
- **Keyboard navigation**: Tabel harus dapat dinavigasi dengan arrow keys.

---

## 10. Panduan shadcn/ui

Komponen yang digunakan dari shadcn/ui dan kustomisasinya:

| Komponen shadcn | Penggunaan | Kustomisasi |
| :--- | :--- | :--- |
| `Table` | ClaimTable | Header sticky, row hover dengan CSS vars |
| `Badge` | RiskBadge, StatusBadge | Override warna dengan CSS vars |
| `Button` | Semua tombol aksi | Variant: default, destructive, ghost |
| `Dialog` | Konfirmasi keputusan klaim | Overlay lebih gelap dari default |
| `Tooltip` | Hover pada kode ICD | Konten: nama lengkap diagnosa |
| `Select` | Filter dropdown | Sesuaikan warna dengan dark theme |
| `Textarea` | Form catatan verifikator | Min-height 80px |
| `Skeleton` | Loading state | Warna `--bg-elevated` |
| `Toast` | Notifikasi aksi | Posisi bottom-right |

**Override Global Theme shadcn:**

Di `globals.css`, override variabel shadcn agar sesuai dengan warna Pramana:

```css
:root {
  --background: 214 10% 7%;          /* --bg-base */
  --foreground: 210 40% 92%;         /* --text-primary */
  --card: 215 12% 10%;               /* --bg-surface */
  --border: 215 10% 22%;             /* --border-subtle */
  --input: 215 10% 18%;
  --primary: 213 89% 56%;            /* --accent-primary */
  --destructive: 0 72% 44%;          /* --risk-high */
  --ring: 213 89% 56%;
  --radius: 0.375rem;                /* 6px */
}
```

---

## 11. Contoh Konvensi Penamaan File & Komponen

```
frontend/src/
├── components/
│   ├── claims/
│   │   ├── ClaimTable.tsx          # Tabel utama
│   │   ├── ClaimTableRow.tsx       # Satu baris tabel
│   │   ├── ClaimFilterBar.tsx      # Filter di atas tabel
│   │   └── ClaimStatusBadge.tsx    # Badge status (bukan risk)
│   ├── risk/
│   │   ├── RiskBadge.tsx           # Badge Hijau/Kuning/Merah
│   │   └── ShapChart.tsx           # Bar chart SHAP values
│   ├── nlp/
│   │   └── NLPCodingPanel.tsx      # Perbandingan koding
│   ├── layout/
│   │   ├── AppSidebar.tsx
│   │   ├── TopBar.tsx
│   │   └── PageContainer.tsx
│   └── ui/                         # shadcn/ui components (auto-generated)
├── pages/
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   └── ClaimDetailPage.tsx
├── hooks/
│   ├── useClaims.ts                # TanStack Query hooks
│   ├── useClaimDetail.ts
│   └── useAuth.ts
├── store/
│   └── authStore.ts                # Zustand store untuk auth state
└── lib/
    ├── api.ts                      # Axios instance + interceptors
    ├── formatters.ts               # Format Rp, tanggal, ICD
    └── riskUtils.ts                # Konversi score → level
```

---

## 12. Checklist Sebelum Demo

Sebelum demo ke stakeholder, pastikan hal-hal ini sudah selesai:

- [ ] Dark theme berjalan konsisten di semua halaman
- [ ] `RiskBadge` sudah menampilkan pulse animation untuk HIGH RISK
- [ ] Semua angka numerik menggunakan `font-mono`
- [ ] Data pasien sudah disamarkan di tabel (`Budi S***`)
- [ ] Skeleton loading tampil saat data sedang diambil
- [ ] Error state tampil dengan tombol "Coba Lagi" jika API gagal
- [ ] Tombol aksi disabled jika klaim sudah diverifikasi
- [ ] Sidebar bisa di-collapse ke icon-only mode
- [ ] `ShapChart` menampilkan bar dengan animasi grow
- [ ] Toast notification muncul setelah aksi verifikator berhasil
- [ ] Semua kode ICD bisa di-hover untuk melihat nama lengkap diagnosa
