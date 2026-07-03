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
      // Not '/app': in dev the frontend container mounts the source at WORKDIR
      // /app, so vite tries to serve that directory for the URL /app and 500s
      // (EISDIR). '/mapa' avoids the collision and reads clearly in the UI.
      path: '/mapa',
      name: 'map',
      component: () => import('../views/MapView.vue'),
    },
  ],
})

export default router
