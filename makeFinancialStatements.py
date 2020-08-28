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
import numpy as np
import matplotlib.dates as mdates


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


def getTrendEstimateForDate(
    statements, key, factory, date, shouldUseZeroValues=False,
):
    # filter out empty statements and 0 values if not shouldUseZeroValues
    nonEmptyStatements = {}
    for date in statements:
        statement = statements[date]
        value = statement[key]
        if (
            statement != factory
            and shouldUseZeroValues
            or not shouldUseZeroValues
            and value
        ):
            nonEmptyStatements[date] = statement

    historicalValues = getHistoricalValuesFromFinancialStatements(
        nonEmptyStatements, key
    )

    if len(historicalValues) == 0:
        return 0

    y = np.array([item["value"] for item in historicalValues])

    # extract and convert date strings to numbers
    dates = [item["date"] for item in historicalValues]
    x = np.array(mdates.datestr2num(dates))

    # machine learning!
    order = (
        2 if len(historicalValues) > 2 else 1
    )  # polynomial regression doesn't work accurately with 2 values
    model = np.polyfit(x, y, order)  # NOTE: 1 == linear, 2+ == polynomial
    predict = np.poly1d(model)
    predictionDate = mdates.datestr2num([date])[0]
    prediction = predict(predictionDate)

    return round(prediction, 2)


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

    return False


def isBalanceSheetEmptyOrInvalid(balanceSheet: BalanceSheet) -> bool:
    if balanceSheet == BalanceSheet():
        return True

    return False


def isCashFlowStatementEmptyOrInvalid(cashFlowStatement: CashFlowStatement) -> bool:
    if cashFlowStatement == CashFlowStatement():
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
            # TODO: should we limit it to the last few years?
            totalRevenue = getTrendEstimateForDate(
                incomeStatements, "totalRevenue", IncomeStatement(), date
            )
            netIncome = getTrendEstimateForDate(
                incomeStatements, "netIncome", IncomeStatement(), date
            )
            incomeBeforeTax = getTrendEstimateForDate(
                incomeStatements, "incomeBeforeTax", IncomeStatement(), date
            )
            interestExpense = getTrendEstimateForDate(
                incomeStatements, "interestExpense", IncomeStatement(), date
            )
            interestIncome = getTrendEstimateForDate(
                incomeStatements, "interestIncome", IncomeStatement(), date
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
            assets = getTrendEstimateForDate(
                balanceSheets, "assets", BalanceSheet(), date
            )
            currentAssets = getTrendEstimateForDate(
                balanceSheets, "currentAssets", BalanceSheet(), date
            )
            liabilities = getTrendEstimateForDate(
                balanceSheets, "liabilities", BalanceSheet(), date
            )
            retainedEarnings = getTrendEstimateForDate(
                balanceSheets, "retainedEarnings", BalanceSheet(), date
            )
            currentLiabilities = getTrendEstimateForDate(
                balanceSheets, "currentLiabilities", BalanceSheet(), date
            )
            cash = getTrendEstimateForDate(balanceSheets, "cash", BalanceSheet(), date)
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
            dividendsPaid = getTrendEstimateForDate(
                cashFlowStatements, "dividendsPaid", CashFlowStatement(), date
            )
            cashFromOperations = getTrendEstimateForDate(
                cashFlowStatements, "cashFromOperations", CashFlowStatement(), date
            )
            capex = getTrendEstimateForDate(
                cashFlowStatements, "capex", CashFlowStatement(), date
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
