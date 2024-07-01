from src.lib.schema import TickerInfo


class TickerValidator:
    @classmethod
    def validate_ticker(cls, ticker: TickerInfo) -> bool:
        return True

def ticker_validators(exchange_id: str) -> TickerValidator:
    validator = exchanges.get(exchange_id)
    if validator:
        return validator()
    return TickerValidator()


class mercado(TickerValidator):
    @classmethod
    def validate_ticker(cls, ticker: TickerInfo) -> bool:
        if ticker.base[-1].isdigit():
            return False
        if ticker.base.startswith("."):
            return False
        return True


exchanges = {
    "mercado": mercado,
}

