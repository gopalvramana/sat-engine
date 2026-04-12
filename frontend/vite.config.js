import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],

  // React app lives at /app in both dev and prod
  base: '/app/',

  build: {
    // Output goes straight into Spring Boot static resources → bundled into JAR
    outDir: path.resolve(__dirname, '../src/main/resources/static/app'),
    emptyOutDir: true,
  },

  server: {
    port: 5173,
    proxy: {
      // In dev: forward all /api calls to Spring Boot at :8080
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      // Proxy static assets shared with existing pages (renderer.js, css)
      '/admin': { target: 'http://localhost:8080', changeOrigin: true },
      '/css':   { target: 'http://localhost:8080', changeOrigin: true },
      '/js':    { target: 'http://localhost:8080', changeOrigin: true },
      '/dev':   { target: 'http://localhost:8080', changeOrigin: true },
      '/oauth2':{ target: 'http://localhost:8080', changeOrigin: true },
      '/login': { target: 'http://localhost:8080', changeOrigin: true },
    },
  },
})
