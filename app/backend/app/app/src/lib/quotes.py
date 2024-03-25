quote_mapper = {
    "USDT": "tether",
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDC": "usd-coin",
    "BUSD": "binance-usd",
    "BNB": "binancecoin",
    "TUSD": "true-usd",
    "USDD": "usdd",
    "XRP": "ripple",
    "FDUSD": "first-digital-usd",
    "DAI": "dai",
    "TRX": "tron",
    "ADA": "cardano",
    "BCH": "bitcoin-cash",
    "BIDR": "binanceidr",
    "KCS": "kucoin-shares",
    "WRX": "wazirx",
    "EOS": "eos",
    "SOL": "solana",
    "USDP": "paxos-standard",
    "XTN": "neutrino",
    "PAX": "paxos-standard",
    "VNST": "vnst-stablecoin"
}

active_exchanges = (
    'ace',
    'alpaca',
    'ascendex',
    'bequant',
    'bigone',
    'binance',
    'bingx',
    'bit2c',
    'bitbank',
    'bitbay',
    'bitbns',
    'bitcoincom',
    'bitfinex',
    'bitflyer',
    'bitforex',
    'bitget',
    'bithumb',
    'bitmart',
    'bitmex',
    'bitopro',
    'bitpanda',
    'bitrue',
    'bitso',
    'bitstamp',
    'bitteam',
    'bitvavo',
    'bl3p',
    'blockchaincom',
    'btcbox',
    'btcmarkets',
    'btcturk',
    'bybit',
    'cex',
    'coinbasepro',
    'coincheck',
    'coinex',
    'coinlist',
    'coinmate',
    'coinone',
    'coinsph',
    # 'coinspot',
    'cryptocom',
    'currencycom',
    'delta',
    'deribit',
    'digifinex',
    'exmo',
    'fmfwio',
    'gateio',
    'gemini',
    'hitbtc',
    'hollaex',
    'htx',
    'idex',
    'independentreserve',
    'indodax',
    'kraken',
    'kucoin',
    'kuna',
    'latoken',
    'lbank',
    'luno',
    'lykke',
    'mercado',
    'mexc',
    'ndax',
    'novadax',
    'oceanex',
    'okcoin',
    'okx',
    'onetrading',
    'p2b',
    'paymium',
    'phemex',
    'poloniex',
    'probit',
    'timex',
    # 'tokocrypto', shit
    'upbit',
    'wavesexchange',
    'wazirx',
    'whitebit',
    'woo',
    'yobit',
    'zaif',
    'zonda',

    'cointrpro',
    'coinw',
    'deepcoin',
    'hotcoinglobal',
    'orangex',
    'toobit',
    'xtcom',

    'tapbit',
    'pionex',
    'bullish',

    'websea',
    'biconomy',
    'fastex',
    'nami_exchange',
    'coinsbit',
    'tidex',
    'btc_alpha',
    'bilaxy',
    'difx',
    'bydfi',

    'bitmake',

)

quotes = ['CRO', 'LA', 'TRX', 'HIT', 'TESTUSDT', 'EUTF0', 'BVND', 'USDCBSC', 'BIDR', 'PZM', 'USDT', 'DGLD', 'TWD',
          'PLN', 'UST', 'USDTBSC', 'BGN', 'CAD', 'ZAR', 'UAHG', 'ETH', 'USDCAVALANCHE', 'BYN', 'CNHT', 'BRL', 'GEL',
          'BTC-WXG', 'USDC-BEP20', 'BTC', 'WRX', 'VET', 'EOSDT', 'USDT-BEP20', 'SBTC', 'WAVES', 'KRW', 'PYUSD',
          'USDCTRON', 'EOS', 'EURS', 'KZT', 'USDCPOLYGONNATIVE', 'USDTTRON', 'VAI', 'BUSD', 'BCH', 'USDC-WXG', 'KCS',
          'RON', 'UAH', 'MXNT', 'XTN', 'INR', 'MIM', 'SOL', 'TUSD', 'XRP', 'BRL20', 'NOK', 'BRZ', 'HKD', 'TESTUSDTF0',
          'CHF', 'PAX', 'USTF0', 'USDT-WXG', 'BNB', 'EAST', 'NGN', 'BFIC', 'AED', 'MXN', 'WBTC', 'USD', 'HUF', 'ARS',
          'CNH', 'OCE', 'SNET', 'USDD', 'DOT', 'USDCPOLYGONBRIDGED', 'XDC', 'AEUR', 'SGD', 'USDC-ERC20', 'BTCF0',
          'DOGE', 'JPY', 'AUDT', 'CZK', 'CNYX', 'GBP', 'USDP', 'VUSD', 'EURT', 'DKK', 'EURST', 'USDTAVALANCHE', 'AUD',
          'TESTUSD', 'TRY', 'DEL', 'USDTPOLYGON', 'USDC', 'ADA', 'BTCB', 'EUR', 'RUB', 'FDUSD', 'SATS', 'BTR', 'NZD',
          'XAUT', 'USDT-ERC20', 'GRB', 'SEK', 'BKRW', 'TRY20', 'DAI', 'USDS', 'IDRT', 'LTC']

