<template>
  <div class="home">
    <div class="hero">
      <h1>AI 智能讲解 PPT</h1>
      <p class="subtitle">上传PPT或PDF，AI自动生成讲解，数字人为您演示</p>
      <button class="btn-share" @click="shareLink">🔗 分享给好友</button>
    </div>

    <div class="upload-area" @dragover.prevent @drop.prevent="onDrop"
         @click="$refs.fileInput.click()" :class="{ uploading }">
      <input ref="fileInput" type="file" accept=".ppt,.pptx,.pdf" @change="onFileSelect" hidden />
      <div v-if="!uploading && !processing">
        <div class="upload-icon">📄</div>
        <p>点击或拖拽上传 PPT / PDF 文件</p>
        <p class="hint">支持 .ppt .pptx .pdf 格式</p>
        <p class="limit-info" v-if="dailyRemaining !== null">
          今日剩余次数：<strong :class="{ 'no-quota': dailyRemaining <= 0 }">{{ dailyRemaining }}</strong> / {{ dailyLimit }}
        </p>
      </div>
      <div v-else class="progress-info">
        <div class="spinner"></div>
        <p>{{ statusText }}</p>
        <div class="progress-bar" v-if="progress > 0">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- 历史记录 -->
    <div class="history" v-if="historyList.length">
      <h3>历史记录</h3>
      <div class="history-grid">
        <div v-for="item in historyList" :key="item.id" class="history-card"
             @click="$router.push('/present/' + item.id)">
          <img v-if="item.thumbnail" :src="item.thumbnail" />
          <div class="card-info">
            <span class="card-name">{{ item.filename }}</span>
            <span class="card-pages">{{ item.totalSlides }}页</span>
          </div>
          <button class="card-share" @click.stop="sharePPT(item.id)">🔗 分享</button>
        </div>
      </div>
    </div>

    <!-- 更多工具推荐 -->
    <div class="more-tools">
      <h3>探索 OpenClaw 更多AI工具</h3>
      <div class="tools-grid">
        <a href="https://yunjunet.cn" target="_blank" rel="noopener" class="tool-card">
          <div class="tool-icon">🎬</div>
          <div class="tool-info">
            <span class="tool-name">All in OpenClaw</span>
            <span class="tool-desc">OpenClaw舆情预测</span>
          </div>
        </a>
        <a href="https://planet.yunjunet.cn" target="_blank" rel="noopener" class="tool-card">
          <div class="tool-icon">🌍</div>
          <div class="tool-info">
            <span class="tool-name">OpenClaw星球</span>
            <span class="tool-desc">AI爱好者社区交流</span>
          </div>
        </a>
      </div>
    </div>

    <Transition name="toast">
      <div v-if="showToast" class="toast">链接已复制到剪贴板</div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiUrl, assetUrl } from '../lib/api'

const router = useRouter()

// 生成设备唯一标识，每个浏览器独立计数
function getDeviceId() {
  let id = localStorage.getItem('aippt_device_id')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('aippt_device_id', id)
  }
  return id
}
const deviceId = getDeviceId()
const deviceHeaders = { 'X-Device-Id': deviceId }

const uploading = ref(false)
const processing = ref(false)
const statusText = ref('')
const progress = ref(0)
const historyList = ref([])
const dailyRemaining = ref(null)
const dailyLimit = ref(5)
const showToast = ref(false)

onMounted(() => {
  loadHistory()
  loadLimit()
})

async function loadHistory() {
  try {
    const res = await fetch(apiUrl('/api/plugins/aippt/list'), { headers: deviceHeaders })
    if (res.ok) {
      const data = await res.json()
      historyList.value = data.map((item) => ({
        ...item,
        thumbnail: assetUrl(item.thumbnail)
      }))
    }
  } catch {}
}

async function loadLimit() {
  try {
    const res = await fetch(apiUrl('/api/plugins/aippt/limit'), { headers: deviceHeaders })
    if (res.ok) {
      const data = await res.json()
      dailyRemaining.value = data.remaining
      dailyLimit.value = data.limit
    }
  } catch {}
}

async function shareLink() {
  const url = window.location.href
  try {
    await navigator.clipboard.writeText(url)
    showToast.value = true
    setTimeout(() => showToast.value = false, 2000)
  } catch {
    prompt('复制此链接分享：', url)
  }
}

async function sharePPT(id) {
  const url = new URL(router.resolve(`/present/${id}`).href, window.location.origin).toString()
  try {
    await navigator.clipboard.writeText(url)
    showToast.value = true
    setTimeout(() => showToast.value = false, 2000)
  } catch {
    prompt('复制此链接分享：', url)
  }
}

function onFileSelect(e) {
  const file = e.target.files[0]
  if (file) uploadFile(file)
}

