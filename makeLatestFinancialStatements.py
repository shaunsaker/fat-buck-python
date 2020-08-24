from models import (
    YahooQueryFinancialStatements,
    YahooQueryIncomeStatement,
    YahooQueryBalanceSheet,
    YahooQueryCashFlowStatement,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    AllFinancialStatements,
    AllIncomeStatements,
    AllBalanceSheets,
    AllCashFlowStatements,
    Currency,
)
import utils


def parseYahooQueryIncomeStatement(
    yahooQueryIncomeStatement: YahooQueryIncomeStatement,
) -> IncomeStatement:
    parsedIncomeStatement = IncomeStatement()

    parsedIncomeStatement.totalRevenue = utils.getCurrencyIfExists(
        "TotalRevenue", yahooQueryIncomeStatement
    )

    parsedIncomeStatement.netIncome = utils.getCurrencyIfExists(
        "NetIncomeCommonStockholders", yahooQueryIncomeStatement
    )
    parsedIncomeStatement.incomeBeforeTax = utils.getCurrencyIfExists(
        "PretaxIncome", yahooQueryIncomeStatement
    )

    try:
        parsedIncomeStatement.interestIncome = utils.stringToCurrency(
            yahooQueryIncomeStatement["InterestIncome"]
        )
    except:
        parsedIncomeStatement.interestIncome = utils.getCurrencyIfExists(
            "NetInterestIncome", yahooQueryIncomeStatement
        )

    try:
        parsedIncomeStatement.interestExpense = utils.stringToCurrency(
            "InterestExpense", yahooQueryIncomeStatement
        )
    except:
        parsedIncomeStatement.interestExpense = utils.getCurrencyIfExists(
            "NetNonOperatingInterestIncomeExpense", yahooQueryIncomeStatement
        )

    return parsedIncomeStatement


def getCurrentAssetsEstimate(
    yahooQueryBalanceSheet: YahooQueryBalanceSheet,
) -> Currency:
    # ASSUMPTION
    currentAssets = (
        utils.stringToCurrency(yahooQueryBalanceSheet["TotalAssets"])
        - utils.getCurrencyIfExists("BuildingsAndImprovements", yahooQueryBalanceSheet)
        - utils.getCurrencyIfExists(
            "GoodwillAndOtherIntangibleAssets", yahooQueryBalanceSheet
        )
        - utils.getCurrencyIfExists("GrossPPE", yahooQueryBalanceSheet)
        - utils.getCurrencyIfExists("InvestmentProperties", yahooQueryBalanceSheet)
        - utils.getCurrencyIfExists("OtherProperties", yahooQueryBalanceSheet)
        - utils.getCurrencyIfExists("Properties", yahooQueryBalanceSheet)
    )

    return currentAssets


def parseYahooQueryBalanceSheet(
    yahooQueryBalanceSheet: YahooQueryBalanceSheet,
) -> BalanceSheet:
    parsedBalanceSheet = BalanceSheet()

    try:
        parsedBalanceSheet.assets = utils.stringToCurrency(
            yahooQueryBalanceSheet["TotalAssets"]
        )
    except:
        try:
            parsedBalanceSheet.assets = utils.stringToCurrency(
                yahooQueryBalanceSheet["TotalLiabilitiesNetMinorityInterest"]
            ) + utils.stringToCurrency(
                yahooQueryBalanceSheet["TotalEquityGrossMinorityInterest"]
            )

        except:
            parsedBalanceSheet.assets = utils.stringToCurrency(
                yahooQueryBalanceSheet["CurrentAssets"]
            )

    try:
        parsedBalanceSheet.currentAssets = utils.stringToCurrency(
            yahooQueryBalanceSheet["CurrentAssets"]
        )
    except:
        parsedBalanceSheet.currentAssets = getCurrentAssetsEstimate(
            yahooQueryBalanceSheet
        )

    try:
        parsedBalanceSheet.liabilities = utils.stringToCurrency(
            yahooQueryBalanceSheet["TotalLiabilitiesNetMinorityInterest"]
        )
    except:
        try:
            parsedBalanceSheet.liabilities = utils.stringToCurrency(
                yahooQueryBalanceSheet["TotalDebt"]
            )
        except:
            parsedBalanceSheet.liabilities = utils.stringToCurrency(
                yahooQueryBalanceSheet["CurrentDebt"]
            )

    try:
        parsedBalanceSheet.currentLiabilities = utils.stringToCurrency(
            yahooQueryBalanceSheet["CurrentLiabilities"]
        )
    except:
        parsedBalanceSheet.currentLiabilities = utils.getCurrencyIfExists(
            "TotalDebt", yahooQueryBalanceSheet
        )

    try:
        parsedBalanceSheet.retainedEarnings = utils.stringToCurrency(
            yahooQueryBalanceSheet["RetainedEarnings"]
        )
    except:
        # ASSUMPTION
        parsedBalanceSheet.retainedEarnings = 0

    try:
        parsedBalanceSheet.cash = utils.stringToCurrency(
            yahooQueryBalanceSheet["CashAndCashEquivalents"]
        )
    except:
        # ASSUMPTION that working capital is the same as cash
        parsedBalanceSheet.cash = utils.getCurrencyIfExists(
            "WorkingCapital", yahooQueryBalanceSheet
        )

    return parsedBalanceSheet


