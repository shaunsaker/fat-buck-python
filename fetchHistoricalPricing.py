from yahooquery import Ticker
import utils
from models import (
    HistoricalPrice,
    HistoricalPricing,
    YahooQueryTickerData,
)


def fetchHistoricalPricing(symbol: str) -> HistoricalPricing:
    data: YahooQueryTickerData = Ticker(symbol)
    priceHistoryDf = data.history(period="1y")
    historicalPricing = {}

    # sometimes iterrows is undefined
    try:
        for index, row in priceHistoryDf.iterrows():
            date = index[1].__str__()
            pricing = HistoricalPrice()
            pricing.open = round(row.open, 2)
            pricing.close = round(row.close, 2)
            historicalPricing[date] = pricing
    except:
        return None

    return historicalPricing

