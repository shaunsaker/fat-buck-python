import copy
from datetime import datetime, timedelta
import math
import simulate
from models import (
    Stock,
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    Stocks,
    SimulateTestStockModel,
    HistoricalPrice,
    Portfolio,
    ValuationModel,
)
import utils


def testMakeDeposit():
    portfolio = Portfolio()
    date = datetime(2020, 5, 17)
    amount = 1000
    transactionId = "1"

    # test that a single deposit can b made
    newPortfolio = simulate.makeDeposit(portfolio, date, amount, transactionId)

    # test that our cash balance was affected
    assert newPortfolio.cash == amount

    # test that the deposit was added to our transaction history
    assert len(newPortfolio.transactionHistory) == 1
    assert newPortfolio.transactionHistory[transactionId]
    assert newPortfolio.transactionHistory[transactionId].transactionType == "DEPOSIT"
    assert newPortfolio.transactionHistory[
        transactionId
    ].date == utils.dateToDateString(date)
    assert newPortfolio.transactionHistory[transactionId].amount == amount

    # test that multiple deposits can be made
    newPortfolio = simulate.makeDeposit(newPortfolio, date, amount)
    assert newPortfolio.cash == amount * 2
    assert len(newPortfolio.transactionHistory) == 2


def testMakePurchase():
    portfolio = Portfolio()
    date = datetime(2020, 5, 17)
    startingCash = 1500
    sharePrice1 = 50
    stock1 = Stock(symbol="SS", currentPrice=sharePrice1)
    model = ValuationModel(buyLimit=1000)

    # make a deposit so we have some cash to work with
    newPortfolio = simulate.makeDeposit(portfolio, date, startingCash, "deposit1")

    # buy some stock when we have more cash than the buyLimit available
    transactionId = "1"
    expectedNoSharesPurchased1 = math.floor(model.buyLimit / sharePrice1)
    expectedCost1 = expectedNoSharesPurchased1 * sharePrice1
    newPortfolio = simulate.makePurchase(
        newPortfolio, date, stock1, model, transactionId
    )

    # test that our cash balance was affected correctly
    assert newPortfolio.cash == startingCash - expectedCost1

    # test that the stock is in stocks
    assert len(newPortfolio.stocks) == 1
    assert newPortfolio.stocks[stock1.symbol]
    assert newPortfolio.stocks[stock1.symbol].avgPrice == sharePrice1
    assert newPortfolio.stocks[stock1.symbol].noShares == expectedNoSharesPurchased1

    # test that the purchase is in our transaction history
    assert len(newPortfolio.transactionHistory) == 2
    assert newPortfolio.transactionHistory[transactionId]
    assert newPortfolio.transactionHistory[transactionId].transactionType == "BUY"
    assert newPortfolio.transactionHistory[
        transactionId
    ].date == utils.dateToDateString(date)
    assert newPortfolio.transactionHistory[transactionId].amount == expectedCost1
    assert newPortfolio.transactionHistory[transactionId].symbol == stock1.symbol
    assert newPortfolio.transactionHistory[transactionId].price == stock1.currentPrice

    sharePrice2 = 100
    stock2 = Stock(symbol="SS2", currentPrice=sharePrice2)

    # make another purchase of a different stock
    transactionId2 = "2"
    expectedNoSharesPurchased2 = math.floor(newPortfolio.cash / sharePrice2)
    expectedCost2 = expectedNoSharesPurchased2 * sharePrice2
    newPortfolio = simulate.makePurchase(
        newPortfolio, date, stock2, model, transactionId2
    )

    # # test that our cash balance was affected correctly
    assert newPortfolio.cash == startingCash - expectedCost1 - expectedCost2

    # test that the stock is in stocks
    assert len(newPortfolio.stocks) == 2
    assert newPortfolio.stocks[stock2.symbol]
    assert newPortfolio.stocks[stock2.symbol].avgPrice == sharePrice2
    assert newPortfolio.stocks[stock2.symbol].noShares == expectedNoSharesPurchased2

    # test that the purchase is in our transaction history
    assert len(newPortfolio.transactionHistory) == 3

    # make a top up
    topUp = 500
    newPortfolio = simulate.makeDeposit(newPortfolio, date, topUp, "deposit2")

    # make another purchase of stock1 but pretends it's price went down
    newStock1 = stock1
    newSharePrice1 = 40
    newStock1.currentPrice = newSharePrice1
    transactionId3 = "3"
    expectedNoSharesPurchased3 = math.floor(newPortfolio.cash / newSharePrice1)
    newPortfolio = simulate.makePurchase(
        newPortfolio, date, newStock1, model, transactionId3
    )

    # test that the new stocks were correctly added to the existing stock
    assert (
        newPortfolio.stocks[stock1.symbol].noShares
        == expectedNoSharesPurchased1 + expectedNoSharesPurchased3
    )
    assert (
        newPortfolio.stocks[stock1.symbol].avgPrice
        == (sharePrice1 + newSharePrice1) / 2
    )


