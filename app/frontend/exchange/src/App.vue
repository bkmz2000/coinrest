<script setup>
import StartPage from './components/StartPage.vue'
</script>

<template>
  <div>
    <router-link to="/">Main</router-link> |
    <router-link to="/lost">Lost coins</router-link>
    <router-view/>
  </div>
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
body {
  background-color: #434B4D;
}
</style>
