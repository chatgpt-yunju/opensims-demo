<template>
  <div class="present" :class="{ fullscreen }" v-if="slides.length">
    <!-- 顶栏 -->
    <div class="topbar">
      <button class="btn-back" @click="$router.push('/')">← 返回</button>
      <span class="slide-counter">{{ current + 1 }} / {{ slides.length }}</span>
      <div class="topbar-right">
        <button class="btn-share" @click="shareLink">🔗 分享</button>
        <button class="btn-edit-topbar" @click="startEditScript">✏️ 编辑讲稿</button>
        <button class="btn-auto" :class="{ active: autoPlay }" @click="toggleAuto">
          {{ autoPlay ? '⏸ 停止' : '▶ 自动播放' }}
        </button>
      </div>
    </div>

    <!-- 主体 -->
    <div class="main-area">
      <!-- 幻灯片 -->
      <div class="slide-panel">
        <img :src="slides[current].image" :key="current" class="slide-img" />
      </div>

      <!-- 右侧面板 -->
      <div class="side-panel">
        <!-- 数字人 + 选择 -->
        <div class="avatar-section">
          <Avatar :speaking="isSpeaking"
                  :name="currentAvatar.name"
                  :hairColor="currentAvatar.hair"
                  :skinColor="currentAvatar.skin"
                  :suitColor="currentAvatar.suit"
                  :photoUrl="customPhotoUrl" />
          <div class="avatar-picker">
            <div v-for="a in avatars" :key="a.id"
                 :class="['avatar-option', { active: selectedAvatarId === a.id }]"
                 :title="a.name"
                 @click="selectAvatar(a.id)">
              <span class="avatar-dot" :style="{ background: a.suit }"></span>
            </div>
          </div>
          <input type="file" ref="photoInput" accept="image/*" style="display:none" @change="uploadAvatarPhoto" />
          <button class="btn-upload-photo" @click="photoInput.click()">📷 上传照片</button>
        </div>
        <!-- 音色选择 -->
        <div class="voice-section">
          <select v-model="selectedVoice" @change="changeVoice" :disabled="voiceLoading">
            <option v-for="v in voices" :key="v.id" :value="v.id">{{ v.name }} - {{ v.desc }}</option>
          </select>
          <span v-if="voiceLoading" class="voice-status">语音生成中...</span>
        </div>
        <!-- 讲解词（可编辑） -->
        <div class="script-section">
          <div v-if="!editingScript" class="script-text" @dblclick="startEditScript">
            {{ slides[current].script }}
            <button class="btn-edit-script" @click="startEditScript">✏️ 编辑</button>
          </div>
          <div v-else class="script-edit">
            <textarea v-model="editScriptText" rows="6"></textarea>
            <div class="script-edit-actions">
              <button class="btn-save" @click="saveScript" :disabled="savingScript">{{ savingScript ? '保存中...' : '保存' }}</button>
              <button class="btn-cancel" @click="cancelEditScript">取消</button>
            </div>
          </div>
        </div>
        <!-- 互动问答 -->
        <div class="chat-section" v-show="false">
          <div class="chat-messages" ref="chatBox">
            <div v-for="(msg, i) in chatMessages" :key="i"
                 :class="['chat-msg', msg.role]">
              {{ msg.content }}
            </div>
          </div>
          <div class="chat-input-row">
            <input v-model="chatInput" placeholder="对当前页面提问..."
                   @keyup.enter="sendChat" :disabled="chatLoading" />
            <button @click="sendChat" :disabled="chatLoading || !chatInput.trim()">发送</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部控制 -->
    <div class="controls">
      <button @click="prev" :disabled="current === 0">⬅ 上一页</button>
      <button @click="playCurrentAudio" class="btn-play">
        {{ isSpeaking ? '⏸ 暂停' : '🔊 播放讲解' }}
      </button>
      <button @click="next" :disabled="current === slides.length - 1">下一页 ➡</button>
      <button class="btn-fs" @click="fullscreen = true">⛶ 全屏</button>
    </div>

    <!-- 缩略图 -->
    <div class="thumbnails">
      <div v-for="(s, i) in slides" :key="i"
           :class="['thumb', { active: i === current }]"
           @click="goTo(i)">
        <img :src="s.image" />
        <span>{{ i + 1 }}</span>
      </div>
    </div>

    <!-- 全屏浮动控制 -->
    <div v-if="fullscreen" class="fs-overlay" @click="exitFullscreen">
      <div class="fs-controls" @click.stop>
        <span class="fs-counter">{{ current + 1 }} / {{ slides.length }}</span>
        <button class="fs-stop" @click="exitFullscreen">✕ 退出全屏</button>
      </div>
      <div class="fs-avatar" @click.stop>
        <Avatar :speaking="isSpeaking"
                :name="currentAvatar.name"
                :hairColor="currentAvatar.hair"
                :skinColor="currentAvatar.skin"
                :suitColor="currentAvatar.suit"
                :photoUrl="customPhotoUrl" />
      </div>
    </div>
  </div>

  <!-- 加载中 -->
  <div v-else class="loading-screen">
    <div class="spinner"></div>
    <p>加载演示文稿...</p>
  </div>

  <Transition name="toast">
    <div v-if="showToast" class="toast">链接已复制到剪贴板</div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Avatar from '../components/Avatar.vue'

