/// <reference types="vitest" />
import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

const CABECERAS_ANTI_FRAMING = {
  'Content-Security-Policy': "frame-ancestors 'none'",
  'X-Frame-Options': 'DENY',
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // frame-ancestors solo surte efecto como cabecera HTTP; en <meta> el
  // navegador lo descarta. X-Frame-Options acompaña para navegadores viejos.
  server: {
    port: 5173,
    headers: CABECERAS_ANTI_FRAMING,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/docs': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  preview: {
    headers: CABECERAS_ANTI_FRAMING,
  },
  assetsInclude: ['**/*.svg', '**/*.csv'],
  build: {
    rollupOptions: {
      output: {
        // maplibre-gl pesa ~800 kB: en su propio chunk para no bloquear el
        // primer render de los KPIs.
        manualChunks: { maplibre: ['maplibre-gl'] },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
