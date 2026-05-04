/**
 * Pramana AI — Formatter utilities
 * Ref: frontend-design.md §3 Tipografi (font-mono untuk angka)
 */

/** Format nominal Rupiah: Rp 12.500.000 */
export function formatRupiah(value: number): string {
  return 'Rp ' + value.toLocaleString('id-ID');
}

/** Format tanggal: 15 Jan 2025 */
export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
}

/** Format datetime: 15 Jan 2025, 14:32 */
export function formatDateTime(dateStr: string): string {
  const d = new Date(dateStr);
  return (
    d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) +
    ', ' +
    d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
  );
}

/** Samarkan nama pasien: "Budi Santoso" → "Bud S***" */
export function maskPatientName(name: string): string {
  const parts = name.trim().split(' ');
  const first = parts[0].slice(0, 3);
  const rest = parts.slice(1).map((p) => p.charAt(0) + '***');
  return [first, ...rest].join(' ');
}

/** Singkat nama RS jika > 25 karakter */
export function shortenHospitalName(name: string): string {
  return name.length > 25 ? name.slice(0, 23) + '…' : name;
}
