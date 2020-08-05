from datetime import datetime
from yahooquery import Ticker
from models import Stock, Currency, YahooQueryTickerData, HistoricalPrice
import utils


def fetchLatestPrice(stock: Stock, exchange: str) -> Currency:
    data: YahooQueryTickerData = Ticker(stock.symbol)
    priceData = data.price[stock.symbol]
    priceString = priceData["regularMarketPrice"]

    currentPrice = utils.stringToCurrency(priceString)

    # JSE data is in cents (fuck knows why)
    if exchange == "JSE":
        currentPrice = currentPrice / 100

    stock.currentPrice = currentPrice

    # check if we have todays price in historical pricing, if not add it
    priceTimeString = priceData["regularMarketTime"].split(" ")[0]
    today = datetime.now()
    todayString = utils.dateToDateString(today)

    if priceTimeString == todayString and todayString not in stock.historicalPricing:
        price = HistoricalPrice(open=currentPrice, close=currentPrice)
        stock.historicalPricing[todayString] = price

    return stock
