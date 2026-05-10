<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { login, initSecurity } from '@/api/auth-service'
import { useAuthStore } from '@/store/auth'
import { encryptRSA } from '@/utils/crypto'
import AuthShell from '@/components/auth/AuthShell.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const showPassword = ref(false)
const isUserFocused = ref(false)

const form = reactive({
  userCode: 'admin',
  password: 'admin123',
  fiscal: 2026,
  captcha: '123456', // Placeholder for mandatory captcha
})

onMounted(async () => {
  try {
    const response = await initSecurity()
    if (response.data?.data) {
      authStore.setSecurity(response.data.data)
    }
  } catch (error) {
    message.error('初始化安全规则失败，请稍后重试')
  }
})

async function onSubmit() {
  if (loading.value) {
    return
  }

  if (!authStore.security?.rsaPublicKey) {
    message.error('安全规则尚未初始化，请刷新页面')
    return
  }

  try {
    loading.value = true
    
    // Use RSA to encrypt password (async)
    let encryptedPassword: string
    try {
      encryptedPassword = await encryptRSA(authStore.security.rsaPublicKey, form.password)
    } catch (e) {
      message.error('密码加密失败')
      return
    }

    const response = await login({
      userCode: form.userCode,
      password: encryptedPassword,
      fiscal: Number(form.fiscal),
      captcha: form.captcha,
      sessionId: authStore.security.sessionId,
    })

    const loginInfo = response.data?.data
    if (loginInfo) {
      authStore.setAuth(loginInfo)
      message.success(`欢迎回来，${loginInfo.userName || loginInfo.userCode || form.userCode}`)
      router.push('/')
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '登录失败'
    message.error(errorMessage)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell :is-typing="isUserFocused" :show-password="showPassword" :password-length="form.password.length">
    <header class="form-header form-header--left">
      <h2>FastApi System</h2>
    </header>

    <form class="login-form" @submit.prevent="onSubmit">
      <label class="field">
        <span>Account</span>
        <div class="field__control">
          <input
            v-model="form.userCode"
            type="text"
            placeholder="请输入 userCode"
            @focus="isUserFocused = true"
            @blur="isUserFocused = false"
          />
        </div>
      </label>

      <label class="field">
        <span>Password</span>
        <div class="field__control">
          <input
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
          />
          <button
            type="button"
            class="password-toggle"
            :aria-label="showPassword ? '隐藏密码' : '显示密码'"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? '隐藏' : '显示' }}
          </button>
        </div>
      </label>

      <label class="field">
        <span>Captcha</span>
        <div class="field__control">
          <input
            v-model="form.captcha"
            type="text"
            placeholder="请输入验证码"
          />
        </div>
      </label>

      <label class="field">
        <span>Fiscal</span>
        <div class="field__control">
          <input v-model="form.fiscal" type="number" min="2020" max="2099" />
        </div>
      </label>

      <button type="submit" class="primary-button" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>
  </AuthShell>
</template>
