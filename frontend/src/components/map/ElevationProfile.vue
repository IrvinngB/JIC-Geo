<script setup lang="ts">
import { computed, ref } from 'vue'
import type { RouteAnalysis } from '@/stores/routeStore'

const props = defineProps<{
  analysis: RouteAnalysis | null
  selectedSeq: number | null
}>()

const emit = defineEmits<{
  selectSegment: [seq: number]
}>()

const hoveredSeq = ref<number | null>(null)
const tooltipX = ref(0)
const tooltipY = ref(0)

const SVG_WIDTH = 800
const SVG_HEIGHT = 180
const PADDING = { top: 10, right: 10, bottom: 25, left: 45 }

const profileData = computed(() => {
  if (!props.analysis?.segments) return []

  let cumDist = 0
  return props.analysis.segments.map((seg) => {
    const startDist = cumDist
    cumDist += (seg.length_m ?? 100) / 1000
    return {
      seq: seg.seq,
      distStart: startDist,
      distEnd: cumDist,
      elevStart: seg.elevation_start ?? 0,
      elevEnd: seg.elevation_end ?? 0,
      risk: seg.risk_score ?? 0,
      slope_pct: seg.slope_pct ?? 0,
    }
  })
})

const chartBounds = computed(() => {
  const data = profileData.value
  if (data.length === 0) return { minDist: 0, maxDist: 1, minElev: 0, maxElev: 100 }

  let minElev = Infinity, maxElev = -Infinity
  for (const d of data) {
    minElev = Math.min(minElev, d.elevStart, d.elevEnd)
    maxElev = Math.max(maxElev, d.elevStart, d.elevEnd)
  }

  const elevRange = maxElev - minElev || 100
  minElev -= elevRange * 0.1
  maxElev += elevRange * 0.1

  return {
    minDist: 0,
    maxDist: data[data.length - 1]?.distEnd ?? 1,
    minElev,
    maxElev,
  }
})

function toSvgX(dist: number): number {
  const b = chartBounds.value
  const plotW = SVG_WIDTH - PADDING.left - PADDING.right
  return PADDING.left + ((dist - b.minDist) / (b.maxDist - b.minDist)) * plotW
}

function toSvgY(elev: number): number {
  const b = chartBounds.value
  const plotH = SVG_HEIGHT - PADDING.top - PADDING.bottom
  return PADDING.top + plotH - ((elev - b.minElev) / (b.maxElev - b.minElev)) * plotH
}

// Generate individual segment paths (for colored rendering)
const segmentPaths = computed(() => {
  const data = profileData.value
  if (data.length === 0) return []

  const plotBottom = SVG_HEIGHT - PADDING.bottom

  return data.map((seg) => {
    // Area path for this segment
    const x1 = toSvgX(seg.distStart)
    const x2 = toSvgX(seg.distEnd)
    const y1 = toSvgY(seg.elevStart)
    const y2 = toSvgY(seg.elevEnd)

    const area = `M ${x1} ${plotBottom} L ${x1} ${y1} L ${x2} ${y2} L ${x2} ${plotBottom} Z`
    const line = `M ${x1} ${y1} L ${x2} ${y2}`

    return {
      seq: seg.seq,
      area,
      line,
      color: riskColor(seg.risk),
      distStart: seg.distStart,
      distEnd: seg.distEnd,
    }
  })
})

const selectedSeg = computed(() => {
  if (props.selectedSeq == null) return null
  return profileData.value.find(p => p.seq === props.selectedSeq) ?? null
})

const hoveredSeg = computed(() => {
  if (hoveredSeq.value == null) return null
  return profileData.value.find(p => p.seq === hoveredSeq.value) ?? null
})

const yTicks = computed(() => {
  const b = chartBounds.value
  const ticks = []
  const step = Math.ceil((b.maxElev - b.minElev) / 4 / 50) * 50
  let elev = Math.ceil(b.minElev / step) * step
  while (elev <= b.maxElev) {
    ticks.push(elev)
    elev += step
  }
  return ticks
})

const xTicks = computed(() => {
  const b = chartBounds.value
  const ticks = []
  const maxDist = b.maxDist
  const step = maxDist <= 5 ? 1 : maxDist <= 20 ? 2 : maxDist <= 50 ? 5 : 10
  for (let d = 0; d <= maxDist; d += step) {
    ticks.push(d)
  }
  return ticks
})

function riskColor(risk: number): string {
  if (risk >= 80) return '#a855f7'
  if (risk >= 60) return '#ef4444'
  if (risk >= 40) return '#f97316'
  if (risk >= 20) return '#eab308'
  return '#22c55e'
}

function riskColorFaded(risk: number): string {
  if (risk >= 80) return 'rgba(168,85,247,0.35)'
  if (risk >= 60) return 'rgba(239,68,68,0.35)'
  if (risk >= 40) return 'rgba(249,115,22,0.35)'
  if (risk >= 20) return 'rgba(234,179,8,0.35)'
  return 'rgba(34,197,94,0.35)'
}

