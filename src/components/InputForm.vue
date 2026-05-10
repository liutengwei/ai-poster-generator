<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useGenerateStore, GenerateParams } from '@/stores/generate'

const router = useRouter()
const store = useGenerateStore()

const materialTypes = [
  { value: 'article', label: '公众号推文', icon: '📝' },
  { value: 'expense', label: '报销凭证', icon: '🧾' },
]

const formState = ref({
  type: 'article' as 'article' | 'expense',
  title: '',
  content: '',
})

const uploadedImages = ref<string[]>([])
const shouldPolish = ref(false)
const isPolishing = ref(false)

// 报销凭证相关
const expenseFiles = ref<string[]>([])
const expenseFilenames = ref<string[]>([])
const isChecking = ref(false)
const expenseError = ref('')
const expenseResult = ref<any>(null)


const isExpenseType = computed(() => formState.value.type === 'expense')

const handleTypeSelect = (value: string) => {
  formState.value.type = value as GenerateParams['type']
  store.currentParams.type = value as GenerateParams['type']  // ← 加这行
  if (value === 'expense') {
    store.clearExpenseResult()
    store.clearPreviewPdfUrl()
    expenseError.value = ''
  }
}

const handleTitleInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  formState.value.title = target.value
}

const handleContentInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  formState.value.content = target.value
}

const polishContent = async () => {
  if (!formState.value.content.trim()) return
  isPolishing.value = true
  try {
    const api = axios.create({ baseURL: '/api', timeout: 60000 })
    const typeLabels: Record<string, string> = { poster: '海报', article: '公众号推文', newsletter: '简报' }
    const response = await api.post('/generate/layout', {
      type: formState.value.type,
      title: formState.value.title,
      content: formState.value.content,
      image_count: 0,
      image_sizes: [],
      polish: true,
    })
    if (response.data.polished_content) {
      formState.value.content = response.data.polished_content
    }
  } catch (e) {
    console.error('Polish failed:', e)
  } finally {
    isPolishing.value = false
  }
}

const handleImageUpload = (images: string[]) => {
  uploadedImages.value = images.slice(0, 6)
}

const triggerFileInput = () => {
  const input = document.getElementById('file-input') as HTMLInputElement
  input?.click()
}

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

// 报销凭证文件上传
const triggerExpenseFileInput = () => {
  const input = document.getElementById('expense-file-input') as HTMLInputElement
  input?.click()
}

const handleExpenseFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = Array.from(target.files || [])
  if (files.length === 0) return

  const validFiles = files.filter((f) =>
    ['image/jpeg', 'image/bmp', 'image/png', 'application/pdf'].includes(f.type)
  )

  // 同步读取，保持顺序
  let readIdx = 0
  const dataUrls: string[] = []
  const filenames: string[] = []

  const processNext = () => {
    if (readIdx >= validFiles.length) {
      expenseFiles.value = [...expenseFiles.value, ...dataUrls].slice(0, 20)
      expenseFilenames.value = [...expenseFilenames.value, ...filenames].slice(0, 20)
      target.value = ''
      return
    }
    const file = validFiles[readIdx]
    filenames.push(file.name)
    const reader = new FileReader()
    reader.onload = (event) => {
      dataUrls.push(event.target?.result as string)
      readIdx++
      processNext()
    }
    reader.readAsDataURL(file)
  }

  processNext()
}

const removeExpenseFile = (idx: number) => {
  expenseFiles.value.splice(idx, 1)
  expenseFilenames.value.splice(idx, 1)
  store.clearPreviewPdfUrl()
}

const handleExpenseCheck = async () => {
  if (expenseFiles.value.length === 0) {
    expenseError.value = '请至少上传一张凭证'
    return
  }

  isChecking.value = true
  expenseError.value = ''

  try {
    const formData = new FormData()
    for (let i = 0; i < expenseFiles.value.length; i++) {
      const dataUrl = expenseFiles.value[i]
      const parts = dataUrl.split(',')
      const meta = parts[0]
      const base64 = parts[1]
      const mime = meta.match(/:(.*?);/)?.[1] || 'image/jpeg'
      const filename = expenseFilenames.value[i] || `凭证_${i}.${mime.includes('pdf') ? 'pdf' : 'jpg'}`

      const binary = atob(base64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i)
      }
      const blob = new Blob([bytes], { type: mime })
      formData.append('files', new File([blob], filename, { type: mime }))
    }

    const response = await fetch('/api/expense/check-and-merge', {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(err.detail || '审核失败')
    }

    const result = await response.json()
    // 按日期排序，无日期的排最后
    result.passed = result.passed.sort((a: any, b: any) => {
      if (!a.date) return 1
      if (!b.date) return -1
      return a.date.localeCompare(b.date)  // 字符串比较，YYYY-MM-DD 格式天然可排序
    })
    expenseResult.value = result
    store.setExpenseResult(result)
    store.currentParams.type = 'expense'
    if (result.passed?.length) {
      await generatePreview(result)
    }
  } catch (e: any) {
    expenseError.value = e.message || '审核过程出错'
  } finally {
    isChecking.value = false
  }
}

