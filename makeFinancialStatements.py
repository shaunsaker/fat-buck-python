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
from datetime import datetime


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

    if not previousDate or previousDate not in statements:
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
    if startIndex >= len(dates) - 1:
        return None

    newStartIndex = startIndex + 1
    nextDate = dates[newStartIndex]

    if not nextDate or nextDate not in statements:
        return None

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


def mergeIncomeStatements(a: IncomeStatement, b: IncomeStatement) -> IncomeStatement:
    return IncomeStatement(
        totalRevenue=a.totalRevenue or b.totalRevenue,
        netIncome=a.netIncome or b.netIncome,
        incomeBeforeTax=a.incomeBeforeTax or b.incomeBeforeTax,
        interestIncome=a.interestIncome or b.interestIncome,
        interestExpense=a.interestExpense or b.interestExpense,
        estimate=a.estimate or b.estimate,
        source=a.source or b.source,
    )


def mergeBalanceSheets(a: BalanceSheet, b: BalanceSheet) -> BalanceSheet:
    return BalanceSheet(
        assets=a.assets or b.assets,
        currentAssets=a.currentAssets or b.currentAssets,
        liabilities=a.liabilities or b.liabilities,
        currentLiabilities=a.currentLiabilities or b.currentLiabilities,
        retainedEarnings=a.retainedEarnings or b.retainedEarnings,
        cash=a.cash or b.cash,
        estimate=a.estimate or b.estimate,
        source=a.source or b.source,
    )


def mergeCashFlowStatements(
    a: CashFlowStatement, b: CashFlowStatement
) -> CashFlowStatement:
    return CashFlowStatement(
        dividendsPaid=a.dividendsPaid or b.dividendsPaid,
        cashFromOperations=a.cashFromOperations or b.cashFromOperations,
        capex=a.capex or b.capex,
        estimate=a.estimate or b.estimate,
        source=a.source or b.source,
    )


def getMergedStatements(
    dates, latestStatements, existingStatements, statementType, factory, merger,
):
    # TODO: this is not preserving our estimate, source and dateAdded fields
    # TODO: it should also prefer actual over estimates
    mergedStatements = {}

    for date in dates:
        latestStatement = (
            date in latestStatements and latestStatements[date] or factory
        )  # could be quarterly or yearly

        if statementType == "yearly":
            # reduce the values to 1/4 to represent their quarterly values
            for key in latestStatement:
                if isinstance(latestStatement[key], float):
                    latestStatement[key] = latestStatement[key] / 4

        existingStatement = (
            date in existingStatements[statementType]
            and not existingStatements[statementType][date].estimate
            and existingStatements[statementType][date]
        ) or factory  # is always quarterly, don't use estimates (we want to extrapolate new values instead)
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
    existingStatements: FinancialStatements, latestStatements: AllFinancialStatements,
) -> FinancialStatements:
    # Get a list of dates from the quarterly statements
    quarterlyDates = getQuarterlyDates(existingStatements, latestStatements)

    # if empty return None
    if not quarterlyDates:
        return None

    # Merge statements for date
    mergedQuarterlyIncomeStatements = getMergedStatements(
        quarterlyDates,
        latestStatements.incomeStatements.quarterly,
        existingStatements,
        "incomeStatements",
        IncomeStatement(),
        mergeIncomeStatements,
    )
    mergedYearlyIncomeStatements = getMergedStatements(
        quarterlyDates,
        latestStatements.incomeStatements.yearly,
        existingStatements,
        "incomeStatements",
        IncomeStatement(),
        mergeIncomeStatements,
    )
    mergedQuarterlyBalanceSheets = getMergedStatements(
        quarterlyDates,
        latestStatements.balanceSheets.quarterly,
        existingStatements,
        "balanceSheets",
        BalanceSheet(),
        mergeBalanceSheets,
    )
    mergedYearlyBalanceSheets = getMergedStatements(
        quarterlyDates,
        latestStatements.balanceSheets.yearly,
        existingStatements,
        "balanceSheets",
        BalanceSheet(),
        mergeBalanceSheets,
    )
    mergedQuarterlyCashFlowStatements = getMergedStatements(
        quarterlyDates,
        latestStatements.cashFlowStatements.quarterly,
        existingStatements,
        "cashFlowStatements",
        CashFlowStatement(),
        mergeCashFlowStatements,
    )
    mergedYearlyCashFlowStatements = getMergedStatements(
        quarterlyDates,
        latestStatements.cashFlowStatements.yearly,
        existingStatements,
        "cashFlowStatements",
        CashFlowStatement(),
        mergeCashFlowStatements,
    )

    incomeStatements = {}
    for date in mergedQuarterlyIncomeStatements:
        quarterlyStatement = mergedQuarterlyIncomeStatements[date]

        # if we have a quarterly statement add it
        if not isIncomeStatementEmptyOrInvalid(quarterlyStatement):
            quarterlyStatement.source = "actual"
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
                    source="yearly",
                    estimate=False,
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
                    source="extrapolated",
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
                    source="trend",
                    estimate=True,
                )
                incomeStatements[date] = incomeStatement

    balanceSheets = {}
    for date in mergedQuarterlyBalanceSheets:
        quarterlyStatement = mergedQuarterlyBalanceSheets[date]

        # if we have a quarterly statement add it
        if not isBalanceSheetEmptyOrInvalid(quarterlyStatement):
            quarterlyStatement.source = "actual"
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
                    source="yearly",
                    estimate=False,
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
                    source="extrapolated",
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
                    source="trend",
                    estimate=True,
                )
                balanceSheets[date] = balanceSheet

    cashFlowStatements = {}
    for date in mergedQuarterlyCashFlowStatements:
        quarterlyStatement = mergedQuarterlyCashFlowStatements[date]

        # if we have a quarterly statement add it
        if not isCashFlowStatementEmptyOrInvalid(quarterlyStatement):
            quarterlyStatement.source = "actual"
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
                    source="yearly",
                    estimate=False,
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
                    source="extrapolated",
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
                    source="trend",
                    estimate=True,
                )
                cashFlowStatements[date] = cashFlowStatement

    financialStatements = FinancialStatements(
        incomeStatements=incomeStatements,
        balanceSheets=balanceSheets,
        cashFlowStatements=cashFlowStatements,
    )

    return financialStatements
