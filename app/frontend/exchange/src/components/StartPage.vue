<script>
export default {
  data() {
    return {
      exchanges: [],
      geckos: [],
      baseUrl: import.meta.env.VITE_BACKEND,
      exchangeSelected: ''
    }
  },
  created() {
    this.getExchanges()
  },
  methods: {
    async getExchanges() {
      let path = '/exchange/'
      console.log(this.baseUrl + path)
      await fetch(this.baseUrl + path).then(response => response.json()).then(data => this.exchanges = data)
      path = '/ticker/'
      await fetch(this.baseUrl + path).then(response => response.json()).then(data => this.geckos = data)
    },
    getRoute(ticker) {
      return '/ticker/' + ticker
    },
    getExRoute() {
      return '/exchange/' + this.exchangeSelected.name
    },
  },
}
</script>

<template>
  <div>
    <form>
      <h2>Exchanges</h2>
      <select v-model="exchangeSelected">
        <option :value="ex" v-for="(ex, i) in exchanges" :key="i" class="text-sm h-14">
          {{ex.name}}
        </option>
      </select>
      <span><a :href="getExRoute()">&nbsp;Submit</a></span>
    </form>
    <hr>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Coin</th>
          <th>TotalVolume</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(gecko, i) in geckos" :key="i" class="text-sm h-14">
          <td>{{i + 1}}</td>
          <td><a :href="getRoute(gecko.base_cg)">{{gecko.base_cg}}</a></td>
          <td>{{gecko.volume_usd.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3})}}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div>
  </div>
</template>

<style scoped>
body {
  background-color: #0a53be;
}
</style>