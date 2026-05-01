import { createRouter, createWebHistory } from 'vue-router'
import Create from '@/views/Create.vue'
import History from '@/views/History.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'create',
      component: Create,
    },
    {
      path: '/history',
      name: 'history',
      component: History,
    },
  ],
})

export default router
