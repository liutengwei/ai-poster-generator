<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useGenerateStore } from '@/stores/generate'

interface HistoryItem {
  id: string
  type: 'poster' | 'article' | 'brief'
  title: string
  content: string
  images: string[]
  layout: any[]
  reasoning: string
  color_theme: string
  createdAt: string
}

const router = useRouter()
const store = useGenerateStore()

const historyList = ref<HistoryItem[]>([])
const loading = ref(false)

const loadHistory = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/history')
    const data = await res.json()
    historyList.value = data.items || []
  } catch (e) {
    console.error('Failed to load history:', e)
  } finally {
    loading.value = false
  }
}

const deleteHistory = async (id: string) => {
  try {
    await fetch(`/api/history/${id}`, { method: 'DELETE' })
    historyList.value = historyList.value.filter(h => h.id !== id)
  } catch (e) {
    console.error('Failed to delete:', e)
  }
}

const clearAllHistory = async () => {
  for (const item of historyList.value) {
    await fetch(`/api/history/${item.id}`, { method: 'DELETE' })
  }
  historyList.value = []
}

const loadToEditor = (item: HistoryItem) => {
  store.loadFromHistory(item)
  router.push('/')
}

const typeLabels: Record<string, string> = {
  poster: '海报',
  article: '公众号推文',
  brief: '简报',
}

const typeIcons: Record<string, string> = {
  poster: '🖼',
  article: '📝',
  brief: '📋',
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="min-h-screen flex flex-col page-enter">
    <!-- Navigation Bar -->
    <header class="navbar glass">
      <div class="navbar-content">
        <div class="logo animate-fade-in-up stagger-1">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="logo-text">AI 宣传助手</span>
        </div>
        <nav class="nav-links animate-fade-in-up stagger-2">
          <RouterLink to="/" class="nav-link">创作</RouterLink>
          <RouterLink to="/history" class="nav-link active">历史记录</RouterLink>
        </nav>
      </div>
      <div class="navbar-divider"></div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <div class="history-header animate-fade-in-up stagger-3">
        <h1 class="history-title">历史记录</h1>
        <button v-if="historyList.length > 0" class="clear-btn" @click="clearAllHistory">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
          清空全部
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state animate-fade-in-up stagger-4">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="historyList.length === 0" class="empty-state animate-fade-in-up stagger-4">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <h2 class="empty-title">暂无历史记录</h2>
        <p class="empty-desc">开始创作，记录你的灵感</p>
        <RouterLink to="/" class="start-btn">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
          </svg>
          开始创作
        </RouterLink>
      </div>

      <!-- History Grid -->
      <div v-else class="history-grid">
        <div
          v-for="(item, index) in historyList"
          :key="item.id"
          class="history-card animate-fade-in-up"
          :style="{ animationDelay: `${0.1 + index * 0.05}s` }"
        >
          <div class="card-header">
            <span class="card-type">
              <span class="type-icon">{{ typeIcons[item.type] || '📄' }}</span>
              {{ typeLabels[item.type] || item.type }}
            </span>
            <button class="delete-btn" @click.stop="deleteHistory(item.id)">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>

          <div class="card-preview" @click="loadToEditor(item)">
            <div v-if="item.images && item.images.length > 0" class="preview-image">
              <img :src="item.images[0]" :alt="item.title" />
            </div>
            <div v-else class="preview-placeholder">
              <span>{{ typeIcons[item.type] || '📄' }}</span>
            </div>
          </div>

          <div class="card-content" @click="loadToEditor(item)">
            <h3 class="card-title">{{ item.title }}</h3>
            <p class="card-excerpt">{{ item.content?.slice(0, 60) }}{{ item.content?.length > 60 ? '...' : '' }}</p>
          </div>

          <div class="card-footer">
            <span class="card-date">{{ formatDate(item.createdAt) }}</span>
            <button class="reload-btn" @click="loadToEditor(item)">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
              </svg>
              重新编辑
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page-enter {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-content {
  max-width: 1400px;
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
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
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
  flex: 1;
  padding: 40px 24px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.history-title {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 28px;
  font-weight: 600;
  color: #f3f4f6;
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #9ca3af;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Noto Sans SC', sans-serif;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.clear-btn svg {
  width: 16px;
  height: 16px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: rgba(99, 102, 241, 0.3);
  margin-bottom: 24px;
}

.empty-title {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 600;
  color: #f3f4f6;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 32px;
}

.start-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35);
}

.start-btn svg {
  width: 18px;
  height: 18px;
}

/* History Grid */
.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.history-card {
  background: rgba(15, 17, 23, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.history-card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.card-type {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}

.type-icon {
  font-size: 14px;
}

.delete-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.delete-btn svg {
  width: 16px;
  height: 16px;
}

.card-preview {
  height: 140px;
  background: rgba(0, 0, 0, 0.2);
  cursor: pointer;
  overflow: hidden;
}

.preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.history-card:hover .preview-image img {
  transform: scale(1.05);
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  opacity: 0.3;
}

.card-content {
  padding: 16px;
  cursor: pointer;
}

.card-title {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 16px;
  font-weight: 600;
  color: #f3f4f6;
  margin-bottom: 8px;
  line-height: 1.4;
}

.card-excerpt {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.card-date {
  font-size: 11px;
  color: #6b7280;
}

.reload-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 8px;
  color: #6366f1;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Noto Sans SC', sans-serif;
}

.reload-btn:hover {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.4);
}

.reload-btn svg {
  width: 14px;
  height: 14px;
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

.stagger-1 { animation-delay: 0.05s; }
.stagger-2 { animation-delay: 0.1s; }
.stagger-3 { animation-delay: 0.15s; }
.stagger-4 { animation-delay: 0.2s; }

.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out both;
  opacity: 0;
}
</style>