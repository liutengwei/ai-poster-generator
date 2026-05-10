<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

interface PageItem {
  source_file: string
  page_num: number
  thumbnail: string
  description: string
  date: string | null
  type: string
  amount: number | null
  reject_reason?: string
  has_applicant?: boolean
  approval_status?: string
}

interface CheckResult {
  passed: PageItem[]
  rejected: PageItem[]
  summary: {
    total: number
    passed: number
    rejected: number
    total_amount: number
  }
}

const uploadedFiles = ref<string[]>([])
const uploadedFilenames = ref<string[]>([])
const isChecking = ref(false)
const checkResult = ref<CheckResult | null>(null)
const isMerging = ref(false)
const isExporting = ref(false)
const errorMsg = ref('')
const previewPdfUrl = ref<string | null>(null)

const triggerFileInput = () => {
  const input = document.getElementById('expense-file-input') as HTMLInputElement
  input?.click()
}

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = Array.from(target.files || [])
  if (files.length === 0) return

  const imageFiles = files.filter((f) =>
    ['image/jpeg', 'image/bmp', 'image/png', 'application/pdf'].includes(f.type)
  )

  imageFiles.forEach((file) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      const result = event.target?.result as string
      uploadedFiles.value = [...uploadedFiles.value, result].slice(0, 20)
      uploadedFilenames.value = [...uploadedFilenames.value, file.name].slice(0, 20)
    }
    reader.readAsDataURL(file)
  })
  target.value = ''
}

const removeFile = (idx: number) => {
  uploadedFiles.value.splice(idx, 1)
  uploadedFilenames.value.splice(idx, 1)
  previewPdfUrl.value = null
}

const buildFormData = () => {
  const formData = new FormData()
  for (let i = 0; i < uploadedFiles.value.length; i++) {
    const dataUrl = uploadedFiles.value[i]
    const base64 = dataUrl.split(',')[1]
    const mime = dataUrl.split(';')[0].split(':')[1]
    const originalFilename = uploadedFilenames.value[i] || `凭证_${i}.${mime.includes('pdf') ? 'pdf' : 'jpg'}`

    const binary = atob(base64)
    const bytes = new Uint8Array(binary.length)
    for (let j = 0; j < binary.length; j++) {
      bytes[j] = binary.charCodeAt(j)
    }
    const blob = new Blob([bytes], { type: mime })
    formData.append('files', new File([blob], originalFilename, { type: mime }))
  }
  return formData
}

const handleCheck = async () => {
  if (uploadedFiles.value.length === 0) {
    alert('请至少上传一张凭证图片或PDF')
    return
  }

  isChecking.value = true
  errorMsg.value = ''
  checkResult.value = null
  previewPdfUrl.value = null

  try {
    const formData = buildFormData()
    const response = await fetch('/api/expense/check-and-merge', {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(err.detail || '审核失败')
    }

    checkResult.value = await response.json()
  } catch (e: any) {
    errorMsg.value = e.message || '审核过程出错'
  } finally {
    isChecking.value = false
  }
}

const generatePreview = async () => {
  if (!checkResult.value?.passed.length) return

  isExporting.value = true
  try {
    const formData = buildFormData()
    const passedFiles = checkResult.value.passed.map((p) => `${p.source_file}:${p.page_num}`)
    formData.append('page_order', passedFiles.join(','))

    const response = await fetch('/api/expense/merge-upload', {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '生成预览失败' }))
      throw new Error(err.detail || '生成预览失败')
    }

    const blob = await response.blob()
    if (previewPdfUrl.value) {
      URL.revokeObjectURL(previewPdfUrl.value)
    }
    previewPdfUrl.value = URL.createObjectURL(blob)
  } catch (e: any) {
    alert(e.message || '生成预览失败')
  } finally {
    isExporting.value = false
  }
}

