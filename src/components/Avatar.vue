<template>
  <div class="avatar-container" :class="{ speaking }"
       :style="{ '--hair': hairColor, '--skin': skinColor, '--suit': suitColor }">
    <div class="avatar-body">
      <div class="avatar-head">
        <!-- 头发 -->
        <div class="hair"></div>
        <!-- 脸 -->
        <div class="face">
          <!-- 眼睛 -->
          <div class="eyes">
            <div class="eye left"><div class="pupil"></div></div>
            <div class="eye right"><div class="pupil"></div></div>
          </div>
          <!-- 嘴巴 -->
          <div class="mouth" :class="{ open: mouthOpen }"></div>
          <!-- 真人照片覆盖 -->
          <img v-if="photoUrl" :src="photoUrl" class="avatar-photo" />
        </div>
      </div>
      <!-- 身体 -->
      <div class="body-suit"></div>
    </div>
    <div class="name-tag" v-if="name">{{ name }}</div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  speaking: { type: Boolean, default: false },
  name: { type: String, default: 'AI 讲师' },
  hairColor: { type: String, default: '#2c2c3a' },
  skinColor: { type: String, default: '#f5d6b8' },
  suitColor: { type: String, default: '#667eea' },
  photoUrl: { type: String, default: null }
})

const mouthOpen = ref(false)
let mouthTimer = null

watch(() => props.speaking, (val) => {
  if (val) {
    // 说话时嘴巴随机开合
    mouthTimer = setInterval(() => {
      mouthOpen.value = !mouthOpen.value
    }, 150 + Math.random() * 100)
  } else {
    clearInterval(mouthTimer)
    mouthOpen.value = false
  }
})

onUnmounted(() => clearInterval(mouthTimer))
</script>

<style scoped>
.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  user-select: none;
}
.avatar-body {
  position: relative;
  width: 120px;
  height: 160px;
}
.avatar-head {
  position: relative;
  width: 80px;
  height: 90px;
  margin: 0 auto;
  z-index: 2;
}
.hair {
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  height: 45px;
  background: var(--hair);
  border-radius: 40px 40px 0 0;
  z-index: 1;
}
.face {
  position: absolute;
  top: 10px;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--skin);
  border-radius: 40px 40px 30px 30px;
  overflow: hidden;
}
.avatar-photo {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  border-radius: 40px 40px 30px 30px;
  z-index: 2;
}
.eyes {
  display: flex;
  justify-content: center;
  gap: 18px;
  margin-top: 25px;
}
.eye {
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  position: relative;
  animation: blink 4s infinite;
}
.pupil {
  width: 6px;
  height: 6px;
  background: var(--hair);
  border-radius: 50%;
  position: absolute;
  top: 3px;
  left: 3px;
  transition: transform 0.3s;
}
.speaking .pupil {
  animation: lookAround 3s ease-in-out infinite;
}
@keyframes blink {
  0%, 95%, 100% { transform: scaleY(1); }
  97% { transform: scaleY(0.1); }
}
@keyframes lookAround {
  0%, 100% { transform: translateX(0); }
  30% { transform: translateX(2px); }
  70% { transform: translateX(-2px); }
}
.mouth {
  width: 14px;
  height: 6px;
  background: #c0392b;
  border-radius: 0 0 7px 7px;
  margin: 12px auto 0;
  transition: all 0.1s;
}
.mouth.open {
  height: 12px;
  width: 16px;
  border-radius: 4px 4px 10px 10px;
}
.body-suit {
  position: absolute;
  bottom: 0;
  left: 10px;
  right: 10px;
  height: 75px;
  background: linear-gradient(180deg, var(--suit), color-mix(in srgb, var(--suit), #000 15%));
  border-radius: 30px 30px 10px 10px;
  z-index: 1;
}
.body-suit::before {
  content: '';
  position: absolute;
  top: 15px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
}
.speaking .avatar-head {
  animation: headBob 0.6s ease-in-out infinite alternate;
}
@keyframes headBob {
  from { transform: translateY(0) rotate(-1deg); }
  to { transform: translateY(-3px) rotate(1deg); }
}
.name-tag {
  margin-top: 8px;
  font-size: 0.8em;
  color: #aaa;
  background: rgba(102,126,234,0.15);
  padding: 3px 12px;
  border-radius: 10px;
}
</style>
