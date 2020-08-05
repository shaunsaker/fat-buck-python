from dateutil.relativedelta import relativedelta
from models import (
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    YahooQueryFinancialStatements,
    YahooQueryIncomeStatement,
    YahooQueryBalanceSheet,
    YahooQueryCashFlowStatement,
    Currency,
    DateRange,
    AllFinancialStatements,
)
import utils
from evaluate import getHistoricalValuesFromFinancialStatements, getGrowthRate


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


def getQuarterlyDates(existingStatements, latestStatements) -> DateRange:
    startDateString = ""
    endDateString = ""
    statementTypes = ["incomeStatements", "balanceSheets", "cashFlowStatements"]
    cycles = ["quarterly", "yearly"]

    for cycle in cycles:
        for statementType in statementTypes:
            for date in existingStatements[statementType]:
                startDateString = utils.getSmallest(startDateString, date)
                endDateString = utils.getLargest(endDateString, date)

            for date in latestStatements[statementType][cycle]:
                startDateString = utils.getSmallest(startDateString, date)
                endDateString = utils.getLargest(endDateString, date)

    if not startDateString and not endDateString:
        return None

    startDate = utils.dateStringToDate(startDateString)
    endDate = utils.dateStringToDate(endDateString)
    quarterlyDates = []
    nextDate = startDate

    while nextDate <= endDate:
        quarterlyDates.append(utils.dateToDateString(nextDate))
        nextDate = utils.getEndOfMonth(nextDate + relativedelta(months=3))

    return quarterlyDates


def getPreviousStatement(startIndex, dates, statements, factory):
    if startIndex < 0:
        return None

    newStartIndex = startIndex - 1
    previousDate = dates[newStartIndex]

    if previousDate not in statements:
        return None

    if statements[previousDate] != factory:
        previousStatement = statements[previousDate]

        return {
            "statement": previousStatement,
            "date": previousDate,
            "index": newStartIndex,
        }

    return getPreviousStatement(newStartIndex, dates, statements, factory)


def getNextStatement(
    startIndex, dates, statements, factory,
):
    newStartIndex = startIndex + 1

    if newStartIndex not in dates:
        return None

    nextDate = dates[newStartIndex]

    if statements[nextDate] != factory:
        nextStatement = statements[nextDate]

        return {"statement": nextStatement, "date": nextDate, "index": newStartIndex}

    return getNextStatement(newStartIndex, dates, statements, factory)


def getExtrapolatedEstimate(key, nextStatement, previousStatement):
    return round(
        previousStatement["statement"][key]
        + (nextStatement["statement"][key] - previousStatement["statement"][key])
        / (nextStatement["index"] - previousStatement["index"]),
        2,
    )


def getTrendEstimate(statements, key, index, previousStatement):
    historicalValues = getHistoricalValuesFromFinancialStatements(statements, key)
    values = []
    for item in historicalValues:
        values.append(item["value"])

    growthRate = getGrowthRate(values)

    # using the previous value, estimate this value using growth rate
    previousValue = previousStatement["statement"][key]
    noOfCycles = index - previousStatement["index"]
    estimatedValue = round(previousValue + (previousValue * growthRate * noOfCycles), 2)

    return estimatedValue


def getParsedStatements(statements, statementType, cycleType, parser):
    parsedStatements = {}
    for date in statements[statementType][cycleType]:
        parsedStatements[date] = parser(statements[statementType][cycleType][date])

    return parsedStatements


def getMergedStatements(
    dates,
    latestStatements,
    existingStatements,
    statementType,
    factory,
    merger,
):
    mergedStatements = {}

    for date in dates:
        latestStatement = date in latestStatements and latestStatements[date] or factory
        existingStatement = (
            date in existingStatements[statementType]
            and existingStatements[statementType][date]
            or factory
        )
        mergedStatement = merger(latestStatement, existingStatement)
        mergedStatements[date] = mergedStatement

    return mergedStatements


def isIncomeStatementEmptyOrInvalid(incomeStatement: IncomeStatement) -> bool:
    if incomeStatement == IncomeStatement():
        return True

    if (
        not incomeStatement.totalRevenue
        or not incomeStatement.netIncome
        or not incomeStatement.incomeBeforeTax
    ):
        return True

    return False


def isBalanceSheetEmptyOrInvalid(balanceSheet: BalanceSheet) -> bool:
    if balanceSheet == BalanceSheet():
        return True

    if (
        not balanceSheet.assets
        or not balanceSheet.currentAssets
        or not balanceSheet.liabilities
        or not balanceSheet.currentLiabilities
        or not balanceSheet.cash
    ):
        return True

    return False


def isCashFlowStatementEmptyOrInvalid(cashFlowStatement: CashFlowStatement) -> bool:
    if cashFlowStatement == CashFlowStatement():
        return True

    if not cashFlowStatement.cashFromOperations or not cashFlowStatement.capex:
        return True

    return False


