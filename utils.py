import os, errno
import uuid
from typing import TypeVar
import urllib.request
import json
from datetime import timedelta, datetime

from models import Currency, IncomeStatement, BalanceSheet, CashFlowStatement

T = TypeVar("T")


def fetchJson(url: str) -> T:
    """
    fetch json from a url
    """
    try:
        response = urllib.request.urlopen(url)
    except:
        return

    data = json.loads(response.read())

    return data


def pandasDateToDateString(date, noTime: bool = False) -> str:
    """
    convert a pandasDate to an ISO date string
    """
    if noTime:
        return date.to_pydatetime().date().__str__()

    return date.to_pydatetime().isoformat()


def stringToCurrency(string: str) -> Currency:
    try:
        return round(float(string), 2)
    except:
        return 0.00


def dateToDateString(date) -> str:
    return date.date().__str__()


def generateUuid() -> str:
    return uuid.uuid4().hex


def mkdirP(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def safeOpenWrite(path):
    mkdirP(os.path.dirname(path))
    return open(path, "w")


def mergeIncomeStatements(a: IncomeStatement, b: IncomeStatement) -> IncomeStatement:
    return IncomeStatement(
        totalRevenue=a.totalRevenue or b.totalRevenue,
        netIncome=a.netIncome or b.netIncome,
        incomeBeforeTax=a.incomeBeforeTax or b.incomeBeforeTax,
        interestIncome=a.interestIncome or b.interestIncome,
        interestExpense=a.interestExpense or b.interestExpense,
    )


def mergeBalanceSheets(a: BalanceSheet, b: BalanceSheet) -> BalanceSheet:
    return BalanceSheet(
        assets=a.assets or b.assets,
        currentAssets=a.currentAssets or b.currentAssets,
        liabilities=a.liabilities or b.liabilities,
        currentLiabilities=a.currentLiabilities or b.currentLiabilities,
        retainedEarnings=a.retainedEarnings or b.retainedEarnings,
        cash=a.cash or b.cash,
    )


def mergeCashFlowStatements(
    a: CashFlowStatement, b: CashFlowStatement
) -> CashFlowStatement:
    return CashFlowStatement(
        dividendsPaid=a.dividendsPaid or b.dividendsPaid,
        cashFromOperations=a.cashFromOperations or b.cashFromOperations,
        capex=a.capex or b.capex,
    )


def fileExists(path: str) -> bool:
    return os.path.isfile(path)


def getCurrencyIfExists(key: str, thing):
    try:
        return stringToCurrency(thing[key])
    except:
        return 0.00


def safeDivide(a, b):
    try:
        return a / b
    except:
        return 0.00


def dateRange(startDate, endDate):
    for n in range(int((endDate - startDate).days)):
        yield startDate + timedelta(n)


def dateStringToDate(dateString):
    return datetime.strptime(dateString, "%Y-%m-%d")


def isEndOfMonth(date):
    currentMonth = date.month
    monthOfNextDay = (date + timedelta(days=1)).month
    return monthOfNextDay != currentMonth


def getEndOfMonth(date):
    if isEndOfMonth(date):
        return date

    # otherwise increment by a day until it is the end of the month
    return getEndOfMonth(date + timedelta(days=1))


def getSmallest(a, b):
    if not a:
        a = b
    elif b < a:
        a = b

    return a


def getLargest(a, b):
    if not a:
        a = b
    elif b > a:
        a = b

    return a


def recursiveReplacer(thing, target, replace):
    for key in thing:
        if thing[key] == target:
            thing[key] = replace
        elif isinstance(thing[key], dict):
            recursiveReplacer(thing[key], target, replace)


def getNumberOfSymbolsToProcess(_exchanges):
    total = 0

    for _exchange in _exchanges:
        _exchangeData = _exchange.to_dict()
        _exchangeSymbols = _exchangeData["symbols"]
        total += len(_exchangeSymbols)

    return total
