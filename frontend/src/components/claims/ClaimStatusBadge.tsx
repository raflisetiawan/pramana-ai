/**
 * Pramana AI — ClaimStatusBadge
 */

import type { ClaimStatus } from '../../lib/types';

const STATUS_LABEL: Record<ClaimStatus, string> = {
  pending:   'Menunggu',
  in_review: 'Direview',
  approved:  'Disetujui',
  returned:  'Dikembalikan',
  escalated: 'Dieskalasi',
};

export function ClaimStatusBadge({ status }: { status: ClaimStatus }) {
  return (
    <span className={`status-badge ${status}`}>
      {STATUS_LABEL[status]}
    </span>
  );
}