def makeFinancialStatements(
    existingStatements: FinancialStatements,
    latestStatements: YahooQueryFinancialStatements,
) -> FinancialStatements:
    # Get a list of quarterly dates for these statements
    quarterlyDates = getQuarterlyDates(existingStatements, latestStatements)

    # if empty return None
    if not quarterlyDates:
        return None

    # Parse the yquery statements into a format we expect
    latestQuarterlyIncomeStatements = getParsedStatements(
        latestStatements,
        "incomeStatements",
        "quarterly",
        parseYahooQueryIncomeStatement,
    )
    latestYearlyIncomeStatements = getParsedStatements(
        latestStatements, "incomeStatements", "yearly", parseYahooQueryIncomeStatement,
    )
    latestQuarterlyBalanceSheets = getParsedStatements(
        latestStatements, "balanceSheets", "quarterly", parseYahooQueryBalanceSheet,
    )
    latestYearlyBalanceSheets = getParsedStatements(
        latestStatements, "balanceSheets", "yearly", parseYahooQueryBalanceSheet,
    )
    latestQuarterlyCashFlowStatements = getParsedStatements(
        latestStatements,
        "cashFlowStatements",
        "quarterly",
        parseYahooQueryCashFlowStatement,
    )
    latestYearlyCashFlowStatements = getParsedStatements(
        latestStatements,
        "cashFlowStatements",
        "yearly",
        parseYahooQueryCashFlowStatement,
    )

    # Merge statements for date
    mergedQuarterlyIncomeStatements = getMergedStatements(
        quarterlyDates,
        latestQuarterlyIncomeStatements,
        existingStatements,
        "incomeStatements",
        IncomeStatement(),
        utils.mergeIncomeStatements,
    )
    mergedYearlyIncomeStatements = getMergedStatements(
        quarterlyDates,
        latestYearlyIncomeStatements,
        existingStatements,
        "incomeStatements",
        IncomeStatement(),
        utils.mergeIncomeStatements,
    )
    mergedQuarterlyBalanceSheets = getMergedStatements(
        quarterlyDates,
        latestQuarterlyBalanceSheets,
        existingStatements,
        "balanceSheets",
        BalanceSheet(),
        utils.mergeBalanceSheets,
    )
    mergedYearlyBalanceSheets = getMergedStatements(
        quarterlyDates,
        latestYearlyBalanceSheets,
        existingStatements,
        "balanceSheets",
        BalanceSheet(),
        utils.mergeBalanceSheets,
    )
    mergedQuarterlyCashFlowStatements = getMergedStatements(
        quarterlyDates,
        latestQuarterlyCashFlowStatements,
        existingStatements,
        "cashFlowStatements",
        CashFlowStatement(),
        utils.mergeCashFlowStatements,
    )
    mergedYearlyCashFlowStatements = getMergedStatements(
        quarterlyDates,
        latestYearlyCashFlowStatements,
        existingStatements,
        "cashFlowStatements",
        CashFlowStatement(),
        utils.mergeCashFlowStatements,
    )

    incomeStatements = {}
    for date in mergedQuarterlyIncomeStatements:
        quarterlyStatement = mergedQuarterlyIncomeStatements[date]

        # if we have a quarterly statement add it
        if not isIncomeStatementEmptyOrInvalid(
            quarterlyStatement
        ):  # TODO if its not empty and has our required values
            incomeStatements[date] = quarterlyStatement

        # if the quarterlyStatement is empty, we need to try and get the values from the yearlyStatement on this date
        else:
            yearlyStatement = mergedYearlyIncomeStatements[date]

            if yearlyStatement and not isIncomeStatementEmptyOrInvalid(yearlyStatement):
                totalRevenue = yearlyStatement.totalRevenue / 4
                netIncome = yearlyStatement.netIncome / 4
                incomeBeforeTax = yearlyStatement.incomeBeforeTax / 4
                interestIncome = yearlyStatement.interestIncome / 4
                interestExpense = yearlyStatement.interestExpense / 4
                estimatedStatement = IncomeStatement(
                    totalRevenue=totalRevenue,
                    netIncome=netIncome,
                    incomeBeforeTax=incomeBeforeTax,
                    interestIncome=interestIncome,
                    interestExpense=interestExpense,
                )
                incomeStatements[date] = estimatedStatement
            else:
                incomeStatements[date] = IncomeStatement()

    # now that we've populated our statements as far as possible
    # we need to try extrapolate empty dates using before and after quarterlyStatements
    for i, date in enumerate(quarterlyDates):
        quarterlyStatement = (
            date in incomeStatements and incomeStatements[date] or IncomeStatement()
        )

        if quarterlyStatement == IncomeStatement():

            # find the previous statement and date
            previousStatement = getPreviousStatement(
                i, quarterlyDates, incomeStatements, IncomeStatement()
            )

            # find the next statement and date
            nextStatement = getNextStatement(
                i, quarterlyDates, incomeStatements, IncomeStatement()
            )

            # calculate the relative value using the difference in values and the index of this statement
            if previousStatement and nextStatement:
                totalRevenue = getExtrapolatedEstimate(
                    "totalRevenue", nextStatement, previousStatement
                )
                netIncome = getExtrapolatedEstimate(
                    "netIncome", nextStatement, previousStatement
                )
                incomeBeforeTax = getExtrapolatedEstimate(
                    "incomeBeforeTax", nextStatement, previousStatement
                )
                interestExpense = getExtrapolatedEstimate(
                    "interestExpense", nextStatement, previousStatement
                )
                interestIncome = getExtrapolatedEstimate(
                    "interestIncome", nextStatement, previousStatement
                )
                incomeStatement = IncomeStatement(
                    totalRevenue=totalRevenue,
                    netIncome=netIncome,
                    incomeBeforeTax=incomeBeforeTax,
                    interestExpense=interestExpense,
                    interestIncome=interestIncome,
                    estimate=True,
                )
                incomeStatements[date] = incomeStatement

            elif previousStatement and not nextStatement:
                # project by trending the previous values
                totalRevenue = getTrendEstimate(
                    incomeStatements, "totalRevenue", i, previousStatement
                )
                netIncome = getTrendEstimate(
                    incomeStatements, "netIncome", i, previousStatement
                )
                incomeBeforeTax = getTrendEstimate(
                    incomeStatements, "incomeBeforeTax", i, previousStatement
                )
                interestExpense = getTrendEstimate(
                    incomeStatements, "interestExpense", i, previousStatement
                )
                interestIncome = getTrendEstimate(
                    incomeStatements, "interestIncome", i, previousStatement
                )
                incomeStatement = IncomeStatement(
                    totalRevenue=totalRevenue,
                    netIncome=netIncome,
                    incomeBeforeTax=incomeBeforeTax,
                    interestExpense=interestExpense,
                    interestIncome=interestIncome,
                    estimate=True,
                )
                incomeStatements[date] = incomeStatement

    balanceSheets = {}
    for date in mergedQuarterlyBalanceSheets:
        quarterlyStatement = mergedQuarterlyBalanceSheets[date]

        # if we have a quarterly statement add it
        if not isBalanceSheetEmptyOrInvalid(quarterlyStatement):
            balanceSheets[date] = quarterlyStatement

        # if the quarterlyStatement is empty, we need to try and get the values from the yearlyStatement on this date
        if quarterlyStatement == BalanceSheet():
            yearlyStatement = mergedYearlyBalanceSheets[date]

            if yearlyStatement and not isBalanceSheetEmptyOrInvalid(yearlyStatement):
                # NOTE we don't divide by 4 here
                assets = yearlyStatement.assets
                currentAssets = yearlyStatement.currentAssets
                liabilities = yearlyStatement.liabilities
                currentLiabilities = yearlyStatement.currentLiabilities
                retainedEarnings = yearlyStatement.retainedEarnings
                cash = yearlyStatement.cash
                estimatedStatement = BalanceSheet(
                    assets=assets,
                    currentAssets=currentAssets,
                    liabilities=liabilities,
                    currentLiabilities=currentLiabilities,
                    retainedEarnings=retainedEarnings,
                    cash=cash,
                )
                balanceSheets[date] = estimatedStatement
            else:
                balanceSheets[date] = BalanceSheet()

    # now that we've populated our statements as far as possible
    # we need to try extrapolate empty dates using before and after quarterlyStatements
    for i, date in enumerate(quarterlyDates):
        quarterlyStatement = (
            date in balanceSheets and balanceSheets[date] or BalanceSheet()
        )

        if quarterlyStatement == BalanceSheet():

            # find the previous statement and date
            previousStatement = getPreviousStatement(
                i, quarterlyDates, balanceSheets, BalanceSheet()
            )

            # find the next statement and date
            nextStatement = getNextStatement(
                i, quarterlyDates, balanceSheets, BalanceSheet()
            )

            # calculate the relative value using the difference in values and the index of this statement
            if previousStatement and nextStatement:
                assets = getExtrapolatedEstimate(
                    "assets", nextStatement, previousStatement
                )
                currentAssets = getExtrapolatedEstimate(
                    "currentAssets", nextStatement, previousStatement
                )
                liabilities = getExtrapolatedEstimate(
                    "liabilities", nextStatement, previousStatement
                )
                retainedEarnings = getExtrapolatedEstimate(
                    "retainedEarnings", nextStatement, previousStatement
                )
                currentLiabilities = getExtrapolatedEstimate(
                    "currentLiabilities", nextStatement, previousStatement
                )
                cash = getExtrapolatedEstimate("cash", nextStatement, previousStatement)
                balanceSheet = BalanceSheet(
                    assets=assets,
                    currentAssets=currentAssets,
                    liabilities=liabilities,
                    currentLiabilities=currentLiabilities,
                    retainedEarnings=retainedEarnings,
                    cash=cash,
                    estimate=True,
                )
                balanceSheets[date] = balanceSheet

            elif previousStatement and not nextStatement:
                # project by trending the previous values
                assets = getTrendEstimate(balanceSheets, "assets", i, previousStatement)
                currentAssets = getTrendEstimate(
                    balanceSheets, "currentAssets", i, previousStatement
                )
                liabilities = getTrendEstimate(
                    balanceSheets, "liabilities", i, previousStatement
                )
                retainedEarnings = getTrendEstimate(
                    balanceSheets, "retainedEarnings", i, previousStatement
                )
                currentLiabilities = getTrendEstimate(
                    balanceSheets, "currentLiabilities", i, previousStatement
                )
                cash = getTrendEstimate(balanceSheets, "cash", i, previousStatement)
                balanceSheet = BalanceSheet(
                    assets=assets,
                    currentAssets=currentAssets,
                    liabilities=liabilities,
                    currentLiabilities=currentLiabilities,
                    retainedEarnings=retainedEarnings,
                    cash=cash,
                    estimate=True,
                )
                balanceSheets[date] = balanceSheet

    cashFlowStatements = {}
    for date in mergedQuarterlyCashFlowStatements:
        quarterlyStatement = mergedQuarterlyCashFlowStatements[date]

        # if we have a quarterly statement add it
        if not isCashFlowStatementEmptyOrInvalid(quarterlyStatement):
            cashFlowStatements[date] = quarterlyStatement

        # if the quarterlyStatement is empty, we need to try and get the values from the yearlyStatement on this date
        if quarterlyStatement == CashFlowStatement():
            yearlyStatement = mergedYearlyCashFlowStatements[date]

            if yearlyStatement and not isCashFlowStatementEmptyOrInvalid(
                yearlyStatement
            ):
                dividendsPaid = yearlyStatement.dividendsPaid / 4
                cashFromOperations = yearlyStatement.cashFromOperations / 4
                capex = yearlyStatement.capex / 4
                estimatedStatement = CashFlowStatement(
                    dividendsPaid=dividendsPaid,
                    cashFromOperations=cashFromOperations,
                    capex=capex,
                )
                cashFlowStatements[date] = estimatedStatement
            else:
                cashFlowStatements[date] = CashFlowStatement()

    # now that we've populated our statements as far as possible
    # we need to try extrapolate empty dates using before and after quarterlyStatements
    for i, date in enumerate(quarterlyDates):
        quarterlyStatement = (
            date in cashFlowStatements
            and cashFlowStatements[date]
            or CashFlowStatement()
        )

        if quarterlyStatement == CashFlowStatement():

            # find the previous statement and date
            previousStatement = getPreviousStatement(
                i, quarterlyDates, cashFlowStatements, CashFlowStatement()
            )

            # find the next statement and date
            nextStatement = getNextStatement(
                i, quarterlyDates, cashFlowStatements, CashFlowStatement()
            )

            # calculate the relative value using the difference in values and the index of this statement
            if previousStatement and nextStatement:
                dividendsPaid = getExtrapolatedEstimate(
                    "dividendsPaid", nextStatement, previousStatement
                )
                cashFromOperations = getExtrapolatedEstimate(
                    "cashFromOperations", nextStatement, previousStatement
                )
                capex = getExtrapolatedEstimate(
                    "capex", nextStatement, previousStatement
                )
                cashFlowStatement = CashFlowStatement(
                    dividendsPaid=dividendsPaid,
                    cashFromOperations=cashFromOperations,
                    capex=capex,
                    estimate=True,
                )
                cashFlowStatements[date] = cashFlowStatement

            elif previousStatement and not nextStatement:
                # project by trending the previous values
                dividendsPaid = getTrendEstimate(
                    cashFlowStatements, "dividendsPaid", i, previousStatement
                )
                cashFromOperations = getTrendEstimate(
                    cashFlowStatements, "cashFromOperations", i, previousStatement
                )
                capex = getTrendEstimate(
                    cashFlowStatements, "capex", i, previousStatement
                )
                cashFlowStatement = CashFlowStatement(
                    dividendsPaid=dividendsPaid,
                    cashFromOperations=cashFromOperations,
                    capex=capex,
                    estimate=True,
                )
                cashFlowStatements[date] = cashFlowStatement

    financialStatements = FinancialStatements(
        incomeStatements=incomeStatements,
        balanceSheets=balanceSheets,
        cashFlowStatements=cashFlowStatements,
    )

    return financialStatements
