<script setup lang="ts">
import { computed, ref } from 'vue'
import type { RouteAnalysis } from '@/stores/routeStore'

const props = defineProps<{
  analysis: RouteAnalysis | null
  selectedSeq: number | null
}>()

const emit = defineEmits<{
  selectSegment: [seq: number | null]
}>()

const hoveredSeq = ref<number | null>(null)
const hoverDist = ref<number | null>(null)
const hoverElev = ref<number | null>(null)

const SVG_WIDTH = 800
const SVG_HEIGHT = 200
const PADDING = { top: 15, right: 15, bottom: 30, left: 50 }

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
      slope: seg.slope_pct ?? 0,
      velocity: seg.velocity_kmh ?? 0,
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
  const range = maxElev - minElev || 100
  return { minDist: 0, maxDist: data[data.length - 1]?.distEnd ?? 1, minElev: minElev - range * 0.1, maxElev: maxElev + range * 0.1 }
})

function toX(dist: number): number {
  const b = chartBounds.value
  return PADDING.left + ((dist - b.minDist) / (b.maxDist - b.minDist)) * (SVG_WIDTH - PADDING.left - PADDING.right)
}

function toY(elev: number): number {
  const b = chartBounds.value
  return PADDING.top + (SVG_HEIGHT - PADDING.top - PADDING.bottom) - ((elev - b.minElev) / (b.maxElev - b.minElev)) * (SVG_HEIGHT - PADDING.top - PADDING.bottom)
}

// Smooth area path (single continuous curve)
const areaPath = computed(() => {
  const data = profileData.value
  if (data.length === 0) return ''
  const bottom = SVG_HEIGHT - PADDING.bottom
  let d = `M ${toX(data[0].distStart)} ${bottom}`
  for (const seg of data) {
    d += ` L ${toX(seg.distStart)} ${toY(seg.elevStart)}`
    d += ` L ${toX(seg.distEnd)} ${toY(seg.elevEnd)}`
  }
  d += ` L ${toX(data[data.length - 1].distEnd)} ${bottom} Z`
  return d
})

// Smooth line path
const linePath = computed(() => {
  const data = profileData.value
  if (data.length === 0) return ''
  let d = `M ${toX(data[0].distStart)} ${toY(data[0].elevStart)}`
  for (const seg of data) {
    d += ` L ${toX(seg.distEnd)} ${toY(seg.elevEnd)}`
  }
  return d
})

// Risk-colored segments for the line
const segmentLines = computed(() => {
  return profileData.value.map(seg => ({
    seq: seg.seq,
    d: `M ${toX(seg.distStart)} ${toY(seg.elevStart)} L ${toX(seg.distEnd)} ${toY(seg.elevEnd)}`,
    color: riskColor(seg.risk),
  }))
})

// Min/Max elevation points
const elevExtremes = computed(() => {
  const data = profileData.value
  if (data.length === 0) return null
  let minElev = Infinity, maxElev = -Infinity
  let minPt = data[0], maxPt = data[0]
  for (const seg of data) {
    if (seg.elevStart < minElev) { minElev = seg.elevStart; minPt = seg }
    if (seg.elevEnd > maxElev) { maxElev = seg.elevEnd; maxPt = seg }
  }
  return {
    min: { x: toX(minPt.distStart), y: toY(minElev), elev: minElev },
    max: { x: toX(maxPt.distEnd), y: toY(maxElev), elev: maxElev },
  }
})

const yTicks = computed(() => {
  const b = chartBounds.value
  const ticks = []
  const step = Math.ceil((b.maxElev - b.minElev) / 4 / 25) * 25
  let elev = Math.ceil(b.minElev / step) * step
  while (elev <= b.maxElev) { ticks.push(elev); elev += step }
  return ticks
})

