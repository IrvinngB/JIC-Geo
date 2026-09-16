<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import maplibregl, { type StyleSpecification } from 'maplibre-gl'
import type { Feature, FeatureCollection, LineString, Point } from 'geojson'
import type { RouteAnalysis, RouteGraph } from '@/stores/routeStore'
import AppIcon from '@/components/icons/AppIcon.vue'

type BaseMapId = 'streets' | 'topo' | 'satellite'

interface BaseMapOption {
  id: BaseMapId
  label: string
  description: string
  attribution: string
  tiles: string[]
  maxZoom?: number
}

const BASE_MAPS: BaseMapOption[] = [
  {
    id: 'streets',
    label: 'Calles',
    description: 'OpenStreetMap estándar',
    attribution: '© OpenStreetMap contributors',
    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
    maxZoom: 19,
  },
  {
    id: 'topo',
    label: 'Topo',
    description: 'Relieve y curvas visuales',
    attribution: '© OpenStreetMap contributors, SRTM | OpenTopoMap',
    tiles: ['https://a.tile.opentopomap.org/{z}/{x}/{y}.png'],
    maxZoom: 17,
  },
  {
    id: 'satellite',
    label: 'Satélite',
    description: 'World Imagery',
    attribution: 'Tiles © Esri',
    tiles: [
      'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ],
    maxZoom: 19,
  },
]

const props = defineProps<{
  analysis: RouteAnalysis | null
  selectedSeq: number | null
  graph: RouteGraph | null
  routingActive: boolean
  routingStart: number | null
  routingEnd: number | null
  routingWaypoints: number[]
  optimalPathFeatures: FeatureCollection<LineString> | null
  hideSegments?: boolean
}>()

const emit = defineEmits<{
  selectSegment: [seq: number | null]
  toggleRoutingNode: [nodeId: number]
}>()

const mapContainer = ref<HTMLDivElement | null>(null)
const selectedBaseMap = ref<BaseMapId>('streets')
const terrainEnabled = ref(false)
let map: maplibregl.Map | null = null
let hasFitRoute = false
let activePopup: maplibregl.Popup | null = null

const currentBaseMap = computed(
  () => BASE_MAPS.find((baseMap) => baseMap.id === selectedBaseMap.value) ?? BASE_MAPS[0],
)

const hasGeometries = computed(
  () => props.analysis?.segments.some((segment) => Boolean(segment.geom)) ?? false,
)

const visibleSegments = computed(() => props.analysis?.segments ?? [])

const showEmptyPrompt = ref(true)
let emptyPromptTimer: ReturnType<typeof setTimeout> | null = null
let resizeObserver: ResizeObserver | null = null

// ── GPS Tracking ──
const gpsTracking = ref(false)
const gpsPosition = ref<{ lat: number; lng: number } | null>(null)
const gpsNearestSeq = ref<number | null>(null)
const gpsRiskScore = ref<number | null>(null)
let gpsWatchId: number | null = null
let gpsMarker: maplibregl.Marker | null = null

// GPS recording for saving track
const gpsRecordedPoints = ref<Array<{ lng: number; lat: number; alt: number }>>([])
let gpsTrackStartTime: number | null = null
let gpsTrackLine: maplibregl.GeoJSONSource | null = null

const gpsRiskColor = computed(() => {
  const s = gpsRiskScore.value ?? 0
  if (s >= 80) return 'bg-purple-500'
  if (s >= 60) return 'bg-red-500'
  if (s >= 40) return 'bg-orange-500'
  if (s >= 20) return 'bg-yellow-500'
  return 'bg-green-500'
})

const gpsRiskTextColor = computed(() => {
  const s = gpsRiskScore.value ?? 0
  if (s >= 80) return 'text-purple-600'
  if (s >= 60) return 'text-red-600'
  if (s >= 40) return 'text-orange-600'
  if (s >= 20) return 'text-yellow-600'
  return 'text-green-600'
})

const gpsMarkerStyle = computed(() => {
  // Not used — MapLibre marker handles positioning
  return {}
})

function haversineDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371000
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function findNearestSegment(lat: number, lng: number): number | null {
  if (!props.analysis?.segments) return null
  let bestSeq: number | null = null
  let bestDist = Infinity
  for (const seg of props.analysis.segments) {
    if (!seg.geom?.coordinates) continue
    for (const coord of seg.geom.coordinates) {
      const [cLng, cLat] = coord
      const dist = haversineDistance(lat, lng, cLat, cLng)
      if (dist < bestDist) {
        bestDist = dist
        bestSeq = seg.seq
      }
    }
  }
  // Only return if within 100m of the route
  return bestDist <= 100 ? bestSeq : null
}

function updateGpsPosition(pos: { lat: number; lng: number }) {
  gpsPosition.value = { lat: pos.lat, lng: pos.lng }

  // Record GPS point for track saving
  if (gpsTracking.value) {
    const point = { lng: pos.lng, lat: pos.lat, alt: 0 }
    gpsRecordedPoints.value.push(point)
    updateTrackLine()
  }

  if (map) {
    if (!gpsMarker) {
      const el = document.createElement('div')
      el.style.cssText = 'width:36px;height:36px;position:relative;'
      el.innerHTML = `
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Outer pulse ring -->
          <circle cx="18" cy="18" r="16" stroke="#22c55e" stroke-width="2" fill="none" opacity="0.3">
            <animate attributeName="r" values="12;16;12" dur="2s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="0.4;0.1;0.4" dur="2s" repeatCount="indefinite"/>
          </circle>
          <!-- Inner filled circle -->
          <circle cx="18" cy="18" r="8" fill="#22c55e" stroke="white" stroke-width="2.5"/>
          <!-- Center dot -->
          <circle cx="18" cy="18" r="2.5" fill="white"/>
        </svg>
      `
      gpsMarker = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([pos.lng, pos.lat])
        .addTo(map)
    } else {
      gpsMarker.setLngLat([pos.lng, pos.lat])
    }
  }

  const nearestSeq = findNearestSegment(pos.lat, pos.lng)
  gpsNearestSeq.value = nearestSeq

  const prevRisk = gpsRiskScore.value
  if (nearestSeq !== null) {
    const seg = props.analysis?.segments.find((s) => s.seq === nearestSeq)
    gpsRiskScore.value = seg?.risk_score ?? null
  } else {
    gpsRiskScore.value = null
  }

  // Alert on entering danger zone (risk >= 60)
  if (gpsRiskScore.value !== null && gpsRiskScore.value >= 60 && prevRisk !== gpsRiskScore.value) {
    triggerDangerAlert(gpsRiskScore.value)
  }
}

let lastAlertTime = 0
function triggerDangerAlert(risk: number) {
  // Vibration feedback (if supported)
  if (navigator.vibrate) {
    if (risk >= 80) {
      navigator.vibrate([200, 100, 200]) // Double pulse for extreme
    } else {
      navigator.vibrate(150) // Single pulse for high
    }
  }
  lastAlertTime = Date.now()
}

const gpsAlertActive = computed(() => {
  return gpsTracking.value && gpsRiskScore.value !== null && gpsRiskScore.value >= 60
})

const gpsAlertLevel = computed(() => {
  const s = gpsRiskScore.value ?? 0
  if (s >= 80) return 'extreme'
  return 'high'
})

function toggleGps() {
  if (gpsTracking.value) {
    stopGps()
  } else {
    startGps()
  }
}

function startGps() {
  if (!navigator.geolocation) return
  gpsTracking.value = true
  gpsRecordedPoints.value = []
  gpsTrackStartTime = Date.now()
  gpsWatchId = navigator.geolocation.watchPosition(
    (pos) =>
      updateGpsPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
    () => {
      gpsTracking.value = false
    },
    { enableHighAccuracy: true, maximumAge: 3000, timeout: 10000 },
  )
}

function stopGps() {
  if (gpsWatchId !== null) {
    navigator.geolocation.clearWatch(gpsWatchId)
    gpsWatchId = null
  }
  gpsTracking.value = false
  gpsPosition.value = null
  gpsNearestSeq.value = null
  gpsRiskScore.value = null
  if (gpsMarker) {
    gpsMarker.remove()
    gpsMarker = null
  }
}

function updateTrackLine() {
  if (!map || gpsRecordedPoints.value.length < 2) return

  const coords = gpsRecordedPoints.value.map(p => [p.lng, p.lat])
  const geojson = { type: 'FeatureCollection' as const, features: [{ type: 'Feature' as const, geometry: { type: 'LineString' as const, coordinates: coords }, properties: {} }] }

  if (!gpsTrackLine) {
    map.addSource('gps-track', { type: 'geojson', data: geojson })
    map.addLayer({
      id: 'gps-track-line',
      type: 'line',
      source: 'gps-track',
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#22c55e', 'line-width': 3, 'line-opacity': 0.8 },
    })
  } else {
    gpsTrackLine.setData(geojson)
  }
}

function getRecordedTrack(): Array<{ lng: number; lat: number; alt: number }> {
  return [...gpsRecordedPoints.value]
}

function getTrackDuration(): number {
  if (!gpsTrackStartTime) return 0
  return Math.round((Date.now() - gpsTrackStartTime) / 1000)
}

onMounted(() => {
  if (!mapContainer.value) return

  // Auto-dismiss prompt banner after 10s on mobile (<768px)
  if (typeof window !== 'undefined' && window.innerWidth < 768) {
    emptyPromptTimer = setTimeout(() => {
      showEmptyPrompt.value = false
    }, 10000)
  }

  map = new maplibregl.Map({
    container: mapContainer.value,
    center: [-79.5, 9.0],
    zoom: 9,
    pitch: terrainEnabled.value ? 60 : 0,
    bearing: terrainEnabled.value ? -25 : 0,
    style: buildMapStyle(currentBaseMap.value),
    preserveDrawingBuffer: true,
  })

  map.on('load', () => {
    applyTerrainMode()
    renderRouteLayer()
    renderRoutingLayers()
  })

  // Click on empty map closes any open popup
  map.on('click', (event) => {
    if (!event.defaultPrevented) {
      activePopup?.remove()
      activePopup = null
    }
  })

  // Watch for container size changes to resize map canvas reliably
  if (typeof ResizeObserver !== 'undefined' && mapContainer.value) {
    resizeObserver = new ResizeObserver(() => {
      map?.resize()
    })
    resizeObserver.observe(mapContainer.value)
  }
})

onBeforeUnmount(() => {
  stopGps()
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (emptyPromptTimer) {
    clearTimeout(emptyPromptTimer)
    emptyPromptTimer = null
  }
  map?.remove()
  map = null
})

/** Captures the current map view as a compressed JPEG data URL. */
function captureImage(): string | null {
  if (!map) return null
  try {
    const src = map.getCanvas()
    // Limit capture size to reduce PDF weight
    const maxW = 1200
    const scale = Math.min(1, maxW / src.width)
    if (scale >= 1) return src.toDataURL('image/jpeg', 0.6)
    const tmp = document.createElement('canvas')
    tmp.width = Math.round(src.width * scale)
    tmp.height = Math.round(src.height * scale)
    const ctx = tmp.getContext('2d')
    if (!ctx) return src.toDataURL('image/jpeg', 0.6)
    ctx.drawImage(src, 0, 0, tmp.width, tmp.height)
    return tmp.toDataURL('image/jpeg', 0.6)
  } catch {
    return null
  }
}

defineExpose({ captureImage, getRecordedTrack, getTrackDuration })

watch(
  () => props.analysis,
  () => {
    hasFitRoute = false
    renderRouteLayer()
  },
  { deep: true },
)

watch(
  () => props.selectedSeq,
  (seq) => {
    renderRouteLayer()
    flyToSegment(seq)
  },
)

watch(selectedBaseMap, () => {
  if (!map) return
  map.setStyle(buildMapStyle(currentBaseMap.value))
  map.once('style.load', () => {
    applyTerrainMode()
    renderRouteLayer()
    renderRoutingLayers()
  })
})

watch(terrainEnabled, () => {
  applyTerrainMode()
})

watch(
  () => props.graph,
  () => renderRoutingLayers(),
)

watch(
  () => [props.routingStart, props.routingEnd, props.routingWaypoints],
  () => renderRoutingLayers(),
  { deep: true },
)

watch(
  () => props.optimalPathFeatures,
  () => renderRoutingLayers(),
)

watch(
  () => props.routingActive,
  () => setRoutingVisibility(),
)

function buildMapStyle(baseMap: BaseMapOption): StyleSpecification {
  return {
    version: 8,
    glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
    sources: {
      'base-raster': {
        type: 'raster',
        tiles: baseMap.tiles,
        tileSize: 256,
        maxzoom: baseMap.maxZoom ?? 19,
        attribution: baseMap.attribution,
      },
      'terrain-dem': {
        type: 'raster-dem',
        tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
        tileSize: 256,
        encoding: 'terrarium',
        maxzoom: 15,
        attribution: 'Elevation tiles © Mapzen / AWS',
      },
    },
    layers: [
      {
        id: 'base-raster',
        type: 'raster',
        source: 'base-raster',
      },
      {
        id: 'terrain-hillshade',
        type: 'hillshade',
        source: 'terrain-dem',
        layout: {
          visibility: baseMap.id === 'satellite' ? 'none' : 'visible',
        },
        paint: {
          'hillshade-exaggeration': 0.25,
          'hillshade-shadow-color': '#334155',
          'hillshade-highlight-color': '#ffffff',
          'hillshade-accent-color': '#64748b',
        },
      },
    ],
  }
}

function applyTerrainMode(): void {
  if (!map?.loaded()) return

  if (terrainEnabled.value) {
    map.setTerrain({ source: 'terrain-dem', exaggeration: 1.35 })
    map.easeTo({ pitch: 62, bearing: -25, duration: 700 })
  } else {
    map.setTerrain(null)
    map.easeTo({ pitch: 0, bearing: 0, duration: 700 })
  }
}

function buildFeatureCollection(): FeatureCollection<LineString> {
  const hasSelection = props.selectedSeq !== null

  const features: Array<Feature<LineString>> =
    props.analysis?.segments
      .filter((segment) => segment.geom)
      .map((segment) => ({
        type: 'Feature',
        properties: {
          seq: segment.seq,
          risk_score: segment.risk_score,
          selected: segment.seq === props.selectedSeq,
          // Dimmed when there IS a selection and this is not the chosen one.
          // No selection => nothing dimmed, whole route stays at full opacity.
          dimmed: hasSelection && segment.seq !== props.selectedSeq,
        },
        geometry: segment.geom as LineString,
      })) ?? []

  return {
    type: 'FeatureCollection',
    features,
  }
}

function buildTopRiskFeatureCollection(): FeatureCollection<Point> {
  const features: Array<Feature<Point>> =
    props.analysis?.segments
      .filter((segment) => segment.is_top_risk && segment.geom)
      .map((segment) => {
        const coords = segment.geom!.coordinates
        const mid = coords[Math.floor(coords.length / 2)]
        return {
          type: 'Feature',
          properties: { seq: segment.seq },
          geometry: { type: 'Point', coordinates: [mid[0], mid[1]] },
        }
      }) ?? []
  return { type: 'FeatureCollection', features }
}

function renderRouteLayer(): void {
  // isStyleLoaded() guards what we actually need (style present to add
  // layers), without waiting for raster tiles like loaded() does. After a
  // base-map switch, loaded() can stay false while tiles download, which
  // previously left the route unpainted on some base maps.
  if (!map?.isStyleLoaded()) return

  const data = buildFeatureCollection()
  const source = map.getSource('route-segments') as maplibregl.GeoJSONSource | undefined

  if (source) {
    source.setData(data)
  } else {
    map.addSource('route-segments', {
      type: 'geojson',
      data,
    })

    // Casing: a dark, slightly wider line under the colored one. It gives the
    // route a consistent outline so it reads clearly over any base map
    // (streets, topo, satellite) instead of blending into the background.
    map.addLayer({
      id: 'route-segments-casing',
      type: 'line',
      source: 'route-segments',
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-width': ['case', ['boolean', ['get', 'selected'], false], 11, 7],
        'line-color': '#0f172a',
        'line-opacity': ['case', ['boolean', ['get', 'dimmed'], false], 0.15, 0.65],
      },
    })

    map.addLayer({
      id: 'route-segments-line',
      type: 'line',
      source: 'route-segments',
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-width': ['case', ['boolean', ['get', 'selected'], false], 7, 4.5],
        // Spotlight: dim the rest of the route when a segment is selected so
        // the chosen one (full opacity + thicker) stands out by contrast.
        'line-opacity': ['case', ['boolean', ['get', 'dimmed'], false], 0.2, 0.95],
        'line-color': [
          'interpolate',
          ['linear'],
          ['get', 'risk_score'],
          0,
          '#22c55e',
          20,
          '#eab308',
          40,
          '#f97316',
          60,
          '#ef4444',
          80,
          '#a855f7',
        ],
      },
    })

    map.on('click', 'route-segments-line', (event) => {
      const seq = event.features?.[0]?.properties?.seq
      const parsedSeq = typeof seq === 'number' ? seq : Number(seq)
      emit('selectSegment', parsedSeq)

      // MAP-02: show MapLibre popup at segment centroid
      const segment = props.analysis?.segments.find((s) => s.seq === parsedSeq)
      if (segment?.geom) {
        activePopup?.remove()
        const coords = segment.geom.coordinates
        const mid = coords[Math.floor(coords.length / 2)]
        const html = buildPopupHTML(segment)
        activePopup = new maplibregl.Popup({ closeButton: false, offset: 12, className: 'segment-popup' })
          .setLngLat([mid[0], mid[1]])
          .setHTML(html)
          .addTo(map!)
      }
    })

    // Add risk warning symbols (MAP-09) — top 10% segments
    const topRiskFeatures = buildTopRiskFeatureCollection()
    const topRiskSource = map.getSource('risk-warnings') as maplibregl.GeoJSONSource | undefined
    if (topRiskSource) {
      topRiskSource.setData(topRiskFeatures)
    } else {
      map.addSource('risk-warnings', { type: 'geojson', data: topRiskFeatures })
      map.addLayer({
        id: 'risk-warnings-symbols',
        type: 'symbol',
        source: 'risk-warnings',
        layout: {
          'text-field': '!',
          'text-size': 16,
          'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
          'text-anchor': 'center',
          'text-offset': [0, -0.8],
        },
        paint: {
          'text-color': '#ef4444',
          'text-halo-color': '#ffffff',
          'text-halo-width': 2,
        },
      })
    }
  }

  if (!hasFitRoute) {
    fitToFeatures(data)
    hasFitRoute = data.features.length > 0
  }
}

