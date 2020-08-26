from yahooquery import Ticker
import utils
from models import (
    Date,
    Symbol,
    YahooQueryTickerData,
    YahooQueryFinancialStatements,
    YahooQueryIncomeStatements,
    YahooQueryBalanceSheets,
    YahooQueryCashFlowStatements,
)


def getFinancialStatementsFromDataFrame(dataframe):
    financialStatements = {}

    try:
        for _, row in dataframe.iterrows():
            dateString: Date = utils.pandasDateToDateString(row["asOfDate"], True)
            rowData = row.to_dict()

            # unfortunately TTM statements are inaccurate (US/ACB), we want actual statements
            if rowData["periodType"] != "TTM":
                financialStatements[dateString] = rowData
    except:
        return financialStatements

    financialStatements = utils.falsyToInt(financialStatements)

    return financialStatements


def fetchLatestFinancialStatements(symbol: Symbol) -> YahooQueryFinancialStatements:
    # fetches the latest quarterly and yearly financial statements
    data: YahooQueryTickerData = Ticker(symbol)

    quarterlyIncomeStatements = {}
    quarterlyIncomeStatementsDf = data.income_statement("q")
    if "data unavailable" not in quarterlyIncomeStatementsDf:
        quarterlyIncomeStatements = getFinancialStatementsFromDataFrame(
            quarterlyIncomeStatementsDf
        )
    yearlyIncomeStatements = {}
    yearlyIncomeStatementsDf = data.income_statement()
    if "data unavailable" not in yearlyIncomeStatementsDf:
        yearlyIncomeStatements = getFinancialStatementsFromDataFrame(
            yearlyIncomeStatementsDf
        )
    incomeStatements = YahooQueryIncomeStatements(
        quarterly=quarterlyIncomeStatements, yearly=yearlyIncomeStatements
    )

    quarterlyBalanceSheets = {}
    quarterlyBalanceSheetsDf = data.balance_sheet("q")
    if "data unavailable" not in quarterlyBalanceSheetsDf:
        quarterlyBalanceSheets = getFinancialStatementsFromDataFrame(
            quarterlyBalanceSheetsDf
        )
    yearlyBalanceSheets = {}
    yearlyBalanceSheetsDf = data.balance_sheet()
    if "data unavailable" not in yearlyBalanceSheetsDf:
        yearlyBalanceSheets = getFinancialStatementsFromDataFrame(yearlyBalanceSheetsDf)
    balanceSheets = YahooQueryBalanceSheets(
        quarterly=quarterlyBalanceSheets, yearly=yearlyBalanceSheets
    )

    quarterlyCashFlowStatements = {}
    quarterlyCashFlowStatementsDf = data.cash_flow("q")
    if "data unavailable" not in quarterlyCashFlowStatementsDf:
        quarterlyCashFlowStatements = getFinancialStatementsFromDataFrame(
            quarterlyCashFlowStatementsDf
        )
    yearlyCashFlowStatements = {}
    yearlyCashFlowStatementsDf = data.cash_flow()
    if "data unavailable" not in yearlyCashFlowStatementsDf:
        yearlyCashFlowStatements = getFinancialStatementsFromDataFrame(
            yearlyCashFlowStatementsDf
        )
    cashFlowStatements = YahooQueryCashFlowStatements(
        quarterly=quarterlyCashFlowStatements, yearly=yearlyCashFlowStatements
    )

    financialStatements = YahooQueryFinancialStatements(
        incomeStatements=incomeStatements,
        balanceSheets=balanceSheets,
        cashFlowStatements=cashFlowStatements,
    )

    return financialStatements
