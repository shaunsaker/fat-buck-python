import json
import argparse
from datetime import datetime
import typedload
from alive_progress import alive_bar
from firebase import db
from utils import (
    falsyToInt,
    getNumberOfSymbolsToProcess,
    dateToDateString,
    safeOpenWrite,
)
from models import Stock, FinancialStatements
from fetchLatestPrice import fetchLatestPrice
from fetchHistoricalFundamentals import fetchHistoricalFundamentals
from makeHistoricalFinancialStatements import makeHistoricalFinancialStatements
from fetchLatestFinancialStatements import fetchLatestFinancialStatements
from makeLatestFinancialStatements import makeLatestFinancialStatements
from makeFinancialStatements import makeFinancialStatements
from fetchHistoricalPricing import fetchHistoricalPricing
from fetchSharesOutstanding import fetchSharesOutstanding
from handleDividendsPaid import handleDividendsPaid
from evaluate import evaluate


argParser = argparse.ArgumentParser()
argParser.add_argument("--exchange", type=str)
argParser.add_argument("--symbol", type=str, default="")
argParser.add_argument("--freshy", type=bool, default=False)
argParser.add_argument("--unprocessed", type=bool, default=False)
args = argParser.parse_known_args()
exchange = args[0].exchange
targetSymbol = args[0].symbol
freshy = args[0].freshy
unprocessed = args[0].unprocessed

today = dateToDateString(datetime.now())


exchangeRef = db.collection("exchanges").document(exchange)
exchangeData = exchangeRef.get().to_dict()
exchangeName = exchangeData["name"]
exchangeSymbols = exchangeData["symbols"]
symbolCount = 0


def removeStock(stockRef, _symbol):
    print(f"Removing {_symbol}...")
    stockRef.delete()

    # remove from list
    newExchangeSymbols = [d for d in exchangeSymbols if d.get("symbol") != _symbol]
    exchangeRef.set({"symbols": newExchangeSymbols}, merge=True)


def processStock(symbol):

    # get the stock
    stockRef = exchangeRef.collection("stocks").document(symbol)
    stockData = stockRef.get().to_dict()

    if not stockData:
        # create new
        if freshy:
            stock = Stock(symbol=symbol)
        else:
            removeStock(stockRef, symbol)
            return
    else:
        # replace any None, NaN values with 0 (lord knows how they got in there, probably my spaghetti code)
        stockData = falsyToInt(stockData)

        stock = typedload.load(stockData, Stock)

    # don't process stocks that have already been updated today
    if unprocessed and stock.lastUpdated == today:
        return

    # get the latest shares outstanding
    sharesOutstanding = fetchSharesOutstanding(symbol)

    if not sharesOutstanding:
        print("No shares.")
        removeStock(stockRef, symbol)
        return

    stock.sharesOutstanding = sharesOutstanding

    # get the latest price
    latestPrice = fetchLatestPrice(stock, exchange)

    # if there is no price or the price is 0, remove the stock
    if not latestPrice:
        print("No price.")
        removeStock(stockRef, symbol)
        return

    stock.currentPrice = latestPrice

    # get the latest financial statements
    yahooStatements = fetchLatestFinancialStatements(symbol)

    # if latest statements are empty
    if yahooStatements.incomeStatements.yearly == {}:
        print("No latest financial statements.")
        removeStock(stockRef, symbol)
        return

    # parse latest statements
    latestFinancialStatements = makeLatestFinancialStatements(yahooStatements)

    # merge the existing and latest financial statements
    if freshy:
        # merge the historical
        historicalFundamentals = fetchHistoricalFundamentals(symbol, exchange)

        if (
            not historicalFundamentals
            or historicalFundamentals.Financials.Income_Statement.yearly == {}
        ):
            print("No historical financial statements.")
            removeStock(stockRef, symbol)
            return

        historicalFinancialStatements = makeHistoricalFinancialStatements(
            historicalFundamentals
        )

        financialStatements = makeFinancialStatements(
            FinancialStatements(), historicalFinancialStatements
        )

        # merge the latest
        financialStatements = makeFinancialStatements(
            financialStatements, latestFinancialStatements
        )

    else:
        financialStatements = makeFinancialStatements(
            stock.financialStatements, latestFinancialStatements
        )

    # if empty financial statements, we don't want to save it
    if not financialStatements:
        print("No financial statements.")
        removeStock(stockRef, symbol)
        return

    stock.financialStatements = financialStatements

    # get new historical pricing
    historicalPricing = fetchHistoricalPricing(symbol)

    if not historicalPricing:
        print("No historical pricing.")
        removeStock(stockRef, symbol)
        return

    if historicalPricing:
        stock.historicalPricing = historicalPricing

    # get the latest dividends
    stock = handleDividendsPaid(stock)

    # evaluate the stock
    stock.valuation = evaluate(stock)

    # add the last updated date
    stock.lastUpdated = today

    # convert our stock class to a json string
    stockJson = json.loads(json.dumps(stock, default=lambda o: o.__dict__, indent=2))

    stockRef.set(stockJson, merge=True)

    if freshy:
        # store the data locally
        filepath = f"data/stocks/{exchange}/{symbol}.json"
        with safeOpenWrite(filepath) as file:
            jsonString = json.dumps(stockJson, default=lambda o: o.__dict__, indent=2)
            file.write(jsonString)

    print(
        f"{symbol} is {stock.valuation.health}. You should {stock.valuation.instruction}. You can expected a return of {stock.valuation.expectedReturn}%. The current price is {stock.currentPrice} and we value the stock at {stock.valuation.fairValue}."
    )

    return


if targetSymbol:
    symbol = targetSymbol
    processStock(symbol)
else:
    for symbolData in exchangeSymbols:
        symbol = symbolData["symbol"]

        symbolCount += 1
        print(
            f"Updating {exchangeName}: {symbol}, {symbolCount} of {len(exchangeSymbols)}..."
        )

        processStock(symbol)
