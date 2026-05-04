/**
 * Pramana AI — Mock Data untuk demo (tanpa backend)
 */

import type { Claim, RiskLevel } from './types';

export const MOCK_CLAIMS: Claim[] = [
  {
    id: 'c001',
    no_sep: '0301R00001230120250001',
    patient_name: 'Budi Santoso',
    hospital: 'RSUD Dr. Soetomo Surabaya',
    diagnosa_utama: 'I50.0',
    diagnosa_utama_desc: 'Congestive Heart Failure',
    total_tagihan: 12500000,
    tgl_pengajuan: '2025-01-15',
    status: 'pending',
    risk_score: 84,
    risk_level: 'high',
    los: 5,
    tgl_masuk: '2025-01-10',
    tgl_pulang: '2025-01-15',
    tarif_ina_cbgs: 10800000,
  },
  {
    id: 'c002',
    no_sep: '0301R00001230120250002',
    patient_name: 'Siti Rahayu',
    hospital: 'RS Panti Waluya Malang',
    diagnosa_utama: 'J18.9',
    diagnosa_utama_desc: 'Pneumonia, tidak spesifik',
    total_tagihan: 7800000,
    tgl_pengajuan: '2025-01-15',
    status: 'in_review',
    risk_score: 58,
    risk_level: 'medium',
    los: 4,
    tgl_masuk: '2025-01-11',
    tgl_pulang: '2025-01-15',
    tarif_ina_cbgs: 7200000,
  },
  {
    id: 'c003',
    no_sep: '0301R00001230120250003',
    patient_name: 'Ahmad Fauzi',
    hospital: 'RSUD Sidoarjo',
    diagnosa_utama: 'E11.9',
    diagnosa_utama_desc: 'Diabetes mellitus tipe 2',
    total_tagihan: 3200000,
    tgl_pengajuan: '2025-01-14',
    status: 'approved',
    risk_score: 18,
    risk_level: 'low',
    los: 3,
    tgl_masuk: '2025-01-11',
    tgl_pulang: '2025-01-14',
    tarif_ina_cbgs: 3400000,
  },
  {
    id: 'c004',
    no_sep: '0301R00001230120250004',
    patient_name: 'Dewi Permatasari',
    hospital: 'RS Universitas Airlangga',
    diagnosa_utama: 'N18.5',
    diagnosa_utama_desc: 'Gagal ginjal kronik stadium 5',
    total_tagihan: 18900000,
    tgl_pengajuan: '2025-01-15',
    status: 'pending',
    risk_score: 77,
    risk_level: 'high',
    los: 7,
    tgl_masuk: '2025-01-08',
    tgl_pulang: '2025-01-15',
    tarif_ina_cbgs: 15000000,
  },
  {
    id: 'c005',
    no_sep: '0301R00001230120250005',
    patient_name: 'Hendra Gunawan',
    hospital: 'RSUD Dr. Soetomo Surabaya',
    diagnosa_utama: 'I21.9',
    diagnosa_utama_desc: 'Acute myocardial infarction, unspecified',
    total_tagihan: 22400000,
    tgl_pengajuan: '2025-01-13',
    status: 'escalated',
    risk_score: 91,
    risk_level: 'high',
    los: 6,
    tgl_masuk: '2025-01-07',
    tgl_pulang: '2025-01-13',
    tarif_ina_cbgs: 18000000,
  },
  {
    id: 'c006',
    no_sep: '0301R00001230120250006',
    patient_name: 'Ratna Dewi',
    hospital: 'RS Islam Surabaya',
    diagnosa_utama: 'I10',
    diagnosa_utama_desc: 'Essential hypertension',
    total_tagihan: 2100000,
    tgl_pengajuan: '2025-01-14',
    status: 'approved',
    risk_score: 12,
    risk_level: 'low',
    los: 2,
    tgl_masuk: '2025-01-12',
    tgl_pulang: '2025-01-14',
    tarif_ina_cbgs: 2300000,
  },
  {
    id: 'c007',
    no_sep: '0301R00001230120250007',
    patient_name: 'Bambang Wijaya',
    hospital: 'RSUD Kota Surabaya',
    diagnosa_utama: 'K80.2',
    diagnosa_utama_desc: 'Calculus of gallbladder without cholecystitis',
    total_tagihan: 9600000,
    tgl_pengajuan: '2025-01-15',
    status: 'pending',
    risk_score: 44,
    risk_level: 'medium',
    los: 4,
    tgl_masuk: '2025-01-11',
    tgl_pulang: '2025-01-15',
    tarif_ina_cbgs: 8900000,
  },
  {
    id: 'c008',
    no_sep: '0301R00001230120250008',
    patient_name: 'Sri Wahyuni',
    hospital: 'RS Darmo Surabaya',
    diagnosa_utama: 'J45.9',
    diagnosa_utama_desc: 'Asthma, unspecified',
    total_tagihan: 4200000,
    tgl_pengajuan: '2025-01-13',
    status: 'returned',
    risk_score: 34,
    risk_level: 'low',
    los: 3,
    tgl_masuk: '2025-01-10',
    tgl_pulang: '2025-01-13',
    tarif_ina_cbgs: 4000000,
  },
  {
    id: 'c009',
    no_sep: '0301R00001230120250009',
    patient_name: 'Agus Prabowo',
    hospital: 'RSUD Dr. Soetomo Surabaya',
    diagnosa_utama: 'G40.9',
    diagnosa_utama_desc: 'Epilepsy, unspecified',
    total_tagihan: 5600000,
    tgl_pengajuan: '2025-01-12',
    status: 'pending',
    risk_score: 52,
    risk_level: 'medium',
    los: 4,
    tgl_masuk: '2025-01-08',
    tgl_pulang: '2025-01-12',
    tarif_ina_cbgs: 5200000,
  },
  {
    id: 'c010',
    no_sep: '0301R00001230120250010',
    patient_name: 'Maria Theresia',
    hospital: 'RS Panti Waluya Malang',
    diagnosa_utama: 'C50.9',
    diagnosa_utama_desc: 'Malignant neoplasm of breast, unspecified',
    total_tagihan: 28500000,
    tgl_pengajuan: '2025-01-11',
    status: 'pending',
    risk_score: 88,
    risk_level: 'high',
    los: 10,
    tgl_masuk: '2025-01-01',
    tgl_pulang: '2025-01-11',
    tarif_ina_cbgs: 24000000,
  },
  {
    id: 'c011',
    no_sep: '0301R00001230120250011',
    patient_name: 'Yusuf Maulana',
    hospital: 'RSUD Sidoarjo',
    diagnosa_utama: 'A09',
    diagnosa_utama_desc: 'Diarrhoea and gastroenteritis',
    total_tagihan: 1800000,
    tgl_pengajuan: '2025-01-15',
    status: 'approved',
    risk_score: 8,
    risk_level: 'low',
    los: 2,
    tgl_masuk: '2025-01-13',
    tgl_pulang: '2025-01-15',
    tarif_ina_cbgs: 1900000,
  },
  {
    id: 'c012',
    no_sep: '0301R00001230120250012',
    patient_name: 'Lina Susanti',
    hospital: 'RS Universitas Airlangga',
    diagnosa_utama: 'K35.8',
    diagnosa_utama_desc: 'Acute appendicitis, other and unspecified',
    total_tagihan: 11200000,
    tgl_pengajuan: '2025-01-14',
    status: 'in_review',
    risk_score: 62,
    risk_level: 'medium',
    los: 3,
    tgl_masuk: '2025-01-11',
    tgl_pulang: '2025-01-14',
    tarif_ina_cbgs: 9800000,
  },
];