function fitToFeatures(data: FeatureCollection<LineString>): void {
  if (!map || data.features.length === 0) return

  map.resize()

  const bounds = new maplibregl.LngLatBounds()
  for (const feature of data.features) {
    for (const coordinate of feature.geometry.coordinates) {
      bounds.extend([coordinate[0], coordinate[1]])
    }
  }

  if (!bounds.isEmpty()) {
    const isMobile = window.innerWidth < 640
    const padding = props.hideSegments
      ? (isMobile ? { top: 25, bottom: 25, left: 20, right: 20 } : { top: 40, bottom: 40, left: 40, right: 40 })
      : (isMobile ? { top: 30, bottom: 90, left: 20, right: 20 } : { top: 50, bottom: 50, left: 60, right: 60 })

    map.fitBounds(bounds, {
      padding,
      maxZoom: 16,
      pitch: terrainEnabled.value ? 55 : 0,
      bearing: terrainEnabled.value ? -20 : 0,
      duration: 800,
    })
  }
}

function recenterRoute(): void {
  const data = buildFeatureCollection()
  if (data.features.length === 0) return
  hasFitRoute = false
  fitToFeatures(data)
  hasFitRoute = true
}

function routingNodeRole(nodeId: number): 'start' | 'end' | 'waypoint' | 'idle' {
  if (nodeId === props.routingStart) return 'start'
  if (nodeId === props.routingEnd) return 'end'
  if (props.routingWaypoints.includes(nodeId)) return 'waypoint'
  return 'idle'
}

