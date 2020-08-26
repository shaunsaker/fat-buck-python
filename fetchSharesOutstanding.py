import sys
from yahooquery import Ticker
from models import Symbol, Shares, YahooQueryTickerData


def fetchSharesOutstanding(symbol: Symbol) -> Shares:
    data: YahooQueryTickerData = Ticker(symbol)

    # sometimes the symbol is not in key_stats?
    try:
        keyStatsData = data.key_stats[symbol]
    except:
        return None

    if (
        "No fundamentals data" in keyStatsData
        or "Quote not found" in keyStatsData
        or "sharesOutstanding" not in keyStatsData
    ):
        return None

    sharesOutstandingString = keyStatsData["sharesOutstanding"]

    sharesOutstanding = int(sharesOutstandingString)

    return sharesOutstanding
