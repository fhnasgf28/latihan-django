import axios from 'axios'
import { API_BASE_URL as CONFIG_API_BASE } from '../config'

const normalizeApiBase = (value) => {
  const raw = String(value || '').trim()
  if (!raw) return '/api'
  const cleaned = raw.replace(/\/+$/, '')
  if (cleaned === '/api' || cleaned.endsWith('/api')) return cleaned
  if (cleaned.startsWith('http://') || cleaned.startsWith('https://')) return `${cleaned}/api`
  if (cleaned.startsWith('/')) return `${cleaned}/api`
  return '/api'
}

// Logika penentuan URL Backend:
// 1. Jika ada VITE_API_BASE di environment, gunakan itu.
// 2. Jika sedang mode DEVELOPMENT (npm run dev), gunakan localhost:8000.
// 3. Jika tidak, gunakan CONFIG_API_BASE (URL Cloud Run).
let backendUrl = import.meta.env.VITE_API_BASE;

if (!backendUrl) {
  if (import.meta.env.DEV) {
    backendUrl = 'http://localhost:8000';
  } else {
    backendUrl = CONFIG_API_BASE;
  }
}

const API_BASE_URL = normalizeApiBase(backendUrl)
const BACKEND_ORIGIN = API_BASE_URL.startsWith('http') ? new URL(API_BASE_URL).origin : ''

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const jobAPI = {
  create: (data) => apiClient.post('/jobs/', data),
  get: (id, config = {}) => apiClient.get(`/jobs/${id}/`, config),
  cancel: (id, token) => apiClient.post(`/jobs/${id}/cancel/`, { token }),
  downloadZipUrl: (id) => `${API_BASE_URL}/jobs/${id}/download-zip/`,
  createLocal: (formData) => apiClient.post('/jobs/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const videoAPI = {
  getAll: (params = {}) => apiClient.get('/videos/', { params }),
  get: (id) => apiClient.get(`/videos/${id}/`),
  create: (data) => apiClient.post('/videos/', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  update: (id, data) => apiClient.put(`/videos/${id}/`, data),
  delete: (id) => apiClient.delete(`/videos/${id}/`),
  getClips: (id) => apiClient.get(`/videos/${id}/clips/`)
}

export const clipAPI = {
  getAll: (params = {}) => apiClient.get('/clips/', { params }),
  get: (id) => apiClient.get(`/clips/${id}/`),
  create: (data) => apiClient.post('/clips/', data),
  update: (id, data) => apiClient.put(`/clips/${id}/`, data),
  delete: (id) => apiClient.delete(`/clips/${id}/`),
  togglePublic: (id) => apiClient.post(`/clips/${id}/toggle_public/`),
  getMyClips: () => apiClient.get('/clips/my_clips/'),
  getPublicClips: () => apiClient.get('/clips/public_clips/')
}

export const resolveBackendUrl = (url) => {
  if (!url) return '#'
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) {
    return BACKEND_ORIGIN ? `${BACKEND_ORIGIN}${url}` : url
  }
  return url
}

export default apiClient
