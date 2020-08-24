import sys
from yahooquery import Ticker
from models import Symbol, Shares, YahooQueryTickerData


def fetchSharesOutstanding(symbol: Symbol) -> Shares:
    data: YahooQueryTickerData = Ticker(symbol)
    keyStatsData = data.key_stats[symbol]

    if "No fundamentals data" in keyStatsData or "Quote not found" in keyStatsData:
        return None

    sharesOutstandingString = keyStatsData["sharesOutstanding"]

    sharesOutstanding = int(sharesOutstandingString)

    return sharesOutstanding