const route = useRoute()
const router = useRouter()
const slides = ref([])
const current = ref(0)
const isSpeaking = ref(false)
const autoPlay = ref(false)
const fullscreen = ref(false)
const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatBox = ref(null)
const showToast = ref(false)

// Avatar & voice
const avatars = ref([])
const voices = ref([])
const selectedAvatarId = ref('default')
const selectedVoice = ref('zh-CN-XiaoxiaoNeural')
const voiceLoading = ref(false)
const customPhotoUrl = ref(null)
const photoInput = ref(null)
const currentAvatar = computed(() =>
  avatars.value.find(a => a.id === selectedAvatarId.value) ||
  { name: 'AI 讲师', hair: '#2c2c3a', skin: '#f5d6b8', suit: '#667eea' }
)

// Script editing
const editingScript = ref(false)
const editScriptText = ref('')
const savingScript = ref(false)

let audio = null

const handleEscape = (e) => {
  if (e.key === 'Escape' && fullscreen.value) exitFullscreen()
}

onMounted(async () => {
  document.addEventListener('keydown', handleEscape)
  try {
    const [slidesRes, avatarsRes, voicesRes] = await Promise.all([
      fetch(`/api/ppt/${route.params.id}/slides`),
      fetch('/api/ppt/avatars'),
      fetch('/api/ppt/voices')
    ])
    if (!slidesRes.ok) { router.push('/'); return }
    slides.value = await slidesRes.json()
    if (avatarsRes.ok) avatars.value = await avatarsRes.json()
    if (voicesRes.ok) voices.value = await voicesRes.json()
  } catch { router.push('/') }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
  stopAudio()
})

function stopAudio() {
  if (audio) {
    audio.pause()
    audio.currentTime = 0
    audio = null
  }
  isSpeaking.value = false
}

function playCurrentAudio() {
  if (isSpeaking.value) {
    stopAudio()
    return
  }
  const slide = slides.value[current.value]
  if (!slide.audio) return

  audio = new Audio(slide.audio)
  isSpeaking.value = true
  audio.play()
  audio.onended = () => {
    isSpeaking.value = false
    if (autoPlay.value && current.value < slides.value.length - 1) {
      next()
    } else if (autoPlay.value) {
      autoPlay.value = false
      fullscreen.value = false
    }
  }
  audio.onerror = () => { isSpeaking.value = false }
}

function prev() {
  if (current.value > 0) {
    stopAudio()
    current.value--
    if (autoPlay.value) setTimeout(playCurrentAudio, 300)
  }
}
function next() {
  if (current.value < slides.value.length - 1) {
    stopAudio()
    current.value++
    if (autoPlay.value) setTimeout(playCurrentAudio, 300)
  }
}
function goTo(i) {
  stopAudio()
  current.value = i
  if (autoPlay.value) setTimeout(playCurrentAudio, 300)
}

function toggleAuto() {
  autoPlay.value = !autoPlay.value
  if (autoPlay.value) {
    fullscreen.value = true
    playCurrentAudio()
  } else {
    fullscreen.value = false
    stopAudio()
  }
}

function exitFullscreen() {
  fullscreen.value = false
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

// Avatar & voice functions
async function selectAvatar(id) {
  selectedAvatarId.value = id
  try {
    await fetch(`/api/ppt/${route.params.id}/avatar`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ avatarId: id })
    })
  } catch {}
}

async function changeVoice() {
  voiceLoading.value = true
  try {
    await fetch(`/api/ppt/${route.params.id}/voice`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ voice: selectedVoice.value })
    })
    // Poll voice-status
    const poll = async () => {
      const res = await fetch(`/api/ppt/${route.params.id}/voice-status`)
      const data = await res.json()
      if (data.status === 'generating') {
        setTimeout(poll, 2000)
      } else {
        voiceLoading.value = false
        // Refresh slides to get new audio URLs
        const slidesRes = await fetch(`/api/ppt/${route.params.id}/slides`)
        if (slidesRes.ok) slides.value = await slidesRes.json()
      }
    }
    setTimeout(poll, 2000)
  } catch {
    voiceLoading.value = false
  }
}

