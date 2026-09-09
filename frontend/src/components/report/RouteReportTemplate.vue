<script setup lang="ts">
/**
 * RouteReportTemplate — A4 two-page dossier for RiskTrail.
 * Page 1: Human-friendly summary. Page 2: Technical appendix.
 * Both pages inside one wrapper div so pdfExport paginates correctly.
 *
 * FIX (space usage): the previous version used `display: table` +
 * `height: '100%'` on children to make the "Autonomy + Climate" and
 * "Technical data" rows fill the remaining vertical space via
 * `flexGrow: 1` on the table. That combo silently fails — table cells
 * don't propagate percentage heights down reliably — so the outer box
 * grew but the cards inside stayed at content height, leaving dead
 * space at the bottom of the page. Replaced with CSS Grid +
 * `align-items: stretch`, which genuinely stretches grid children to
 * the row's real height. Also converted the recommendations list from
 * a single full-width column to a 2-column grid, since it was only
 * using ~40% of the available width per line.
 */

import type { RouteAnalysis } from '@/stores/routeStore'
import type { HikerProfile } from '@/composables/useHikerProfile'
import { computed } from 'vue'
import { formatDurationHours, formatNumber } from '@/utils/formatters'

const props = defineProps<{
  analysis: RouteAnalysis
  profile: HikerProfile
  generatedAt: Date
  hikerName?: string
  mapImageBase64?: string
}>()

// ── Design tokens ─────────────────────────────────────────────────────────────
const DS = {
  bg: '#F4F6F1',
  surface: '#FFFFFF',
  surfaceHigh: '#F5F9E9',
  fg: '#16241B',
  fgSoft: '#5B6B60',
  fgMuted: '#6B7A6E',
  border: '#E1E6DC',
  borderSubtle: '#EDF0E9',
  accent: '#6E8A1E',
  accentBg: '#EAF2C9',
  accentBorder: '#C9D98A',
  accentFill: '#A9C93E',
  ok: '#6E8A1E',
  okBg: '#F5F9E9',
  okBorder: '#C9D98A',
  warn: '#9A6400',
  warnBg: '#FBF0DA',
  warnBorder: '#EFC376',
  alert: '#B3261E',
  alertBg: '#FBE5E2',
  alertBorder: '#F2B4AE',
  info: '#2E6C7A',
  infoBg: '#E3F1F4',
  infoBorder: '#A5D3DC',
  appendixBg: '#E8EBE4',
}

