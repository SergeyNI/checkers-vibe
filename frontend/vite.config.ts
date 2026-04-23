import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
  server: {
    proxy: {
      '/api': 'http://backend:8000',
      '/ws': {
        target: 'ws://backend:8000',
        ws: true,
      },
    },
  },
})
