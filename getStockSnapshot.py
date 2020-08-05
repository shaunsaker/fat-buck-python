from datetime import timedelta
from models import Stock, Currency, FinancialStatements
import utils

# TODO this date range style function is shared between so many functions
def getHistoricalPricingDateRange(stock: Stock):
    # find the date range of the pricing
    earliestDate = ""
    latestDate = ""

    for date in stock.historicalPricing:
        earliestDate = utils.getSmallest(earliestDate, date)
        latestDate = utils.getLargest(latestDate, date)

    return [earliestDate, latestDate]


def getHistoricalPrice(stock: Stock, date) -> Currency:
    dateRange = getHistoricalPricingDateRange(stock)
    dateString = utils.dateToDateString(date)

    if dateString in stock.historicalPricing:
        return stock.historicalPricing[
            dateString
        ].open  # ASSUMPTION using open and not avg of open and close
    else:
        # try a previous date recursively but make sure its within our range
        previousDate = date - timedelta(days=1)
        previousDateString = utils.dateToDateString(previousDate)

        if previousDateString >= dateRange[0]:
            return getHistoricalPrice(stock, previousDate)
        else:
            return 0


def getHistoricalFinancialStatements(stock: Stock, targetDate) -> FinancialStatements:
    # return all of the financial statements that exist prior to date
    financialStatements = FinancialStatements()
    dateString = utils.dateToDateString(targetDate)

    for date in stock.financialStatements.incomeStatements:
        if date <= dateString:
            financialStatements.incomeStatements[
                date
            ] = stock.financialStatements.incomeStatements[date]

    for date in stock.financialStatements.balanceSheets:
        if date <= dateString:
            financialStatements.balanceSheets[
                date
            ] = stock.financialStatements.balanceSheets[date]

    for date in stock.financialStatements.cashFlowStatements:
        if date <= dateString:
            financialStatements.cashFlowStatements[
                date
            ] = stock.financialStatements.cashFlowStatements[date]

    return financialStatements


def stockHasStatements(stock: Stock) -> bool:
    if (
        not bool(stock.financialStatements.incomeStatements)
        or not bool(stock.financialStatements.balanceSheets)
        or not bool(stock.financialStatements.cashFlowStatements)
    ):
        return False

    return True


def getStockSnapshot(stock: Stock, date) -> Stock:
    stockSnapshot = Stock()
    stockSnapshot.symbol = stock.symbol
    stockSnapshot.currentPrice = getHistoricalPrice(stock, date)

    if not stockSnapshot.currentPrice:
        return None

    # ASSUMPTION sharesOutstanding did not change (we don't have that data)
    stockSnapshot.sharesOutstanding = stock.sharesOutstanding
    stockSnapshot.financialStatements = getHistoricalFinancialStatements(stock, date)
    stockSnapshot.historicalPricing = stock.historicalPricing

    if not stockHasStatements(stockSnapshot):
        return None

    return stockSnapshot
