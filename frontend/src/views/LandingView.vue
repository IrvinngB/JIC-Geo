<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/authStore'
import AppIcon, { type IconName } from '@/components/icons/AppIcon.vue'

const { currentTheme, toggleTheme } = useTheme()
const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/')
}

// ── Data ──────────────────────────────────────────

const painPoints: Array<{ icon: IconName; title: string; text: string }> = [
  { icon: 'map', title: 'Mapas estáticos', text: 'Solo muestran distancia y elevación, ignorando el estado del terreno.' },
  { icon: 'sun', title: 'Clima ignorado', text: 'Un sendero "moderado" en sol puede ser peligroso bajo lluvia tropical.' },
  { icon: 'thermometer', title: 'Humedad extrema', text: 'Drena tu energía sin advertencia, aumentando el riesgo de agotamiento.' },
  { icon: 'alert-triangle', title: 'Descensos peligrosos', text: 'Bajar una loma mojada es más riesgoso que subirla: resbalones y caídas.' },
]

const features: Array<{ icon: IconName; title: string; description: string }> = [
  { icon: 'compass', title: 'Índice MIDE dinámico', description: 'Severidad, orientación y esfuerzo calculados tramo a tramo con modelos biomecánicos reales.' },
  { icon: 'cloud-rain', title: 'Simulación climática', description: 'Compara la ruta en seco, lluvia o calor extremo. El clima ajusta el riesgo en vivo.' },
  { icon: 'route', title: 'Ruta óptima', description: 'El motor encuentra el camino de menor costo considerando pendiente, superficie, clima y tu perfil.' },
]

const steps = [
  { number: '01', title: 'Sube tu ruta', description: 'GPX o GeoJSON. Interpolamos elevación y corregimos puntos sueltos.' },
  { number: '02', title: 'Analizamos el esfuerzo', description: 'Velocidad, calorías, fatiga y riesgo por cada tramo del recorrido.' },
  { number: '03', title: 'Simula condiciones', description: 'Cambia el clima y observa cómo cambia el riesgo y el tiempo estimado.' },
  { number: '04', title: 'Encuentra el mejor camino', description: 'La ruta óptima evita los tramos más costosos según tu perfil.' },
]

const differentiators: Array<{ icon: IconName; title: string; description: string }> = [
  { icon: 'brain', title: 'Motor biomecánico real', description: 'Costo metabólico con fórmulas científicas, no suposiciones.' },
  { icon: 'wind', title: 'WBGT en vivo', description: 'Estrés térmico con temperatura, humedad y radiación solar.' },
  { icon: 'shield', title: 'Alertas de fatiga', description: 'Detecta cuándo alcanzarás agotamiento severo.' },
  { icon: 'footprints', title: 'Corrección GPS', description: 'Savitzky-Golay suaviza errores de elevación.' },
]

const impactMetrics = [
  { value: '40%', label: 'Menos accidentes', description: 'Reducción potencial de resbalones en descensos mojados.' },
  { value: 'Real', label: 'Biomecánica', description: 'Modelos científicos, no estimaciones de fitness apps.' },
  { value: 'Vivo', label: 'Clima en tiempo real', description: 'Datos meteorológicos cruzados con cada tramo.' },
]

const techStack = [
  { category: 'Backend', items: ['Python', 'FastAPI', 'PostgreSQL', 'pgRouting', 'PostGIS'] },
  { category: 'Frontend', items: ['Vue 3', 'TypeScript', 'MapLibre GL', 'Tailwind CSS', 'DaisyUI'] },
]

const authors = [
  { name: 'Irvin Benitez', role: 'Full Stack & Arquitectura', github: 'https://github.com/IrvinngB', portfolio: 'https://irvincodes.dev/', linkedin: 'https://www.linkedin.com/in/irvin-benitez-11313231b', avatar: 'https://avatars.githubusercontent.com/u/157191495' },
  { name: 'Kelvin He Wu', role: 'Backend', github: 'https://github.com/kelvinhe04', portfolio: 'https://kelvin-he.netlify.app/', linkedin: 'https://www.linkedin.com/in/kelvin-he-wu/?locale=es', avatar: 'https://avatars.githubusercontent.com/u/91310516' },
  { name: 'Roy Barrera', role: 'Backend & Database', github: 'https://github.com/Roy-x24', linkedin: 'https://www.linkedin.com/in/roy-barrera-0077b1340/', avatar: 'https://ui-avatars.com/api/?name=Roy+Barrera&background=random' },
]