def parseYahooQueryCashFlowStatement(
    yahooQueryCashFlowStatement: YahooQueryCashFlowStatement,
) -> CashFlowStatement:
    parsedCashFlowStatement = CashFlowStatement()
    # yfinance does not contain this field in any of its financial statements
    # so we will add it in a separate flow afterwards
    parsedCashFlowStatement.dividendsPaid = 0.00
    parsedCashFlowStatement.cashFromOperations = utils.getCurrencyIfExists(
        "OperatingCashFlow", yahooQueryCashFlowStatement
    )

    try:
        parsedCashFlowStatement.capex = utils.stringToCurrency(
            yahooQueryCashFlowStatement["CapitalExpenditure"]
        )
    except:
        # if CapitalExpenditure is not available work backwards from FreeCashFlow
        parsedCashFlowStatement.capex = (
            parsedCashFlowStatement.cashFromOperations
            - utils.getCurrencyIfExists("FreeCashFlow", yahooQueryCashFlowStatement)
        )

    return parsedCashFlowStatement


def parseYahooStatements(statements, statementType, cycleType, parser):
    parsedStatements = {}
    for date in statements[statementType][cycleType]:
        parsedStatements[date] = parser(statements[statementType][cycleType][date])

    return parsedStatements


def makeLatestFinancialStatements(
    data: YahooQueryFinancialStatements,
) -> AllFinancialStatements:
    # Parse the yquery statements into a format we expect
    latestQuarterlyIncomeStatements = parseYahooStatements(
        data, "incomeStatements", "quarterly", parseYahooQueryIncomeStatement,
    )
    latestYearlyIncomeStatements = parseYahooStatements(
        data, "incomeStatements", "yearly", parseYahooQueryIncomeStatement,
    )
    latestQuarterlyBalanceSheets = parseYahooStatements(
        data, "balanceSheets", "quarterly", parseYahooQueryBalanceSheet,
    )
    latestYearlyBalanceSheets = parseYahooStatements(
        data, "balanceSheets", "yearly", parseYahooQueryBalanceSheet,
    )
    latestQuarterlyCashFlowStatements = parseYahooStatements(
        data, "cashFlowStatements", "quarterly", parseYahooQueryCashFlowStatement,
    )
    latestYearlyCashFlowStatements = parseYahooStatements(
        data, "cashFlowStatements", "yearly", parseYahooQueryCashFlowStatement,
    )

    latestIncomeStatements = AllIncomeStatements(
        quarterly=latestQuarterlyIncomeStatements, yearly=latestYearlyIncomeStatements
    )
    latestBalanceSheets = AllBalanceSheets(
        quarterly=latestQuarterlyBalanceSheets, yearly=latestYearlyBalanceSheets
    )
    latestCashFlowStatements = AllCashFlowStatements(
        quarterly=latestQuarterlyCashFlowStatements,
        yearly=latestYearlyCashFlowStatements,
    )
    latestFinancialStatements = AllFinancialStatements(
        incomeStatements=latestIncomeStatements,
        balanceSheets=latestBalanceSheets,
        cashFlowStatements=latestCashFlowStatements,
    )

    return latestFinancialStatements
