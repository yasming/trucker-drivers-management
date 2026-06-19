import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // In production builds, assets are served by Django under /static/.
  // In dev, the Vite server serves them from the root so hot-reload works.
  base: command === 'build' ? '/static/' : '/',
  build: {
    outDir: path.resolve(__dirname, './static'),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to the Django backend during development.
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
}))