/** Daftar RS unik yang diekstrak dari mock claims */
export const MOCK_HOSPITALS: string[] = Array.from(
  new Set(MOCK_CLAIMS.map((c) => c.hospital))
).sort();

export const MOCK_CLAIM_DETAIL = MOCK_CLAIMS[0]; // c001 dipakai untuk detail

/* ── Per-claim risk scores ── */
export interface MockRiskScore {
  claim_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  shap_values: Record<string, number>;
  top_risk_factors: string[];
}

export const MOCK_RISK_SCORES: Record<string, MockRiskScore> = {
  c001: {
    claim_id: 'c001',
    risk_score: 84,
    risk_level: 'high',
    shap_values: {
      rasio_terhadap_ina_cbgs: 0.28,
      tagihan_per_hari: 0.19,
      pola_historis_rs: 0.11,
      los: -0.05,
      diagnosa_utama: -0.08,
    },
    top_risk_factors: [
      'Tagihan 15% di atas tarif INA-CBGs untuk diagnosa ini',
      'Tagihan per hari lebih tinggi dari RS setipe di wilayah yang sama',
      'RS memiliki riwayat klaim di atas rata-rata 30 hari terakhir',
    ],
  },
  c002: {
    claim_id: 'c002',
    risk_score: 58,
    risk_level: 'medium',
    shap_values: {
      rasio_terhadap_ina_cbgs: 0.15,
      tagihan_per_hari: 0.10,
      los: 0.06,
      diagnosa_utama: -0.04,
      pola_historis_rs: -0.03,
    },
    top_risk_factors: [
      'Tagihan 8% di atas tarif INA-CBGs standar',
      'Length of Stay sedikit di bawah rata-rata untuk pneumonia',
    ],
  },
  c004: {
    claim_id: 'c004',
    risk_score: 77,
    risk_level: 'high',
    shap_values: {
      rasio_terhadap_ina_cbgs: 0.32,
      tagihan_per_hari: 0.12,
      jumlah_prosedur: 0.08,
      los: -0.03,
      diagnosa_utama: -0.06,
    },
    top_risk_factors: [
      'Tagihan 26% di atas tarif INA-CBGs untuk CKD stadium 5',
      'Jumlah prosedur lebih banyak dari rata-rata untuk diagnosa ini',
    ],
  },
  c005: {
    claim_id: 'c005',
    risk_score: 91,
    risk_level: 'high',
    shap_values: {
      rasio_terhadap_ina_cbgs: 0.35,
      tagihan_per_hari: 0.22,
      pola_historis_rs: 0.14,
      jumlah_prosedur: 0.06,
      diagnosa_utama: -0.04,
    },
    top_risk_factors: [
      'Tagihan 24% di atas tarif INA-CBGs untuk AMI',
      'Tagihan per hari sangat tinggi dibanding RS setipe',
      'RS memiliki pola klaim tinggi dalam 30 hari terakhir',
    ],
  },
  c010: {
    claim_id: 'c010',
    risk_score: 88,
    risk_level: 'high',
    shap_values: {
      rasio_terhadap_ina_cbgs: 0.30,
      los: 0.18,
      tagihan_per_hari: 0.10,
      diagnosa_utama: -0.02,
      pola_historis_rs: -0.04,
    },
    top_risk_factors: [
      'Tagihan 19% di atas tarif INA-CBGs untuk neoplasma payudara',
      'Length of Stay 10 hari — unusually high for this diagnosis',
    ],
  },
};