const xTicks = computed(() => {
  const b = chartBounds.value
  const ticks = []
  const step = b.maxDist <= 5 ? 1 : b.maxDist <= 20 ? 2 : b.maxDist <= 50 ? 5 : 10
  for (let d = 0; d <= b.maxDist; d += step) ticks.push(d)
  return ticks
})

function riskColor(risk: number): string {
  if (risk >= 80) return '#a855f7'
  if (risk >= 60) return '#ef4444'
  if (risk >= 40) return '#f97316'
  if (risk >= 20) return '#eab308'
  return '#22c55e'
}

function riskLabel(risk: number): string {
  if (risk >= 80) return 'Extremo'
  if (risk >= 60) return 'Alto'
  if (risk >= 40) return 'Medio'
  if (risk >= 20) return 'Moderado'
  return 'Bajo'
}

function getSvgX(event: MouseEvent): number {
  const svg = (event.target as SVGElement).closest('svg')
  if (!svg) return 0
  return ((event.clientX - svg.getBoundingClientRect().left) / svg.getBoundingClientRect().width) * SVG_WIDTH
}

function onMouseMove(event: MouseEvent) {
  const svgX = getSvgX(event)
  const b = chartBounds.value
  const dist = b.minDist + ((svgX - PADDING.left) / (SVG_WIDTH - PADDING.left - PADDING.right)) * (b.maxDist - b.minDist)

  // Find segment and interpolate elevation
  for (const seg of profileData.value) {
    if (dist >= seg.distStart && dist <= seg.distEnd) {
      hoveredSeq.value = seg.seq
      hoverDist.value = dist
      // Linear interpolation
      const t = (dist - seg.distStart) / (seg.distEnd - seg.distStart || 1)
      hoverElev.value = seg.elevStart + t * (seg.elevEnd - seg.elevStart)
      return
    }
  }
  hoveredSeq.value = null
  hoverDist.value = null
  hoverElev.value = null
}

function onMouseLeave() {
  hoveredSeq.value = null
  hoverDist.value = null
  hoverElev.value = null
}
</script>