// Script editing functions
function startEditScript() {
  editScriptText.value = slides.value[current.value].script
  editingScript.value = true
}

function cancelEditScript() {
  editingScript.value = false
}

async function uploadAvatarPhoto(e) {
  const file = e.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('photo', file)
  try {
    const res = await fetch('/api/ppt/avatar-photo', { method: 'POST', body: formData })
    const data = await res.json()
    if (data.url) customPhotoUrl.value = data.url
  } catch {}
}

async function saveScript() {
  savingScript.value = true
  try {
    const res = await fetch(`/api/ppt/${route.params.id}/slides/${current.value}/script`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script: editScriptText.value })
    })
    const data = await res.json()
    if (data.success) {
      slides.value[current.value].script = editScriptText.value
      if (data.audio) slides.value[current.value].audio = data.audio
      editingScript.value = false
    }
  } catch {}
  savingScript.value = false
}

// Reset script editing when changing slides
watch(current, () => {
  editingScript.value = false
})

async function sendChat() {
  const q = chatInput.value.trim()
  if (!q) return
  chatMessages.value.push({ role: 'user', content: q })
  chatInput.value = ''
  chatLoading.value = true
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight

  try {
    const res = await fetch(`/api/ppt/${route.params.id}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, slideIndex: current.value })
    })
    const data = await res.json()
    chatMessages.value.push({ role: 'ai', content: data.answer })
  } catch {
    chatMessages.value.push({ role: 'ai', content: '抱歉，回答失败，请重试。' })
  }
  chatLoading.value = false
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}
</script>

<style scoped>
.present {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0f0f1a;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: #1a1a2e;
  border-bottom: 1px solid #2a2a3e;
}
.btn-back {
  background: none;
  border: none;
  color: #aaa;
  cursor: pointer;
  font-size: 0.95em;
}
.btn-back:hover { color: #fff; }
.slide-counter { color: #888; font-size: 0.9em; }
.topbar-right { display: flex; gap: 8px; align-items: center; }
.btn-share {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #444;
  background: none;
  color: #ccc;
  cursor: pointer;
  font-size: 0.85em;
}
.btn-share:hover { border-color: #667eea; color: #fff; }
.btn-auto {
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid #444;
  background: none;
  color: #ccc;
  cursor: pointer;
  font-size: 0.85em;
}
.btn-auto.active {
  border-color: #667eea;
  color: #667eea;
}
.main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 0;
}
.slide-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: #111122;
  min-width: 0;
}
.slide-img {
  max-width: 100%;
  max-height: calc(100vh - 180px);
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 30px rgba(0,0,0,0.5);
}
.side-panel {
  width: 240px;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  background: #1a1a2e;
  border-left: 1px solid #2a2a3e;
}
.avatar-section {
  padding: 12px;
  display: flex;
  justify-content: center;
  border-bottom: 1px solid #2a2a3e;
}
.script-section {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  border-bottom: 1px solid #2a2a3e;
}
.script-text {
  font-size: 0.9em;
  line-height: 1.7;
  color: #ccc;
}
.chat-section {
  height: 200px;
  display: flex;
  flex-direction: column;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}
.chat-msg {
  margin-bottom: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 0.85em;
  line-height: 1.5;
}
.chat-msg.user {
  background: #667eea;
  color: white;
  margin-left: 20px;
  text-align: right;
}
.chat-msg.ai {
  background: #2a2a3e;
  color: #ddd;
  margin-right: 20px;
}
.chat-input-row {
  display: flex;
  padding: 8px;
  gap: 6px;
  border-top: 1px solid #2a2a3e;
}
.chat-input-row input {
  flex: 1;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #444;
  background: #111;
  color: #eee;
  font-size: 0.85em;
}
.chat-input-row button {
  padding: 6px 14px;
  border-radius: 6px;
  border: none;
  background: #667eea;
  color: white;
  cursor: pointer;
  font-size: 0.85em;
}
.chat-input-row button:disabled {
  opacity: 0.5;
  cursor: default;
}
.controls {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 12px;
  background: #1a1a2e;
  border-top: 1px solid #2a2a3e;
}
.controls button {
  padding: 8px 24px;
  border-radius: 8px;
  border: 1px solid #444;
  background: #222;
  color: #ddd;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
}
.controls button:hover:not(:disabled) {
  border-color: #667eea;
  color: #fff;
}
.controls button:disabled {
  opacity: 0.3;
  cursor: default;
}
.btn-fs {
  background: none !important;
  border-color: #555 !important;
  color: #aaa !important;
}
.btn-fs:hover {
  border-color: #667eea !important;
  color: #fff !important;
}
.btn-play {
  background: linear-gradient(135deg, #667eea, #764ba2) !important;
  border: none !important;
  color: white !important;
}
.thumbnails {
  display: flex;
  gap: 8px;
  padding: 10px 20px;
  overflow-x: auto;
  background: #141425;
}
.thumb {
  flex-shrink: 0;
  width: 64px;
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.2s;
  position: relative;
}
.thumb.active {
  border-color: #667eea;
}
.thumb img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
}
.thumb span {
  position: absolute;
  bottom: 2px;
  right: 4px;
  font-size: 0.7em;
  color: #aaa;
}
.loading-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
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
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* 全屏模式 */
.present.fullscreen .topbar,
.present.fullscreen .side-panel,
.present.fullscreen .controls,
.present.fullscreen .thumbnails {
  display: none !important;
}
.present.fullscreen .main-area {
  height: 100vh;
}
.present.fullscreen .slide-panel {
  padding: 0;
  background: #000;
}
.present.fullscreen .slide-img {
  max-height: 100vh;
  max-width: 100vw;
  border-radius: 0;
}
.fs-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 100;
  pointer-events: none;
}
.fs-controls {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  pointer-events: auto;
  opacity: 0;
  transition: opacity 0.3s;
}
.fs-overlay:hover .fs-controls {
  opacity: 1;
}
.fs-counter {
  color: #fff;
  font-size: 0.9em;
  background: rgba(0,0,0,0.6);
  padding: 6px 14px;
  border-radius: 20px;
}
.fs-stop {
  padding: 6px 16px;
  border-radius: 20px;
  border: none;
  background: rgba(255,255,255,0.15);
  color: #fff;
  cursor: pointer;
  font-size: 0.85em;
  backdrop-filter: blur(8px);
  transition: background 0.2s;
}
.fs-stop:hover {
  background: rgba(255,255,255,0.3);
}
.fs-avatar {
  position: absolute;
  bottom: 24px;
  right: 24px;
  pointer-events: auto;
  background: rgba(0,0,0,0.4);
  border-radius: 50%;
  padding: 8px;
  backdrop-filter: blur(8px);
}

/* Avatar picker */
.avatar-section {
  flex-direction: column;
  align-items: center;
}
.avatar-picker {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  justify-content: center;
}
.avatar-option {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #444;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s;
}
.avatar-option:hover { border-color: #888; }
.avatar-option.active { border-color: #667eea; }
.avatar-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}

/* Voice section */
.voice-section {
  padding: 10px 12px;
  border-bottom: 1px solid #2a2a3e;
  display: flex;
  align-items: center;
  gap: 8px;
}
.voice-section select {
  flex: 1;
  padding: 5px 8px;
  border-radius: 6px;
  border: 1px solid #444;
  background: #111;
  color: #eee;
  font-size: 0.8em;
}
.voice-section select:disabled { opacity: 0.5; }
.voice-status {
  font-size: 0.75em;
  color: #667eea;
  white-space: nowrap;
}

/* Script editing */
.btn-edit-script {
  display: inline-block;
  margin-top: 8px;
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid #444;
  background: none;
  color: #aaa;
  cursor: pointer;
  font-size: 0.8em;
}
.btn-edit-script:hover { border-color: #667eea; color: #fff; }
.script-edit {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.script-edit textarea {
  width: 100%;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #444;
  background: #111;
  color: #eee;
  font-size: 0.85em;
  line-height: 1.6;
  resize: vertical;
}
.script-edit-actions {
  display: flex;
  gap: 8px;
}
.btn-save {
  padding: 5px 16px;
  border-radius: 6px;
  border: none;
  background: #667eea;
  color: white;
  cursor: pointer;
  font-size: 0.8em;
}
.btn-save:disabled { opacity: 0.5; cursor: default; }
.btn-cancel {
  padding: 5px 16px;
  border-radius: 6px;
  border: 1px solid #444;
  background: none;
  color: #aaa;
  cursor: pointer;
  font-size: 0.8em;
}
.btn-cancel:hover { border-color: #667eea; color: #fff; }

/* Upload photo button */
.btn-upload-photo {
  margin-top: 8px;
  padding: 5px 14px;
  border-radius: 14px;
  border: 1px solid #444;
  background: none;
  color: #aaa;
  cursor: pointer;
  font-size: 0.8em;
}
.btn-upload-photo:hover { border-color: #667eea; color: #fff; }

/* Topbar edit script button */
.btn-edit-topbar {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #444;
  background: none;
  color: #ccc;
  cursor: pointer;
  font-size: 0.85em;
}
.btn-edit-topbar:hover { border-color: #667eea; color: #fff; }
</style>