// SVG icon paths (from AppIcon.vue / Lucide)
const ICONS = {
  mountain: 'm8 3 4 8 5-5 5 15H2L8 3z',
  thermometer: 'M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z',
  cloudRain: 'M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242 M16 14v6 M8 14v6 M12 16v6',
  sun: 'M12 2v2 M12 20v2 m4.93 4.93 1.41 1.41 m17.66 17.66 1.41 1.41 M2 12h2 M20 12h2 m6.34 17.66-1.41 1.41 m19.07 4.93-1.41 1.41',
  glasses: 'M10 13a1 1 0 0 1-1-1 4 4 0 0 0-8 0 1 1 0 0 1-1-1M23 13a1 1 0 0 1-1-1 4 4 0 0 0-8 0 1 1 0 0 1-1-1M7 13h2M15 13h2',
  droplets: 'M7 16.3c.7.7 1.7 1.2 2.7 1.2s2-.5 2.7-1.2c.8-.8 1.3-1.9 1.3-3.1 0-2.3-1.9-5.2-4-7.3-2.1 2.1-4 5-4 7.3 0 1.2.5 2.3 1.3 3.1Z',
  zap: 'M13 2 3 14h9l-1 8 10-12h-9l1-8z',
  activity: 'M22 12h-4l-3 9L9 3l-3 9H2',
  shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  wind: 'M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2 M9.6 4.6A2 2 0 1 1 11 8H2 M12.6 19.4A2 2 0 1 0 14 16H2',
  footprints: 'M4 16v-2.38C4 11.5 2.97 10.5 3 8c.03-2.72 1.49-6 4.5-6C9.37 2 10 3.8 10 5.5c0 3.11-2 5.66-2 8.68V16a2 2 0 1 1-4 0Z M20 20v-2.38c0-2.12 1.03-3.12 1-5.62-.03-2.72-1.49-6-4.5-6C14.63 6 14 7.8 14 9.5c0 3.11 2 5.66 2 8.68V20a2 2 0 1 0 4 0Z M16 17h4 M4 13h4',
  map: 'M3 7l6-3 6 3 6-3v13l-6 3-6-3-6 3V7z M9 4v13 M15 7v13',
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatDate(date: Date): string {
  return date.toLocaleString('es-MX', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const mideLabel = (n: number): string =>
  ({ 1: 'Fácil', 2: 'Moderado', 3: 'Exigente', 4: 'Difícil', 5: 'Muy Difícil' }[n] ?? String(n))

const fitnessLabel = (f: string): string =>
  ({ low: 'Baja', medium: 'Media', high: 'Alta', athlete: 'Atleta' }[f] ?? f)

const surfaceLabel = (s: string): string =>
  ({
    dirt: 'Tierra compactada', paved: 'Pavimento', gravel: 'Grava',
    mud: 'Barro', sand: 'Arena', scrub: 'Matorral', dense_scrub: 'Matorral denso',
  }[s] ?? s)

// ── Derived ───────────────────────────────────────────────────────────────────
const summary = computed(() => props.analysis.summary)
const mideGlobal = computed(() => summary.value.mide_global)

const difficultyPhrase = computed(() => {
  const m = mideGlobal.value
  if (m <= 1) return 'Ruta fácil, ideal para todo tipo de caminantes'
  if (m === 2) return 'Ruta moderada, apta para la mayoría con condición física media'
  if (m === 3) return 'Ruta exigente, recomendada para personas con experiencia'
  if (m === 4) return 'Ruta difícil, requiere buena condición física y experiencia técnica'
  return 'Ruta muy difícil, solo para caminantes experimentados con equipo completo'
})

const difficultyTonal = computed(() => {
  const m = mideGlobal.value
  if (m <= 2) return { bg: DS.okBg, border: DS.okBorder, text: DS.ok, dot: DS.accentFill }
  if (m === 3) return { bg: DS.warnBg, border: DS.warnBorder, text: DS.warn, dot: '#E8A020' }
  return { bg: DS.alertBg, border: DS.alertBorder, text: DS.alert, dot: DS.alert }
})

const hasClimate = computed(() => summary.value.wbgt != null)
const wbgtAlert = computed(() => (summary.value.wbgt ?? 0) >= 28)
const uvAlert = computed(() => (summary.value.uv_index ?? 0) >= 8)
const hasEccentricFatigue = computed(() => props.analysis.segments.some(s => s.is_eccentric_fatigue))
const hasOffPath = computed(() => props.analysis.segments.some(s => !s.is_on_path))
const isFatigueWithinRoute = computed(() => {
  const f = summary.value.time_to_severe_fatigue_h
  return f != null && f <= summary.value.estimated_time_h
})

const fatiguePhrase = computed(() => {
  const f = summary.value.time_to_severe_fatigue_h
  if (f == null) return null
  return isFatigueWithinRoute.value
    ? 'El cansancio fuerte puede aparecer antes de terminar. Dosificá el esfuerzo desde el inicio y planificá pausas.'
    : 'Tenés margen de sobra — la ruta termina bien antes de que llegues al límite.'
})

// Climate rows without emojis
const climateItems = computed(() => {
  if (!hasClimate.value) return []
  const temp = summary.value.temperature_c ?? 0
  const precip = summary.value.precip_mm ?? 0
  const uv = summary.value.uv_index ?? 0
  return [
    { iconPath: ICONS.thermometer, label: 'Temperatura', value: `${formatNumber(temp, 1)} °C`, flag: temp > 32 },
    { iconPath: ICONS.droplets, label: precip > 1 ? 'Lluvia prevista' : 'Sin lluvia', value: precip > 1 ? `${formatNumber(precip, 1)} mm` : 'Despejado', flag: precip > 5 },
    { iconPath: ICONS.sun, label: 'Índice UV', value: uv <= 2 ? 'Bajo' : uv <= 5 ? 'Moderado' : uv <= 7 ? 'Alto' : 'Muy alto', flag: uvAlert.value },
    ...(wbgtAlert.value ? [{ iconPath: ICONS.wind, label: 'Calor intenso', value: 'Hidratate más de lo normal', flag: true }] : []),
  ]
})

const recommendations = computed(() => {
  const recs: { text: string; type: 'ok' | 'warn' | 'alert' | 'info'; label: string; iconPath: string }[] = []
  const m = mideGlobal.value
  const f = summary.value.time_to_severe_fatigue_h
  const est = summary.value.estimated_time_h

  if (m >= 4)
    recs.push({ type: 'alert', label: 'Dificultad alta', iconPath: ICONS.shield, text: 'Llevá equipo de navegación y botiquín. No salgas solo.' })
  else if (m === 3)
    recs.push({ type: 'warn', label: 'Ritmo constante', iconPath: ICONS.footprints, text: 'Pausá 5–10 min cada hora. No empieces muy rápido.' })
  else
    recs.push({ type: 'ok', label: 'Ruta accesible', iconPath: ICONS.footprints, text: 'Apta para la mayoría. Calzado de senderismo y ropa cómoda son suficientes.' })

  if (f != null) {
    if (f <= est)
      recs.push({ type: 'alert', label: 'Esfuerzo intenso', iconPath: ICONS.zap, text: 'Salí descansado, mantené agua siempre a mano y reducí el ritmo si te falta el aire.' })
    else
      recs.push({ type: 'ok', label: 'Buena autonomía', iconPath: ICONS.zap, text: `Tenés energía de sobra para completar la ruta con tu perfil actual.` })
  }

  if (wbgtAlert.value)
    recs.push({ type: 'alert', label: 'Calor intenso', iconPath: ICONS.wind, text: 'Bebé al menos 750 mL de agua por hora. Salí temprano y evitá el mediodía.' })
  else
    recs.push({ type: 'info', label: 'Hidratación', iconPath: ICONS.droplets, text: 'Llevá al menos 500 mL de agua por cada 2 horas de caminata.' })

  if (uvAlert.value)
    recs.push({ type: 'warn', label: 'Sol fuerte', iconPath: ICONS.sun, text: 'Protector solar FPS 50+, gorra y gafas. El índice UV está muy alto.' })

  if (hasEccentricFatigue.value)
    recs.push({ type: 'warn', label: 'Bajadas largas', iconPath: ICONS.activity, text: 'Los bastones de trekking protegen las rodillas en las bajadas. Muy recomendados.' })

  if (hasOffPath.value)
    recs.push({ type: 'info', label: 'Tramos sin sendero', iconPath: ICONS.map, text: 'Parte de la ruta va por campo abierto. Revisá el GPS periódicamente.' })

  return recs
})

function recTagStyle(type: string) {
  if (type === 'alert') return { bg: DS.alertBg, text: DS.alert, border: DS.alertBorder }
  if (type === 'warn') return { bg: DS.warnBg, text: DS.warn, border: DS.warnBorder }
  if (type === 'info') return { bg: DS.infoBg, text: DS.info, border: DS.infoBorder }
  return { bg: DS.okBg, text: DS.ok, border: DS.okBorder }
}

const dimColor = (val: number): string =>
  val >= 4 ? DS.alert : val === 3 ? DS.warn : DS.accentFill

const cleanRouteName = computed(() =>
  ((props.analysis.route_name ?? '').trim() || 'Ruta sin nombre')
    .replace(/\s*-\s*(wikiloc|strava|garmin|alltrails|komoot).*$/i, '').trim()
)
</script>

<template>
  <!-- Outer wrapper: both pages stacked — pdfExport paginates by height -->
  <div style="width: 794px">

    <!-- ══════════════════════════════════════
         PÁGINA 1 — Vista para el usuario
    ══════════════════════════════════════════ -->
    <div
      :style="{
        width: '794px',
        height: '1123px',
        background: DS.bg,
        color: DS.fg,
        fontFamily: '\'Helvetica Neue\', Arial, sans-serif',
        fontSize: '10px',
        lineHeight: '1.5',
        padding: '32px 36px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
      }"
    >
      <!-- HEADER -->
      <div
        :style="{
          background: DS.surface, border: '1px solid ' + DS.border,
          borderRadius: '14px', padding: '14px 20px',
          display: 'grid', gridTemplateColumns: 'auto 1fr auto',
          alignItems: 'center', gap: '18px',
        }"
      >
        <div style="display: flex; align-items: center; gap: 6px; white-space: nowrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" :stroke="DS.accent" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path :d="ICONS.mountain"/>
          </svg>
          <span :style="{ fontSize: '15px', fontWeight: '800', color: DS.accent, letterSpacing: '-0.3px' }">RiskTrail</span>
        </div>
        <div>
          <div :style="{ fontSize: '13px', fontWeight: '700', color: DS.fg, lineHeight: '1.3' }">{{ cleanRouteName }}</div>
          <div :style="{ fontSize: '8px', color: DS.fgMuted, marginTop: '2px' }">
            {{ analysis.source_format.toUpperCase() }} · <span style="font-family: monospace">{{ analysis.route_id.slice(0, 10) }}</span>
          </div>
        </div>
        <div :style="{ textAlign: 'right', fontSize: '8.5px', color: DS.fgSoft }">
          {{ formatDate(generatedAt) }}
          <div v-if="hikerName" :style="{ marginTop: '2px' }">
            Para: <strong :style="{ color: DS.fg }">{{ hikerName }}</strong>
          </div>
        </div>
      </div>

      <!-- DIFFICULTY BANNER — large, prominent -->
      <div
        :style="{
          background: difficultyTonal.bg, border: '1px solid ' + difficultyTonal.border,
          borderRadius: '14px', padding: '18px 22px',
          display: 'grid', gridTemplateColumns: '56px 1fr auto',
          alignItems: 'center', gap: '4px 16px',
        }"
      >
        <!-- Dot with number -->
        <div
          :style="{
            width: '48px', height: '48px', borderRadius: '50%',
            background: difficultyTonal.dot,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }"
        >
          <span :style="{ fontSize: '22px', fontWeight: '900', color: '#FFFFFF', lineHeight: '1' }">{{ mideGlobal }}</span>
        </div>
        <!-- Phrase -->
        <div>
          <div :style="{ fontSize: '15px', fontWeight: '700', color: difficultyTonal.text, lineHeight: '1.3' }">
            {{ difficultyPhrase }}
          </div>
          <div :style="{ fontSize: '9px', color: DS.fgMuted, marginTop: '3px' }">
            Dificultad MIDE {{ mideGlobal }} de 5 · {{ mideLabel(mideGlobal) }}
          </div>
        </div>
        <!-- Profile pill -->
        <div style="text-align: right; white-space: nowrap">
          <div :style="{ fontSize: '8px', color: DS.fgMuted, marginBottom: '2px' }">Tu perfil</div>
          <div :style="{ fontSize: '9px', fontWeight: '700', color: DS.fg }">{{ fitnessLabel(profile.fitness_level) }} · {{ profile.weight_kg + profile.load_kg }} kg</div>
          <div :style="{ fontSize: '8px', color: DS.fgMuted, marginTop: '1px' }">{{ surfaceLabel(profile.surface_type) }}</div>
        </div>
      </div>

      <!-- 4 STAT CARDS -->
      <div :style="{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }">
        <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '20px 12px', textAlign: 'center' }">
          <div :style="{ fontSize: '34px', fontWeight: '800', color: DS.fg, lineHeight: '1.1' }">
            {{ formatNumber(summary.total_distance_km, 2) }}<span :style="{ fontSize: '13px', fontWeight: '700', color: DS.accent }"> km</span>
          </div>
          <div :style="{ fontSize: '8px', color: DS.fgMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '6px' }">Distancia total</div>
        </div>
        <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '20px 12px', textAlign: 'center' }">
          <div :style="{ fontSize: '30px', fontWeight: '800', color: DS.fg, lineHeight: '1.1' }">
            {{ formatDurationHours(summary.estimated_time_h) }}
          </div>
          <div :style="{ fontSize: '8.5px', color: DS.fgMuted, marginTop: '3px' }">en marcha</div>
          <div :style="{ fontSize: '8px', color: DS.fgMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '3px' }">Tiempo estimado</div>
        </div>
        <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '20px 12px', textAlign: 'center' }">
          <div :style="{ fontSize: '28px', fontWeight: '800', color: DS.fg, lineHeight: '1.1' }">
            +{{ formatNumber(summary.elevation_gain_m, 0) }}m
          </div>
          <div :style="{ fontSize: '13px', color: DS.fgMuted, fontWeight: '400', lineHeight: '1.2', marginTop: '2px' }">
            −{{ formatNumber(summary.elevation_loss_m, 0) }}m
          </div>
          <div :style="{ fontSize: '8px', color: DS.fgMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '4px' }">Desnivel</div>
        </div>
        <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '20px 12px', textAlign: 'center' }">
          <div :style="{ fontSize: '34px', fontWeight: '800', color: DS.fg, lineHeight: '1.1' }">
            {{ formatNumber(summary.total_kcal, 0) }}<span :style="{ fontSize: '13px', fontWeight: '700', color: DS.accent }"> kcal</span>
          </div>
          <div :style="{ fontSize: '8px', color: DS.fgMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '6px' }">Energía estimada</div>
        </div>
      </div>

      <!-- AUTONOMY + CLIMATE — grid with stretch so both cards match each
           other's height (based on content, not forced to fill the whole
           remaining page — that was making both cards balloon with dead
           space when there wasn't much to say). The footer below is
           pinned to the bottom of the page with margin-top: auto, so any
           leftover space becomes plain breathing room instead of an
           empty bordered box. -->
      <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', alignItems: 'stretch' }">
        <div
          v-if="fatiguePhrase"
          :style="{
            background: isFatigueWithinRoute ? DS.alertBg : DS.okBg,
            border: '1px solid ' + (isFatigueWithinRoute ? DS.alertBorder : DS.okBorder),
            borderRadius: '14px', padding: '18px 20px',
            display: 'flex', flexDirection: 'column',
          }"
        >
          <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" :stroke="isFatigueWithinRoute ? DS.alert : DS.ok" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path :d="ICONS.activity"/>
            </svg>
            <span :style="{ fontSize: '10px', fontWeight: '700', color: isFatigueWithinRoute ? DS.alert : DS.ok }">
              {{ isFatigueWithinRoute ? 'Esfuerzo alto para tu perfil' : 'Autonomía suficiente' }}
            </span>
          </div>
          <div :style="{ fontSize: '10px', color: DS.fg, lineHeight: '1.6' }">{{ fatiguePhrase }}</div>
          <!-- pushed to the bottom of the card so the card uses its full stretched height -->
          <div
            v-if="summary.time_to_severe_fatigue_h != null"
            :style="{
              fontSize: '8.5px', color: DS.fgMuted, marginTop: 'auto', paddingTop: '10px',
              borderTop: '1px solid ' + (isFatigueWithinRoute ? DS.alertBorder : DS.okBorder),
            }"
          >
            Duración de ruta: <strong>{{ formatDurationHours(summary.estimated_time_h) }}</strong>
            &nbsp;·&nbsp;
            Límite estimado: <strong>{{ formatDurationHours(summary.time_to_severe_fatigue_h) }}</strong>
          </div>
        </div>
        <div v-else :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '18px 20px' }">
          <div :style="{ fontSize: '9px', color: DS.fgMuted }">Sin datos de autonomía disponibles.</div>
        </div>

        <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '18px 20px', display: 'flex', flexDirection: 'column' }">
          <div :style="{ fontSize: '10px', fontWeight: '700', color: DS.fg, marginBottom: '12px' }">Condiciones del día</div>
          <template v-if="hasClimate">
            <div
              v-for="(item, i) in climateItems"
              :key="i"
              :style="{
                display: 'flex', alignItems: 'center', gap: '8px',
                padding: '9px 0',
                borderBottom: i < climateItems.length - 1 ? '1px solid ' + DS.borderSubtle : 'none',
              }"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" :stroke="item.flag ? DS.alert : DS.fgMuted" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path :d="item.iconPath"/>
              </svg>
              <span :style="{ fontSize: '9.5px', color: DS.fgMuted, flex: '1' }">{{ item.label }}</span>
              <strong :style="{ fontSize: '9.5px', color: item.flag ? DS.alert : DS.fg }">{{ item.value }}</strong>
            </div>
          </template>
          <div v-else :style="{ fontSize: '9px', color: DS.fgMuted }">Sin datos meteorológicos disponibles.</div>
        </div>
      </div>

      <!-- RECOMMENDATIONS — 2-column grid so it uses the full page width
           instead of one narrow full-width list -->
      <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '18px 22px' }">
        <div :style="{ fontSize: '10px', fontWeight: '700', color: DS.fg, marginBottom: '12px' }">
          Antes de salir — qué tener en cuenta
        </div>
        <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 20px' }">
          <div
            v-for="(rec, i) in recommendations"
            :key="i"
            :style="{ display: 'grid', gridTemplateColumns: 'auto 1fr', alignItems: 'start', gap: '10px' }"
          >
            <span
              :style="{
                display: 'inline-flex', alignItems: 'center',
                fontSize: '8px', fontWeight: '700',
                border: '1px solid ' + recTagStyle(rec.type).border,
                background: recTagStyle(rec.type).bg,
                color: recTagStyle(rec.type).text,
                borderRadius: '9999px', padding: '3px 10px',
                whiteSpace: 'nowrap', marginTop: '1px',
              }"
            >{{ rec.label }}</span>
            <div :style="{ fontSize: '9.5px', color: DS.fg, lineHeight: '1.55' }">{{ rec.text }}</div>
          </div>
        </div>
      </div>

      <!-- FOOTER PAGE 1 — pinned to the bottom of the fixed-height page -->
      <div
        :style="{
          background: DS.surface, border: '1px solid ' + DS.border,
          borderRadius: '14px', padding: '10px 18px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginTop: 'auto',
        }"
      >
        <div :style="{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '8.5px', color: DS.fgSoft }">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" :stroke="DS.accent" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path :d="ICONS.mountain"/>
          </svg>
          <strong :style="{ color: DS.fg }">RiskTrail</strong>
          <span>· Análisis biomecánico Minetti / Pandolf</span>
        </div>
        <div :style="{ fontSize: '8px', color: DS.fgSoft }">
          <span style="font-family: monospace">{{ analysis.route_id.slice(0, 12) }}</span>
          <span style="margin: 0 6px">·</span>
          <strong :style="{ color: DS.fg }">Página 1 / 2</strong>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════
         PÁGINA 2 — Apéndice técnico
    ══════════════════════════════════════════ -->
    <div
      :style="{
        width: '794px',
        height: '1123px',
        background: DS.appendixBg,
        color: DS.fg,
        fontFamily: '\'Helvetica Neue\', Arial, sans-serif',
        fontSize: '10px',
        lineHeight: '1.5',
        padding: '32px 36px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
      }"
    >
      <!-- Appendix header -->
      <div :style="{ background: DS.fg, borderRadius: '14px', padding: '16px 22px', display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center', flexShrink: '0' }">
        <div>
          <div :style="{ fontSize: '12px', fontWeight: '700', color: '#FFFFFF' }">Apéndice Técnico</div>
          <div :style="{ fontSize: '8.5px', color: 'rgba(255,255,255,0.45)', marginTop: '2px' }">
            {{ cleanRouteName }} · {{ formatDate(generatedAt) }}
          </div>
        </div>
        <span :style="{ fontSize: '8px', color: 'rgba(255,255,255,0.35)', fontStyle: 'italic' }">
          Motor Biomecánico Minetti / Pandolf
        </span>
      </div>

      <!-- MIDE DIMENSIONS -->
      <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '18px 22px', flexShrink: '0' }">
        <div :style="{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }">
          <div :style="{ fontSize: '11px', fontWeight: '700', color: DS.fg }">
            Diagnóstico MIDE — Escala de Dificultad de Montaña
          </div>
          <span :style="{ display: 'inline-block', fontSize: '9px', fontWeight: '700', color: DS.accent, border: '1px solid ' + DS.accentBorder, background: DS.surfaceHigh, borderRadius: '9999px', padding: '3px 12px' }">
            Nivel {{ mideGlobal }} de 5 · {{ mideLabel(mideGlobal) }}
          </span>
        </div>

        <div :style="{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', alignItems: 'stretch' }">
          <div
            v-for="dim in [
              { label: 'Severidad\ndel Medio', key: 'severity', val: summary.mide_dimensions.severity, desc: 'Exposición al entorno' },
              { label: 'Orientación\ny Navegación', key: 'orientation', val: summary.mide_dimensions.orientation, desc: 'Facilidad de seguir la ruta' },
              { label: 'Dificultad de\nDesplazamiento', key: 'displacement', val: summary.mide_dimensions.displacement, desc: 'Exigencia del terreno' },
              { label: 'Esfuerzo\nRequerido', key: 'effort', val: summary.mide_dimensions.effort, desc: 'Carga física total' },
            ]"
            :key="dim.key"
            :style="{ background: DS.appendixBg, border: '1px solid ' + DS.border, borderRadius: '12px', padding: '16px 12px', textAlign: 'center', display: 'flex', flexDirection: 'column' }"
          >
            <div :style="{ fontSize: '26px', fontWeight: '800', color: DS.fg }">
              {{ dim.val }}<span :style="{ fontSize: '13px', fontWeight: '400', color: DS.fgMuted }"> / 5</span>
            </div>
            <div :style="{ height: '3px', background: DS.border, margin: '8px auto', width: '70%', borderRadius: '9999px' }">
              <div :style="{ height: '3px', width: (dim.val / 5 * 100) + '%', background: dimColor(dim.val), borderRadius: '9999px' }" />
            </div>
            <div :style="{ fontSize: '8.5px', color: DS.fg, fontWeight: '600', whiteSpace: 'pre-wrap', lineHeight: '1.3' }">{{ dim.label }}</div>
            <div :style="{ fontSize: '7.5px', color: DS.fgMuted, fontStyle: 'italic', marginTop: 'auto', paddingTop: '4px' }">{{ dim.desc }}</div>
          </div>
        </div>
      </div>

      <!-- TECHNICAL DATA — same fix as page 1: stretch to match each
           other, size to content, don't force-fill the page. -->
      <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', alignItems: 'stretch', flexShrink: '0' }">
        <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '18px 20px', display: 'flex', flexDirection: 'column' }">
          <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }">
            <div
              :style="{
                width: '24px', height: '24px', borderRadius: '50%',
                background: DS.accentBg, border: '1px solid ' + DS.accentBorder,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: '0', lineHeight: '0',
              }"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" :stroke="DS.accent" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:block">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <span :style="{ fontSize: '10.5px', fontWeight: '700', color: DS.fg }">Análisis Biomecánico</span>
          </div>

          <div
            v-for="(row, i) in [
              { label: 'Tramos analizados', val: analysis.segments.length + ' segmentos', color: DS.fg },
              { label: 'Correcciones Savitzky-Golay', val: summary.points_corrected + ' puntos', color: DS.fg },
              { label: 'Confianza modelo Minetti', val: formatNumber(summary.high_confidence_segments_pct, 1) + '%', color: DS.accent },
              { label: 'Fatiga excéntrica', val: hasEccentricFatigue ? 'Detectada' : 'No detectada', color: hasEccentricFatigue ? DS.alert : DS.fg },
              { label: 'Tramos campo a través', val: hasOffPath ? 'Presentes' : 'No detectados', color: hasOffPath ? DS.warn : DS.fg },
            ]"
            :key="row.label"
            :style="{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '9px 0', fontSize: '9.5px',
              borderBottom: i < 4 ? '1px solid ' + DS.borderSubtle : 'none',
            }"
          >
            <span :style="{ color: DS.fgSoft }">{{ row.label }}</span>
            <strong :style="{ color: row.color, textAlign: 'right' }">{{ row.val }}</strong>
          </div>
        </div>

        <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '18px 20px', display: 'flex', flexDirection: 'column' }">
          <div :style="{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }">
            <div :style="{ display: 'flex', alignItems: 'center', gap: '8px' }">
              <div
                :style="{
                  width: '24px', height: '24px', borderRadius: '50%',
                  background: DS.accentBg, border: '1px solid ' + DS.accentBorder,
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: '0', lineHeight: '0',
                }"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" :stroke="DS.accent" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:block">
                  <circle cx="12" cy="12" r="4"/>
                  <path d="M12 2v2M12 20v2m-7.07-14.07 1.41 1.41m12.73 12.73 1.41 1.41M2 12h2m16 0h2m-4.93 7.07-1.41-1.41M6.34 6.34 4.93 4.93"/>
                </svg>
              </div>
              <span :style="{ fontSize: '10.5px', fontWeight: '700', color: DS.fg }">Meteorología</span>
            </div>
            <span v-if="hasClimate"
              :style="{
                fontSize: '8px', fontWeight: '700',
                color: summary.climate_source === 'api' ? DS.accent : DS.info,
                border: '1px solid ' + (summary.climate_source === 'api' ? DS.accentBorder : DS.infoBorder),
                background: summary.climate_source === 'api' ? DS.surfaceHigh : DS.infoBg,
                borderRadius: '9999px', padding: '2px 10px',
              }"
            >{{ summary.climate_source === 'api' ? 'Tiempo Real' : 'Simulación' }}</span>
          </div>

          <template v-if="hasClimate">
            <div
              v-for="(row, i) in [
                { label: 'Temperatura', val: formatNumber(summary.temperature_c ?? 0, 1) + ' °C', flag: false },
                { label: 'Humedad relativa', val: formatNumber(summary.humidity_pct ?? 0, 0) + '%', flag: false },
                { label: 'WBGT (Estrés Térmico)', val: formatNumber(summary.wbgt ?? 0, 1) + ' °C · ' + (wbgtAlert ? 'Alto' : 'OK'), flag: wbgtAlert },
                { label: 'Índice UV (valor numérico)', val: formatNumber(summary.uv_index ?? 0, 1) + ' · ' + (uvAlert ? 'Muy Alto' : 'Moderado'), flag: uvAlert },
                { label: 'Precipitación', val: formatNumber(summary.precip_mm ?? 0, 1) + ' mm', flag: false },
              ]"
              :key="row.label"
              :style="{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '9px 0', fontSize: '9.5px',
                borderBottom: i < 4 ? '1px solid ' + DS.borderSubtle : 'none',
              }"
            >
              <span :style="{ color: DS.fgSoft }">{{ row.label }}</span>
              <strong :style="{ color: row.flag ? DS.alert : DS.fg }">{{ row.val }}</strong>
            </div>
          </template>
          <div v-else :style="{ fontSize: '9px', color: DS.fgMuted, padding: '8px 0' }">Sin datos meteorológicos.</div>
        </div>
      </div>

      <!-- HIKER PROFILE TECHNICAL -->
      <div :style="{ background: DS.surface, border: '1px solid ' + DS.border, borderRadius: '14px', padding: '16px 22px', display: 'grid', gridTemplateColumns: 'auto 1fr', alignItems: 'center', flexShrink: '0' }">
        <div :style="{ fontSize: '9px', letterSpacing: '0.08em', textTransform: 'uppercase', color: DS.fgMuted }">
          Perfil del senderista
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 24px">
          <div
            v-for="item in [
              { label: 'Peso', value: profile.weight_kg + ' kg' },
              { label: 'Carga', value: profile.load_kg + ' kg' },
              { label: 'Total', value: (profile.weight_kg + profile.load_kg) + ' kg' },
              { label: 'Condición', value: fitnessLabel(profile.fitness_level) },
              { label: 'Superficie', value: surfaceLabel(profile.surface_type) },
            ]"
            :key="item.label"
          >
            <div :style="{ fontSize: '8px', color: DS.fgMuted }">{{ item.label }}</div>
            <div :style="{ fontSize: '10.5px', fontWeight: '700', color: DS.fg }">{{ item.value }}</div>
          </div>
        </div>
      </div>


      <!-- MAP SNAPSHOT — only shown when a capture is available -->
      <div
        v-if="mapImageBase64"
        :style="{
          background: DS.surface, border: '1px solid ' + DS.border,
          borderRadius: '14px', overflow: 'hidden',
          flexGrow: '1', minHeight: '0',
          display: 'flex', flexDirection: 'column',
        }"
      >
        <div :style="{ padding: '10px 18px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: '0' }">
          <span :style="{ fontSize: '9px', fontWeight: '700', letterSpacing: '0.06em', textTransform: 'uppercase', color: DS.fgMuted }">Vista de la ruta</span>
          <span :style="{ fontSize: '8px', color: DS.fgMuted, fontStyle: 'italic' }">© OpenStreetMap contributors</span>
        </div>
        <img
          :src="mapImageBase64"
          :style="{ width: '100%', height: '0', minHeight: '100%', objectFit: 'cover', objectPosition: 'center', display: 'block', flexShrink: '1' }"
          alt="Captura de la ruta en el mapa"
        />
      </div>

      <!-- FOOTER PAGE 2 — pinned to the bottom of the fixed-height page -->
      <div
        :style="{
          background: DS.surface, border: '1px solid ' + DS.border,
          borderRadius: '14px', padding: '10px 18px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginTop: 'auto',
        }"
      >
        <div :style="{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '8.5px', color: DS.fgSoft }">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" :stroke="DS.accent" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path :d="ICONS.mountain"/>
          </svg>
          <strong :style="{ color: DS.fg }">RiskTrail</strong>
          <span>· Apéndice Técnico · Motor Biomecánico Minetti / Pandolf</span>
        </div>
        <div :style="{ fontSize: '8px', color: DS.fgSoft }">
          <span style="font-family: monospace">{{ analysis.route_id.slice(0, 12) }}</span>
          <span style="margin: 0 6px">·</span>
          <strong :style="{ color: DS.fg }">Página 2 / 2</strong>
        </div>
      </div>
    </div>

  </div>
</template>