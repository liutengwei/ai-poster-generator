import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 60000,
})

export interface ImageSize {
  index: number
  ratio: 'landscape' | 'portrait' | 'square'
}

export interface LayoutItem {
  type: 'text' | 'image'
  image_index?: number
  position?: 'hero' | 'inline' | 'sidebar' | 'footer'
  size?: 'full' | 'half' | 'third'
  caption?: string
  content?: string
  style?: 'title' | 'body' | 'highlight'
}

export interface GenerateParams {
  type: 'poster' | 'article' | 'brief'
  title: string
  content: string
  color_theme: 'government' | 'china-red' | 'ink-green' | 'warm-orange'
  images: string[]  // base64 encoded images
}

export interface HistoryItem {
  id: string
  type: 'poster' | 'article' | 'brief'
  title: string
  content: string
  images: string[]
  layout: LayoutItem[]
  reasoning: string
  color_theme: string
  createdAt: string
}

const MAX_HISTORY = 10

export const useGenerateStore = defineStore('generate', () => {
  const isGenerating = ref(false)
  const error = ref<string | null>(null)

  const currentParams = ref<GenerateParams>({
    type: 'poster',
    title: '',
    content: '',
    color_theme: 'government',
    images: [],
  })

  const layout = ref<LayoutItem[]>([])
  const reasoning = ref('')
  const isAllDone = ref(false)

  const saveToHistory = () => {
    try {
      const item: HistoryItem = {
        id: Date.now().toString(),
        type: currentParams.value.type as 'poster' | 'article' | 'brief',
        title: currentParams.value.title,
        content: currentParams.value.content,
        images: [...currentParams.value.images],
        layout: [...layout.value],
        reasoning: reasoning.value,
        color_theme: currentParams.value.color_theme,
        createdAt: new Date().toISOString(),
      }

      const stored = localStorage.getItem('generate_history')
      const list: HistoryItem[] = stored ? JSON.parse(stored) : []
      const newList = [item, ...list.filter(h => h.id !== item.id)].slice(0, MAX_HISTORY)
      localStorage.setItem('generate_history', JSON.stringify(newList))
    } catch (e) {
      console.error('Failed to save history:', e)
    }
  }

  const startLayoutAnalysis = async (params: GenerateParams) => {
    isGenerating.value = true
    error.value = null
    layout.value = []
    reasoning.value = ''
    isAllDone.value = false
    currentParams.value = { ...params }

    // 计算图片尺寸比例
    const imageSizes: ImageSize[] = params.images.map((_, idx) => {
      return {
        index: idx,
        ratio: 'landscape' as const
      }
    })

    try {
      const response = await api.post('/generate/layout', {
        type: params.type,
        title: params.title,
        content: params.content,
        image_count: params.images.length,
        image_sizes: imageSizes,
      })

      layout.value = response.data.layout || []
      reasoning.value = response.data.reasoning || ''
      isAllDone.value = true
      saveToHistory()
    } catch (e: any) {
      if (e.response?.data?.detail) {
        error.value = e.response.data.detail
      } else {
        error.value = e.message || '排版分析失败'
      }
    } finally {
      isGenerating.value = false
    }
  }

  const reset = () => {
    isGenerating.value = false
    error.value = null
    currentParams.value = {
      type: 'poster',
      title: '',
      content: '',
      color_theme: 'government',
      images: [],
    }
    layout.value = []
    reasoning.value = ''
    isAllDone.value = false
  }

  const loadFromHistory = (item: HistoryItem) => {
    reset()
    currentParams.value = {
      type: item.type,
      title: item.title,
      content: item.content,
      images: item.images || [],
      color_theme: item.color_theme as GenerateParams['color_theme'],
    }
    layout.value = item.layout || []
    reasoning.value = item.reasoning || ''
    isAllDone.value = true
  }

  return {
    isGenerating,
    error,
    currentParams,
    layout,
    reasoning,
    isAllDone,
    startLayoutAnalysis,
    reset,
    loadFromHistory,
  }
})