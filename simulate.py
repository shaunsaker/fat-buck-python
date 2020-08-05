import argparse
import json
from typing import List
from datetime import datetime
import math
import typedload
from dateutil.relativedelta import relativedelta
from alive_progress import alive_bar
from models import (
    Stocks,
    Stock,
    Portfolio,
    Date,
    PortfolioTransaction,
    PortfolioStock,
    ValuationModel,
)
from getStockSnapshot import getStockSnapshot
from evaluate import evaluate
import utils
from getStocks import getStocks


def makeDeposit(
    portfolio: Portfolio, date, amount: float, transactionId: str = ""
) -> Portfolio:
    transactionId = transactionId or utils.generateUuid()
    dateString = utils.dateToDateString(date)

    # add the deposit to our portfolio cash
    portfolio.cash = round(portfolio.cash + amount, 2)

    # add the transaction
    transaction = PortfolioTransaction(
        date=dateString, transactionType="DEPOSIT", amount=amount
    )
    portfolio.transactionHistory[transactionId] = transaction

    return portfolio


def makeDividendPayment(
    portfolio: Portfolio,
    date,
    stock: Stock,
    model: ValuationModel,
    transactionId: str = "",
) -> Portfolio:
    # sanity check
    # need to own the stock
    # need to have shares
    # stock needs to have a dividend yield
    if (
        stock.symbol not in portfolio.stocks
        or not portfolio.stocks[stock.symbol].noShares
        or not stock.valuation.dividendYield
    ):
        return portfolio

    transactionId = transactionId or utils.generateUuid()
    dateString = utils.dateToDateString(date)

    # check how many shares we own and calculate the dividends due (minus tax)
    noSharesOwned = portfolio.stocks[stock.symbol].noShares
    dividendsDue = round(
        stock.valuation.dividendYield * noSharesOwned * (1 - model.taxRate), 2,
    )

    # add the dividend payment to our portfolio cash
    portfolio.cash = round(portfolio.cash + dividendsDue, 2)

    # add the transaction
    transaction = PortfolioTransaction(
        date=dateString,
        transactionType="DIVIDEND",
        amount=dividendsDue,
        symbol=stock.symbol,
    )
    portfolio.transactionHistory[transactionId] = transaction

    # print(
    #     "Dividend payments of",
    #     dividendsDue,
    #     "for",
    #     stock.symbol,
    #     "on",
    #     dateString,
    #     "with",
    #     noSharesOwned,
    #     "shares owned and",
    #     stock.valuation.dividendYield,
    #     "dividend yield",
    # )

    return portfolio


def makeSale(
    portfolio: Portfolio,
    date,
    stock: Stock,
    model: ValuationModel,
    transactionId: str = "",
) -> Portfolio:
    # sanity check
    if not stock.symbol in portfolio.stocks:
        return portfolio

    transactionId = transactionId or utils.generateUuid()
    dateString = utils.dateToDateString(date)

    # check how many shares we own
    portfolioStock = portfolio.stocks[stock.symbol]
    noSharesOwned = portfolioStock.noShares

    # calculate the sale amount including tax deduction
    capitalGained = noSharesOwned * (stock.currentPrice - portfolioStock.avgPrice)

    # don't deduct capital gains losses
    if capitalGained < 0:
        capitalGained = 0.00

    cashFromSale = round(
        noSharesOwned * stock.currentPrice - capitalGained * (1 - model.taxRate), 2,
    )

    # add the cash from the sale to our portfolio cash
    portfolio.cash = round(portfolio.cash + cashFromSale, 2)

    # remove the stock from list of owned stocks in portfolio
    portfolio.stocks.pop(stock.symbol)

    # add the transaction to the portfolio
    transaction = PortfolioTransaction(
        date=dateString,
        transactionType="SELL",
        amount=cashFromSale,
        symbol=stock.symbol,
        price=stock.currentPrice,  # TODO should we include avg price?
        noShares=noSharesOwned,
    )
    portfolio.transactionHistory[transactionId] = transaction

    # print(
    #     "Sold",
    #     noSharesOwned,
    #     "shares of",
    #     stock.symbol,
    #     "at",
    #     stock.currentPrice,
    #     "with",
    #     cashFromSale,
    #     "cash from sale",
    # )

    return portfolio


