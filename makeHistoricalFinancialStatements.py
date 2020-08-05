from typing import Dict
from models import (
    HistoricalFundamentals,
    AllFinancialStatements,
    AllIncomeStatements,
    AllBalanceSheets,
    AllCashFlowStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
)
from utils import stringToCurrency


def getHistoricalIncomeStatementsByCycleType(
    data, cycleType
) -> Dict[str, IncomeStatement]:
    incomeStatements = {}

    for date in data.Financials.Income_Statement[cycleType]:
        historicalIncomeStatement = data.Financials.Income_Statement[cycleType][date]
        incomeStatement = IncomeStatement()
        incomeStatement.totalRevenue = stringToCurrency(
            historicalIncomeStatement.totalRevenue
        )

        # we don't want discontinued operations profits to affect our valuation
        # let's aviod it and use net income from continuous ops instead
        if (
            historicalIncomeStatement.discontinuedOperations
            > historicalIncomeStatement.netIncome
        ):
            netIncome = historicalIncomeStatement.netIncomeFromContinuingOps
        else:
            netIncome = historicalIncomeStatement.netIncome

        incomeStatement.netIncome = stringToCurrency(netIncome)
        incomeStatement.incomeBeforeTax = stringToCurrency(
            historicalIncomeStatement.incomeBeforeTax
        )
        incomeStatement.interestIncome = stringToCurrency(
            historicalIncomeStatement.interestIncome
        )
        incomeStatement.interestExpense = stringToCurrency(
            historicalIncomeStatement.interestExpense
        )

        incomeStatements[date] = incomeStatement

    return incomeStatements


def getHistoricalBalanceSheetsByCycleType(data, cycleType) -> Dict[str, BalanceSheet]:
    balanceSheets = {}

    for date in data.Financials.Balance_Sheet[cycleType]:
        historicalBalanceSheet = data.Financials.Balance_Sheet[cycleType][date]
        balanceSheet = BalanceSheet()
        balanceSheet.assets = stringToCurrency(historicalBalanceSheet.totalAssets)
        balanceSheet.currentAssets = stringToCurrency(
            historicalBalanceSheet.totalCurrentAssets
        )
        balanceSheet.liabilities = stringToCurrency(historicalBalanceSheet.totalLiab)
        balanceSheet.currentLiabilities = stringToCurrency(
            historicalBalanceSheet.totalCurrentLiabilities
        )
        balanceSheet.cash = stringToCurrency(historicalBalanceSheet.cash)
        balanceSheet.retainedEarnings = stringToCurrency(
            historicalBalanceSheet.retainedEarnings
        )

        balanceSheets[date] = balanceSheet

    return balanceSheets


def getHistoricalCashFlowStatementsByCycleType(
    data, cycleType
) -> Dict[str, CashFlowStatement]:
    cashFlowStatements = {}

    for date in data.Financials.Cash_Flow[cycleType]:
        historicalCashFlowStatement = data.Financials.Cash_Flow[cycleType][date]
        cashFlowStatement = CashFlowStatement()
        cashFlowStatement.dividendsPaid = abs(
            stringToCurrency(historicalCashFlowStatement.dividendsPaid)
        )
        cashFlowStatement.cashFromOperations = stringToCurrency(
            historicalCashFlowStatement.totalCashFromOperatingActivities
        )
        cashFlowStatement.capex = stringToCurrency(
            historicalCashFlowStatement.capitalExpenditures
        )

        cashFlowStatements[date] = cashFlowStatement

    return cashFlowStatements


def makeHistoricalFinancialStatements(
    data: HistoricalFundamentals,
) -> AllFinancialStatements:
    quarterlyIncomeStatements = getHistoricalIncomeStatementsByCycleType(
        data, "quarterly"
    )
    yearlyIncomeStatements = getHistoricalIncomeStatementsByCycleType(data, "yearly")
    allIncomeStatements = AllIncomeStatements(
        quarterly=quarterlyIncomeStatements, yearly=yearlyIncomeStatements
    )

    quarterlyBalanceSheets = getHistoricalBalanceSheetsByCycleType(data, "quarterly")
    yearlyBalanceSheets = getHistoricalBalanceSheetsByCycleType(data, "yearly")
    allBalanceSheets = AllBalanceSheets(
        quarterly=quarterlyBalanceSheets, yearly=yearlyBalanceSheets
    )

    quarterlyCashFlowStatements = getHistoricalCashFlowStatementsByCycleType(
        data, "quarterly"
    )
    yearlyCashFlowStatements = getHistoricalCashFlowStatementsByCycleType(
        data, "yearly"
    )
    allCashFlowStatements = AllCashFlowStatements(
        quarterly=quarterlyCashFlowStatements, yearly=yearlyCashFlowStatements
    )

    financialStatements = AllFinancialStatements(
        incomeStatements=allIncomeStatements,
        balanceSheets=allBalanceSheets,
        cashFlowStatements=allCashFlowStatements,
    )

    return financialStatements
