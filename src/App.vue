<template>
  <router-view />

  <footer class="site-footer">
    <span>客服QQ：2042132648</span>
    <span class="footer-sep">·</span>
    <span>QQ交流群：796340811</span>
    <span class="footer-sep">·</span>
    <span>技术微信：19966519194</span>
    <span class="footer-sep">·</span>
    <a href="https://customer.claude-code.club/invite/CNCQSH" target="_blank" rel="noopener">友情链接：CC Club</a>
  </footer>

  <PopupNotice
    v-if="showPopup"
    :config="popupConfig"
    @close="showPopup = false"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PopupNotice from './components/PopupNotice.vue'

const showPopup = ref(false)
const popupConfig = ref({
  text: '欢迎使用 AI 智能讲解 PPT！上传您的PPT或PDF，AI将自动生成专业讲解词并配合数字人演示。每日可免费使用3次。',
  image_url: ''
})

onMounted(() => {
  const key = 'aippt_popup_shown'
  const lastShown = localStorage.getItem(key)
  const today = new Date().toISOString().slice(0, 10)
  if (lastShown !== today) {
    showPopup.value = true
    localStorage.setItem(key, today)
  }
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
  background: #0f0f1a;
  color: #e0e0e0;
  min-height: 100vh;
}
.site-footer {
  text-align: center;
  padding: 20px 16px;
  font-size: 13px;
  color: #666;
  background: #0a0a15;
  border-top: 1px solid #1a1a2e;
}
.site-footer a {
  color: #667eea;
  text-decoration: none;
}
.site-footer a:hover {
  text-decoration: underline;
}
.footer-sep {
  margin: 0 8px;
  color: #444;
}
</style>
