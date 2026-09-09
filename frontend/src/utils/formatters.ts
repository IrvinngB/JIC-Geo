/**
 * Formatters for numeric values and durations across the UI and reports.
 */

export function formatNumber(value: number, digits = 1): string {
  return value.toLocaleString('es-MX', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })
}

/**
 * Formats a duration in decimal hours into a human-friendly format.
 * Converts from scientific/decimal hours (e.g. 0.82 h) to clock time (e.g. 49 min).
 *
 * Examples:
 *   0.82 -> "49 min"
 *   1.0  -> "1 h"
 *   1.25 -> "1 h 15 min"
 *   2.5  -> "2 h 30 min"
 */
export function formatDurationHours(hours: number | null | undefined): string {
  if (hours == null || isNaN(hours) || hours <= 0) return '0 min'
  const totalMinutes = Math.round(hours * 60)
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60

  if (h === 0) return `${m} min`
  if (m === 0) return `${h} h`
  return `${h} h ${m} min`
}
