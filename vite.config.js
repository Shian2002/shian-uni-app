import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  optimizeDeps: {
    exclude: ['@dcloudio/uni-shared']
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:5199',
        changeOrigin: true
      }
    }
  }
})