const generatePreview = async (result?: any) => {
  const data = result || store.expenseResult
  if (!data?.passed?.length) return

  isChecking.value = true
  try {
    const formData = new FormData()
    for (let i = 0; i < expenseFiles.value.length; i++) {
      const dataUrl = expenseFiles.value[i]
      const parts = dataUrl.split(',')
      const meta = parts[0]
      const base64 = parts[1]
      const mime = meta.match(/:(.*?);/)?.[1] || 'image/jpeg'
      const filename = expenseFilenames.value[i] || `凭证_${i}.${mime.includes('pdf') ? 'pdf' : 'jpg'}`

      const binary = atob(base64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
      const blob = new Blob([bytes], { type: mime })
      formData.append('files', new File([blob], filename, { type: mime }))
    }

    const passedFiles = data.passed.map((p: any) => `${p.source_file}:${p.page_num}`)
    formData.append('page_order', passedFiles.join(','))

    const response = await fetch('/api/expense/merge-upload', {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) throw new Error('生成预览失败')

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    store.setPreviewPdfUrl(url)
  } catch (e: any) {
    expenseError.value = e.message || '生成预览失败'
  } finally {
    isChecking.value = false
  }
}

const handleExpenseMerge = async () => {
  if (!store.expenseResult?.passed?.length) return

  isChecking.value = true
  try {
    const formData = new FormData()
    for (let i = 0; i < expenseFiles.value.length; i++) {
      const dataUrl = expenseFiles.value[i]
      const parts = dataUrl.split(',')
      const base64 = parts[1]
      const mime = parts[0].match(/:(.*?);/)?.[1] || 'image/jpeg'
      const filename = expenseFilenames.value[i] || `凭证_${i}.${mime.includes('pdf') ? 'pdf' : 'jpg'}`

      const binary = atob(base64)
      const bytes = new Uint8Array(binary.length)
      for (let j = 0; j < binary.length; j++) {
        bytes[j] = binary.charCodeAt(j)
      }
      const blob = new Blob([bytes], { type: mime })
      formData.append('files', new File([blob], filename, { type: mime }))
    }

    const passedFiles = store.expenseResult?.passed?.map(
      (p: any) => `${p.source_file}:${p.page_num}`
    )
    formData.append('page_order', passedFiles.join(','))

    const response = await fetch('/api/expense/merge-upload', {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error('合并失败')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `报销凭证_${new Date().toISOString().slice(0, 10)}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    expenseError.value = e.message || '合并失败'
  } finally {
    isChecking.value = false
  }
}

const handleGenerate = async () => {
  if (isExpenseType.value) {
    await handleExpenseCheck()
    return
  }

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

  if (shouldPolish.value) {
    await polishContent()
  }

  store.startLayoutAnalysis({
    type: formState.value.type,
    title: formState.value.title,
    content: formState.value.content,
    images: uploadedImages.value,
    color_theme: 'government',
  })
}

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

      <!-- 报销凭证模式 -->
      <template v-if="isExpenseType">
        <!-- 报销凭证说明 -->
        <div class="form-section expense-intro">
          <p>上传发票、收据等凭证图片或PDF，AI自动识别章印、签字，审核通过后可合并导出PDF。</p>
        </div>

        <!-- 报销凭证文件上传 -->
        <div class="form-section" style="animation-delay: 0.15s">
          <label class="form-label">
            <span class="label-text">凭证上传</span>
            <span class="upload-hint">（支持 JPG/BMP/PDF，最多20张）</span>
          </label>
          <input
            id="expense-file-input"
            type="file"
            accept="image/jpeg,image/bmp,image/png,application/pdf"
            multiple
            style="display: none"
            @change="handleExpenseFileChange"
          />
          <div class="upload-area" @click="triggerExpenseFileInput">
            <div class="upload-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>点击或拖拽上传凭证</span>
            </div>
          </div>

          <div v-if="expenseFiles.length > 0" class="uploaded-files">
            <div v-for="(img, idx) in expenseFiles" :key="idx" class="uploaded-thumb expense-thumb">
              <img :src="img" alt="" />
              <button class="remove-btn" @click.stop="removeExpenseFile(idx)">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 审核结果 -->
        <template v-if="store.expenseResult">
          <div class="form-section expense-result">
            <div class="summary-cards">
              <div class="summary-card">
                <span class="summary-num">{{ store.expenseResult.summary.total }}</span>
                <span class="summary-label">总页数</span>
              </div>
              <div class="summary-card passed">
                <span class="summary-num">{{ store.expenseResult.summary.passed }}</span>
                <span class="summary-label">合格</span>
              </div>
              <div class="summary-card rejected">
                <span class="summary-num">{{ store.expenseResult.summary.rejected }}</span>
                <span class="summary-label">不合格</span>
              </div>
              <div class="summary-card amount">
                <span class="summary-num">¥{{ store.expenseResult.summary.total_amount }}</span>
                <span class="summary-label">金额合计</span>
              </div>
            </div>
          </div>
        </template>

        <div v-if="expenseError" class="error-msg">{{ expenseError }}</div>
        
        <!-- 生成按钮 -->
        <div class="form-section" style="animation-delay: 0.2s">
          <button
              class="generate-btn btn-glow"
              :class="{ loading: isChecking }"
              :disabled="isChecking"
              @click="handleGenerate"
          >
    <span v-if="!isChecking" class="btn-content">
      <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
        <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" />
      </svg>
      <span class="btn-text">{{ store.expenseResult ? '重新审核' : 'AI 审核凭证' }}</span>
    </span>
            <span v-else class="btn-loading">
      <div class="loading-dot"></div>
      <div class="loading-dot"></div>
      <div class="loading-dot"></div>
    </span>
          </button>

          <!-- 审核通过后显示合并导出按钮 -->
          <button
              v-if="store.expenseResult?.passed?.length"
              class="generate-btn btn-glow"
              style="margin-top: 12px; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%)"
              :disabled="isChecking"
              @click="handleExpenseMerge"
          >
    <span class="btn-content">
      <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
      </svg>
      <span class="btn-text">合并导出 PDF</span>
    </span>
          </button>
        </div>
      </template>

      <!-- 普通素材模式 -->
      <template v-else>
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
          <div class="polish-option">
            <label class="checkbox-label">
              <input type="checkbox" v-model="shouldPolish" class="checkbox-input" />
              <span class="checkbox-text">使用 AI 润色文案</span>
            </label>
            <span v-if="isPolishing" class="polish-loading">润色中...</span>
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
      </template>
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

/* Polish Option */
.polish-option {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  width: 16px;
  height: 16px;
  accent-color: #6366f1;
  cursor: pointer;
}

.checkbox-text {
  font-size: 13px;
  color: #9ca3af;
}

.polish-loading {
  font-size: 12px;
  color: #6366f1;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
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

/* Expense Form Styles */
.expense-intro {
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 20px;
}

.expense-intro p {
  font-size: 13px;
  color: #9ca3af;
  line-height: 1.6;
  margin: 0;
}

.uploaded-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.uploaded-thumb {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.uploaded-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.expense-thumb {
  width: 60px;
  height: 60px;
}

.remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  background: rgba(0, 0, 0, 0.7);
  border: none;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn svg {
  width: 10px;
  height: 10px;
}

/* Expense Result */
.expense-result {
  margin-top: 8px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.summary-card {
  background: rgba(15, 17, 23, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 10px 8px;
  text-align: center;
}

.summary-num {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #f3f4f6;
  margin-bottom: 2px;
}

.summary-label {
  font-size: 10px;
  color: #6b7280;
}

.summary-card.passed .summary-num { color: #22c55e; }
.summary-card.rejected .summary-num { color: #ef4444; }
.summary-card.amount .summary-num { color: #f59e0b; }

.error-msg {
  color: #ef4444;
  font-size: 13px;
  text-align: center;
  margin-top: 8px;
}
</style>