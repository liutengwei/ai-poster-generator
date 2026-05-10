import { createRouter, createWebHistory } from 'vue-router'
import Create from '@/views/Create.vue'
import History from '@/views/History.vue'
import ExpenseCheck from '@/views/ExpenseCheck.vue'

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
    {
      path: '/expense',
      name: 'expense',
      component: ExpenseCheck,
    },
  ],
})

export default router