/** Get risk score data for a claim, fallback to default */
export function getRiskScoreForClaim(claimId: string): MockRiskScore {
  return MOCK_RISK_SCORES[claimId] || {
    claim_id: claimId,
    risk_score: MOCK_CLAIMS.find((c) => c.id === claimId)?.risk_score || 30,
    risk_level: MOCK_CLAIMS.find((c) => c.id === claimId)?.risk_level || 'low',
    shap_values: {
      rasio_terhadap_ina_cbgs: 0.05,
      tagihan_per_hari: 0.03,
      los: -0.02,
      diagnosa_utama: -0.04,
      pola_historis_rs: -0.01,
    },
    top_risk_factors: ['Klaim dalam parameter normal'],
  };
}

/* ── Per-claim NLP results ── */
export interface NLPCodingEntry {
  diklaim: { kode: string; desc: string };
  saran: { kode: string; desc: string; confidence: number; match: boolean };
  flag_reason?: string;
}

export interface MockNLPResult {
  diagnosa_utama: NLPCodingEntry;
  diagnosa_sekunder: NLPCodingEntry[];
  prosedur: NLPCodingEntry[];
}

export const MOCK_NLP_RESULTS: Record<string, MockNLPResult> = {
  c001: {
    diagnosa_utama: {
      diklaim: { kode: 'I50.0', desc: 'Congestive Heart Failure' },
      saran: { kode: 'I50.0', desc: 'Congestive Heart Failure', confidence: 0.92, match: true },
    },
    diagnosa_sekunder: [
      {
        diklaim: { kode: 'J18.1', desc: 'Lobar Pneumonia' },
        saran: { kode: 'J18.9', desc: 'Pneumonia, tidak spesifik', confidence: 0.67, match: false },
        flag_reason: 'Kode lebih spesifik — tarif lebih tinggi. Perlu verifikasi dokumen.',
      },
    ],
    prosedur: [
      {
        diklaim: { kode: '99.04', desc: 'Transfusi Whole Blood' },
        saran: { kode: '99.04', desc: 'Transfusi Whole Blood', confidence: 0.88, match: true },
      },
    ],
  },
  c004: {
    diagnosa_utama: {
      diklaim: { kode: 'N18.5', desc: 'Gagal ginjal kronik stadium 5' },
      saran: { kode: 'N18.5', desc: 'Gagal ginjal kronik stadium 5', confidence: 0.95, match: true },
    },
    diagnosa_sekunder: [
      {
        diklaim: { kode: 'I10', desc: 'Essential hypertension' },
        saran: { kode: 'I10', desc: 'Essential hypertension', confidence: 0.90, match: true },
      },
    ],
    prosedur: [
      {
        diklaim: { kode: '39.95', desc: 'Hemodialysis' },
        saran: { kode: '39.95', desc: 'Hemodialysis', confidence: 0.94, match: true },
      },
    ],
  },
  c005: {
    diagnosa_utama: {
      diklaim: { kode: 'I21.0', desc: 'Acute transmural MI of anterior wall' },
      saran: { kode: 'I21.9', desc: 'Acute myocardial infarction, unspecified', confidence: 0.72, match: false },
      flag_reason: 'RS mengklaim kode lebih spesifik (I21.0) — perlu verifikasi EKG atau angiografi.',
    },
    diagnosa_sekunder: [],
    prosedur: [
      {
        diklaim: { kode: '36.01', desc: 'PTCA single vessel' },
        saran: { kode: '36.01', desc: 'PTCA single vessel', confidence: 0.85, match: true },
      },
      {
        diklaim: { kode: '88.56', desc: 'Coronary arteriography' },
        saran: { kode: '88.56', desc: 'Coronary arteriography', confidence: 0.91, match: true },
      },
    ],
  },
};

