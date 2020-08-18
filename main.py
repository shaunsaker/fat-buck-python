import json
import argparse
from datetime import datetime
import typedload
from alive_progress import alive_bar
from firebase import db
from utils import (
    recursiveReplacer,
    getNumberOfSymbolsToProcess,
    dateToDateString,
)
from models import Stock
from fetchLatestPrice import fetchLatestPrice
from fetchLatestFinancialStatements import fetchLatestFinancialStatements
from makeFinancialStatements import makeFinancialStatements
from fetchHistoricalPricing import fetchHistoricalPricing
from fetchSharesOutstanding import fetchSharesOutstanding
from handleDividendsPaid import handleDividendsPaid
from evaluate import evaluate


def removeStock(ref, _symbol):
    print(f"Removing {_symbol}...")
    ref.delete()


argParser = argparse.ArgumentParser()
argParser.add_argument("--exchange", type=str)
argParser.add_argument("--symbol", type=str)
args = argParser.parse_known_args()
exchange = args[0].exchange
targetSymbol = args[0].symbol

today = dateToDateString(datetime.now())


exchangeRef = db.collection("exchanges").document(exchange)
exchangeData = exchangeRef.get().to_dict()
exchangeName = exchangeData["name"]
exchangeSymbols = exchangeData["symbols"]
symbolCount = 0


for symbolData in exchangeSymbols:
    symbol = symbolData["symbol"]

    # if we're targetting a specific symbol and it matches or we're not targetting any symbols
    if (targetSymbol and targetSymbol == symbol) or not targetSymbol:
        symbolCount += 1
        print(
            f"Updating {exchangeName}: {symbol}, {symbolCount} of {len(exchangeSymbols)}..."
        )

        # get the stock
        stockRef = exchangeRef.collection("stocks").document(symbol)
        stockData = stockRef.get().to_dict()

        # skip stocks that don't exist
        if not stockData:
            if targetSymbol:
                break

            continue

        # replace any None values with 0 (lord knows how they got in there, probably my spaghetti code)
        recursiveReplacer(stockData, None, 0)

        stock = typedload.load(stockData, Stock)

        # don't process stocks that have already been updated today
        if not targetSymbol and stock.lastUpdated == today:
            continue

        try:
            # get the latest price
            stock = fetchLatestPrice(stock, exchange)

            # if there is no price or the price is 0, remove the stock
            if not stock.currentPrice:
                removeStock(stockRef, symbol)

                if targetSymbol:
                    break

                continue

            # get and merge the latest financial statements
            latestFinancialStatements = fetchLatestFinancialStatements(symbol)

            financialStatements = makeFinancialStatements(
                stock.financialStatements, latestFinancialStatements
            )

            # if empty financial statements, we don't want to save it
            if not financialStatements:
                removeStock(stockRef, symbol)

                if targetSymbol:
                    break

                continue

            stock.financialStatements = financialStatements

            # get new historical pricing
            historicalPricing = fetchHistoricalPricing(symbol)

            if historicalPricing:
                stock.historicalPricing = historicalPricing

            # get the latest shares outstanding
            stock.sharesOutstanding = fetchSharesOutstanding(symbol)

            # get the latest dividends
            stock = handleDividendsPaid(stock)

        except:
            removeStock(stockRef, symbol)

            if targetSymbol:
                break

            continue

        # evaluate the stock
        stock.valuation = evaluate(stock)

        # add the last updated date
        stock.lastUpdated = today

        # convert our stock class to a json string
        stockJson = json.loads(
            json.dumps(stock, default=lambda o: o.__dict__, indent=2)
        )

        stockRef.set(stockJson, merge=True)

        if targetSymbol:
            break
