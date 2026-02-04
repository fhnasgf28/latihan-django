import axios from 'axios'

// Gunakan path relatif agar proxy Vite menangani request
const API_BASE_URL = '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const jobAPI = {
  create: (data) => apiClient.post('/jobs/', data),
  get: (id) => apiClient.get(`/jobs/${id}/`),
  downloadZipUrl: (id) => `${API_BASE_URL}/jobs/${id}/download-zip/`
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

export default apiClient
