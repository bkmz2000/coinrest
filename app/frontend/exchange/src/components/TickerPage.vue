<script>
export default {
  data() {
    return {
      gecko: '',
      tickers: [],
      baseUrl: import.meta.env.VITE_BACKEND,
      sorting: [0,0,0,0,0]
    }
  },
  created() {
    this.gecko = location.href.split("/")[4]
    this.getGeckoTickers()
  },
  methods: {
    async getGeckoTickers() {
      let path = '/ticker/gecko/' + this.gecko
      await fetch(this.baseUrl + path).then(response => response.json()).then(data => this.tickers = data)
    },
    buildTicker(base, quote) {
      return base + '/' + quote
    },
    getDateFromUnix(stamp) {
      let date = new Date(stamp * 1000)
      date = date.toLocaleString()
      return date
    },
    sortTable(index) {
      if (this.sorting[index] === 0) {
        switch (index) {
          case 1: {
            this.tickers.sort((x, y) => x.name.localeCompare(y.name))
          } break;
          case 2: {
            this.tickers.sort((x, y) => (x.base_cg ? x.base_cg : '').localeCompare(y.base_cg ? y.base_cg : ''))
          } break;
          case 3: {
            this.tickers.sort((x, y) => (y.price_usd ? y.price_usd : 0) - (x.price_usd ? x.price_usd : 0))
          } break;
          case 4: {
            this.tickers.sort((x, y) => (y.volume_usd ? y.volume_usd : 0) - (x.volume_usd ? x.volume_usd : 0))
          } break;
          case 5: {
            this.tickers.sort((x, y) => (y.last_update ? y.last_update : 0) - (x.last_update ? x.last_update : 0))
          } break;
        }
        this.sorting = new Array(6).fill(0);
        this.sorting[index] = 1
      }
      else if (this.sorting[index] === 1) {
        this.tickers = this.tickers.reverse()
        this.sorting = new Array(6).fill(0);
      }
    }
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
          <th><a href="#" @click="sortTable(1)">exchange</a></th>
          <th><a href="#" @click="sortTable(2)">ticker</a></th>
          <th class="right"><a href="#" @click="sortTable(3)">price, $</a></th>
          <th class="right volume"><a href="#" @click="sortTable(4)">volume, $</a></th>
          <th class="right volume"><a href="#" @click="sortTable(5)">update</a></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(prop, i) in tickers" :key="i" class="text-sm h-14">
          <td>{{i + 1}}</td>
          <td>{{prop.name}}</td>
          <td>{{ buildTicker(prop.base, prop.quote) }}</td>
          <td class="right">{{ prop.price_usd.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3}) }}</td>
          <td class="right volume">{{ prop.volume_usd.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3}) }}</td>
          <td class="right volume">{{ getDateFromUnix(prop.last_update) }}</td>
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