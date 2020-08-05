from yahooquery import Ticker
from models import SymbolData, YahooQueryTickerData


def checkSymbolExists(symbolData: SymbolData, retryCount: int = 0) -> bool:
    symbol = symbolData.symbol
    data: YahooQueryTickerData = Ticker(symbol)

    if symbol not in data.price:
        return False

    priceData = data.price[symbol]
    keyStatsData = data.key_stats[symbol]

    if (
        "regularMarketPrice" not in priceData
        or "Quote not found" in priceData
        or "No fundamentals data found" in keyStatsData
        or "sharesOutstanding" not in keyStatsData
        or not keyStatsData["sharesOutstanding"]
    ):
        # retry n times
        if retryCount < 5:
            checkSymbolExists(symbolData, retryCount + 1)
        else:
            return False
    else:
        return True
