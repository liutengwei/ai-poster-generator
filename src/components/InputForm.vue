<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGenerateStore, GenerateParams } from '@/stores/generate'

const store = useGenerateStore()

const materialTypes = [
  { value: 'poster', label: '海报', icon: '🖼' },
  { value: 'article', label: '公众号推文', icon: '📝' },
  { value: 'newsletter', label: '简报', icon: '📋' },
]

const colorPalettes = [
  { value: 'government', label: '政务蓝', colors: ['#1e40af', '#3b82f6', '#93c5fd'] },
  { value: 'china-red', label: '中国红', colors: ['#dc2626', '#ef4444', '#fca5a5'] },
  { value: 'ink-green', label: '墨绿', colors: ['#059669', '#10b981', '#6ee7b7'] },
  { value: 'warm-orange', label: '暖橙', colors: ['#ea580c', '#f97316', '#fdba74'] },
]

const formState = ref({
  type: 'poster' as 'poster' | 'article' | 'newsletter',
  title: '',
  content: '',
  color_theme: 'government' as 'government' | 'china-red' | 'ink-green' | 'warm-orange',
})

// 模拟图片上传区域 - 实际项目中需要结合 el-upload 或类似组件
const uploadedImages = ref<string[]>([])

const handleTypeSelect = (value: string) => {
  formState.value.type = value as GenerateParams['type']
}

const handleTitleInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  formState.value.title = target.value
}

const handleContentInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  formState.value.content = target.value
}

const handleColorSelect = (value: string) => {
  formState.value.color_theme = value as GenerateParams['color_theme']
}

// 处理图片上传
const handleImageUpload = (images: string[]) => {
  uploadedImages.value = images.slice(0, 6)
}

// 触发文件选择
const triggerFileInput = () => {
  const input = document.getElementById('file-input') as HTMLInputElement
  input?.click()
}

// 处理文件选择
const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = Array.from(target.files || [])
  if (files.length === 0) return

  const imageFiles = files.filter((file) => file.type.startsWith('image/'))
  if (imageFiles.length === 0) return

  imageFiles.forEach((file) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      const result = event.target?.result as string
      uploadedImages.value = [...uploadedImages.value, result].slice(0, 6)
    }
    reader.readAsDataURL(file)
  })
  target.value = ''
}

const handleGenerate = () => {
  // 校验
  if (!formState.value.title.trim()) {
    alert('请输入标题')
    return
  }
  if (!formState.value.content.trim()) {
    alert('请输入正文内容')
    return
  }
  if (uploadedImages.value.length === 0) {
    alert('请至少上传1张图片')
    return
  }

  store.startLayoutAnalysis({
    type: formState.value.type,
    title: formState.value.title,
    content: formState.value.content,
    color_theme: formState.value.color_theme,
    images: uploadedImages.value,
  })
}

// 检查是否正在生成
const isLoading = computed(() => store.isGenerating)
</script>

<template>
<div class="input-form gradient-border">
    <div class="form-inner">
      <!-- Material Type Selection -->
      <div class="form-section" style="animation-delay: 0.1s">
        <label class="form-label">
          <span class="label-text">素材类型</span>
        </label>
        <div class="type-options">
          <button
            v-for="type in materialTypes"
            :key="type.value"
            :class="['type-btn', { active: formState.type === type.value }]"
            @click="handleTypeSelect(type.value)"
          >
            <span class="type-icon">{{ type.icon }}</span>
            <span class="type-label">{{ type.label }}</span>
          </button>
        </div>
      </div>

      <!-- Title Input -->
      <div class="form-section" style="animation-delay: 0.15s">
        <label class="form-label">
          <span class="label-text">标题</span>
          <span class="required">*</span>
        </label>
        <div class="input-wrapper">
          <input
            type="text"
            class="text-input input-glow"
            placeholder="请输入标题"
            :value="formState.title"
            @input="handleTitleInput"
          />
        </div>
      </div>

      <!-- Content Textarea -->
      <div class="form-section" style="animation-delay: 0.2s">
        <label class="form-label">
          <span class="label-text">正文内容</span>
          <span class="required">*</span>
        </label>
        <div class="input-wrapper">
          <textarea
            class="textarea-input input-glow"
            placeholder="请直接粘贴或输入正文内容..."
            rows="8"
            :value="formState.content"
            @input="handleContentInput"
          ></textarea>
        </div>
      </div>

      <!-- Color Palette Selection -->
      <div class="form-section" style="animation-delay: 0.25s">
        <label class="form-label">
          <span class="label-text">配色方向</span>
        </label>
        <div class="color-options">
          <button
            v-for="palette in colorPalettes"
            :key="palette.value"
            :class="['color-card', { active: formState.color_theme === palette.value }]"
            @click="handleColorSelect(palette.value)"
          >
            <div class="color-gradient" :style="{ background: `linear-gradient(135deg, ${palette.colors[0]}, ${palette.colors[1]}, ${palette.colors[2]})` }"></div>
            <span class="color-label">{{ palette.label }}</span>
          </button>
        </div>
      </div>

      <!-- Image Upload Area -->
      <div class="form-section" style="animation-delay: 0.3s">
        <label class="form-label">
          <span class="label-text">图片上传</span>
          <span class="upload-hint">（最多6张）</span>
        </label>
        <input
          id="file-input"
          type="file"
          accept="image/*"
          multiple
          style="display: none"
          @change="handleFileChange"
        />
        <div class="upload-area" @click="triggerFileInput">
          <div class="upload-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>点击或拖拽上传图片</span>
          </div>
        </div>
        <!-- 实际项目中这里需要集成 el-upload 或类似组件 -->
        <!-- 为演示目的，模拟已有图片显示 -->
        <div v-if="uploadedImages.length > 0" class="uploaded-images">
          <div v-for="(img, idx) in uploadedImages" :key="idx" class="uploaded-image">
            <img :src="img" alt="" />
          </div>
        </div>
      </div>

      <!-- Generate Button -->
      <div class="form-section" style="animation-delay: 0.35s">
        <button
          class="generate-btn btn-glow"
          :class="{ loading: isLoading }"
          :disabled="isLoading"
          @click="handleGenerate"
        >
          <span v-if="!isLoading" class="btn-content">
            <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" />
            </svg>
            <span class="btn-text">✨ 生成排版</span>
          </span>
          <span v-else class="btn-loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.input-form {
  border-radius: 20px;
  padding: 2px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(168, 85, 247, 0.2), rgba(236, 72, 153, 0.2));
}

