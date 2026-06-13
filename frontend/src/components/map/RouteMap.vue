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

onMounted(() => {
  if (!mapContainer.value) return

  map = new maplibregl.Map({
    container: mapContainer.value,
    center: [-79.5, 9.0],
    zoom: 9,
    pitch: terrainEnabled.value ? 60 : 0,
    bearing: terrainEnabled.value ? -25 : 0,
    style: buildMapStyle(currentBaseMap.value),
  })

  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
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
})

onBeforeUnmount(() => {
  map?.remove()
  map = null
})

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
          45,
          '#eab308',
          75,
          '#ef4444',
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
          'text-field': '⚠',
          'text-size': 16,
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

  const bounds = new maplibregl.LngLatBounds()
  for (const feature of data.features) {
    for (const coordinate of feature.geometry.coordinates) {
      bounds.extend([coordinate[0], coordinate[1]])
    }
  }

  if (!bounds.isEmpty()) {
    map.fitBounds(bounds, {
      // Asymmetric padding leaves room for the floating panels so the route
      // is never hidden behind them: extra space at the bottom (segment list)
      // and on the right (base-map control).
      padding: { top: 90, bottom: 280, left: 60, right: 90 },
      maxZoom: terrainEnabled.value ? 14 : 15,
      pitch: terrainEnabled.value ? 62 : 0,
      bearing: terrainEnabled.value ? -25 : 0,
      duration: 900,
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
    padding: 160,
    maxZoom: 16,
    duration: 800,
  })
}

function setBaseMap(baseMapId: BaseMapId): void {
  selectedBaseMap.value = baseMapId
}

function riskBadgeClass(score: number): string {
  if (score >= 75) return 'badge-error'
  if (score >= 45) return 'badge-warning'
  return 'badge-success'
}

function buildPopupHTML(segment: RouteAnalysis['segments'][number]): string {
  const dir = segment.direction === 'ascent' ? 'Subida' : segment.direction === 'descent' ? 'Bajada' : 'Plano'
  const badgeColor = segment.risk_score >= 75 ? '#ef4444' : segment.risk_score >= 45 ? '#f59e0b' : '#22c55e'
  const badgeBg = segment.risk_score >= 75 ? 'rgba(239,68,68,0.15)' : segment.risk_score >= 45 ? 'rgba(245,158,11,0.15)' : 'rgba(34,197,94,0.15)'
  const topRisk = segment.is_top_risk ? '<div style="color: #ef4444; font-size: 11px; font-weight: 600; margin-top: 6px;">⚠ Top 10% de riesgo</div>' : ''
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

    <div class="absolute right-4 top-16 z-10 w-64 rounded-box bg-base-100/95 p-3 shadow-xl backdrop-blur">
      <div class="mb-3 flex items-center justify-between gap-3">
        <div>
          <h3 class="text-sm font-bold">Mapa</h3>
          <p class="text-xs text-base-content/60">{{ currentBaseMap.description }}</p>
        </div>
        <label class="swap btn btn-ghost btn-sm">
          <input v-model="terrainEnabled" type="checkbox" />
          <span class="swap-off text-xs font-bold">2D</span>
          <span class="swap-on text-xs font-bold">3D</span>
        </label>
      </div>

      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="baseMap in BASE_MAPS"
          :key="baseMap.id"
          class="btn btn-xs"
          :class="baseMap.id === selectedBaseMap ? 'btn-primary text-white' : 'btn-ghost'"
          @click="setBaseMap(baseMap.id)"
        >
          {{ baseMap.label }}
        </button>
      </div>

      <button
        v-if="hasGeometries"
        class="btn btn-outline btn-xs mt-2 w-full"
        @click="recenterRoute"
      >
        Ver ruta completa
      </button>
    </div>

    <div class="pointer-events-none absolute inset-x-4 top-4 flex flex-col gap-3 md:inset-x-auto md:left-4 md:w-80">
      <div
        v-if="!props.analysis"
        class="rounded-2xl border border-base-300/60 bg-base-100/90 p-4 shadow-lg backdrop-blur"
      >
        <div class="flex items-start gap-3">
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary"
          >
            <AppIcon name="map" :size="20" />
          </span>
          <div>
            <h3 class="font-bold">Carga una ruta para empezar</h3>
            <p class="mt-1 text-xs text-base-content/70">
              Sube tu GPX o GeoJSON en el panel. El mapa mostrará el recorrido coloreado por riesgo
              en cuanto termine el análisis.
            </p>
          </div>
        </div>
      </div>

      <div v-else-if="!hasGeometries" class="alert alert-warning bg-base-100/90 shadow-lg backdrop-blur">
        <div>
          <h3 class="font-bold">Análisis listo</h3>
          <p class="text-xs text-base-content/70">
            No hay geometrías disponibles para dibujar la línea de ruta.
          </p>
        </div>
      </div>
    </div>

    <div
      v-if="props.analysis"
      class="absolute bottom-4 left-4 right-4 hidden max-h-64 overflow-y-auto rounded-box bg-base-100/95 p-3 shadow-xl backdrop-blur md:right-auto md:block md:w-96"
    >
      <div class="mb-2 flex items-center justify-between">
        <h3 class="text-sm font-bold">Segmentos</h3>
        <span class="badge badge-ghost">{{ props.analysis.segments.length }}</span>
      </div>
      <div class="space-y-2">
        <button
          v-for="segment in visibleSegments"
          :key="segment.seq"
          class="btn btn-ghost h-auto min-h-0 w-full justify-start p-2 text-left"
          :class="segment.seq === props.selectedSeq ? 'bg-primary/10' : ''"
          @click="emit('selectSegment', segment.seq)"
        >
          <div class="flex w-full items-center justify-between gap-3">
            <div>
              <p class="text-xs font-semibold">#{{ segment.seq }} · {{ segment.direction }}</p>
              <p class="text-xs text-base-content/60">
                {{ segment.velocity_kmh }} km/h · {{ segment.kcal }} kcal · S {{ segment.slope_pct }}
              </p>
            </div>
            <span class="badge badge-sm" :class="riskBadgeClass(segment.risk_score)">
              {{ segment.risk_score }}
            </span>
          </div>
        </button>
      </div>
    </div>

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