function buildGraphNodesFeatureCollection(): FeatureCollection<Point> {
  const features: Array<Feature<Point>> =
    props.graph?.nodes.map((node) => ({
      type: 'Feature',
      properties: {
        id: node.id,
        role: routingNodeRole(node.id),
      },
      geometry: {
        type: 'Point',
        coordinates: [node.lon, node.lat],
      },
    })) ?? []

  return { type: 'FeatureCollection', features }
}

function renderRoutingLayers(): void {
  if (!map?.isStyleLoaded()) return

  const nodesData = buildGraphNodesFeatureCollection()
  const nodesSource = map.getSource('routing-nodes') as maplibregl.GeoJSONSource | undefined

  if (nodesSource) {
    nodesSource.setData(nodesData)
  } else {
    map.addSource('routing-nodes', { type: 'geojson', data: nodesData })

    map.addLayer({
      id: 'routing-nodes-circle',
      type: 'circle',
      source: 'routing-nodes',
      layout: {
        visibility: props.routingActive ? 'visible' : 'none',
      },
      paint: {
        'circle-radius': ['match', ['get', 'role'], 'start', 9, 'end', 9, 'waypoint', 7, 5],
        'circle-color': [
          'match',
          ['get', 'role'],
          'start',
          '#22c55e',
          'end',
          '#ef4444',
          'waypoint',
          '#3b82f6',
          '#94a3b8',
        ],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
      },
    })

    map.on('click', 'routing-nodes-circle', (event) => {
      const id = event.features?.[0]?.properties?.id
      emit('toggleRoutingNode', typeof id === 'number' ? id : Number(id))
    })
  }

  const pathData: FeatureCollection<LineString> =
    props.optimalPathFeatures ?? { type: 'FeatureCollection', features: [] }
  const pathSource = map.getSource('optimal-path') as maplibregl.GeoJSONSource | undefined

  if (pathSource) {
    pathSource.setData(pathData)
  } else {
    map.addSource('optimal-path', { type: 'geojson', data: pathData })

    map.addLayer({
      id: 'optimal-path-line',
      type: 'line',
      source: 'optimal-path',
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
        visibility: props.routingActive ? 'visible' : 'none',
      },
      paint: {
        'line-width': 6,
        'line-color': '#a855f7',
        'line-dasharray': [0.2, 1.5],
      },
    })
  }

  setRoutingVisibility()
}

