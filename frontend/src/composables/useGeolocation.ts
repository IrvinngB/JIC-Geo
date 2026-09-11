/**
 * useGeolocation — composable for browser geolocation tracking.
 * Provides current position, tracking state, and distance calculation.
 */

import { ref, computed, onUnmounted } from 'vue'

export interface GeolocationPosition {
  lat: number
  lng: number
  accuracy: number
  timestamp: number
}

export function useGeolocation() {
  const position = ref<GeolocationPosition | null>(null)
  const isTracking = ref(false)
  const error = ref<string | null>(null)
  const watchId = ref<number | null>(null)

  const hasPosition = computed(() => position.value !== null)

  function startTracking(): void {
    if (!navigator.geolocation) {
      error.value = 'Geolocation not supported'
      return
    }

    isTracking.value = true
    error.value = null

    watchId.value = navigator.geolocation.watchPosition(
      (pos) => {
        position.value = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          timestamp: pos.timestamp,
        }
      },
      (err) => {
        isTracking.value = false
        switch (err.code) {
          case err.PERMISSION_DENIED:
            error.value = 'Permiso de ubicación denegado'
            break
          case err.POSITION_UNAVAILABLE:
            error.value = 'Ubicación no disponible'
            break
          case err.TIMEOUT:
            error.value = 'Tiempo de espera agotado'
            break
          default:
            error.value = 'Error al obtener ubicación'
        }
      },
      {
        enableHighAccuracy: true,
        maximumAge: 5000,
        timeout: 10000,
      },
    )
  }

  function stopTracking(): void {
    if (watchId.value !== null) {
      navigator.geolocation.clearWatch(watchId.value)
      watchId.value = null
    }
    isTracking.value = false
  }

  function getCurrentPosition(): Promise<GeolocationPosition> {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'))
        return
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const p: GeolocationPosition = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            timestamp: pos.timestamp,
          }
          position.value = p
          resolve(p)
        },
        (err) => reject(err),
        { enableHighAccuracy: true, timeout: 10000 },
      )
    })
  }

  onUnmounted(() => {
    stopTracking()
  })

  return {
    position,
    isTracking,
    hasPosition,
    error,
    startTracking,
    stopTracking,
    getCurrentPosition,
  }
}

/**
 * Haversine distance between two lat/lng points in meters.
 */
export function haversineDistance(
  lat1: number, lng1: number,
  lat2: number, lng2: number,
): number {
  const R = 6371000 // Earth radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) *
    Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

/**
 * Find the nearest segment to a given position.
 * Uses the segment's geometry (LineString) to find the closest point.
 */
export function findNearestSegment(
  lat: number,
  lng: number,
  segments: Array<{ seq: number; geom?: { coordinates: number[][] } }>,
): { seq: number; distance: number } | null {
  let bestSeq: number | null = null
  let bestDist = Infinity

  for (const seg of segments) {
    if (!seg.geom?.coordinates) continue

    // Check distance to each point in the segment's LineString
    for (const coord of seg.geom.coordinates) {
      const [cLng, cLat] = coord // GeoJSON is [lng, lat]
      const dist = haversineDistance(lat, lng, cLat, cLng)
      if (dist < bestDist) {
        bestDist = dist
        bestSeq = seg.seq
      }
    }
  }

  return bestSeq !== null ? { seq: bestSeq, distance: bestDist } : null
}