def makePurchase(
    portfolio: Portfolio,
    date,
    stock: Stock,
    model: ValuationModel,
    transactionId: str = "",
) -> Portfolio:

    # sanity check
    # not enough cash to purchase at least one share
    if portfolio.cash < stock.currentPrice:
        return portfolio

    transactionId = transactionId or utils.generateUuid()
    dateString = utils.dateToDateString(date)

    # check how many shares we can purchase
    if portfolio.cash <= model.buyLimit:
        noSharesToPurchase = math.floor(portfolio.cash / stock.currentPrice)
    else:
        noSharesToPurchase = math.floor(model.buyLimit / stock.currentPrice)

    # adjust the avg price of the stock and the number of shares that we own
    if stock.symbol in portfolio.stocks:
        portfolioStock = portfolio.stocks[stock.symbol]
        portfolioStock.avgPrice = round(
            (portfolioStock.avgPrice + stock.currentPrice) / 2, 2
        )
        portfolioStock.noShares = portfolioStock.noShares + noSharesToPurchase

    else:
        portfolioStock = PortfolioStock(
            avgPrice=stock.currentPrice, noShares=noSharesToPurchase
        )

    # reassign the updated stock
    portfolio.stocks[stock.symbol] = portfolioStock

    # remove purchase amount from our portfolio cash
    sharesCost = round(noSharesToPurchase * stock.currentPrice, 2)
    portfolio.cash = round(portfolio.cash - sharesCost, 2)

    # add the transaction to the portfolio
    transaction = PortfolioTransaction(
        date=dateString,
        transactionType="BUY",
        amount=sharesCost,
        symbol=stock.symbol,
        price=stock.currentPrice,
        noShares=noSharesToPurchase,
    )
    portfolio.transactionHistory[transactionId] = transaction

    # print(
    #     "Purchased",
    #     noSharesToPurchase,
    #     "shares of",
    #     stock.symbol,
    #     "at",
    #     stock.currentPrice,
    #     "with",
    #     portfolio.cash,
    #     "left over and",
    #     portfolio.cash,
    #     "to start with",
    # )

    return portfolio


def getPortfolio(startAmount, filename) -> Portfolio:
    # if a portfolio exists, use it
    if utils.fileExists(filename):
        with open(filename) as file:
            portfolio = typedload.load(json.load(file), Portfolio)

    else:
        portfolio = Portfolio()
        date = datetime.now()
        portfolio = makeDeposit(portfolio, date, startAmount)

    return portfolio


def getStartDate(stocks: Stocks) -> Date:
    # get the earliest date we can start running the simulation
    # by finding the earliest set of financial statements in stocks
    startDate = ""

    for symbol in stocks:
        for date in stocks[symbol].financialStatements.incomeStatements:
            startDate = utils.getSmallest(startDate, date)

        for date in stocks[symbol].financialStatements.balanceSheets:
            startDate = utils.getSmallest(startDate, date)

        for date in stocks[symbol].financialStatements.cashFlowStatements:
            startDate = utils.getSmallest(startDate, date)

    return startDate


def stockHasHistoricalPriceForDate(stock: Stock, date) -> bool:
    dateString = utils.dateToDateString(date)

    if dateString not in stock.historicalPricing:
        return False
    elif (
        dateString in stock.historicalPricing
        and stock.historicalPricing[dateString] == 0.0
    ):
        return False

    return True


def trade(
    portfolio: Portfolio,
    stocksToBuy: List[Stock],
    stocksToSell: List[Stock],
    date,
    stocks: Stocks,
    model: ValuationModel,
):
    if utils.isEndOfMonth(date):
        portfolio = makeDeposit(portfolio, date, model.topUp)

    # buy stocks and add them to our portfolio
    # TODO distribute buy amount proportionally based on mos
    stocksToBuy.sort(key=lambda e: e["valuation"]["mos"], reverse=True)  # sort by mos
    for stock in stocksToBuy:
        portfolio = makePurchase(portfolio, date, stock, model)

    # sell stocks if we own them in our portfolio
    for stock in stocksToSell:
        if stock.symbol in portfolio.stocks:
            portfolio = makeSale(portfolio, date, stock, model)

    # for any stocks in our portfolio
    # if the current date matches a date in its cash flow statements (TODO this will break if we use quarterly statements or if statement dates aren't yearly)
    # and dividends were paid, pay out the dividends
    dateString = utils.dateToDateString(date)
    for symbol in portfolio.stocks:
        if dateString in stocks[symbol].financialStatements.cashFlowStatements:
            portfolio = makeDividendPayment(portfolio, date, stocks[symbol], model)

    return portfolio


def getSnapshotUrl(symbol, date, modelName, exchange):
    return (
        f"data/snapshots/{exchange}/{modelName}/{date.date().__str__()}/{symbol}.json"
    )


def saveSnapshot(snapshotUrl, snapshot):
    with utils.safeOpenWrite(snapshotUrl) as file:
        jsonString2 = json.dumps(snapshot, default=lambda o: o.__dict__, indent=2)
        file.write(jsonString2)