/** Get NLP result for a claim, fallback to default */
export function getNLPResultForClaim(claimId: string): MockNLPResult {
  if (MOCK_NLP_RESULTS[claimId]) return MOCK_NLP_RESULTS[claimId];

  const claim = MOCK_CLAIMS.find((c) => c.id === claimId);
  return {
    diagnosa_utama: {
      diklaim: { kode: claim?.diagnosa_utama || 'Z00', desc: claim?.diagnosa_utama_desc || 'Pemeriksaan umum' },
      saran: { kode: claim?.diagnosa_utama || 'Z00', desc: claim?.diagnosa_utama_desc || 'Pemeriksaan umum', confidence: 0.85, match: true },
    },
    diagnosa_sekunder: [],
    prosedur: [],
  };
}

/* ── Per-claim audit trails ── */
export interface AuditEntry {
  id: string;
  timestamp: string;
  user: string;
  role: string;
  action: string;
  action_type: 'system' | 'ai' | 'approve' | 'return' | 'escalate' | 'resubmit';
  note: string | null;
}

export const MOCK_AUDIT_TRAILS: Record<string, AuditEntry[]> = {
  c001: [
    {
      id: 'a1',
      timestamp: '2025-01-10T08:00:00',
      user: 'Sistem',
      role: 'Otomatis',
      action: 'Klaim diterima dari SIMRS RSUD Dr. Soetomo.',
      action_type: 'system',
      note: null,
    },
    {
      id: 'a2',
      timestamp: '2025-01-10T08:01:22',
      user: 'Pramana AI',
      role: 'AI Engine',
      action: 'Risk scoring selesai. Score: 84 (HIGH RISK).',
      action_type: 'ai',
      note: null,
    },
    {
      id: 'a3',
      timestamp: '2025-01-10T08:01:45',
      user: 'Pramana AI',
      role: 'NLP Engine',
      action: 'Analisis koding selesai. Mismatch terdeteksi pada diagnosa sekunder (J18.1 vs J18.9).',
      action_type: 'ai',
      note: null,
    },
    {
      id: 'a4',
      timestamp: '2025-01-15T09:30:00',
      user: 'Rina Kusuma',
      role: 'Verifikator BPJS',
      action: 'Klaim dikembalikan ke rumah sakit.',
      action_type: 'return',
      note: 'Kode diagnosa sekunder perlu klarifikasi dari dokter DPJP.',
    },
    {
      id: 'a5',
      timestamp: '2025-01-16T14:22:00',
      user: 'Admin RS Soetomo',
      role: 'Admin RS',
      action: 'Klaim diajukan ulang dengan revisi koding.',
      action_type: 'resubmit',
      note: null,
    },
  ],
  c003: [
    {
      id: 'b1',
      timestamp: '2025-01-11T07:15:00',
      user: 'Sistem',
      role: 'Otomatis',
      action: 'Klaim diterima dari SIMRS RSUD Sidoarjo.',
      action_type: 'system',
      note: null,
    },
    {
      id: 'b2',
      timestamp: '2025-01-11T07:15:30',
      user: 'Pramana AI',
      role: 'AI Engine',
      action: 'Risk scoring selesai. Score: 18 (LOW RISK).',
      action_type: 'ai',
      note: null,
    },
    {
      id: 'b3',
      timestamp: '2025-01-14T10:05:00',
      user: 'Rina Kusuma',
      role: 'Verifikator BPJS',
      action: 'Klaim disetujui.',
      action_type: 'approve',
      note: null,
    },
  ],
  c005: [
    {
      id: 'd1',
      timestamp: '2025-01-07T09:00:00',
      user: 'Sistem',
      role: 'Otomatis',
      action: 'Klaim diterima dari SIMRS RSUD Dr. Soetomo.',
      action_type: 'system',
      note: null,
    },
    {
      id: 'd2',
      timestamp: '2025-01-07T09:01:00',
      user: 'Pramana AI',
      role: 'AI Engine',
      action: 'Risk scoring selesai. Score: 91 (HIGH RISK).',
      action_type: 'ai',
      note: null,
    },
    {
      id: 'd3',
      timestamp: '2025-01-13T11:30:00',
      user: 'Rina Kusuma',
      role: 'Verifikator BPJS',
      action: 'Klaim dieskalasi ke supervisor.',
      action_type: 'escalate',
      note: 'Tagihan sangat tinggi dan kode AMI perlu diverifikasi dengan hasil angiografi.',
    },
  ],
};

