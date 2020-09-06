import os, errno
import uuid
from typing import TypeVar
import urllib.request
import json
from datetime import timedelta, datetime
import numpy as np
import matplotlib.dates as mdates

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


# replace all falsy, non-string values in a nested dict 0
def falsyToInt(obj):
    cleanObj = {}

    for key in obj:
        field = obj[key]
        # print(f"processing {key} with type: {type(field)} and value: {field}")

        if isinstance(field, list):
            cleanList = []

            for item in field:
                cleanItem = falsyToInt(item)
                cleanList.append(cleanItem)

            cleanObj[key] = cleanList

        elif isinstance(field, dict):
            cleanObj[key] = falsyToInt(field)

        elif isinstance(field, str):
            cleanObj[key] = field

        elif isinstance(field, bool):
            cleanObj[key] = field

        else:
            # its an int/float, attempt to parse it
            # if we can't parse it, convert it to 0
            try:
                int(field)
                cleanObj[key] = field
            except:
                # print(f"Found unparseable int/float at {key}.")
                cleanObj[key] = 0

    return cleanObj


def getNumberOfSymbolsToProcess(_exchanges):
    total = 0

    for _exchange in _exchanges:
        _exchangeData = _exchange.to_dict()
        _exchangeSymbols = _exchangeData["symbols"]
        total += len(_exchangeSymbols)

    return total


def getHistoricalValuesFromFinancialStatements(
    statements, key: str, limitTo: int = None
):
    statementDates = []
    historicalValues = []

    for date in statements:
        statementDates.append(date)

    if limitTo:
        # reverse sort if needed so that we can get the latest X items
        if statementDates[0] < statementDates[1]:
            statementDates = sorted(statementDates, reverse=True)

        noOfValues = min(limitTo, len(statementDates))
    else:
        noOfValues = len(statementDates)

    for i in range(noOfValues):
        date = statementDates[i]
        value = statements[date][key]

        if value or value == 0.00:
            historicalValue = float(value)
            historicalValues.append({"date": date, "value": historicalValue})

    if len(historicalValues) <= 1:
        return historicalValues

    # get the correct asc sorting
    if historicalValues[0]["date"] > historicalValues[1]["date"]:
        historicalValues = sorted(historicalValues, key=lambda k: k["date"])

    return historicalValues


def getTrendEstimateForDate(statements, key, factory, targetDate, order=2):
    # filter out empty statements and 0 values if not shouldUseZeroValues
    nonEmptyStatements = {}
    for date in statements:
        statement = statements[date]
        value = statement[key]
        if statement != factory and value:
            nonEmptyStatements[date] = statement
    historicalValues = getHistoricalValuesFromFinancialStatements(
        nonEmptyStatements, key
    )

    # require at least 3 values
    if len(historicalValues) <= 2:
        return 0

    y = np.array([item["value"] for item in historicalValues])

    # extract and convert date strings to numbers
    dates = [item["date"] for item in historicalValues]
    x = np.array(mdates.datestr2num(dates))

    # machine learning!
    model = np.polyfit(x, y, order)  # NOTE: 1 == linear, 2+ == polynomial
    predict = np.poly1d(model)
    predictionDate = mdates.datestr2num([targetDate])[0]
    prediction = predict(predictionDate)

    return round(prediction, 2)
