from yahooquery import Ticker
import utils
from models import HistoricalPrice, HistoricalPricing, YahooQueryTickerData


def fetchHistoricalPricing(symbol: str) -> HistoricalPricing:
    data: YahooQueryTickerData = Ticker(symbol)
    priceHistoryDf = data.history(period="2y")
    historicalPricing = {}

    try:
        for index, row in priceHistoryDf.iterrows():
            date = utils.pandasDateToDateString(index, True)  # don't save time
            pricing = HistoricalPrice()
            pricing.open = round(row.open, 2)
            pricing.close = round(row.close, 2)
            historicalPricing[date] = pricing

        return historicalPricing
    except:
        return None
