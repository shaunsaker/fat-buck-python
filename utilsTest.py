import datetime
import utils
from models import IncomeStatement, BalanceSheet, CashFlowStatement


# enable as needed
# def testFetchJson():
#     json = utils.fetchJson(
#         "https://finnhub.io/api/v1/stock/symbol?exchange=JO&token=brprbgvrh5rbpquqc50g"
#     )
#     assert json


def testStringToCurrency():
    # if we pass in nothing, it returns 0.00
    assert utils.stringToCurrency(None) == 0.00
    assert utils.stringToCurrency("None") == 0.00
    assert utils.stringToCurrency(float("nan")) == 0.00

    # if we pass in a normal string, it works
    assert utils.stringToCurrency("999.99") == 999.99

    # if we pass in any other string, it returns 0.00
    assert utils.stringToCurrency("one hundred million") == 0.00


def testDateToDateString():
    date = datetime.datetime.now()
    assert isinstance(utils.dateToDateString(date), str)


def testGenerateUuid():
    uuid = utils.generateUuid()
    assert uuid
    assert isinstance(uuid, str)


def testMergeIncomeStatement():
    # it does not overwrite truthy values with falsy values
    totalRevenue = 10000.00
    assert (
        utils.mergeIncomeStatement(
            IncomeStatement(totalRevenue=totalRevenue), IncomeStatement()
        ).totalRevenue
        == totalRevenue
    )

    # it overwrites falsy values with truthy values
    assert (
        utils.mergeIncomeStatement(
            IncomeStatement(), IncomeStatement(totalRevenue=totalRevenue)
        ).totalRevenue
        == totalRevenue
    )


def testMergeBalanceSheet():
    # it does not overwrite truthy values with falsy values
    assets = 10000.00
    assert (
        utils.mergeBalanceSheet(BalanceSheet(assets=assets), BalanceSheet()).assets
        == assets
    )

    # it overwrites falsy values with truthy values
    assert (
        utils.mergeBalanceSheet(BalanceSheet(), BalanceSheet(assets=assets)).assets
        == assets
    )


def testMergeCashFlowStatement():
    # it does not overwrite truthy values with falsy values
    dividendsPaid = 10000.00
    assert (
        utils.mergeCashFlowStatement(
            CashFlowStatement(dividendsPaid=dividendsPaid), CashFlowStatement()
        ).dividendsPaid
        == dividendsPaid
    )

    # it overwrites falsy values with truthy values
    assert (
        utils.mergeCashFlowStatement(
            CashFlowStatement(), CashFlowStatement(dividendsPaid=dividendsPaid)
        ).dividendsPaid
        == dividendsPaid
    )


def testDateStringToDate():
    dateString = "2020-08-26"
    assert utils.dateStringToDate(dateString)


def testIsEndOfMonth():
    # returns False for date not at end of month
    assert not utils.isEndOfMonth(datetime.datetime(2020, 3, 1))

    # returns True for date at end of month
    assert utils.isEndOfMonth(datetime.datetime(2020, 3, 31))