def testMakeDividendPayment():
    portfolio = Portfolio()
    date = datetime(2020, 5, 17)
    model = ValuationModel()
    symbol = "SS"
    stock = Stock(symbol=symbol, currentPrice=100)
    stock.valuation.dividendYield = 2

    # it should just return the original portfolio when we have no stocks in our portfolio
    newPortfolio = simulate.makeDividendPayment(portfolio, date, stock, model)
    assert newPortfolio == portfolio

    # to receive a dividend payment, we need:
    # a dividendYield in the stock's valuation
    # the stock in our portfolio
    newPortfolio = simulate.makeDeposit(newPortfolio, date, 1000, "deposit")
    newPortfolio = simulate.makePurchase(newPortfolio, date, stock, model, "purchase")
    transactionId = "1"
    newPortfolio = simulate.makeDividendPayment(
        newPortfolio, date, stock, model, transactionId
    )

    # test that our cash balance reflects the dividends paid
    expectedDividends = round(
        (newPortfolio.stocks[stock.symbol].noShares * stock.valuation.dividendYield)
        * (1 - model.taxRate),
        2,
    )
    assert newPortfolio.cash == expectedDividends

    # test that the transaction was added
    assert len(newPortfolio.transactionHistory) == 3
    assert newPortfolio.transactionHistory[transactionId]
    assert newPortfolio.transactionHistory[transactionId].transactionType == "DIVIDEND"
    assert newPortfolio.transactionHistory[
        transactionId
    ].date == utils.dateToDateString(date)
    assert newPortfolio.transactionHistory[transactionId].amount == expectedDividends
    assert newPortfolio.transactionHistory[transactionId].symbol == stock.symbol


def testMakeSale():
    portfolio = Portfolio()
    date = datetime(2020, 5, 17)
    model = ValuationModel()
    symbol = "SS"
    sharePrice = 100
    stock = Stock(symbol=symbol, currentPrice=sharePrice)

    # first buy a stock
    startingCash = 2000
    newPortfolio = simulate.makeDeposit(portfolio, date, startingCash)
    newPortfolio = simulate.makePurchase(newPortfolio, date, stock, model)
    assert newPortfolio.stocks[symbol]

    # buy some more of the updated stock to average out the price
    stock.currentPrice = 50
    newPortfolio = simulate.makePurchase(newPortfolio, date, stock, model)

    # now sell the stock at a higher price
    stock.currentPrice = 120
    expectedCapitalGained = newPortfolio.stocks[symbol].noShares * (
        stock.currentPrice - newPortfolio.stocks[symbol].avgPrice
    )
    expectedCashFromSale = round(
        newPortfolio.stocks[symbol].noShares * stock.currentPrice
        - expectedCapitalGained * (1 - model.taxRate),
        2,
    )
    transactionId = "1"
    newPortfolio = simulate.makeSale(newPortfolio, date, stock, model, transactionId)
    assert newPortfolio.cash == expectedCashFromSale

    # the stock should have been removed from our portfolio
    assert symbol not in newPortfolio.stocks

    # a transaction should have been added
    assert newPortfolio.transactionHistory[transactionId]
    assert newPortfolio.transactionHistory[transactionId].transactionType == "SELL"
    assert newPortfolio.transactionHistory[
        transactionId
    ].date == utils.dateToDateString(date)
    assert newPortfolio.transactionHistory[transactionId].amount == expectedCashFromSale
    assert newPortfolio.transactionHistory[transactionId].symbol == stock.symbol


def testGetNewPortfolio():
    portfolio = simulate.getNewPortfolio(simulate.startingCash)

    assert portfolio.cash == simulate.startingCash
    assert len(portfolio.transactionHistory) == 1


# slow test (enable as needed)
# def testGetStocks():
#     # just make sure something is returned (typedload will ensure that the data is expected)
#     assert(bool(simulate.getStocks()) == True)


def makeStock(model: SimulateTestStockModel) -> Stock:
    startDateObj = utils.dateStringToDate(model.startDate)
    endDateObj = utils.dateStringToDate(model.endDate)
    dateRange = utils.dateRange(startDateObj, endDateObj)

    historicalPricing = {}
    incomeStatements = {}
    balanceSheets = {}
    cashFlowStatements = {}

    for date in dateRange:
        dateString = utils.dateToDateString(date)
        historicalPricing[dateString] = HistoricalPrice()
        incomeStatements[dateString] = IncomeStatement()
        balanceSheets[dateString] = BalanceSheet()
        cashFlowStatements[dateString] = CashFlowStatement()

    financialStatements = FinancialStatements(
        incomeStatements=incomeStatements,
        balanceSheets=balanceSheets,
        cashFlowStatements=cashFlowStatements,
    )

    stock = Stock(
        symbol=model.symbol,
        historicalPricing=historicalPricing,
        financialStatements=financialStatements,
    )

    return stock