function setRoutingVisibility(): void {
  if (!map?.isStyleLoaded()) return

  const visibility = props.routingActive ? 'visible' : 'none'
  if (map.getLayer('routing-nodes-circle')) {
    map.setLayoutProperty('routing-nodes-circle', 'visibility', visibility)
  }
  if (map.getLayer('optimal-path-line')) {
    map.setLayoutProperty('optimal-path-line', 'visibility', visibility)
  }
}

function flyToSegment(seq: number | null): void {
  if (!map || seq === null) return

  const segment = props.analysis?.segments.find((item) => item.seq === seq)
  if (!segment?.geom) return

  const bounds = new maplibregl.LngLatBounds()
  for (const coordinate of segment.geom.coordinates) {
    bounds.extend([coordinate[0], coordinate[1]])
  }
  if (bounds.isEmpty()) return

  map.fitBounds(bounds, {
    padding: window.innerWidth < 640 ? 80 : 160,
    maxZoom: 16,
    duration: 800,
  })
}

function setBaseMap(baseMapId: BaseMapId): void {
  selectedBaseMap.value = baseMapId
}

function riskBadgeClass(score: number): string {
  if (score >= 80) return 'badge-secondary'
  if (score >= 60) return 'badge-error'
  if (score >= 40) return 'badge-warning'
  if (score >= 20) return 'badge-warning badge-outline'
  return 'badge-success'
}

