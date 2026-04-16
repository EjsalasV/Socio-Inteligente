import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  root: 'src/renderer',
  server: {
    port: 5173,
  },
  build: {
    outDir: '../../dist/renderer',
    emptyOutDir: true,
  },
  base: './',
})
