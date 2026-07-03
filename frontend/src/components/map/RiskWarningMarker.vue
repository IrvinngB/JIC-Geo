<script setup lang="ts">
import { computed, inject, onMounted, onBeforeUnmount, watch } from 'vue'
import type maplibregl from 'maplibre-gl'
import type { Segment } from '@/stores/routeStore'

const props = defineProps<{
  segments: Segment[]
}>()

const map = inject<maplibregl.Map | null>('map', null)

const topRiskSegments = computed(() => props.segments.filter((s) => s.is_top_risk && s.geom))

function buildWarningFeatures() {
  const features = topRiskSegments.value.map((segment) => {
    const coords = segment.geom!.coordinates
    const midIndex = Math.floor(coords.length / 2)
    const [lon, lat] = coords[midIndex]
    return {
      type: 'Feature' as const,
      properties: {
        seq: segment.seq,
        risk_score: segment.risk_score,
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [lon, lat],
      },
    }
  })
  return { type: 'FeatureCollection' as const, features }
}

function renderLayer() {
  if (!map) return

  const data = buildWarningFeatures()
  const source = map.getSource('risk-warnings') as maplibregl.GeoJSONSource | undefined

  if (source) {
    source.setData(data)
  } else {
    map.addSource('risk-warnings', { type: 'geojson', data })
    map.addLayer({
      id: 'risk-warnings-symbols',
      type: 'symbol',
      source: 'risk-warnings',
      layout: {
        'text-field': '⚠',
        'text-size': 18,
        'text-anchor': 'center',
        'text-offset': [0, -0.5],
      },
      paint: {
        'text-color': '#ef4444',
        'text-halo-color': '#ffffff',
        'text-halo-width': 2,
      },
    })
  }
}

function removeLayer() {
  if (!map) return
  if (map.getLayer('risk-warnings-symbols')) {
    map.removeLayer('risk-warnings-symbols')
  }
  if (map.getSource('risk-warnings')) {
    map.removeSource('risk-warnings')
  }
}

onMounted(() => {
  if (map?.loaded()) {
    renderLayer()
  } else {
    map?.once('load', renderLayer)
  }
})

onBeforeUnmount(() => {
  removeLayer()
})

watch(() => props.segments, renderLayer, { deep: true })
</script>

<template>
  <!-- This component has no visual template; it manages a MapLibre layer. -->
</template>