// ── Scroll reveal ─────────────────────────────────

const heroVisible = ref(false)
const sectionsVisible = ref<Set<string>>(new Set())

onMounted(() => {
  requestAnimationFrame(() => { heroVisible.value = true })

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          sectionsVisible.value.add(entry.target.id)
        }
      })
    },
    { threshold: 0.15 }
  )

  document.querySelectorAll('[data-reveal]').forEach((el) => observer.observe(el))
})
</script>

<template>
  <div class="landing">

    <!-- ═══════════════════════════════════════════════
         NAVBAR — Minimal, translucent
         ═══════════════════════════════════════════════ -->
    <header class="nav">
      <div class="nav__inner">
        <!-- Logo -->
        <RouterLink to="/" class="nav__logo">
          <div class="nav__logo-icon">
            <AppIcon name="footprints" :size="18" />
          </div>
          <span class="nav__logo-text">RiskTrail</span>
        </RouterLink>

        <!-- Desktop nav -->
        <nav class="nav__links">
          <a href="#problema" class="nav__link">Problema</a>
          <a href="#como-funciona" class="nav__link">Cómo funciona</a>
          <a href="#equipo" class="nav__link">Equipo</a>
          <button class="nav__theme" :title="currentTheme === 'jic-dark' ? 'Modo claro' : 'Modo oscuro'" @click="toggleTheme">
            <AppIcon :name="currentTheme === 'jic-dark' ? 'sun' : 'moon'" :size="16" />
          </button>
          <template v-if="auth.isAuthenticated">
            <span class="nav__user">{{ auth.user?.name }}</span>
            <RouterLink to="/mapa" class="nav__cta">Abrir app</RouterLink>
            <button class="nav__ghost" @click="handleLogout">Salir</button>
          </template>
          <template v-else>
            <RouterLink to="/login" class="nav__ghost">Iniciar sesión</RouterLink>
            <RouterLink to="/register" class="nav__cta">Registrarse</RouterLink>
          </template>
        </nav>

        <!-- Mobile nav -->
        <div class="nav__mobile">
          <button class="nav__theme" @click="toggleTheme">
            <AppIcon :name="currentTheme === 'jic-dark' ? 'sun' : 'moon'" :size="16" />
          </button>
          <RouterLink v-if="auth.isAuthenticated" to="/mapa" class="nav__cta">Abrir app</RouterLink>
          <RouterLink v-else to="/login" class="nav__cta">Iniciar sesión</RouterLink>
        </div>
      </div>
    </header>

    <!-- ═══════════════════════════════════════════════
         HERO — One strong statement
         ═══════════════════════════════════════════════ -->
    <section class="hero" :class="{ 'hero--visible': heroVisible }">
      <div class="hero__bg" aria-hidden="true">
        <div class="hero__orb hero__orb--1" />
        <div class="hero__orb hero__orb--2" />
      </div>

      <div class="hero__content">
        <div class="hero__badge">
          <span class="hero__badge-dot" />
          Análisis biomecánico de senderos
        </div>

        <h1 class="hero__title">
          Conoce el riesgo
          <span class="hero__title-accent">antes de caminarlo</span>
        </h1>

        <p class="hero__sub">
          Los mapas tradicionales ignoran un punto ciego:
          <strong>cómo el entorno afecta tu cuerpo.</strong>
          Un sendero "moderado" puede ser letal tras un aguacero tropical.
        </p>

        <div class="hero__actions">
          <RouterLink to="/mapa" class="btn-primary-lg">
            <span>Analizar mi ruta</span>
            <AppIcon name="arrow-right" :size="18" />
          </RouterLink>
          <a href="#como-funciona" class="btn-ghost-lg">Cómo funciona</a>
        </div>

        <div class="hero__tags">
          <span class="hero__tag"><span class="hero__tag-dot hero__tag-dot--green" /> MIDE dinámico</span>
          <span class="hero__tag"><span class="hero__tag-dot hero__tag-dot--blue" /> Clima en vivo</span>
          <span class="hero__tag"><span class="hero__tag-dot hero__tag-dot--teal" /> Ruta óptima</span>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         PROBLEM
         ═══════════════════════════════════════════════ -->
    <section id="problema" class="section section--alt" data-reveal>
      <div class="section__inner">
        <div class="section__header">
          <h2 class="section__title">El problema</h2>
          <p class="section__sub">Los mapas tradicionales ignoran cómo el entorno transforma tu cuerpo en tiempo real.</p>
        </div>

        <div class="grid-2">
          <div v-for="point in painPoints" :key="point.title" class="card card--pain">
            <div class="card__icon card__icon--red">
              <AppIcon :name="point.icon" :size="18" />
            </div>
            <div>
              <h3 class="card__title">{{ point.title }}</h3>
              <p class="card__text">{{ point.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         SOLUTION
         ═══════════════════════════════════════════════ -->
    <section class="section" data-reveal>
      <div class="section__inner">
        <div class="section__header">
          <h2 class="section__title">La solución</h2>
          <p class="section__sub">Un sistema que transforma mapas estáticos en herramientas de seguridad vivas.</p>
        </div>

        <div class="grid-3">
          <article v-for="feature in features" :key="feature.title" class="card card--feature">
            <div class="card__icon card__icon--green">
              <AppIcon :name="feature.icon" :size="20" />
            </div>
            <h3 class="card__title">{{ feature.title }}</h3>
            <p class="card__text">{{ feature.description }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         HOW IT WORKS
         ═══════════════════════════════════════════════ -->
    <section id="como-funciona" class="section section--alt" data-reveal>
      <div class="section__inner">
        <div class="section__header">
          <h2 class="section__title">Cómo funciona</h2>
          <p class="section__sub">De un archivo a una decisión informada en cuatro pasos.</p>
        </div>

        <div class="steps">
          <div v-for="(step, i) in steps" :key="step.number" class="step">
            <div class="step__number">{{ step.number }}</div>
            <div class="step__connector" v-if="i < steps.length - 1" />
            <h3 class="step__title">{{ step.title }}</h3>
            <p class="step__text">{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         WHY DIFFERENT + IMPACT
         ═══════════════════════════════════════════════ -->
    <section class="section" data-reveal>
      <div class="section__inner">
        <div class="section__header">
          <h2 class="section__title">Por qué es diferente</h2>
          <p class="section__sub">No es una app de fitness. Es un motor de riesgo con ciencia real.</p>
        </div>

        <div class="diff-grid">
          <!-- Differentials -->
          <div class="diff-grid__left">
            <div v-for="item in differentiators" :key="item.title" class="card card--diff">
              <div class="card__icon card__icon--green">
                <AppIcon :name="item.icon" :size="18" />
              </div>
              <div>
                <h3 class="card__title">{{ item.title }}</h3>
                <p class="card__text">{{ item.description }}</p>
              </div>
            </div>
          </div>

          <!-- Impact metrics -->
          <div class="diff-grid__right">
            <div v-for="metric in impactMetrics" :key="metric.label" class="metric">
              <div class="metric__value">{{ metric.value }}</div>
              <div>
                <div class="metric__label">{{ metric.label }}</div>
                <p class="metric__text">{{ metric.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         CTA
         ═══════════════════════════════════════════════ -->
    <section class="section section--alt" data-reveal>
      <div class="section__inner">
        <div class="cta">
          <div class="cta__bg" aria-hidden="true" />
          <h2 class="cta__title">Tu próxima ruta, sin sorpresas</h2>
          <p class="cta__sub">Sube tu recorrido y obtén el análisis completo en segundos.</p>
          <RouterLink to="/mapa" class="btn-white-lg">
            <span>Empezar ahora</span>
            <AppIcon name="arrow-right" :size="18" />
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         TECH STACK
         ═══════════════════════════════════════════════ -->
    <section class="section" data-reveal>
      <div class="section__inner">
        <div class="section__header">
          <h2 class="section__title">Stack tecnológico</h2>
          <p class="section__sub">Herramientas de producción real aplicadas a seguridad en senderismo.</p>
        </div>

        <div class="grid-2">
          <div v-for="group in techStack" :key="group.category" class="card card--tech">
            <h3 class="card__category">{{ group.category }}</h3>
            <div class="card__tags">
              <span v-for="item in group.items" :key="item" class="card__tag">{{ item }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         TEAM
         ═══════════════════════════════════════════════ -->
    <section id="equipo" class="section section--alt" data-reveal>
      <div class="section__inner">
        <div class="section__header">
          <h2 class="section__title">Equipo</h2>
          <p class="section__sub">Tres desarrolladores, una visión: que ningún sendero tome por sorpresa.</p>
        </div>

        <div class="grid-3">
          <div v-for="author in authors" :key="author.name" class="card card--author">
            <img :src="author.avatar" :alt="author.name" class="card__avatar" />
            <h3 class="card__name">{{ author.name }}</h3>
            <p class="card__role">{{ author.role }}</p>
            <div class="card__socials">
              <a :href="author.github" target="_blank" class="card__social" title="GitHub">
                <AppIcon name="github" :size="16" />
              </a>
              <a v-if="author.portfolio" :href="author.portfolio" target="_blank" class="card__social" title="Portfolio">
                <AppIcon name="globe" :size="16" />
              </a>
              <a v-if="author.linkedin" :href="author.linkedin" target="_blank" class="card__social" title="LinkedIn">
                <AppIcon name="linkedin" :size="16" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         FOOTER
         ═══════════════════════════════════════════════ -->
    <footer class="footer">
      <div class="footer__inner">
        <div class="footer__left">
          <AppIcon name="shield" :size="14" />
          <span>MIT · © 2026 Irvin Benitez, Roy Barrera, Kelvin He</span>
          <a href="https://github.com/IrvinngB/JIC-Geo/blob/main/LICENSE" target="_blank" class="footer__link">Ver licencia</a>
        </div>
        <div class="footer__right">
          <span class="footer__brand">RiskTrail</span>
          <span>· Índice dinámico de riesgo en senderismo</span>
        </div>
      </div>
    </footer>

  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════
   APPLE DESIGN — Landing Page

   Principles:
   1. Response: all interactive elements respond on :active
   2. Spatial consistency: sections reveal from below
   3. Minimal material: glass cards, no decoration
   4. Typographic hierarchy: clear weight/size progression
   5. Restraint: whitespace as design element
   ═══════════════════════════════════════════════════ */

/* ── Base ───────────────────────────────────────── */
.landing {
  min-height: 100vh;
  background: #fafafa;
}

:global(html[data-theme="jic-dark"]) .landing {
  background: #0b0f19;
}

/* ── Navbar ─────────────────────────────────────── */
.nav {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(250, 250, 250, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
}

:global(html[data-theme="jic-dark"]) .nav {
  border-bottom-color: rgba(255, 255, 255, 0.06);
  background: rgba(11, 15, 25, 0.8);
}

.nav__inner {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
}

.nav__logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  transition: transform 100ms ease-out;
}

.nav__logo:active { transform: scale(0.96); }

.nav__logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #059669, #047857);
  color: white;
}

.nav__logo-text {
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #18181b;
}

:global(html[data-theme="jic-dark"]) .nav__logo-text { color: #fafafa; }

.nav__links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav__mobile {
  display: none;
  align-items: center;
  gap: 8px;
}

.nav__link {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #71717a;
  text-decoration: none;
  transition: color 150ms ease, background 150ms ease, transform 100ms ease-out;
}

.nav__link:hover { color: #18181b; background: rgba(0, 0, 0, 0.04); }
.nav__link:active { transform: scale(0.97); }

:global(html[data-theme="jic-dark"]) .nav__link { color: #a1a1aa; }
:global(html[data-theme="jic-dark"]) .nav__link:hover { color: #fafafa; background: rgba(255, 255, 255, 0.06); }

.nav__theme {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #71717a;
  cursor: pointer;
  transition: color 150ms ease, background 150ms ease, transform 100ms ease-out;
}

.nav__theme:hover { color: #18181b; background: rgba(0, 0, 0, 0.04); }
.nav__theme:active { transform: scale(0.88); }

:global(html[data-theme="jic-dark"]) .nav__theme { color: #a1a1aa; }
:global(html[data-theme="jic-dark"]) .nav__theme:hover { color: #fafafa; background: rgba(255, 255, 255, 0.06); }

.nav__user {
  font-size: 12px;
  color: #a1a1aa;
  padding: 0 4px;
}

.nav__ghost {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #71717a;
  background: transparent;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition: color 150ms ease, background 150ms ease, transform 100ms ease-out;
}

.nav__ghost:hover { color: #18181b; background: rgba(0, 0, 0, 0.04); }
.nav__ghost:active { transform: scale(0.97); }

:global(html[data-theme="jic-dark"]) .nav__ghost { color: #a1a1aa; }
:global(html[data-theme="jic-dark"]) .nav__ghost:hover { color: #fafafa; background: rgba(255, 255, 255, 0.06); }

.nav__cta {
  padding: 6px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: white;
  background: #059669;
  text-decoration: none;
  transition: transform 100ms ease-out, box-shadow 200ms ease;
}

.nav__cta:hover { box-shadow: 0 2px 12px rgba(5, 150, 105, 0.3); }
.nav__cta:active { transform: scale(0.96); }

:global(html[data-theme="jic-dark"]) .nav__cta { background: #34d399; color: #022c22; }

@media (max-width: 768px) {
  .nav__links { display: none; }
  .nav__mobile { display: flex; }
}

/* ── Hero ───────────────────────────────────────── */
.hero {
  position: relative;
  padding: 100px 20px 80px;
  overflow: hidden;
}

.hero__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero__orb {
  position: absolute;
  border-radius: 9999px;
  filter: blur(100px);
}

.hero__orb--1 {
  top: -20%;
  right: -10%;
  width: 500px;
  height: 400px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
  opacity: 0;
  animation: orb-in 1.4s ease-out 0.3s forwards;
}

.hero__orb--2 {
  bottom: -20%;
  left: -10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.06) 0%, transparent 70%);
  opacity: 0;
  animation: orb-in 1.4s ease-out 0.6s forwards;
}

@keyframes orb-in { to { opacity: 1; } }

.hero__content {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;

  /* Spring-like entrance */
  opacity: 0;
  transform: translateY(20px);
  transition:
    opacity 0.6s cubic-bezier(0.2, 0.8, 0.2, 1),
    transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.hero--visible .hero__content {
  opacity: 1;
  transform: translateY(0);
}

.hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #059669;
  background: rgba(5, 150, 105, 0.08);
  border: 1px solid rgba(5, 150, 105, 0.15);
  margin-bottom: 24px;
}

:global(html[data-theme="jic-dark"]) .hero__badge {
  color: #34d399;
  background: rgba(52, 211, 153, 0.1);
  border-color: rgba(52, 211, 153, 0.15);
}

.hero__badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.hero__title {
  font-size: clamp(32px, 5vw, 56px);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.08;
  color: #18181b;
  max-width: 640px;
}

.hero__title-accent {
  display: block;
  background: linear-gradient(135deg, #059669, #047857);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

:global(html[data-theme="jic-dark"]) .hero__title { color: #fafafa; }
:global(html[data-theme="jic-dark"]) .hero__title-accent {
  background: linear-gradient(135deg, #34d399, #10b981);
  -webkit-background-clip: text;
  background-clip: text;
}

.hero__sub {
  margin-top: 20px;
  font-size: 17px;
  line-height: 1.6;
  color: #71717a;
  max-width: 520px;
}

.hero__sub strong { color: #18181b; font-weight: 600; }

:global(html[data-theme="jic-dark"]) .hero__sub { color: #a1a1aa; }
:global(html[data-theme="jic-dark"]) .hero__sub strong { color: #fafafa; }

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 32px;
}

.hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 40px;
}

.hero__tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #a1a1aa;
}

.hero__tag-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.hero__tag-dot--green { background: #059669; }
.hero__tag-dot--blue { background: #3b82f6; }
.hero__tag-dot--teal { background: #14b8a6; }

/* ── Buttons ────────────────────────────────────── */
.btn-primary-lg {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  color: white;
  background: linear-gradient(135deg, #059669, #047857);
  text-decoration: none;
  box-shadow: 0 2px 12px rgba(5, 150, 105, 0.3);
  transition: transform 100ms ease-out, box-shadow 200ms ease;
}

.btn-primary-lg:hover { box-shadow: 0 4px 24px rgba(5, 150, 105, 0.4); }
.btn-primary-lg:active { transform: scale(0.97); }

:global(html[data-theme="jic-dark"]) .btn-primary-lg {
  background: linear-gradient(135deg, #34d399, #10b981);
  color: #022c22;
}

.btn-ghost-lg {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 600;
  color: #3f3f46;
  background: transparent;
  text-decoration: none;
  border: 1.5px solid #e4e4e7;
  transition: transform 100ms ease-out, border-color 150ms ease, background 150ms ease;
}

.btn-ghost-lg:hover { border-color: #a1a1aa; background: rgba(0, 0, 0, 0.02); }
.btn-ghost-lg:active { transform: scale(0.97); }

:global(html[data-theme="jic-dark"]) .btn-ghost-lg {
  color: #d4d4d8;
  border-color: #27272a;
}

:global(html[data-theme="jic-dark"]) .btn-ghost-lg:hover {
  border-color: #52525b;
  background: rgba(255, 255, 255, 0.04);
}

.btn-white-lg {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  color: #047857;
  background: white;
  text-decoration: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: transform 100ms ease-out, box-shadow 200ms ease;
}

.btn-white-lg:hover { box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15); }
.btn-white-lg:active { transform: scale(0.97); }

/* ── Sections ───────────────────────────────────── */
.section {
  padding: 80px 20px;
}

.section--alt {
  background: rgba(0, 0, 0, 0.015);
}

:global(html[data-theme="jic-dark"]) .section--alt {
  background: rgba(255, 255, 255, 0.015);
}

.section__inner {
  max-width: 1120px;
  margin: 0 auto;
}

.section__header {
  margin-bottom: 48px;
  max-width: 560px;
}

.section__title {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #18181b;
  margin: 0;
}

.section__sub {
  margin-top: 8px;
  font-size: 15px;
  color: #71717a;
  line-height: 1.5;
}

:global(html[data-theme="jic-dark"]) .section__title { color: #fafafa; }
:global(html[data-theme="jic-dark"]) .section__sub { color: #a1a1aa; }

/* ── Grids ──────────────────────────────────────── */
.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 768px) {
  .grid-2, .grid-3 { grid-template-columns: 1fr; }
}

/* ── Cards ──────────────────────────────────────── */
.card {
  padding: 20px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  transition: transform 100ms ease-out, box-shadow 200ms ease, border-color 200ms ease;
}

.card:active { transform: scale(0.985); }

:global(html[data-theme="jic-dark"]) .card {
  border-color: rgba(255, 255, 255, 0.06);
  background: rgba(24, 24, 27, 0.6);
}

.card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 11px;
  margin-bottom: 14px;
  flex-shrink: 0;
}

.card__icon--red {
  background: rgba(239, 68, 68, 0.08);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.12);
}

.card__icon--green {
  background: rgba(5, 150, 105, 0.08);
  color: #059669;
  border: 1px solid rgba(5, 150, 105, 0.12);
}

:global(html[data-theme="jic-dark"]) .card__icon--red {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.15);
}

:global(html[data-theme="jic-dark"]) .card__icon--green {
  background: rgba(52, 211, 153, 0.1);
  color: #34d399;
  border-color: rgba(52, 211, 153, 0.15);
}

.card__title {
  font-size: 14px;
  font-weight: 700;
  color: #18181b;
  margin: 0 0 4px;
}

.card__text {
  font-size: 13px;
  line-height: 1.5;
  color: #71717a;
  margin: 0;
}

:global(html[data-theme="jic-dark"]) .card__title { color: #fafafa; }
:global(html[data-theme="jic-dark"]) .card__text { color: #a1a1aa; }

/* Pain cards */
.card--pain {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

/* Feature cards */
.card--feature:hover {
  border-color: rgba(5, 150, 105, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

:global(html[data-theme="jic-dark"]) .card--feature:hover {
  border-color: rgba(52, 211, 153, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* Diff cards */
.card--diff {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

/* Tech cards */
.card--tech {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.06);
  backdrop-filter: none;
}

:global(html[data-theme="jic-dark"]) .card--tech {
  border-color: rgba(255, 255, 255, 0.06);
  background: transparent;
}

.card__category {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #059669;
  margin: 0 0 12px;
}

:global(html[data-theme="jic-dark"]) .card__category { color: #34d399; }

.card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.card__tag {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  color: #3f3f46;
  background: rgba(0, 0, 0, 0.04);
}

:global(html[data-theme="jic-dark"]) .card__tag {
  color: #d4d4d8;
  background: rgba(255, 255, 255, 0.06);
}

/* Author cards */
.card--author {
  text-align: center;
  padding: 28px 20px;
}

.card--author:hover {
  border-color: rgba(5, 150, 105, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

:global(html[data-theme="jic-dark"]) .card--author:hover {
  border-color: rgba(52, 211, 153, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.card__avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(0, 0, 0, 0.06);
  margin: 0 auto 12px;
  display: block;
  transition: border-color 200ms ease;
}

.card--author:hover .card__avatar {
  border-color: rgba(5, 150, 105, 0.4);
}

:global(html[data-theme="jic-dark"]) .card__avatar {
  border-color: rgba(255, 255, 255, 0.08);
}

.card--author:hover .card__avatar {
  border-color: rgba(52, 211, 153, 0.4);
}

.card__name {
  font-size: 15px;
  font-weight: 700;
  color: #18181b;
  margin: 0;
}

.card__role {
  font-size: 12px;
  color: #a1a1aa;
  margin: 4px 0 0;
}

.card__socials {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 14px;
}

.card__social {
  color: #a1a1aa;
  transition: color 150ms ease, transform 100ms ease-out;
}

.card__social:hover { color: #059669; }
.card__social:active { transform: scale(0.88); }

:global(html[data-theme="jic-dark"]) .card__social { color: #52525b; }
:global(html[data-theme="jic-dark"]) .card__social:hover { color: #34d399; }

:global(html[data-theme="jic-dark"]) .card__name { color: #fafafa; }

/* ── Steps ──────────────────────────────────────── */
.steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 768px) {
  .steps { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
  .steps { grid-template-columns: 1fr; }
}

.step {
  position: relative;
  padding: 24px 20px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(12px);
}

:global(html[data-theme="jic-dark"]) .step {
  background: rgba(24, 24, 27, 0.6);
  border-color: rgba(255, 255, 255, 0.06);
}

.step__number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #059669, #047857);
  color: white;
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 16px;
}

:global(html[data-theme="jic-dark"]) .step__number {
  background: linear-gradient(135deg, #34d399, #10b981);
  color: #022c22;
}

.step__title {
  font-size: 14px;
  font-weight: 700;
  color: #18181b;
  margin: 0 0 6px;
}

.step__text {
  font-size: 13px;
  line-height: 1.5;
  color: #71717a;
  margin: 0;
}

:global(html[data-theme="jic-dark"]) .step__title { color: #fafafa; }
:global(html[data-theme="jic-dark"]) .step__text { color: #a1a1aa; }

/* ── Diff grid ──────────────────────────────────── */
.diff-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 24px;
}

.diff-grid__left {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.diff-grid__right {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (max-width: 768px) {
  .diff-grid { grid-template-columns: 1fr; }
  .diff-grid__left { grid-template-columns: 1fr; }
}

/* ── Metrics ────────────────────────────────────── */
.metric {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(12px);
}

:global(html[data-theme="jic-dark"]) .metric {
  background: rgba(24, 24, 27, 0.6);
  border-color: rgba(255, 255, 255, 0.06);
}

.metric__value {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #059669;
  flex-shrink: 0;
}

:global(html[data-theme="jic-dark"]) .metric__value { color: #34d399; }

.metric__label {
  font-size: 14px;
  font-weight: 700;
  color: #18181b;
}

.metric__text {
  font-size: 12px;
  color: #a1a1aa;
  margin: 2px 0 0;
}

:global(html[data-theme="jic-dark"]) .metric__label { color: #fafafa; }

/* ── CTA ────────────────────────────────────────── */
.cta {
  position: relative;
  padding: 64px 32px;
  border-radius: 24px;
  background: linear-gradient(135deg, #059669, #047857);
  text-align: center;
  overflow: hidden;
}

.cta__bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.08) 0%, transparent 50%);
}

.cta__title {
  position: relative;
  font-size: clamp(24px, 3.5vw, 36px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: white;
  margin: 0;
}

.cta__sub {
  position: relative;
  margin-top: 12px;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.8);
  max-width: 420px;
  margin-left: auto;
  margin-right: auto;
}

/* ── Footer ─────────────────────────────────────── */
.footer {
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding: 24px 20px;
}

:global(html[data-theme="jic-dark"]) .footer {
  border-top-color: rgba(255, 255, 255, 0.06);
}

.footer__inner {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #a1a1aa;
}

.footer__left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer__right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.footer__link {
  color: #059669;
  text-decoration: none;
  transition: transform 100ms ease-out;
}

.footer__link:active { transform: scale(0.97); }
.footer__link:hover { text-decoration: underline; }

:global(html[data-theme="jic-dark"]) .footer__link { color: #34d399; }

.footer__brand {
  font-weight: 700;
  color: #71717a;
}

:global(html[data-theme="jic-dark"]) .footer__brand { color: #d4d4d8; }

@media (max-width: 640px) {
  .footer__inner {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>

<!--
  Non-scoped dark mode overrides.
  Non-scoped styles have higher cascade priority than scoped + DaisyUI.
  This is the correct pattern when a UI framework (DaisyUI) owns dark mode
  and you need your custom styles to win.
-->
<style>
html[data-theme="jic-dark"] .landing { background: #0b0f19 !important; }
html[data-theme="jic-dark"] .nav { border-bottom-color: rgba(255,255,255,0.06) !important; background: rgba(11,15,25,0.8) !important; }
html[data-theme="jic-dark"] .nav__logo-text { color: #fafafa !important; }
html[data-theme="jic-dark"] .nav__link { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .nav__link:hover { color: #fafafa !important; background: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .nav__theme { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .nav__theme:hover { color: #fafafa !important; background: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .nav__ghost { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .nav__ghost:hover { color: #fafafa !important; background: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .nav__cta { background: #34d399 !important; color: #022c22 !important; }
html[data-theme="jic-dark"] .hero__badge { color: #34d399 !important; background: rgba(52,211,153,0.1) !important; border-color: rgba(52,211,153,0.15) !important; }
html[data-theme="jic-dark"] .hero__title { color: #fafafa !important; }
html[data-theme="jic-dark"] .hero__title-accent { background: linear-gradient(135deg,#34d399,#10b981) !important; -webkit-background-clip: text !important; background-clip: text !important; }
html[data-theme="jic-dark"] .hero__sub { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .hero__sub strong { color: #fafafa !important; }
html[data-theme="jic-dark"] .btn-primary-lg { background: linear-gradient(135deg,#34d399,#10b981) !important; color: #022c22 !important; }
html[data-theme="jic-dark"] .btn-ghost-lg { color: #d4d4d8 !important; border-color: #27272a !important; }
html[data-theme="jic-dark"] .btn-ghost-lg:hover { border-color: #52525b !important; background: rgba(255,255,255,0.04) !important; }
html[data-theme="jic-dark"] .section--alt { background: rgba(255,255,255,0.015) !important; }
html[data-theme="jic-dark"] .section__title { color: #fafafa !important; }
html[data-theme="jic-dark"] .section__sub { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .card { border-color: rgba(255,255,255,0.06) !important; background: rgba(24,24,27,0.6) !important; }
html[data-theme="jic-dark"] .card__icon--red { background: rgba(239,68,68,0.1) !important; color: #f87171 !important; border-color: rgba(239,68,68,0.15) !important; }
html[data-theme="jic-dark"] .card__icon--green { background: rgba(52,211,153,0.1) !important; color: #34d399 !important; border-color: rgba(52,211,153,0.15) !important; }
html[data-theme="jic-dark"] .card__title { color: #fafafa !important; }
html[data-theme="jic-dark"] .card__text { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .card--feature:hover { border-color: rgba(52,211,153,0.2) !important; box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important; }
html[data-theme="jic-dark"] .card--tech { border-color: rgba(255,255,255,0.06) !important; background: transparent !important; }
html[data-theme="jic-dark"] .card__category { color: #34d399 !important; }
html[data-theme="jic-dark"] .card__tag { color: #d4d4d8 !important; background: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .card--author:hover { border-color: rgba(52,211,153,0.2) !important; box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important; }
html[data-theme="jic-dark"] .card__avatar { border-color: rgba(255,255,255,0.08) !important; }
html[data-theme="jic-dark"] .card--author:hover .card__avatar { border-color: rgba(52,211,153,0.4) !important; }
html[data-theme="jic-dark"] .card__name { color: #fafafa !important; }
html[data-theme="jic-dark"] .card__social { color: #52525b !important; }
html[data-theme="jic-dark"] .card__social:hover { color: #34d399 !important; }
html[data-theme="jic-dark"] .step { background: rgba(24,24,27,0.6) !important; border-color: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .step__number { background: linear-gradient(135deg,#34d399,#10b981) !important; color: #022c22 !important; }
html[data-theme="jic-dark"] .step__title { color: #fafafa !important; }
html[data-theme="jic-dark"] .step__text { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .metric { background: rgba(24,24,27,0.6) !important; border-color: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .metric__value { color: #34d399 !important; }
html[data-theme="jic-dark"] .metric__label { color: #fafafa !important; }
html[data-theme="jic-dark"] .footer { border-top-color: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .footer__link { color: #34d399 !important; }
html[data-theme="jic-dark"] .footer__brand { color: #d4d4d8 !important; }
</style>
