<script setup lang="ts">
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'vue-router'
import {
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const authStore = useAuthStore()
const router = useRouter()

const onLogout = async () => {
  await authStore.logout()
  message.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <!-- Breadcrumb or Title can go here -->
    </div>
    <div class="header-right">
      <a-space :size="20">
        <!-- Internal Messages / Notifications -->
        <a-badge :count="5" :offset="[0, 2]">
          <a-button type="text" class="header-icon-btn">
            <template #icon><BellOutlined /></template>
          </a-button>
        </a-badge>

        <!-- User Info Dropdown -->
        <a-dropdown :trigger="['click']">
          <div class="user-profile">
            <a-avatar size="small" style="background-color: #ff8e94">
              {{ authStore.userInfo?.userName?.charAt(0) || 'U' }}
            </a-avatar>
            <span class="user-name">{{ authStore.userInfo?.userName || 'User' }}</span>
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile">
                <template #icon><UserOutlined /></template>
                个人中心
              </a-menu-item>
              <a-menu-item key="settings">
                <template #icon><SettingOutlined /></template>
                系统设置
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout" @click="onLogout">
                <template #icon><LogoutOutlined /></template>
                退出登录
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </a-space>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: 64px;
  padding: 0 24px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 10;
}

.header-icon-btn {
  font-size: 18px;
  color: #667085;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-profile:hover {
  background: #f9fafb;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #344054;
}
</style>