def getRoi(portfolio: Portfolio, stocks: Stocks, startDate, endDate) -> Portfolio:
    # TODO test this
    # cash + current price of the stocks we own
    valueOfPortfolio = portfolio.cash

    for symbol in portfolio.stocks:
        noShares = portfolio.stocks[symbol].noShares
        currentPrice = stocks[symbol].currentPrice
        valueOfShares = noShares * currentPrice
        valueOfPortfolio = valueOfPortfolio + valueOfShares

    # how much cash have we deposited
    totalInvested = 0
    for transactionId in portfolio.transactionHistory:
        if portfolio.transactionHistory[transactionId].transactionType == "DEPOSIT":
            totalInvested = (
                totalInvested + portfolio.transactionHistory[transactionId].amount
            )

    # how many years have we been trading
    noYrs = relativedelta(endDate, startDate).years or 1

    roi = (valueOfPortfolio - totalInvested) / totalInvested / noYrs

    return roi


def simulate(
    portfolio: Portfolio,
    stocks: Stocks,
    model: ValuationModel,
    startDateArg,
    endDateArg,
    exchange,
) -> Portfolio:
    startDateString = model.startDate or getStartDate(stocks)

    # from start date increment a day
    startDate = (
        startDateArg
        and utils.dateStringToDate(startDateArg)
        or utils.dateStringToDate(startDateString)
    )
    endDate = endDateArg and utils.dateStringToDate(endDateArg) or datetime.now()
    stock = None
    stockSnapshot = None

    with alive_bar(len(list(utils.dateRange(startDate, endDate)))) as aliveBar:
        for date in utils.dateRange(startDate, endDate):
            print(f"Simulating {date}...")
            stocksToBuy = []
            stocksToSell = []

            for symbol in stocks:
                stock = stocks[symbol]

                if stockHasHistoricalPriceForDate(stock, date):
                    # get the stock's snapshot at that date and
                    # evaluate it
                    stockSnapshot = getStockSnapshot(stock, date)

                    if stockSnapshot:
                        stockSnapshot.valuation = evaluate(stockSnapshot, model)
                        snapshotUrl = getSnapshotUrl(
                            stock.symbol, date, model.name, exchange
                        )

                        if stockSnapshot.valuation.instruction == "BUY":
                            stocksToBuy.append(stockSnapshot)
                            print(
                                f"{utils.dateToDateString(date)}: Buying {stock.symbol}! {snapshotUrl}"
                            )

                            # NOTE this function call increases execution time by 33%
                            saveSnapshot(snapshotUrl, stockSnapshot)

                        elif stockSnapshot.valuation.instruction == "HOT":
                            print(
                                f"{utils.dateToDateString(date)}: {stock.symbol} is hot! {snapshotUrl}"
                            )

                            # NOTE this function call increases execution time by 33%
                            saveSnapshot(snapshotUrl, stockSnapshot)

                        elif stockSnapshot.valuation.instruction == "SELL":
                            stocksToSell.append(stockSnapshot)

            portfolio = trade(portfolio, stocksToBuy, stocksToSell, date, stocks, model)

            aliveBar()

    portfolio.roi = getRoi(portfolio, stocks, startDate, endDate)
    portfolio.model = model

    return portfolio


startingCash = 1000


def runSimulations():
    startTime = datetime.now()

    # parse args
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--exchange", type=str)
    argParser.add_argument("--startDate", type=str)
    argParser.add_argument("--endDate", type=str)
    argParser.add_argument("--fromIndex", type=int)
    argParser.add_argument("--toIndex", type=int)
    args = argParser.parse_known_args()

    exchange = args[0].exchange
    startDate = args[0].startDate
    endDate = args[0].endDate
    fromIndex = args[0].fromIndex
    toIndex = args[0].toIndex

    # for model in simulation models, run the simulation and store the result
    with open("data/models.json") as file:
        models = typedload.load(json.load(file), List[ValuationModel])

    today = datetime.now().date().__str__()
    stocks = getStocks(exchange, toIndex, fromIndex)
    portfolio = None

    for model in models:
        filename = f"data/simulations/{exchange}/{today}/{model.name}.json"

        # TEMP
        # if utils.fileExists(filename):
        #     print("Skipping", model.name)
        # else:
        print(f"Simulation started for: {model.name}")
        portfolio = getPortfolio(startingCash, filename)
        portfolio = simulate(portfolio, stocks, model, startDate, endDate, exchange)
        print(f"Simulation completed. Annualised roi: {round(portfolio.roi, 2) * 100}%")

        with utils.safeOpenWrite(filename) as file:
            jsonString = json.dumps(portfolio, default=lambda o: o.__dict__, indent=2)
            file.write(jsonString)

    endTime = datetime.now()
    print(f"Simulation complete in: {endTime - startTime}.")


runSimulations()
