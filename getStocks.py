import os
from datetime import datetime
import json
import typedload
from models import Stocks, Stock


def getStockList(exchange, toIndex=0, fromIndex=0):
    stockList = []

    pathToStocks = f"data/stocks/{exchange}/"
    fileList = os.listdir(pathToStocks)

    for i, filename in enumerate(fileList):
        if (
            (toIndex and i >= fromIndex and i <= toIndex)
            or not toIndex
            and filename.endswith(".json")
        ):
            stockList.append(filename.replace(".json", ""))

    return stockList


def getStocks(exchange, toIndex=0, fromIndex=0) -> Stocks:
    # create a list of stocks from each file in data/stocks/{exchange}
    print("Getting stocks...")
    startTime = datetime.now()

    pathToStocks = f"data/stocks/{exchange}/"
    stockList = getStockList(exchange, toIndex, fromIndex)

    stocks = {}
    stock = None
    for fileName in stockList:
        with open(f"{pathToStocks}{fileName}") as file:
            stock = typedload.load(json.load(file), Stock)
            stocks[stock.symbol] = stock

    endTime = datetime.now()
    print(f"Got stocks. It took {endTime - startTime}.")

    return stocks