.form-inner {
  background: var(--color-card);
  border-radius: 18px;
  padding: 28px;
}

.form-section {
  margin-bottom: 24px;
  animation: fadeInUp 0.5s ease-out both;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.label-text {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 13px;
  font-weight: 500;
  color: #9ca3af;
  letter-spacing: 1px;
}

.required {
  color: #ef4444;
  font-size: 12px;
}

.upload-hint {
  font-size: 11px;
  color: #6b7280;
}

/* Type Options */
.type-options {
  display: flex;
  gap: 12px;
}

.type-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 12px;
  background: rgba(15, 17, 23, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.type-btn:hover {
  border-color: rgba(99, 102, 241, 0.4);
  background: rgba(99, 102, 241, 0.08);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
}

.type-btn.active {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.15);
  box-shadow: 0 0 0 1px #6366f1, 0 8px 32px rgba(99, 102, 241, 0.25);
}

.type-icon {
  font-size: 26px;
  filter: grayscale(0);
  transition: transform 0.3s ease;
}

.type-btn:hover .type-icon {
  transform: scale(1.1);
}

.type-label {
  font-size: 13px;
  color: #9ca3af;
  transition: color 0.2s;
  font-weight: 500;
}

.type-btn:hover .type-label,
.type-btn.active .type-label {
  color: #f3f4f6;
}

/* Text Input */
.input-wrapper {
  position: relative;
}

.text-input {
  width: 100%;
  padding: 15px 18px;
  background: rgba(15, 17, 23, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  font-size: 15px;
  color: #f3f4f6;
  transition: all 0.25s ease;
  font-family: 'Noto Sans SC', sans-serif;
}

.text-input::placeholder {
  color: #4b5563;
}

.text-input:hover {
  border-color: rgba(255, 255, 255, 0.12);
}

.text-input:focus {
  border-color: #6366f1;
  background: rgba(15, 17, 23, 0.8);
}

/* Textarea */
.textarea-input {
  width: 100%;
  padding: 15px 18px;
  background: rgba(15, 17, 23, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  font-size: 15px;
  color: #f3f4f6;
  transition: all 0.25s ease;
  resize: vertical;
  min-height: 200px;
  font-family: 'Noto Sans SC', sans-serif;
  line-height: 1.7;
}

.textarea-input::placeholder {
  color: #4b5563;
}

.textarea-input:hover {
  border-color: rgba(255, 255, 255, 0.12);
}

.textarea-input:focus {
  border-color: #6366f1;
  background: rgba(15, 17, 23, 0.8);
}

/* Color Options */
.color-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.color-card {
  position: relative;
  padding: 0;
  background: rgba(15, 17, 23, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.color-card:hover {
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.color-card.active {
  border-color: transparent;
  box-shadow: 0 0 0 2px #6366f1, 0 0 24px rgba(99, 102, 241, 0.3);
  animation: selectPulse 0.4s ease-out;
}

@keyframes selectPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.03); }
  100% { transform: scale(1); }
}

.color-gradient {
  height: 52px;
  width: 100%;
  transition: filter 0.3s ease;
}

.color-card:hover .color-gradient {
  filter: brightness(1.1);
}

.color-label {
  display: block;
  padding: 10px;
  font-size: 13px;
  color: #9ca3af;
  text-align: center;
  transition: color 0.2s;
  font-weight: 500;
}

.color-card:hover .color-label,
.color-card.active .color-label {
  color: #f3f4f6;
}

/* Upload Area */
.upload-area {
  border: 2px dashed rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
  background: rgba(15, 17, 23, 0.3);
}

.upload-area:hover {
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(99, 102, 241, 0.05);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #6b7280;
}

.upload-placeholder svg {
  width: 32px;
  height: 32px;
  opacity: 0.5;
}

.upload-placeholder span {
  font-size: 13px;
}

.uploaded-images {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.uploaded-image {
  aspect-ratio: 1;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.uploaded-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Generate Button */
.generate-btn {
  width: 100%;
  padding: 18px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  background-size: 200% 200%;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: 'Noto Sans SC', sans-serif;
  position: relative;
  overflow: hidden;
}

.generate-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.25) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.generate-btn:hover:not(:disabled)::before {
  opacity: 1;
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.45);
  background-position: right center;
}

.generate-btn:active:not(:disabled) {
  transform: translateY(-1px);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.generate-btn.loading {
  background: linear-gradient(135deg, #4b5563 0%, #6b7280 100%);
  background-size: 200% 200%;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.btn-icon {
  width: 22px;
  height: 22px;
}

.btn-text {
  letter-spacing: 2px;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.loading-dot {
  width: 8px;
  height: 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: loadingBounce 1.2s ease-in-out infinite;
}

.loading-dot:nth-child(1) { animation-delay: 0s; }
.loading-dot:nth-child(2) { animation-delay: 0.15s; }
.loading-dot:nth-child(3) { animation-delay: 0.3s; }

@keyframes loadingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>