function onDrop(e) {
  const file = e.dataTransfer.files[0]
  if (file) uploadFile(file)
}

async function uploadFile(file) {
  if (dailyRemaining.value !== null && dailyRemaining.value <= 0) {
    alert('今日上传次数已用完，请明天再来！')
    return
  }

  uploading.value = true
  statusText.value = '上传中...'
  progress.value = 0

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await fetch(apiUrl('/api/plugins/aippt/upload'), { method: 'POST', body: formData, headers: deviceHeaders })
    const data = await res.json()
    if (!res.ok) {
      uploading.value = false
      alert(data.error || '上传失败')
      loadLimit()
      return
    }
    if (data.remaining !== undefined) dailyRemaining.value = data.remaining
    processing.value = true
    uploading.value = false
    pollStatus(data.id)
  } catch (err) {
    uploading.value = false
    alert('上传失败: ' + err.message)
  }
}

async function pollStatus(id) {
  const poll = async () => {
    try {
      const res = await fetch(apiUrl(`/api/plugins/aippt/${id}/status`))
      const data = await res.json()
      statusText.value = data.message
      progress.value = data.progress || 0

      if (data.status === 'done') {
        processing.value = false
        router.push(`/present/${id}`)
      } else if (data.status === 'error') {
        processing.value = false
        alert('处理失败: ' + data.message)
      } else {
        setTimeout(poll, 2000)
      }
    } catch {
      setTimeout(poll, 3000)
    }
  }
  poll()
}
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
  padding: 60px 20px;
}
.hero {
  text-align: center;
  margin-bottom: 40px;
}
.hero h1 {
  font-size: 2.4em;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
}
.subtitle {
  color: #888;
  font-size: 1.1em;
}
.upload-area {
  border: 2px dashed #444;
  border-radius: 16px;
  padding: 60px 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #1a1a2e;
}
.upload-area:hover {
  border-color: #667eea;
  background: #1e1e35;
}
.upload-area.uploading {
  cursor: default;
  border-color: #667eea;
}
.upload-icon {
  font-size: 3em;
  margin-bottom: 16px;
}
.hint {
  color: #666;
  font-size: 0.9em;
  margin-top: 8px;
}
.limit-info {
  color: #888;
  font-size: 0.85em;
  margin-top: 12px;
}
.limit-info strong {
  color: #667eea;
}
.limit-info .no-quota {
  color: #e74c3c;
}
.progress-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.spinner {
  width: 40px; height: 40px;
  border: 3px solid #333;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.progress-bar {
  width: 100%;
  max-width: 400px;
  height: 6px;
  background: #333;
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.5s;
}
.history {
  margin-top: 50px;
}
.history h3 {
  margin-bottom: 16px;
  color: #aaa;
}
.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.history-card {
  background: #1a1a2e;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}
.history-card:hover {
  transform: translateY(-4px);
}
.history-card img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
}
.card-info {
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  font-size: 0.85em;
}
.card-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}
.card-pages { color: #888; }
.card-share {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 10px;
  border-radius: 14px;
  border: none;
  background: rgba(102, 126, 234, 0.85);
  color: #fff;
  font-size: 0.75em;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
  backdrop-filter: blur(4px);
}
.history-card {
  position: relative;
}
.history-card:hover .card-share {
  opacity: 1;
}
.card-share:hover {
  background: rgba(102, 126, 234, 1);
}
.btn-share {
  margin-top: 16px;
  padding: 8px 20px;
  border-radius: 20px;
  border: 1px solid #444;
  background: none;
  color: #ccc;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
}
.btn-share:hover {
  border-color: #667eea;
  color: #fff;
}
.toast {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(102, 126, 234, 0.9);
  color: #fff;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 0.9em;
  z-index: 9999;
  backdrop-filter: blur(8px);
}
.more-tools {
  margin-top: 50px;
}
.more-tools h3 {
  margin-bottom: 16px;
  color: #aaa;
  font-size: 1em;
}
.tools-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.tool-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #1a1a2e;
  border-radius: 12px;
  padding: 20px;
  text-decoration: none;
  transition: transform 0.2s, border-color 0.2s;
  border: 1px solid #2a2a3e;
}
.tool-card:hover {
  transform: translateY(-3px);
  border-color: #667eea;
}
.tool-icon {
  font-size: 2em;
  flex-shrink: 0;
}
.tool-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.tool-name {
  color: #e0e0e0;
  font-weight: 600;
  font-size: 0.95em;
}
.tool-desc {
  color: #888;
  font-size: 0.8em;
}
@media (max-width: 500px) {
  .tools-grid { grid-template-columns: 1fr; }
}
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }
</style>
