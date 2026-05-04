/**
 * Pramana AI — Shared TypeScript types
 */

export type RiskLevel = 'low' | 'medium' | 'high';
export type ClaimStatus = 'pending' | 'in_review' | 'approved' | 'returned' | 'escalated';

export interface Claim {
  id: string;
  no_sep: string;
  patient_name: string;
  hospital: string;
  diagnosa_utama: string;
  diagnosa_utama_desc: string;
  total_tagihan: number;
  tgl_pengajuan: string;
  status: ClaimStatus;
  risk_score: number;
  risk_level: RiskLevel;
  los: number;
  tgl_masuk: string;
  tgl_pulang: string;
  tarif_ina_cbgs: number;
}

export interface ShapFactor {
  feature: string;
  value: number;
  label: string;
}

export interface RiskScoreResult {
  claim_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  shap_values: Record<string, number>;
  top_risk_factors: string[];
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  user: string;
  role: string;
  action: string;
  note: string | null;
}
