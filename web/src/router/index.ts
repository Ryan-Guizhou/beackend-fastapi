import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/login' },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login',
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
