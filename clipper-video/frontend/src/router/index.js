import { createRouter, createWebHistory } from 'vue-router'
import VideoClipper from '@/pages/VideoClipper.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: VideoClipper
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
