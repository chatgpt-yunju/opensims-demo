<template>
  <Transition name="fade">
    <div v-if="visible" class="popup-overlay" @click="handleClose">
      <div class="popup-card" @click.stop>
        <button class="close-btn" @click="handleClose" aria-label="关闭">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>

        <div v-if="config.image_url" class="popup-image">
          <img :src="config.image_url" :alt="config.text" />
        </div>

        <div class="popup-content">
          <p>{{ config.text }}</p>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  config: { type: Object, required: true }
})

const emit = defineEmits(['close'])
const visible = ref(false)

const handleClose = () => {
  visible.value = false
  setTimeout(() => emit('close'), 300)
}

const handleEscape = (e) => {
  if (e.key === 'Escape') handleClose()
}

onMounted(() => {
  visible.value = true
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})
</script>

<style scoped>
.popup-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}
.popup-card {
  background: #1a1a2e;
  border-radius: 12px;
  max-width: 500px;
  width: 100%;
  position: relative;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  border: 1px solid #2a2a3e;
}
.close-btn {
  position: absolute;
  top: 12px; right: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  width: 32px; height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #aaa;
  transition: background 0.2s;
  z-index: 1;
}
.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}
.popup-image { width: 100%; }
.popup-image img { width: 100%; height: auto; display: block; }
.popup-content { padding: 24px; }
.popup-content p {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
  color: #ccc;
  text-align: center;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
