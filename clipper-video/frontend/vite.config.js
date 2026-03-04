import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

const devProxyTarget = process.env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    allowedHosts: true,
    host: true,
    proxy: {
      '/api': {
        target: devProxyTarget,
        changeOrigin: true,
        secure: false,
      },
      '/media': {
        target: devProxyTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
