import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
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
  images: string[]
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

  const startLayoutAnalysis = async (params: GenerateParams) => {
    isGenerating.value = true
    error.value = null
    layout.value = []
    reasoning.value = ''
    isAllDone.value = false
    currentParams.value = { ...params }

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

      // Save to backend history
      try {
        await api.post('/history', {
          type: params.type,
          title: params.title,
          content: params.content,
          images: params.images,
          layout: layout.value,
          reasoning: reasoning.value,
          color_theme: params.color_theme,
        })
      } catch (e) {
        console.error('Failed to save history:', e)
      }
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
      type: item.type as GenerateParams['type'],
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