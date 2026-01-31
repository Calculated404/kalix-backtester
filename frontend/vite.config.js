import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    // Add this section to allow your domain
    allowedHosts: [
      'halabieh.de',
      'www.halabieh.de',
      'localhost',
      'host.docker.internal'
    ]
  }
})