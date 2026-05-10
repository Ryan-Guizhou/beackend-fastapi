<script setup lang="ts">
import AppCopyright from '@/components/layout/AppCopyright.vue'
import AuthIllustration from './AuthIllustration.vue'
import PeachCloudLogo from './PeachCloudLogo.vue'

defineProps<{
  isTyping: boolean
  showPassword: boolean
  passwordLength: number
}>()
</script>

<template>
  <div class="auth-shell">
    <aside class="hero-panel">
      <div class="hero-panel__brand">
        <PeachCloudLogo />
      </div>

      <div class="hero-copy">
        <span class="hero-copy__eyebrow">数据管理平台</span>
        <h1>统一数据、权限与流程协同。</h1>
        <p>为团队提供清晰一致的系统登录入口。</p>
      </div>

      <div class="hero-panel__art">
        <AuthIllustration
          :is-typing="isTyping"
          :show-password="showPassword"
          :password-length="passwordLength"
        />
      </div>

      <div class="hero-panel__footer">
        <AppCopyright light compact />
      </div>

      <div class="hero-grid" />
      <div class="hero-glow hero-glow--top" />
      <div class="hero-glow hero-glow--bottom" />
    </aside>

    <main class="form-panel">
      <div class="form-wrap form-wrap--wide">
        <div class="mobile-brand">
          <PeachCloudLogo :compact="true" />
        </div>
        <slot />
      </div>
    </main>
  </div>
</template>