counters = {'USDT': 18860, # +
            'BTC': 3216, # +
            'ETH': 1820, # +
            'USD': 1583,# +
            'USDC': 1001, # +
            'EUR': 800, # -
            'TRY': 468,# -
            'INR': 383,# -
            'BUSD': 381,# +
            'BRL': 345, #-
            'BNB': 289, #+
            'PLN': 163,#-
            'GBP': 157,#-
            'KRW': 119,#-
            'TUSD': 102,#+
            'USDD': 85,#+
            'XRP': 83,#+
            'FDUSD': 65,#+
            'USTF0': 64, #-
            'DAI': 58, #+
            'XTN': 51, #+
            'AUD': 40,#-
            'TRX': 39,#+
            'PAX': 39,#+
            'CHF': 38,#-
            'JPY': 37,#-
            'ADA': 34,#+
            'UAH': 33,#-
            'BCH': 28,#+
            'RUB': 27,#-
            'BIDR': 27,#+
            'HIT': 23,
            'KCS': 23,#+
            'HKD': 21,#-
            'TWD': 20,#-
            'WRX': 19,#+
            'EOS': 18,#+
            'SOL': 18,#+
            'EOSDT': 17,
            'USDP': 16,#+
            'EURS': 16,
            'VET': 16, 'TESTUSD': 16,
            'TESTUSDTF0': 16, 'WAVES': 14, 'CAD': 13, 'SGD': 13, 'NGN': 12, 'ZAR': 11, 'BKRW': 11, 'BTR': 11, 'MXN': 10,
            'SEK': 10, 'LA': 10, 'AUDT': 9, 'PYUSD': 8, 'CNH': 7, 'USDT-WXG': 7, 'EURST': 6, 'DEL': 6, 'BYN': 6,
            'NOK': 6, 'USDC-WXG': 6, 'IDRT': 5, 'EURT': 5, 'CZK': 5, 'DKK': 5, 'SATS': 5, 'USDT-ERC20': 5, 'BTCF0': 5,
            'HUF': 4, 'UST': 4, 'RON': 4, 'BTC-WXG': 4, 'MXNT': 4, 'TRY20': 3, 'BRL20': 3, 'VUSD': 3, 'NZD': 3,
            'USDS': 3, 'VAI': 3, 'DOGE': 3, 'AEUR': 3, 'KZT': 3, 'AED': 3, 'CNHT': 3, 'GRB': 2, 'XDC': 2, 'BFIC': 2,
            'BVND': 2, 'DOT': 2, 'ARS': 2, 'GEL': 2, 'CRO': 2, 'TESTUSDT': 2, 'XAUT': 2, 'EUTF0': 2, 'PZM': 1, 'LTC': 1,
            'SBTC': 1, 'DGLD': 1, 'BGN': 1, 'BRZ': 1, 'UAHG': 1, 'USDCAVALANCHE': 1, 'USDCBSC': 1,
            'USDCPOLYGONBRIDGED': 1, 'USDCPOLYGONNATIVE': 1, 'USDCTRON': 1, 'USDTAVALANCHE': 1, 'USDTBSC': 1,
            'USDTPOLYGON': 1, 'USDTTRON': 1, 'WBTC': 1, 'USDT-BEP20': 1, 'USDC-ERC20': 1, 'BTCB': 1, 'USDC-BEP20': 1,
            'EAST': 1, 'OCE': 1, 'SNET': 1, 'CNYX': 1, 'MIM': 1}

errors = ['USD', 'USTF0', 'BIDR', 'TESTUSD', 'TESTUSDTF0', 'BKRW', 'USDT-WXG', 'USDC-WXG', 'USDT-ERC20', 'BTCF0',
          'BTC-WXG', 'MXNT', 'TRY20', 'BRL20', 'VUSD', 'CNHT', 'BVND', 'TESTUSDT', 'EUTF0', 'DGLD', 'BRZ', 'UAHG',
          'USDCAVALANCHE', 'USDCBSC', 'USDCPOLYGONBRIDGED', 'USDCPOLYGONNATIVE', 'USDCTRON', 'USDTAVALANCHE', 'USDTBSC',
          'USDTPOLYGON', 'USDTTRON', 'USDT-BEP20', 'USDC-ERC20', 'USDC-BEP20', 'EAST', 'CNYX']
