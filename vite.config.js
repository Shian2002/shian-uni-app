import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:5199'

export default defineConfig({
  plugins: [uni()],
  optimizeDeps: {
    exclude: ['@dcloudio/uni-shared']
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true
      }
    }
  }
})