/** Get audit trail for a claim, fallback to default */
export function getAuditTrailForClaim(claimId: string): AuditEntry[] {
  if (MOCK_AUDIT_TRAILS[claimId]) return MOCK_AUDIT_TRAILS[claimId];

  const claim = MOCK_CLAIMS.find((c) => c.id === claimId);
  return [
    {
      id: `auto-${claimId}-1`,
      timestamp: claim?.tgl_masuk ? `${claim.tgl_masuk}T08:00:00` : '2025-01-10T08:00:00',
      user: 'Sistem',
      role: 'Otomatis',
      action: `Klaim diterima dari SIMRS ${claim?.hospital || 'RS'}.`,
      action_type: 'system',
      note: null,
    },
    {
      id: `auto-${claimId}-2`,
      timestamp: claim?.tgl_masuk ? `${claim.tgl_masuk}T08:01:00` : '2025-01-10T08:01:00',
      user: 'Pramana AI',
      role: 'AI Engine',
      action: `Risk scoring selesai. Score: ${claim?.risk_score || 0} (${(claim?.risk_level || 'low').toUpperCase()} RISK).`,
      action_type: 'ai',
      note: null,
    },
  ];
}

// Legacy aliases for backward compatibility
export const MOCK_RISK_SCORE = MOCK_RISK_SCORES['c001']!;
export const MOCK_NLP_RESULT = MOCK_NLP_RESULTS['c001']!;
export const MOCK_AUDIT_TRAIL = MOCK_AUDIT_TRAILS['c001']!;

/** Helper: hitung statistik dari data klaim */
export function computeStats(claims: Claim[]) {
  const total = claims.length;
  const high = claims.filter((c) => c.risk_level === 'high').length;
  const medium = claims.filter((c) => c.risk_level === 'medium').length;
  const low = claims.filter((c) => c.risk_level === 'low').length;
  const pending = claims.filter((c) => c.status === 'pending' || c.status === 'in_review').length;
  const processed = claims.filter((c) => c.status === 'approved' || c.status === 'returned').length;

  return {
    total,
    high_risk: high,
    medium_risk: medium,
    low_risk: low,
    pending,
    processed_today: processed,
    high_risk_delta: +12, // mock trend
    pct_high: total > 0 ? Math.round((high / total) * 100) : 0,
    pct_medium: total > 0 ? Math.round((medium / total) * 100) : 0,
    pct_low: total > 0 ? Math.round((low / total) * 100) : 0,
  };
}

export const MOCK_STATS = computeStats(MOCK_CLAIMS);
