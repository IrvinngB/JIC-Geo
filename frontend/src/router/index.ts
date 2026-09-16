import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('../views/LandingView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/mapa',
      name: 'map',
      component: () => import('../views/MapView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/mapa/nueva',
      name: 'map-new',
      component: () => import('../views/UploadFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/perfiles',
      name: 'profiles',
      component: () => import('../views/ProfilesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/historial',
      name: 'history',
      component: () => import('../views/HistoryView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/share/:code',
      name: 'share',
      component: () => import('../views/ShareView.vue'),
    },
  ],
})

// Navigation guard: redirect to /login if not authenticated
router.beforeEach((to) => {
  const token = localStorage.getItem('rt_token')

  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }

  if (to.meta.guest && token) {
    return { name: 'map' }
  }
})

export default router