// FIX: Scale mouse X from screen pixels to SVG viewBox coordinates
function getSvgX(event: MouseEvent): number {
  const svg = (event.target as SVGElement).closest('svg')
  if (!svg) return 0
  const rect = svg.getBoundingClientRect()
  const screenX = event.clientX - rect.left
  // Convert screen pixels → SVG viewBox units
  return (screenX / rect.width) * SVG_WIDTH
}

function onMouseMove(event: MouseEvent) {
  const svgX = getSvgX(event)
  const b = chartBounds.value
  const plotW = SVG_WIDTH - PADDING.left - PADDING.right
  const dist = b.minDist + ((svgX - PADDING.left) / plotW) * (b.maxDist - b.minDist)

  const data = profileData.value
  for (const seg of data) {
    if (dist >= seg.distStart && dist <= seg.distEnd) {
      hoveredSeq.value = seg.seq

      // Tooltip in screen coordinates
      const svg = (event.target as SVGElement).closest('svg')
      if (svg) {
        const rect = svg.getBoundingClientRect()
        tooltipX.value = event.clientX - rect.left
        tooltipY.value = event.clientY - rect.top
      }
      return
    }
  }
  hoveredSeq.value = null
}

function onMouseLeave() {
  hoveredSeq.value = null
}
</script>

<template>
  <div v-if="profileData.length > 0" class="relative w-full overflow-hidden">
    <svg
      :viewBox="`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`"
      class="w-full h-auto cursor-crosshair"
      preserveAspectRatio="xMidYMid meet"
      @mousemove="onMouseMove"
      @mouseleave="onMouseLeave"
      @click="hoveredSeq != null && emit('selectSegment', hoveredSeq)"
    >
      <!-- Y axis grid lines -->
      <g v-for="elev in yTicks" :key="'y' + elev">
        <line
          :x1="PADDING.left"
          :y1="toSvgY(elev)"
          :x2="SVG_WIDTH - PADDING.right"
          :y2="toSvgY(elev)"
          class="stroke-base-300"
          stroke-dasharray="3,3"
          stroke-width="0.5"
        />
        <text
          :x="PADDING.left - 5"
          :y="toSvgY(elev) + 3"
          text-anchor="end"
          class="fill-base-content/40"
          font-size="9"
        >{{ Math.round(elev) }}m</text>
      </g>

      <!-- X axis labels -->
      <g v-for="dist in xTicks" :key="'x' + dist">
        <text
          :x="toSvgX(dist)"
          :y="SVG_HEIGHT - 5"
          text-anchor="middle"
          class="fill-base-content/40"
          font-size="9"
        >{{ dist.toFixed(0) }}km</text>
      </g>

      <!-- Segment area fills (colored by risk) -->
      <path
        v-for="seg in segmentPaths"
        :key="'area-' + seg.seq"
        :d="seg.area"
        :fill="riskColorFaded(profileData.find(p => p.seq === seg.seq)?.risk ?? 0)"
      />

      <!-- Segment line strokes (colored by risk) -->
      <path
        v-for="seg in segmentPaths"
        :key="'line-' + seg.seq"
        :d="seg.line"
        fill="none"
        :stroke="seg.color"
        stroke-width="2"
        stroke-linejoin="round"
      />

      <!-- Hover segment highlight -->
      <rect
        v-if="hoveredSeg"
        :x="toSvgX(hoveredSeg.distStart)"
        :y="PADDING.top"
        :width="Math.max(2, toSvgX(hoveredSeg.distEnd) - toSvgX(hoveredSeg.distStart))"
        :height="SVG_HEIGHT - PADDING.top - PADDING.bottom"
        fill="white"
        opacity="0.15"
        rx="2"
      />

      <!-- Selected segment highlight -->
      <rect
        v-if="selectedSeg"
        :x="toSvgX(selectedSeg.distStart)"
        :y="PADDING.top"
        :width="Math.max(2, toSvgX(selectedSeg.distEnd) - toSvgX(selectedSeg.distStart))"
        :height="SVG_HEIGHT - PADDING.top - PADDING.bottom"
        fill="white"
        opacity="0.25"
        rx="2"
      />

      <!-- Selected segment marker dot -->
      <circle
        v-if="selectedSeg"
        :cx="toSvgX((selectedSeg.distStart + selectedSeg.distEnd) / 2)"
        :cy="toSvgY(selectedSeg.elevEnd)"
        r="4"
        :fill="riskColor(selectedSeg.risk)"
        stroke="white"
        stroke-width="2"
      />
    </svg>

    <!-- Tooltip -->
    <div
      v-if="hoveredSeq != null"
      class="pointer-events-none absolute z-10 rounded-lg border border-base-200 bg-base-100 px-2.5 py-1.5 text-[10px] shadow-md"
      :style="{ left: tooltipX + 'px', top: (tooltipY - 40) + 'px' }"
    >
      <span class="font-bold">Tramo #{{ hoveredSeq }}</span>
    </div>
  </div>
</template>
