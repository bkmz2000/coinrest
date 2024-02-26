import './style.css'

import App from './App.vue'
import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import StartPage from "./components/StartPage.vue";
import exPage from "./components/ExPage.vue";
import TickerPage from "./components/TickerPage.vue";

const app = createApp(App)

const router = createRouter({
  history: createWebHistory(),
  routes: [
      {path: '/', component: StartPage},
      {
          path: '/exchange/:exchange',
          name: 'exchange',
          component: exPage
      },
      {
          path: '/ticker/:ticker',
          name: 'ticker',
          component: TickerPage
      },
  ]
})

app.use(router)
app.mount('#app')
