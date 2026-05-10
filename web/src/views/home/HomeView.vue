<script setup lang="ts">
import { useAuthStore } from '@/store/auth'
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const authStore = useAuthStore()
const route = useRoute()

const pageTitle = computed(() => {
  switch (route.name) {
    case 'user-management': return '用户管理'
    case 'menu-management': return '菜单管理'
    case 'route-management': return '路由管理'
    case 'resource-management': return '资源管理'
    default: return '仪表盘'
  }
})
</script>

<template>
  <div class="home-view">
    <div class="page-header">
      <h2 class="page-title">{{ pageTitle }}</h2>
      <p class="page-desc">欢迎回来，{{ authStore.userInfo?.userName }}。这是您的{{ pageTitle }}页面。</p>
    </div>

    <div class="content-grid">
      <a-card class="stat-card" :bordered="false">
        <a-statistic title="活跃用户" :value="1128" />
      </a-card>
      <a-card class="stat-card" :bordered="false">
        <a-statistic title="今日访问" :value="93" />
      </a-card>
      <a-card class="stat-card" :bordered="false">
        <a-statistic title="系统消息" :value="5" />
      </a-card>
      <a-card class="stat-card" :bordered="false">
        <a-statistic title="安全指数" :value="98" suffix="%" />
      </a-card>
    </div>

    <a-card class="main-card" :bordered="false" title="系统动态">
      <a-empty description="暂无数据" />
    </a-card>
  </div>
</template>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  margin-bottom: 8px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #101828;
  margin-bottom: 4px;
}

.page-desc {
  color: #667085;
  font-size: 14px;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.stat-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.1), 0 1px 2px rgba(16, 24, 40, 0.06);
}

.main-card {
  border-radius: 12px;
  min-height: 400px;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.1), 0 1px 2px rgba(16, 24, 40, 0.06);
}
</style>
