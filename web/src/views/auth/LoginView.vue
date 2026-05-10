<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { login } from '@/api/auth-service'
import AuthShell from '@/components/auth/AuthShell.vue'

const loading = ref(false)
const showPassword = ref(false)
const isUserFocused = ref(false)

const form = reactive({
  userCode: 'admin',
  password: 'admin123',
  fiscal: 2026,
})

async function onSubmit() {
  if (loading.value) {
    return
  }

  try {
    loading.value = true
    const response = await login({
      userCode: form.userCode,
      password: form.password,
      fiscal: Number(form.fiscal),
    })

    const loginInfo = response.data?.data
    if (loginInfo?.token) {
      localStorage.setItem('token', loginInfo.token)
    }
    localStorage.setItem('loginInfo', JSON.stringify(loginInfo ?? {}))

    message.success(`欢迎回来，${loginInfo?.userName || loginInfo?.userCode || form.userCode}`)
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
        <span>Passwrod</span>
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
        <span>fiscal</span>
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