function buildPopupHTML(segment: RouteAnalysis['segments'][number]): string {
  const dir = segment.direction === 'ascent' ? 'Subida' : segment.direction === 'descent' ? 'Bajada' : 'Plano'
  const badgeColor = segment.risk_score >= 80 ? '#a855f7' : segment.risk_score >= 60 ? '#ef4444' : segment.risk_score >= 40 ? '#f97316' : segment.risk_score >= 20 ? '#eab308' : '#22c55e'
  const badgeBg = segment.risk_score >= 80 ? 'rgba(168,85,247,0.15)' : segment.risk_score >= 60 ? 'rgba(239,68,68,0.15)' : segment.risk_score >= 40 ? 'rgba(249,115,22,0.15)' : segment.risk_score >= 20 ? 'rgba(234,179,8,0.15)' : 'rgba(34,197,94,0.15)'
  const topRisk = segment.is_top_risk
    ? '<div style="color: #ef4444; font-size: 11px; font-weight: 600; margin-top: 6px; display: flex; align-items: center; gap: 4px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>Top 10% de riesgo</div>'
    : ''
  const ecc = segment.is_eccentric_fatigue ? '<div style="color: #ef4444; font-size: 10px; margin-top: 4px;">Bajada fatigante</div>' : ''
  return `
    <div style="font-family: ui-sans-serif, system-ui, sans-serif; font-size: 13px; min-width: 200px; color: #e2e8f0;">
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px;">
        <strong style="font-size: 14px; color: #f1f5f9;">Tramo #${segment.seq}</strong>
        <span style="font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; color: ${badgeColor}; background: ${badgeBg};">${segment.risk_score}/100</span>
      </div>
      <div style="font-size: 12px; color: #94a3b8; line-height: 1.5;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
          <span>${dir}</span>
          <span style="font-weight: 500; color: #cbd5e1;">${segment.slope_pct}%</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
          <span>Velocidad</span>
          <span style="font-weight: 500; color: #cbd5e1;">${segment.velocity_kmh} km/h</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span>CoT</span>
          <span style="font-weight: 500; color: #cbd5e1;">${segment.cot_j_per_kg_m} J/kg·m</span>
        </div>
      </div>
      ${topRisk}${ecc}
    </div>
  `
}
</script>

