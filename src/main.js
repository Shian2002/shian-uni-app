import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.config.errorHandler = function(err, instance, info) {
    if (err && err.message && (
      err.message.indexOf('read only property') > -1 ||
      err.message.indexOf("Cannot read properties of null (reading 'type')") > -1
    )) {
      return
    }
    console.error('[Vue]', err)
  }
  return { app }
}
