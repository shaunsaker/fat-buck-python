import copy
from yahooquery import Ticker
from models import Stock, YahooQueryTickerData


def handleDividendsPaid(stock: Stock) -> Stock:
    """
    if any of the cash flow statements don't have an amount for dividendsPaid
    (which is common for yfinance), get the fiveYearAvgDividendYield
    calculate the dividendsPaid based on sharesOutstanding
    and add that to the cash flow statement
    """

    newStock = copy.deepcopy(stock)

    symbol = stock.symbol
    data: YahooQueryTickerData = Ticker(symbol)
    summaryDetailData = data.summary_detail

    # try use the fiveYearAvgDividendYield, otherwise we assume no dividends were paid in the last 5 years
    try:
        avgDividendYield = float(summaryDetailData[symbol]["fiveYearAvgDividendYield"])
        sharesOutstanding = stock.sharesOutstanding
        avgDividendsPaid = avgDividendYield * sharesOutstanding
    except:
        avgDividendsPaid = 0.00

    cashFlowStatements = stock.financialStatements.cashFlowStatements
    for date in cashFlowStatements:
        field = cashFlowStatements[date].dividendsPaid

        if not field or field == 0.00:
            field = avgDividendsPaid / 4  # quarterly statements

    return newStock
