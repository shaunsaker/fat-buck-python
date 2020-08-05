import argparse
import json
from typing import List
import typedload
from alive_progress import alive_bar
from models import SymbolData, Stock, ValuationModel
from checkSymbolExists import checkSymbolExists
from fetchHistoricalData import fetchHistoricalData
from fetchLatestPrice import fetchLatestPrice
from fetchLatestFinancialStatements import fetchLatestFinancialStatements
from makeFinancialStatements import makeFinancialStatements
from fetchSharesOutstanding import fetchSharesOutstanding
from handleDividendsPaid import handleDividendsPaid
from evaluate import evaluate
import utils
from removeSymbol import removeSymbol

# constants
model = ValuationModel()

argParser = argparse.ArgumentParser()
argParser.add_argument("--exchange", type=str)
args = argParser.parse_known_args()

exchange = args[0].exchange
symbolsFilename = f"data/symbols/{exchange}.json"

with open(symbolsFilename) as file:
    symbols = typedload.load(json.load(file), List[SymbolData])

with alive_bar(len(symbols)) as bar:
    for symbolData in symbols:
        symbol = symbolData.symbol
        filename = f"data/stocks/{exchange}/{symbol}.json"

        # if utils.fileExists(filename):
        #     # TODO temp while fixing scripts
        #     print(f"Skipping {symbol}")
        # else:
        symbolExists = checkSymbolExists(symbolData)

        if symbolExists:
            print(f"Fetching data for {symbol}...")

            stock = Stock()
            stock.symbol = symbol

            try:
                # once-off functions
                stock = fetchHistoricalData(stock, exchange)

                if stock:
                    # regular functions
                    stock = fetchLatestPrice(stock, exchange)

                    if stock:
                        latestFinancialStatements = fetchLatestFinancialStatements(
                            stock.symbol
                        )
                        stock.financialStatements = makeFinancialStatements(
                            stock.financialStatements, latestFinancialStatements
                        )
                        stock.sharesOutstanding = fetchSharesOutstanding(stock.symbol)
                        stock = handleDividendsPaid(stock)
                        # stock.valuation = evaluate(stock, model)

                        with utils.safeOpenWrite(filename) as file:
                            jsonString = json.dumps(
                                stock, default=lambda o: o.__dict__, indent=2
                            )
                            file.write(jsonString)

                else:
                    print(f"{symbol} does not exist.")
                    removeSymbol(symbol, exchange)
            except:
                print(f"{symbol} error.")
                removeSymbol(symbol, exchange)

        bar()
