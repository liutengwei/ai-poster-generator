import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 30000,
})

export interface ExportParams {
  title: string
  content: string
  layout: any[]
  images: string[]
}

export interface ImageExportParams {
  type: string
  title: string
  content: string
  layout: any[]
  images: string[]
  unit_name?: string
  date?: string
}

export const exportWord = async (params: ExportParams): Promise<Blob> => {
  const response = await api.post('/export/word', params, {
    responseType: 'blob',
  })
  return response.data
}

export const exportPdf = async (params: ExportParams): Promise<Blob> => {
  const response = await api.post('/export/pdf', params, {
    responseType: 'blob',
  })
  return response.data
}

export const exportImage = async (params: ImageExportParams): Promise<Blob> => {
  const response = await api.post('/export/image', params, {
    responseType: 'blob',
  })
  return response.data
}

export default api
