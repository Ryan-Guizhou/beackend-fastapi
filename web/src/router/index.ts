import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import MainLayout from '@/components/layout/MainLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/home/HomeView.vue'),
      },
      {
        path: 'system/user',
        name: 'user-management',
        component: () => import('@/views/system/user/index.vue'),
      },
      {
        path: 'system/menu',
        name: 'menu-management',
        component: () => import('@/views/system/menu/index.vue'),
      },
      {
        path: 'system/route',
        name: 'route-management',
        component: () => import('@/views/system/router/index.vue'),
      },
      {
        path: 'system/resource',
        name: 'resource-management',
        component: () => import('@/views/system/resource/index.vue'),
      },
      {
        path: 'system/function',
        name: 'function-management',
        component: () => import('@/views/system/function/index.vue'),
      },
      {
        path: 'system/dict',
        name: 'dict-management',
        component: () => import('@/views/system/dict/index.vue'),
      },
      {
        path: 'audit/login-log',
        name: 'login-log',
        component: () => import('@/views/audit/login-log/index.vue'),
      },
      {
        path: 'audit/auth-log',
        name: 'auth-log',
        component: () => import('@/views/audit/auth-log/index.vue'),
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.name === 'login' && authStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
