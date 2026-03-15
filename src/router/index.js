import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Present from '../views/Present.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/present/:id', component: Present }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
