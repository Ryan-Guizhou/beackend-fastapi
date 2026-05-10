<script setup lang="ts">
withDefaults(
  defineProps<{
    light?: boolean
    compact?: boolean
  }>(),
  {
    light: false,
    compact: false,
  },
)
</script>

<template>
  <footer class="copyright" :class="{ 'is-light': light, 'is-compact': compact }">
    <div>
      <strong>PeachCloud DataOS</strong>
      <span>Copyright 2026 PeachCloud Systems. All rights reserved.</span>
    </div>
    <div>
      <span>Data Security Compliance Center</span>
      <span>Terms of Service | Privacy Policy</span>
    </div>
  </footer>
</template>

<style scoped>
.copyright {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: rgba(16, 24, 40, 0.6);
  font-size: 12px;
}

.copyright strong,
.copyright span {
  display: block;
}

.copyright strong {
  margin-bottom: 4px;
  color: #101828;
}

.is-light {
  color: rgba(255, 255, 255, 0.72);
}

.is-light strong {
  color: #ffffff;
}

.is-compact {
  font-size: 11px;
}

@media (max-width: 900px) {
  .copyright {
    flex-direction: column;
  }
}
</style>