<template>
  <div v-if="profileData.length > 0" class="relative w-full">
    <svg
      :viewBox="`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`"
      class="w-full h-auto cursor-crosshair"
      preserveAspectRatio="xMidYMid meet"
      @mousemove="onMouseMove"
      @mouseleave="onMouseLeave"
      @click="hoveredSeq != null && emit('selectSegment', hoveredSeq === props.selectedSeq ? null : hoveredSeq)"
    >
      <defs>
        <!-- Area gradient -->
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#22c55e" stop-opacity="0.25" />
          <stop offset="100%" stop-color="#22c55e" stop-opacity="0.02" />
        </linearGradient>
        <!-- Clip path for area -->
        <clipPath id="areaClip">
          <rect :x="PADDING.left" :y="PADDING.top" :width="SVG_WIDTH - PADDING.left - PADDING.right" :height="SVG_HEIGHT - PADDING.top - PADDING.bottom" />
        </clipPath>
      </defs>

      <!-- Y axis grid -->
      <g v-for="elev in yTicks" :key="'y' + elev">
        <line :x1="PADDING.left" :y1="toY(elev)" :x2="SVG_WIDTH - PADDING.right" :y2="toY(elev)" stroke="currentColor" class="text-base-content/5" stroke-width="1" />
        <text :x="PADDING.left - 6" :y="toY(elev) + 3" text-anchor="end" class="fill-base-content/30" font-size="9" font-family="system-ui">{{ Math.round(elev) }}m</text>
      </g>

      <!-- X axis labels -->
      <g v-for="dist in xTicks" :key="'x' + dist">
        <text :x="toX(dist)" :y="SVG_HEIGHT - 8" text-anchor="middle" class="fill-base-content/30" font-size="9" font-family="system-ui">{{ dist.toFixed(0) }}km</text>
      </g>

      <!-- Area fill (smooth gradient) -->
      <path :d="areaPath" fill="url(#areaGrad)" clip-path="url(#areaClip)" />

      <!-- Risk-colored line segments -->
      <path
        v-for="seg in segmentLines"
        :key="'line-' + seg.seq"
        :d="seg.d"
        fill="none"
        :stroke="seg.color"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="transition-opacity duration-150"
        :opacity="hoveredSeq != null && hoveredSeq !== seg.seq ? 0.3 : 1"
      />

      <!-- Hover crosshair -->
      <g v-if="hoverDist != null && hoverElev != null">
        <line :x1="toX(hoverDist)" :y1="PADDING.top" :x2="toX(hoverDist)" :y2="SVG_HEIGHT - PADDING.bottom" stroke="currentColor" class="text-base-content/15" stroke-width="1" stroke-dasharray="4,4" />
        <line :x1="PADDING.left" :y1="toY(hoverElev)" :x2="SVG_WIDTH - PADDING.right" :y2="toY(hoverElev)" stroke="currentColor" class="text-base-content/15" stroke-width="1" stroke-dasharray="4,4" />
        <circle :cx="toX(hoverDist)" :cy="toY(hoverElev)" r="5" fill="#22c55e" stroke="white" stroke-width="2" />
      </g>

      <!-- Min/Max markers -->
      <g v-if="elevExtremes">
        <!-- Max -->
        <circle :cx="elevExtremes.max.x" :cy="elevExtremes.max.y" r="3.5" fill="#ef4444" stroke="white" stroke-width="1.5" />
        <text :x="elevExtremes.max.x" :y="elevExtremes.max.y - 8" text-anchor="middle" class="fill-red-500" font-size="8" font-weight="600" font-family="system-ui">{{ Math.round(elevExtremes.max.elev) }}m</text>
        <!-- Min -->
        <circle :cx="elevExtremes.min.x" :cy="elevExtremes.min.y" r="3.5" fill="#22c55e" stroke="white" stroke-width="1.5" />
        <text :x="elevExtremes.min.x" :y="elevExtremes.min.y + 14" text-anchor="middle" class="fill-emerald-500" font-size="8" font-weight="600" font-family="system-ui">{{ Math.round(elevExtremes.min.elev) }}m</text>
      </g>
    </svg>

    <!-- Floating tooltip -->
    <Transition
      enter-active-class="transition-all duration-150 ease-out"
      leave-active-class="transition-all duration-100 ease-in"
      enter-from-class="opacity-0 scale-95"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="hoveredSeq != null && hoverElev != null"
        class="pointer-events-none absolute z-10 rounded-xl border border-base-200 bg-base-100/95 px-3 py-2 shadow-lg backdrop-blur-sm"
        :style="{
          left: Math.min(Math.max((hoverDist ?? 0) / (chartBounds.maxDist) * 100, 10), 80) + '%',
          top: '8px',
          transform: 'translateX(-50%)',
        }"
      >
        <div class="flex items-center gap-2">
          <span class="h-2 w-2 rounded-full" :style="{ background: riskColor(profileData.find(p => p.seq === hoveredSeq)?.risk ?? 0) }"></span>
          <span class="text-[11px] font-bold text-base-content">Tramo #{{ hoveredSeq }}</span>
          <span class="text-[10px] text-base-content/40">·</span>
          <span class="text-[10px] font-medium text-base-content/60">{{ Math.round(hoverElev) }}m</span>
        </div>
        <div class="mt-0.5 flex gap-3 text-[9px] text-base-content/40">
          <span>{{ riskLabel(profileData.find(p => p.seq === hoveredSeq)?.risk ?? 0) }}</span>
          <span>{{ profileData.find(p => p.seq === hoveredSeq)?.slope?.toFixed(1) }}%</span>
          <span>{{ profileData.find(p => p.seq === hoveredSeq)?.velocity?.toFixed(1) }} km/h</span>
        </div>
      </div>
    </Transition>
  </div>
</template>
