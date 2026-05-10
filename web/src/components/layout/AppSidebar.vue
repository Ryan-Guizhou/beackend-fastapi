<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppstoreOutlined,
  UserOutlined,
  MenuOutlined,
  BlockOutlined,
  ApiOutlined,
  FunctionOutlined,
  AuditOutlined,
  BookOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons-vue'
import PeachCloudLogo from '@/components/auth/PeachCloudLogo.vue'

const route = useRoute()
const router = useRouter()

const selectedKeys = ref<string[]>([route.name as string])
const openKeys = ref<string[]>(['sub-system', 'sub-audit'])

watch(() => route.name, (newName) => {
  selectedKeys.value = [newName as string]
})

const onMenuClick = ({ key }: { key: string }) => {
  router.push({ name: key })
}
</script>

<template>
  <aside class="app-sidebar">
    <div class="logo-container">
      <div class="logo-wrapper">
        <PeachCloudLogo only-icon />
      </div>
      <span class="logo-text">PeachCloud</span>
    </div>

    <a-menu
      v-model:selectedKeys="selectedKeys"
      v-model:openKeys="openKeys"
      mode="inline"
      class="sidebar-menu"
      @click="onMenuClick"
    >
      <a-sub-menu key="sub-system">
        <template #icon>
          <AppstoreOutlined />
        </template>
        <template #title>系统管理</template>
        
        <a-menu-item key="user-management">
          <template #icon><UserOutlined /></template>
          用户管理
        </a-menu-item>
        
        <a-menu-item key="menu-management">
          <template #icon><MenuOutlined /></template>
          菜单管理
        </a-menu-item>
        
        <a-menu-item key="route-management">
          <template #icon><BlockOutlined /></template>
          路由管理
        </a-menu-item>
        
        <a-menu-item key="resource-management">
          <template #icon><ApiOutlined /></template>
          资源管理
        </a-menu-item>
        
        <a-menu-item key="function-management">
          <template #icon><FunctionOutlined /></template>
          功能定义
        </a-menu-item>
        
        <a-menu-item key="dict-management">
          <template #icon><BookOutlined /></template>
          字典管理
        </a-menu-item>
      </a-sub-menu>

      <a-sub-menu key="sub-audit">
        <template #icon>
          <AuditOutlined />
        </template>
        <template #title>审计管理</template>
        
        <a-menu-item key="login-log">
          <template #icon><FileTextOutlined /></template>
          登录日志
        </a-menu-item>
        
        <a-menu-item key="auth-log">
          <template #icon><SafetyCertificateOutlined /></template>
          授权日志
        </a-menu-item>
      </a-sub-menu>
    </a-menu>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: 256px;
  height: 100vh;
  background: #fff;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
}

.logo-container {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #f9fafb;
}

.logo-wrapper {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #101828;
  letter-spacing: -0.02em;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
  padding-top: 16px;
}

:deep(.ant-menu-item-selected) {
  background-color: #fff1f2 !important;
  color: #ff4d4f !important;
}

:deep(.ant-menu-item-selected::after) {
  border-right: 3px solid #ff4d4f !important;
}
</style>
