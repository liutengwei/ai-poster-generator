<script setup lang="ts">
import { computed } from 'vue'
import { useGenerateStore } from '@/stores/generate'
import { exportWord, exportPdf } from '@/api/generate'

const store = useGenerateStore()

const today = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
})

const canExport = computed(() => store.isAllDone && store.layout.length > 0)

const handleExportWord = async () => {
  if (!canExport.value) return
  try {
    const blob = await exportWord({
      title: store.currentParams.title,
      content: store.currentParams.content,
      layout: store.layout,
      images: store.currentParams.images,
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${store.currentParams.title || 'export'}.docx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Export word failed:', e)
  }
}

const handleExportPdf = async () => {
  if (!canExport.value) return
  try {
    const blob = await exportPdf({
      title: store.currentParams.title,
      content: store.currentParams.content,
      layout: store.layout,
      images: store.currentParams.images,
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${store.currentParams.title || 'export'}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Export pdf failed:', e)
  }
}

// 根据 layout 渲染内容
const renderContent = computed(() => {
  return store.layout.map((item, idx) => {
    if (item.type === 'text') {
      return {
        type: 'text',
        style: item.style || 'body',
        content: item.content || '',
      }
    } else if (item.type === 'image') {
      const imgIdx = item.image_index ?? 0
      const imgSrc = store.currentParams.images[imgIdx] || ''
      return {
        type: 'image',
        src: imgSrc,
        position: item.position || 'inline',
        size: item.size || 'half',
        caption: item.caption || '',
      }
    }
    return null
  }).filter(Boolean)
})
</script>

<template>
  <div class="preview-panel">
    <!-- Empty State -->
    <div v-if="!store.isGenerating && !store.isAllDone" class="empty-state">
      <svg class="empty-illustration" viewBox="0 0 200 200" fill="none">
        <circle cx="100" cy="100" r="80" stroke="rgba(99, 102, 241, 0.12)" stroke-width="1" stroke-dasharray="4 4"/>
        <circle cx="100" cy="100" r="60" stroke="rgba(99, 102, 241, 0.15)" stroke-width="1"/>
        <circle cx="100" cy="100" r="40" stroke="rgba(99, 102, 241, 0.2)" stroke-width="1"/>
        <g transform="translate(70, 70)">
          <rect x="10" y="10" width="50" height="50" rx="8" stroke="#6366f1" stroke-width="2" fill="none"/>
          <path d="M25 35h20M25 45h12" stroke="#6366f1" stroke-width="2" stroke-linecap="round"/>
          <circle cx="42" cy="42" r="10" stroke="#8b5cf6" stroke-width="1.5" fill="none"/>
          <path d="M48 48l8 8" stroke="#a855f7" stroke-width="1.5" stroke-linecap="round"/>
        </g>
        <circle cx="40" cy="60" r="3" fill="rgba(99, 102, 241, 0.3)"/>
        <circle cx="160" cy="80" r="4" fill="rgba(168, 85, 247, 0.3)"/>
        <circle cx="50" cy="140" r="3" fill="rgba(236, 72, 153, 0.3)"/>
        <circle cx="150" cy="130" r="3" fill="rgba(99, 102, 241, 0.3)"/>
      </svg>
      <h3 class="empty-title"><span class="gradient-text">填写左侧表单</span></h3>
      <p class="empty-desc">点击"生成排版"，开启 AI 创作之旅</p>
    </div>

    <!-- Loading State -->
    <div v-else-if="store.isGenerating" class="loading-state">
      <div class="loading-animation">
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
      </div>
      <p class="loading-text">🎨 AI正在分析排版方案...</p>
    </div>

    <!-- Poster Preview -->
    <div v-else-if="store.currentParams.type === 'poster'" class="poster-preview">
      <div class="poster-card">
        <!-- Render layout items -->
        <template v-for="(item, idx) in renderContent" :key="idx">
          <!-- Hero Image -->
          <div v-if="item.type === 'image' && item.position === 'hero'" class="poster-image">
            <img :src="item.src" alt="" />
            <div v-if="item.caption" class="image-caption">{{ item.caption }}</div>
          </div>
          <!-- Title -->
          <div v-else-if="item.type === 'text' && item.style === 'title'" class="poster-title">
            {{ item.content }}
          </div>
          <!-- Body Text -->
          <div v-else-if="item.type === 'text' && item.style === 'body'" class="poster-content">
            <p>{{ item.content }}</p>
          </div>
          <!-- Highlight -->
          <div v-else-if="item.type === 'text' && item.style === 'highlight'" class="poster-highlight">
            <p>{{ item.content }}</p>
          </div>
          <!-- Inline/Sidebar Image -->
          <div v-else-if="item.type === 'image' && (item.position === 'inline' || item.position === 'sidebar')" class="poster-inline-image">
            <img :src="item.src" alt="" />
            <div v-if="item.caption" class="image-caption">{{ item.caption }}</div>
          </div>
        </template>

        <!-- Footer -->
        <div class="poster-footer">
          <span class="org-name">XX 单位</span>
          <span class="date">{{ today }}</span>
        </div>
      </div>
    </div>

    <!-- Article Preview -->
    <div v-else-if="store.currentParams.type === 'article'" class="article-preview">
      <div class="article-card">
        <template v-for="(item, idx) in renderContent" :key="idx">
          <!-- Title -->
          <h1 v-if="item.type === 'text' && item.style === 'title'" class="article-title">
            {{ item.content }}
          </h1>
          <!-- Hero Image -->
          <div v-else-if="item.type === 'image' && item.position === 'hero'" class="article-image">
            <img :src="item.src" alt="" />
            <div v-if="item.caption" class="image-caption">{{ item.caption }}</div>
          </div>
          <!-- Body Text -->
          <div v-else-if="item.type === 'text' && item.style === 'body'" class="article-content">
            <p class="article-paragraph">{{ item.content }}</p>
          </div>
          <!-- Highlight -->
          <div v-else-if="item.type === 'text' && item.style === 'highlight'" class="article-highlight">
            <p>{{ item.content }}</p>
          </div>
          <!-- Inline Image -->
          <div v-else-if="item.type === 'image' && item.position === 'inline'" class="article-inline-image">
            <img :src="item.src" alt="" />
            <div v-if="item.caption" class="image-caption">{{ item.caption }}</div>
          </div>
        </template>

        <div class="article-meta">
          <span class="author">AI 创作</span>
          <span class="meta-dot">·</span>
          <span class="date">{{ today }}</span>
        </div>
      </div>
    </div>

    <!-- Newsletter Preview -->
    <div v-else-if="store.currentParams.type === 'newsletter'" class="newsletter-preview">
      <div class="newsletter-card">
        <div class="newsletter-header">
          <div class="header-line"></div>
          <span class="header-title">内部简报</span>
          <div class="header-line"></div>
        </div>

        <template v-for="(item, idx) in renderContent" :key="idx">
          <!-- Title -->
          <h1 v-if="item.type === 'text' && item.style === 'title'" class="newsletter-title">
            {{ item.content }}
          </h1>
          <!-- Image -->
          <div v-else-if="item.type === 'image'" class="newsletter-image">
            <img :src="item.src" alt="" />
            <div v-if="item.caption" class="image-caption">{{ item.caption }}</div>
          </div>
          <!-- Body Text -->
          <div v-else-if="item.type === 'text' && item.style === 'body'" class="newsletter-content">
            <p class="newsletter-paragraph">{{ item.content }}</p>
          </div>
        </template>

        <div class="newsletter-footer">
          <div class="footer-line"></div>
          <span class="footer-text">第 {{ new Date().getMonth() + 1 }} 期 | {{ today }}</span>
        </div>
      </div>
    </div>

    <!-- Export Buttons -->
    <div v-if="canExport" class="export-actions">
      <button class="export-btn" @click="handleExportWord">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
        导出 Word
      </button>
    </div>
  </div>
</template>

<style scoped>
.preview-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  position: relative;
  overflow-y: auto;
  padding: 24px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  animation: fadeInUp 0.6s ease-out;
  padding-top: 80px;
}

.empty-illustration {
  width: 200px;
  height: 200px;
  margin-bottom: 32px;
}

.empty-title {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 26px;
  font-weight: 600;
  color: #f3f4f6;
  margin-bottom: 12px;
}

.empty-desc {
  font-size: 14px;
  color: #6b7280;
}

.gradient-text {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 120px;
  animation: fadeInUp 0.4s ease-out;
}

.loading-animation {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.loading-dot {
  width: 12px;
  height: 12px;
  background: #6366f1;
  border-radius: 50%;
  animation: loadingBounce 1.2s ease-in-out infinite;
}

.loading-dot:nth-child(1) { animation-delay: 0s; }
.loading-dot:nth-child(2) { animation-delay: 0.15s; }
.loading-dot:nth-child(3) { animation-delay: 0.3s; }

.loading-text {
  font-size: 16px;
  color: #9ca3af;
}

@keyframes loadingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* ===== Card Styles ===== */
.poster-card,
.article-card,
.newsletter-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.25),
    0 2px 8px rgba(0, 0, 0, 0.15);
  animation: cardEnter 0.5s ease-out;
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Poster Preview */
.poster-preview {
  width: 100%;
  display: flex;
  justify-content: center;
  animation: fadeInUp 0.4s ease-out;
}

.poster-card {
  width: 380px;
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.poster-image {
  width: 100%;
  overflow: visible;
}

.poster-image img {
  width: 100%;
  height: auto;
  object-fit: contain;
  display: block;
  border-radius: 0;
}

.poster-title {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  padding: 20px 24px;
  line-height: 1.4;
}

.poster-content {
  padding: 0 24px 16px;
  color: #333;
  font-size: 14px;
  line-height: 1.9;
}

.poster-content p {
  margin: 0;
}

.poster-highlight {
  padding: 16px 24px;
  background: #f8f8f8;
  margin: 0 24px 16px;
  border-radius: 8px;
}

.poster-highlight p {
  margin: 0;
  color: #dc2626;
  font-weight: 500;
}

.poster-inline-image {
  padding: 0 24px 16px;
  width: 100%;
}

.poster-inline-image img {
  width: 100%;
  height: auto;
  object-fit: contain;
  display: block;
  border-radius: 8px;
}

.image-caption {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin-top: 6px;
  font-style: italic;
}

.poster-footer {
  margin-top: auto;
  padding: 16px 24px;
  background: #fafafa;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #666;
  border-top: 1px solid #eee;
}

/* Article Preview */
.article-preview {
  width: 100%;
  max-width: 680px;
  animation: fadeInUp 0.4s ease-out;
}

.article-card {
  padding: 0;
}

.article-title {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 26px;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.5;
  margin-bottom: 12px;
  padding: 36px 40px 0;
}

.article-image {
  width: calc(100% - 80px);
  border-radius: 12px;
  margin: 0 40px 28px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.article-image img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
}

.article-inline-image {
  width: calc(100% - 80px);
  margin: 0 40px 20px;
}

.article-inline-image img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
  border-radius: 8px;
}

.article-content {
  padding: 0 40px 24px;
  color: #333;
  font-size: 15px;
  line-height: 1.9;
}

.article-paragraph {
  margin-bottom: 18px;
  text-indent: 2em;
}

.article-highlight {
  padding: 16px 40px;
  background: #fff5f5;
  margin: 0 0 20px;
}

.article-highlight p {
  margin: 0;
  color: #dc2626;
  font-weight: 500;
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #999;
  padding: 24px 40px 40px;
  border-top: 1px solid #f0f0f0;
}

/* Newsletter Preview */
.newsletter-preview {
  width: 100%;
  max-width: 800px;
  animation: fadeInUp 0.4s ease-out;
}

.newsletter-card {
  padding: 48px 56px;
}

.newsletter-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 28px;
}

.header-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #ddd, transparent);
}

.header-title {
  font-size: 11px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 3px;
}

.newsletter-title {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  text-align: center;
  margin-bottom: 28px;
}

.newsletter-image {
  width: 100%;
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
}

.newsletter-image img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
  border-radius: 8px;
}

.newsletter-content {
  color: #333;
  font-size: 14px;
  line-height: 1.9;
}

.newsletter-paragraph {
  margin-bottom: 14px;
  text-indent: 2em;
}

.newsletter-footer {
  margin-top: 40px;
}

.footer-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, #ddd, transparent);
  margin-bottom: 14px;
}

.footer-text {
  font-size: 12px;
  color: #999;
  display: block;
  text-align: center;
}

/* Export Actions */
.export-actions {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  padding: 16px 28px;
  background: rgba(15, 17, 23, 0.92);
  backdrop-filter: blur(16px);
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  animation: slideUp 0.4s ease-out;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 13px 22px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  color: #f3f4f6;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: 'Noto Sans SC', sans-serif;
}

.export-btn:hover {
  background: rgba(99, 102, 241, 0.18);
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.2);
}

.export-btn:active {
  transform: translateY(0);
}

.export-btn svg {
  width: 18px;
  height: 18px;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translate(-50%, 24px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}
</style>