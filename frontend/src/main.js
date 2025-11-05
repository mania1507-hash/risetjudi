import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/base.css'
import './assets/custom.css'
import Vue3Toastify from 'vue3-toastify'

const app = createApp(App)
app.use(createPinia())
app.use(Vue3Toastify, {
  autoClose: 3000,
})
app.use(router)
app.mount('#app')