def makeStocks(models: SimulateTestStockModel) -> Stocks:
    stocks = {}

    for model in models:
        stocks[model.symbol] = makeStock(model)

    return stocks


def testGetStartDate():
    mockStartDate = "1988-06-23"
    stockModels = [
        SimulateTestStockModel(
            symbol="AS", startDate="1992-08-26", endDate="1994-08-26"
        ),
        SimulateTestStockModel(
            symbol="IS", startDate="1990-08-26", endDate="1992-08-26"
        ),
        SimulateTestStockModel(
            symbol="SS", startDate=mockStartDate, endDate="1990-08-26"
        ),
        SimulateTestStockModel(
            symbol="CS", startDate="1991-08-23", endDate="1991-08-26"
        ),
    ]
    stocks = makeStocks(stockModels)
    startDate = simulate.getStartDate(stocks)
    assert startDate == mockStartDate


def testGetHistoricalPrice():
    # works when price exists on date
    startDate = "1992-08-26"
    startDateObj = utils.dateStringToDate(startDate)
    nextDay = startDateObj + timedelta(days=1)
    nextDayString = utils.dateToDateString(nextDay)
    stock = makeStock(
        SimulateTestStockModel(symbol="AS", startDate=startDate, endDate="1994-08-26")
    )

    # works when price does not exist on date
    assert simulate.getHistoricalPrice(stock, nextDay) == 0.00

    # set the price on the day
    openPrice = 10.00
    stock.historicalPricing[nextDayString].open = openPrice

    assert simulate.getHistoricalPrice(stock, nextDay) == openPrice


def testGetHistoricalFinancialStatements():
    stock = makeStock(
        SimulateTestStockModel(
            symbol="SS", startDate="2020-07-01", endDate="2020-07-07"
        )
    )
    targetDate = "2020-07-04"
    targetDateObj = utils.dateStringToDate(targetDate)
    financialStatements = simulate.getHistoricalFinancialStatements(
        stock, targetDateObj
    )
    # 4 days worth of statements since we generate one statement per day
    assert len(financialStatements.incomeStatements) == 4
    assert len(financialStatements.balanceSheets) == 4
    assert len(financialStatements.cashFlowStatements) == 4


def testStockHasStatements():
    emptyStock = Stock()
    assert not simulate.stockHasStatements(emptyStock)

    incomeStatements = {}
    incomeStatements["2020-07-04"] = IncomeStatement()
    financialStatements = FinancialStatements(
        incomeStatements=incomeStatements, balanceSheets={}, cashFlowStatements={},
    )
    stockWithOnlyIncomeStatements = Stock(financialStatements=financialStatements)
    assert not simulate.stockHasStatements(stockWithOnlyIncomeStatements)

    balanceSheets = {}
    balanceSheets["2020-07-04"] = BalanceSheet()
    financialStatements = FinancialStatements(
        incomeStatements={}, balanceSheets=balanceSheets, cashFlowStatements={},
    )
    stockWithOnlyBalanceSheets = Stock(financialStatements=financialStatements)
    assert not simulate.stockHasStatements(stockWithOnlyBalanceSheets)

    cashFlowStatements = {}
    cashFlowStatements["2020-07-04"] = CashFlowStatement()
    financialStatements = FinancialStatements(
        incomeStatements={}, balanceSheets={}, cashFlowStatements=cashFlowStatements,
    )
    stockWithOnlyCashFlowStatements = Stock(financialStatements=financialStatements)
    assert not simulate.stockHasStatements(stockWithOnlyCashFlowStatements)

    financialStatements = FinancialStatements(
        incomeStatements=incomeStatements,
        balanceSheets=balanceSheets,
        cashFlowStatements=cashFlowStatements,
    )
    stockWithAllStatements = Stock(financialStatements=financialStatements)
    assert simulate.stockHasStatements(stockWithAllStatements)


def testStockHasHistoricalPriceForDate():
    # returns False for a blank stock
    stock = Stock()
    assert not simulate.stockHasHistoricalPriceForDate(stock, datetime.now())

    # returns False for a date before startDate
    startDate = "2020-07-01"
    startDateObj = utils.dateStringToDate(startDate)
    stock = makeStock(
        SimulateTestStockModel(symbol="SS", startDate=startDate, endDate="2020-07-07")
    )
    dayBefore = startDateObj - timedelta(days=1)
    assert not simulate.stockHasHistoricalPriceForDate(stock, dayBefore)

    # returns True when there is a price on that date
    assert simulate.stockHasHistoricalPriceForDate(stock, startDateObj)
