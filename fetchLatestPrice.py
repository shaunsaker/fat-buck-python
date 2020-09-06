from datetime import datetime
from yahooquery import Ticker
from models import Stock, Currency, YahooQueryTickerData, HistoricalPrice
import utils


def fetchLatestPrice(stock: Stock, exchange: str) -> Currency:
    data: YahooQueryTickerData = Ticker(stock.symbol)
    priceData = data.price[stock.symbol]

    # sometimes we get the string indices must be integers error
    try:
        priceString = priceData["regularMarketPrice"]
    except:
        return None

    currentPrice = utils.stringToCurrency(priceString)

    # JSE data is in cents (fuck knows why)
    if exchange == "JSE":
        currentPrice = currentPrice / 100

    return currentPrice
