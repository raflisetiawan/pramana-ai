/**
 * Pramana AI — RiskBadge
 * Komponen paling kritis: warna risk level harus dapat dibaca dalam sepersekian detik.
 * Ref: frontend-design.md §5.1
 */

import type { RiskLevel } from '../../lib/types';
import { RISK_LABEL } from '../../lib/riskUtils';

interface RiskBadgeProps {
  score: number;
  level: RiskLevel;
  showScore?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function RiskBadge({ score, level, showScore = true, size = 'md' }: RiskBadgeProps) {
  const ariaLabel = `${RISK_LABEL[level]}, skor ${score}`;

  const sizeStyle: Record<string, React.CSSProperties> = {
    sm: { padding: '2px 7px', fontSize: '10px' },
    md: {},
    lg: { padding: '6px 14px', fontSize: '13px', gap: '8px' },
  };

  const dotSize: Record<string, React.CSSProperties> = {
    sm: { width: '5px', height: '5px' },
    md: {},
    lg: { width: '10px', height: '10px' },
  };

  const scoreStyle: Record<string, React.CSSProperties> = {
    sm: { fontSize: '11px' },
    md: {},
    lg: { fontSize: '15px' },
  };

  return (
    <span
      className={`risk-badge ${level}`}
      style={sizeStyle[size]}
      aria-label={ariaLabel}
      role="img"
    >
      <span className="risk-badge-dot" style={dotSize[size]} />
      <span>{RISK_LABEL[level]}</span>
      {showScore && (
        <span className="risk-badge-score" style={scoreStyle[size]}>{score}</span>
      )}
    </span>
  );
}