const handleMerge = async () => {
  if (!checkResult.value?.passed.length) return

  isMerging.value = true
  try {
    const formData = buildFormData()
    const passedFiles = checkResult.value.passed.map((p) => `${p.source_file}:${p.page_num}`)
    formData.append('page_order', passedFiles.join(','))

    const response = await fetch('/api/expense/merge-upload', {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '合并失败' }))
      throw new Error(err.detail || '合并失败')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `报销凭证_${new Date().toISOString().slice(0, 10)}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    alert(e.message || '合并失败')
  } finally {
    isMerging.value = false
  }
}

const goBack = () => {
  router.push('/')
}
</script>

<template>
  <div class="expense-page">
    <header class="navbar glass">
      <div class="navbar-content">
        <div class="logo">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="logo-text">AI 宣传助手</span>
        </div>
        <nav class="nav-links">
          <RouterLink to="/" class="nav-link">创作</RouterLink>
          <RouterLink to="/history" class="nav-link">历史记录</RouterLink>
          <span class="nav-link active">报销凭证审核</span>
        </nav>
      </div>
      <div class="navbar-divider"></div>
    </header>

    <main class="main-content">
      <div class="expense-container">
        <!-- 两栏布局：左侧上传+结果，右侧预览 -->
        <div class="expense-two-col">
          <!-- 左侧 -->
          <div class="left-col">
            <!-- 顶部返回 + 标题 -->
            <div class="page-header">
              <button class="back-btn" @click="goBack">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/>
                </svg>
                返回创作
              </button>
              <div class="page-title-area">
                <h1 class="page-title">报销凭证审核</h1>
                <p class="page-subtitle">上传发票、收据等凭证，AI 自动识别章印、签字，智能审核并合并导出</p>
              </div>
            </div>

            <!-- 上传区域 -->
            <div class="upload-section">
              <input
                id="expense-file-input"
                type="file"
                accept="image/jpeg,image/bmp,image/png,application/pdf"
                multiple
                style="display: none"
                @change="handleFileChange"
              />
              <div class="upload-area" @click="triggerFileInput">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>点击或拖拽上传凭证（支持 JPG/BMP/PDF，最多20张）</span>
              </div>

              <div v-if="uploadedFiles.length > 0" class="uploaded-files">
                <div v-for="(img, idx) in uploadedFiles" :key="idx" class="uploaded-thumb">
                  <img :src="img" alt="" />
                  <button class="remove-btn" @click.stop="removeFile(idx)">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                  </button>
                </div>
              </div>

              <div class="action-row">
                <button
                  class="check-btn"
                  :disabled="isChecking || uploadedFiles.length === 0"
                  @click="handleCheck"
                >
                  <span v-if="!isChecking">AI 审核凭证</span>
                  <span v-else>审核中...</span>
                </button>
              </div>

              <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
            </div>

            <!-- 审核结果 -->
            <div v-if="checkResult" class="result-section">
              <!-- 摘要 -->
              <div class="summary-cards">
                <div class="summary-card">
                  <span class="summary-num">{{ checkResult.summary.total }}</span>
                  <span class="summary-label">总页数</span>
                </div>
                <div class="summary-card passed">
                  <span class="summary-num">{{ checkResult.summary.passed }}</span>
                  <span class="summary-label">合格</span>
                </div>
                <div class="summary-card rejected">
                  <span class="summary-num">{{ checkResult.summary.rejected }}</span>
                  <span class="summary-label">不合格</span>
                </div>
                <div class="summary-card amount">
                  <span class="summary-num">¥{{ checkResult.summary.total_amount }}</span>
                  <span class="summary-label">金额合计</span>
                </div>
              </div>

              <!-- 合格页面列表 -->
              <div v-if="checkResult.passed.length" class="result-group">
                <h3 class="group-title passed-title">
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707 9.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414l1.293 1.293 3.293-3.293a1 1 0 011.414 1.414z" clip-rule="evenodd"/>
                  </svg>
                  合格凭证 ({{ checkResult.passed.length }})
                </h3>
                <div class="page-list">
                  <div v-for="(page, idx) in checkResult.passed" :key="idx" class="page-card passed">
                    <div class="page-thumb">
                      <img :src="page.thumbnail" alt="" />
                    </div>
                    <div class="page-info">
                      <div class="page-meta">
                        <span class="source-file">{{ page.source_file }}</span>
                        <span class="page-num">第{{ page.page_num }}页</span>
                        <span class="page-type">{{ page.type }}</span>
                        <span v-if="page.amount" class="page-amount">¥{{ page.amount }}</span>
                      </div>
                      <div class="page-desc">{{ page.description }}</div>
                      <div class="page-date">{{ page.date || '无日期' }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 不合格页面 -->
              <div v-if="checkResult.rejected.length" class="result-group">
                <h3 class="group-title rejected-title">
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                  </svg>
                  不合格凭证 ({{ checkResult.rejected.length }})
                </h3>
                <div class="page-list">
                  <div v-for="(page, idx) in checkResult.rejected" :key="idx" class="page-card rejected">
                    <div class="page-thumb">
                      <img :src="page.thumbnail" alt="" />
                    </div>
                    <div class="page-info">
                      <div class="page-meta">
                        <span class="source-file">{{ page.source_file }}</span>
                        <span class="page-num">第{{ page.page_num }}页</span>
                        <span class="reject-tag">{{ page.reject_reason }}</span>
                      </div>
                      <div class="page-desc">{{ page.description }}</div>
                      <div class="page-date">{{ page.date || '无日期' }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 合并导出按钮 -->
              <div class="merge-action">
                <button class="merge-btn" :disabled="isMerging || !checkResult?.passed.length" @click="handleMerge">
                  <span v-if="!isMerging">合并导出 PDF</span>
                  <span v-else>合并中...</span>
                </button>
              </div>
            </div>
          </div>

          <!-- 右侧：固定 PDF 预览面板 -->
          <div class="right-col">
            <div class="preview-panel">
              <div class="preview-panel-title-row">
                <span class="preview-panel-label">凭证预览</span>
                <button
                  class="preview-btn"
                  :disabled="isExporting"
                  @click="generatePreview"
                >
                  {{ previewPdfUrl ? '刷新预览' : '生成预览' }}
                </button>
              </div>

              <!-- PDF预览 -->
              <div v-if="previewPdfUrl" class="pdf-preview">
                <iframe :src="previewPdfUrl" class="pdf-frame"></iframe>
              </div>
              <div v-else class="preview-placeholder">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M14 2v6h6M12 11v6M9 14h6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <p>点击上方"生成预览"按钮<br/>查看合并后的 PDF</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.expense-page {
  min-height: 100vh;
  background: var(--color-bg);
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: #6366f1;
  filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.4));
}

.logo-text {
  font-family: 'ZCOOL XiaoWei', serif;
  font-size: 20px;
  font-weight: 600;
  color: #f3f4f6;
  letter-spacing: 1px;
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-link {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #9ca3af;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: #f3f4f6;
  background: rgba(255, 255, 255, 0.05);
}

.nav-link.active {
  color: #6366f1;
  background: rgba(99, 102, 241, 0.12);
}

.navbar-divider {
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(99, 102, 241, 0.4) 20%,
    rgba(168, 85, 247, 0.4) 50%,
    rgba(236, 72, 153, 0.4) 80%,
    transparent 100%
  );
}

.main-content {
  padding: 32px 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.expense-container {
  width: 100%;
}

/* Two column layout */
.expense-two-col {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 24px;
  align-items: start;
}

.left-col {
  min-width: 0;
}

.right-col {
  position: sticky;
  top: 88px;
}

.preview-panel {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 20px;
  height: 600px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.preview-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.preview-panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.preview-panel-label {
  font-size: 16px;
  font-weight: 600;
  color: #f3f4f6;
}

.preview-panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #f3f4f6;
  margin: 0;
}

.page-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 32px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #9ca3af;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.back-btn:hover {
  border-color: rgba(99, 102, 241, 0.4);
  color: #f3f4f6;
}

.back-btn svg {
  width: 16px;
  height: 16px;
}

.page-title-area {
  flex: 1;
}

.page-title {
  font-family: 'ZCOOL XiaoWei', serif;
  font-size: 24px;
  color: #f3f4f6;
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 13px;
  color: #6b7280;
}

/* Upload Section */
.upload-section {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.upload-area {
  border: 2px dashed rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s;
  color: #6b7280;
}

.upload-area:hover {
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(99, 102, 241, 0.05);
}

.upload-area svg {
  width: 36px;
  height: 36px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.upload-area span {
  display: block;
  font-size: 14px;
}

.uploaded-files {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.uploaded-thumb {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.uploaded-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
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
  width: 12px;
  height: 12px;
}

.action-row {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.check-btn {
  padding: 12px 36px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Noto Sans SC', sans-serif;
}

.check-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

.check-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg {
  margin-top: 12px;
  color: #ef4444;
  font-size: 13px;
  text-align: center;
}

/* Result Section */
.result-section {
  animation: fadeInUp 0.4s ease-out;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.summary-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.summary-num {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #f3f4f6;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 12px;
  color: #6b7280;
}

.summary-card.passed .summary-num { color: #22c55e; }
.summary-card.rejected .summary-num { color: #ef4444; }
.summary-card.amount .summary-num { color: #f59e0b; }

/* Preview Section */
.preview-btn {
  padding: 8px 20px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.4);
  border-radius: 8px;
  color: #818cf8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Noto Sans SC', sans-serif;
}

.preview-btn:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.25);
  border-color: rgba(99, 102, 241, 0.6);
}

.preview-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pdf-preview {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
  min-height: 0;
}

.pdf-frame {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.preview-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: #6b7280;
}

.preview-placeholder svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.preview-placeholder p {
  font-size: 14px;
  margin: 0;
  text-align: center;
}

/* Result Groups */
.result-group {
  margin-bottom: 24px;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
}

.group-title svg {
  width: 18px;
  height: 18px;
}

.passed-title {
  color: #22c55e;
}

.rejected-title {
  color: #ef4444;
}

.page-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-card {
  display: flex;
  gap: 12px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 12px;
}

.page-thumb {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.page-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.page-info {
  flex: 1;
  min-width: 0;
}

.page-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}

.source-file {
  font-size: 12px;
  color: #9ca3af;
}

.page-num {
  font-size: 11px;
  color: #6b7280;
  background: rgba(255, 255, 255, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
}

.page-type {
  font-size: 11px;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.page-amount {
  font-size: 12px;
  color: #22c55e;
  font-weight: 600;
}

.reject-tag {
  font-size: 11px;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.page-desc {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-date {
  font-size: 11px;
  color: #6b7280;
}

/* Merge Action */
.merge-action {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  margin-bottom: 32px;
}

.merge-btn {
  padding: 14px 60px;
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Noto Sans SC', sans-serif;
}

.merge-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(34, 197, 94, 0.5);
}

.merge-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
