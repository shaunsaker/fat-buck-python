import json
from datetime import datetime
import typedload
from alive_progress import alive_bar
from firebase import db
from utils import recursiveReplacer, getNumberOfSymbolsToProcess, dateToDateString
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


# get the exchanges
exchangesRef = db.collection("exchanges")
exchanges = exchangesRef.get()


today = dateToDateString(datetime.now())

with alive_bar(getNumberOfSymbolsToProcess(exchanges)) as bar:
    for exchange in exchanges:
        exchangeData = exchange.to_dict()
        exchangeName = exchangeData["name"]
        exchangeSymbols = exchangeData["symbols"]

        for symbolData in exchangeSymbols:
            symbol = symbolData["symbol"]

            print(f"Updating {symbol}...")

            # get the stock
            stockRef = (
                exchangesRef.document(exchangeName)
                .collection("stocks")
                .document(symbol)
            )
            stockData = stockRef.get().to_dict()

            # skip stocks that don't exist
            if not stockData:
                bar()
                continue

            # replace any None values with 0 (lord knows how they got in there, probably my spaghetti code)
            recursiveReplacer(stockData, None, 0)

            stock = typedload.load(stockData, Stock)

            # don't process stocks that have already been updated today
            if stock.lastUpdated == today:
                bar()
                continue

            try:
                # get the latest price
                stock = fetchLatestPrice(stock, exchange)

                # get and merge the latest financial statements
                latestFinancialStatements = fetchLatestFinancialStatements(symbol)

                financialStatements = makeFinancialStatements(
                    stock.financialStatements, latestFinancialStatements
                )

                # if empty financial statements, we don't want to save it
                if not financialStatements:
                    removeStock(stockRef, symbol)
                    bar()
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
                bar()
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

            bar()