<template>
  <section class="relative h-full w-full bg-base-300">
    <div ref="mapContainer" class="h-full w-full"></div>

    <!-- Danger Alert Banner -->
    <Transition
      enter-active-class="transition-all duration-400 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
      leave-active-class="transition-all duration-200 ease-[cubic-bezier(0.36,0,0.66,-0.56)]"
      enter-from-class="-translate-y-full opacity-0 scale-95"
      leave-to-class="-translate-y-full opacity-0 scale-95"
    >
      <div
        v-if="gpsAlertActive"
        class="absolute left-0 right-0 top-0 z-30 flex items-center justify-center gap-3 px-4 py-3 shadow-lg"
        :class="gpsAlertLevel === 'extreme'
          ? 'bg-gradient-to-r from-red-600 to-purple-600 text-white'
          : 'bg-gradient-to-r from-orange-500 to-red-500 text-white'"
      >
        <AppIcon name="alert-triangle" :size="20" />
        <span class="text-sm font-bold">
          {{ gpsAlertLevel === 'extreme'
            ? '⚠ RIESGO EXTREMO — Tramo #' + gpsNearestSeq
            : '⚠ ZONA PELIGROSA — Tramo #' + gpsNearestSeq
          }}
        </span>
        <span class="text-xs opacity-80">Riesgo {{ gpsRiskScore }}/100</span>
      </div>
    </Transition>

    <!-- ═══ MAP CONTROLS — Floating, minimal ═══ -->

    <!-- Top-right: Map style pill -->
    <div class="absolute right-3 top-3 z-10 sm:right-4">
      <div class="flex items-center gap-1 rounded-full border border-base-200 bg-base-100/90 p-1 shadow-lg backdrop-blur">
        <button
          v-for="baseMap in BASE_MAPS"
          :key="baseMap.id"
          class="rounded-full px-3 py-1.5 text-[11px] font-semibold transition-all duration-200"
          :class="baseMap.id === selectedBaseMap
            ? 'bg-emerald-600 text-white shadow-sm'
            : 'text-base-content/50 hover:text-base-content hover:bg-base-200/60'"
          @click="setBaseMap(baseMap.id)"
        >
          {{ baseMap.label }}
        </button>
        <div class="mx-0.5 h-4 w-px bg-base-300"></div>
        <label class="swap btn btn-ghost btn-xs btn-circle h-7 w-7 min-h-0">
          <input v-model="terrainEnabled" type="checkbox" />
          <span class="swap-off text-[10px] font-bold">2D</span>
          <span class="swap-on text-[10px] font-bold">3D</span>
        </label>
      </div>
    </div>

    <!-- Top-right below map style: Recenter button -->
    <button
      v-if="hasGeometries"
      class="absolute right-3 top-14 z-10 flex h-8 items-center gap-1.5 rounded-full border border-base-200 bg-base-100/90 px-3 text-[11px] font-semibold text-base-content/60 shadow-lg backdrop-blur transition-all hover:bg-base-100 hover:text-base-content sm:right-4 sm:top-14"
      @click="recenterRoute"
    >
      <AppIcon name="route" :size="12" />
      <span class="hidden sm:inline">Ver ruta</span>
    </button>

    <!-- Left side: GPS button -->
    <div class="absolute left-3 top-3 z-10 flex flex-col gap-2 sm:left-4">
      <!-- GPS toggle -->
      <button
        class="flex h-10 w-10 items-center justify-center rounded-full border shadow-lg backdrop-blur transition-all duration-300"
        :class="gpsTracking
          ? 'border-emerald-400/40 bg-emerald-500/90 text-white shadow-emerald-500/20 hover:bg-emerald-500'
          : 'border-base-200 bg-base-100/90 text-base-content/60 hover:bg-base-100 hover:text-base-content'"
        :title="gpsTracking ? 'Detener seguimiento' : '¿Dónde estoy?'"
        @click="toggleGps"
      >
        <AppIcon :name="gpsTracking ? 'compass' : 'map'" :size="18" />
      </button>

      <!-- GPS Risk badge (when tracking) -->
      <Transition
        enter-active-class="transition-all duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
        leave-active-class="transition-all duration-200 ease-in"
        enter-from-class="opacity-0 scale-90 -translate-y-2"
        leave-to-class="opacity-0 scale-90 -translate-y-2"
      >
        <div
          v-if="gpsTracking && gpsRiskScore !== null"
          class="flex items-center gap-2 rounded-full border border-base-200 bg-base-100/90 px-3 py-1.5 shadow-lg backdrop-blur"
        >
          <div class="h-2.5 w-2.5 rounded-full" :class="gpsRiskColor"></div>
          <span class="text-xs font-bold" :class="gpsRiskTextColor">{{ gpsRiskScore }}</span>
        </div>
      </Transition>
    </div>

    <!-- Bottom: Segment strip (mobile: horizontal, desktop: panel) -->
    <div
      v-if="props.analysis && !props.hideSegments"
      class="absolute bottom-3 left-3 right-3 z-10 sm:bottom-4 sm:left-4 sm:right-auto sm:w-80"
    >
      <!-- Mobile: compact pill strip -->
      <div class="flex items-center gap-2 rounded-2xl border border-base-200 bg-base-100/90 p-2 shadow-xl backdrop-blur sm:hidden">
        <span class="shrink-0 pl-1 text-[10px] font-bold text-base-content/40">{{ props.analysis.segments.length }}</span>
        <div class="flex gap-1 overflow-x-auto scrollbar-none">
          <button
            v-for="segment in visibleSegments"
            :key="segment.seq"
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[9px] font-bold transition-all"
            :class="segment.seq === props.selectedSeq
              ? 'bg-emerald-600 text-white shadow-sm'
              : 'bg-base-200/60 text-base-content/50 hover:bg-base-200'"
            @click="emit('selectSegment', segment.seq)"
          >
            {{ segment.seq }}
          </button>
        </div>
      </div>

      <!-- Desktop: compact panel -->
      <div class="hidden sm:block rounded-2xl border border-base-200 bg-base-100/90 p-3 shadow-xl backdrop-blur">
        <div class="mb-2 flex items-center justify-between">
          <span class="text-xs font-bold text-base-content/50">Segmentos</span>
          <span class="text-[10px] text-base-content/30">{{ props.analysis.segments.length }}</span>
        </div>
        <div class="max-h-40 space-y-1 overflow-y-auto pr-1">
          <button
            v-for="segment in visibleSegments"
            :key="segment.seq"
            class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-all"
            :class="segment.seq === props.selectedSeq
              ? 'bg-emerald-50 ring-1 ring-emerald-200'
              : 'hover:bg-base-200/40'"
            @click="emit('selectSegment', segment.seq)"
          >
            <span
              class="h-2 w-2 shrink-0 rounded-full"
              :class="segment.risk_score >= 80 ? 'bg-purple-500' : segment.risk_score >= 60 ? 'bg-red-500' : segment.risk_score >= 40 ? 'bg-orange-500' : segment.risk_score >= 20 ? 'bg-yellow-500' : 'bg-emerald-500'"
            ></span>
            <span class="flex-1 text-[11px] font-medium text-base-content/70">
              #{{ segment.seq }}
              <span class="text-base-content/30">· {{ segment.direction }}</span>
            </span>
            <span class="text-[10px] font-bold text-base-content/40">{{ segment.risk_score }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state prompt -->
    <Transition
      enter-active-class="transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
      leave-active-class="transition-all duration-300 ease-in"
      enter-from-class="opacity-0 translate-y-4"
      leave-to-class="opacity-0 translate-y-4"
    >
      <div
        v-if="!props.analysis && showEmptyPrompt"
        class="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2"
      >
        <div class="flex items-center gap-3 rounded-2xl border border-base-200 bg-base-100/90 px-5 py-3.5 shadow-xl backdrop-blur">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600">
            <AppIcon name="map" :size="20" />
          </div>
          <div>
            <p class="text-sm font-bold text-base-content">Subí tu ruta GPX o GeoJSON</p>
            <p class="text-[11px] text-base-content/40">Arrastrá el archivo o usá el panel lateral</p>
          </div>
          <button
            class="ml-2 btn btn-ghost btn-circle btn-xs text-base-content/30 hover:text-base-content"
            @click="showEmptyPrompt = false"
          >
            <AppIcon name="x" :size="14" />
          </button>
        </div>
      </div>
    </Transition>
  </section>
</template>

<style scoped>
/* Dark themed popup styling */
:deep(.maplibregl-popup-content) {
  background: #1e293b !important;
  border: 1px solid #334155 !important;
  border-radius: 12px !important;
  padding: 12px !important;
  box-shadow: 0 10px 25px rgba(0,0,0,0.4) !important;
}
:deep(.maplibregl-popup-tip) {
  border-top-color: #1e293b !important;
}
</style>
