/**
 * gpxExport — Generate GPX files from route analysis data.
 * Compatible with Garmin, Suunto, Coros, Komoot, etc.
 */

import type { RouteAnalysis } from '@/stores/routeStore'

function formatCoord(coord: number[], ele?: number): string {
  const [lng, lat, z] = coord
  const eleVal = ele ?? (coord.length > 2 ? z : 0)
  return `        <trkpt lat="${lat}" lon="${lng}"><ele>${eleVal}</ele></trkpt>`
}

function formatTime(date: Date): string {
  return date.toISOString()
}

export function exportRouteAsGpx(analysis: RouteAnalysis, filename?: string): void {
  const routeName = analysis.route_name ?? 'RiskTrail Route'
  const now = new Date()

  // Build trackpoints from segment geometries
  const trackpoints: string[] = []
  for (const seg of analysis.segments) {
    if (!seg.geom?.coordinates) continue
    for (const coord of seg.geom.coordinates) {
      trackpoints.push(formatCoord(coord))
    }
  }

  const gpx = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="RiskTrail"
  xmlns="http://www.topografix.com/GPX/1/1"
  xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3"
  xmlns:wptx1="http://www.garmin.com/xmlschemas/WaypointExtension/v1">
  <metadata>
    <name>${escapeXml(routeName)}</name>
    <desc>Ruta analizada con RiskTrail. MIDE ${analysis.summary.mide_global}, ${analysis.summary.total_distance_km.toFixed(1)} km, ${analysis.summary.estimated_time_h.toFixed(1)}h.</desc>
    <time>${formatTime(now)}</time>
  </metadata>
  <trk>
    <name>${escapeXml(routeName)}</name>
    <type>Hiking</type>
    <trkseg>
${trackpoints.join('\n')}
    </trkseg>
  </trk>
</gpx>`

  const blob = new Blob([gpx], { type: 'application/gpx+xml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename ?? `${routeName.replace(/[^a-zA-Z0-9]/g, '_')}.gpx`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}
