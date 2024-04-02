<script>
export default {
  data() {
    return {
      gecko: '',
      lostCoins: [],
      baseUrl: import.meta.env.VITE_BACKEND,
      sorting: [0,0,0,0,0]
    }
  },
  created() {
    this.getLostCoins()
  },
  methods: {
    async getLostCoins() {
      let path = '/coins/lost'
      await fetch(this.baseUrl + path).then(response => response.json()).then(data => this.lostCoins = data)
      console.log(this.lostCoins)
    },
  },
}

</script>

<template class="dark">
  <div>
    <div class="left">
      <h3><a href="/"><- Back</a></h3>
    </div>
    <h2>{{gecko}}</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th><a href="#" @click="sortTable(2)">coin</a></th>
          <th class="right"><a href="#" @click="sortTable(3)">last price, $</a></th>
          <th class="right volume"><a href="#" @click="sortTable(4)">lastVolume, $</a></th>
          <th class="right volume"><a href="#" @click="sortTable(5)">lastUpdate</a></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(prop, i) in lostCoins" :key="i" class="text-sm h-14">
          <td>{{i + 1}}</td>
          <td>{{prop.cg_id}}</td>
          <td class="right">{{ prop.price_usd.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3}) }}</td>
          <td class="right volume">{{ prop.volume_usd.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3}) }}</td>
          <td class="right volume">{{ prop.last_update }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.left {
  text-align:left;
}
.volume {
  min-width: 250px;
}
.right {
  text-align:right;
}
</style>