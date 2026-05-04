/**
 * Pramana AI — Risk Utilities
 * Konversi score 0–100 → level 'low' | 'medium' | 'high'
 */

export type RiskLevel = 'low' | 'medium' | 'high';

export function scoreToLevel(score: number): RiskLevel {
  if (score < 40)  return 'low';
  if (score < 70)  return 'medium';
  return 'high';
}

export const RISK_LABEL: Record<RiskLevel, string> = {
  low:    'LOW RISK',
  medium: 'MED RISK',
  high:   'HIGH RISK',
};
