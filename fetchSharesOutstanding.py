import sys
from yahooquery import Ticker
from models import Symbol, Shares, YahooQueryTickerData


def fetchSharesOutstanding(symbol: Symbol) -> Shares:
    data: YahooQueryTickerData = Ticker(symbol)
    keyStatsData = data.key_stats[symbol]
    sharesOutstandingString = keyStatsData["sharesOutstanding"]

    sharesOutstanding = int(sharesOutstandingString)

    return sharesOutstanding
