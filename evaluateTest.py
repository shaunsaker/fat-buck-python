import evaluate
from models import (
    Stock,
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    Valuation,
    ValuationModel,
)

# contants
marginOfSafety = 0.25
discountRate = 0.07
declineRate = 0.05

# variables
currentPrice = 78.15
sharesOutstanding = 109944000
dividendsPaid = 594000000.00
assets = 23133000000.00
prevAssets = 22275000000.00
currentAssets = 11249000000.00
liabilities = 12049000000.00
currentLiabilities = 5285000000.00
totalRevenue = 24799000000.00
netIncome = 1294000000.00
cashFromOperations = 1274000000.00
capex = 819000000.00
cash = 1978000000.00
retainedEarnings = 9315000000.00
# incomeBeforeTax + interestExpense - interestIncome
earningsBeforeInterestAndTax = 2295000000.00
historicalNetIncomes = [
    949000000.00,
    1099000000.00,
    1010000000.00,
    780000000.00,
    953000000.00,
    993000000.00,
    netIncome,
]
historicalAssets = [
    14393000000.00,
    14787000000.00,
    17794000000.00,
    15820000000.00,
    15971000000.00,
    22275000000.00,
    assets,
]
historicalLiabilities = [
    7516000000.00,
    6984000000.00,
    8752000000.00,
    6774000000.00,
    6615000000.00,
    12070000000.00,
    liabilities,
]


peList = []
for netIncomeForYr in historicalNetIncomes:
    # TODO we should do this for each year's sharesOutstanding but we don't have that info
    historicalEps = historicalEps = evaluate.getEps(netIncomeForYr, sharesOutstanding)
    historicalPe = evaluate.getPe(currentPrice, historicalEps)
    peList.append(historicalPe)
avgPe = sum(peList) / len(peList)

roeList = []
for i, netIncomeForYr in enumerate(historicalNetIncomes):
    assetsForYr = historicalAssets[i]
    liabilitiesForYr = historicalLiabilities[i]
    equityForYr = evaluate.getEquity(assetsForYr, liabilitiesForYr)
    roeForYr = evaluate.getRoe(netIncomeForYr, equityForYr)
    roeList.append(roeForYr)
avgRoe = sum(roeList) / len(roeList)

dividendYield = evaluate.getDividendYield(
    dividendsPaid, sharesOutstanding, currentPrice
)
fcf = evaluate.getFcf(cashFromOperations, capex)
marketCap = evaluate.getMarketCap(sharesOutstanding, currentPrice)
equity = evaluate.getEquity(assets, liabilities)
eps = evaluate.getEps(netIncome, sharesOutstanding)
previousEps = evaluate.getEps(993000000, sharesOutstanding)
pe = evaluate.getPe(currentPrice, eps)
growthRate = evaluate.getGrowthRate(historicalNetIncomes, discountRate)


def testDividendYield():
    # real world example
    assert (
        evaluate.getDividendYield(dividendsPaid, sharesOutstanding, currentPrice)
        == 0.06913308370005292
    )


def testMarketCap():
    # real world example
    assert evaluate.getMarketCap(sharesOutstanding, currentPrice) == 8592123600.00


def testEquity():
    # real world example
    assert evaluate.getEquity(assets, liabilities) == 11084000000.00


def testRoe():
    # real world example
    assert evaluate.getRoe(netIncome, equity) == 0.11674485745218333


def testDte():
    # real world example
    assert evaluate.getDte(currentLiabilities, equity) == 0.47681342475640565


def testCr():
    # real world example
    assert evaluate.getCr(currentAssets, currentLiabilities) == 2.128476821192053


def testFcf():
    # real world example
    assert evaluate.getFcf(cashFromOperations, capex) == 455000000.00


def testEps():
    # real world example
    assert evaluate.getEps(netIncome, sharesOutstanding) == 11.769628174343302


def testPe():
    # real world example
    assert evaluate.getPe(currentPrice, eps) == 6.639971870170016


def testPeg():
    # real world example
    assert evaluate.getPeg(pe, eps, previousEps) == 0.02012720576959894


def testPb():
    # real world example
    assert evaluate.getPb(currentPrice, equity, sharesOutstanding) == 0.7751825694695057


def testGrowthRate():
    # real world example
    assert (
        evaluate.getGrowthRate(historicalNetIncomes, discountRate)
        == 0.06937417927186325
    )


def testNpv():
    futureValue = currentPrice

    # real world example works with no year lookahead
    assert (evaluate.getNpv(futureValue, discountRate, 0)) == futureValue

    # real world example works with years set
    assert (evaluate.getNpv(futureValue, discountRate, 5)) == 55.71986992664868


def testPeMultipleIv():
    # comparable example
    assert (evaluate.getPeMultipleIv(11.89, 15.4, 0.12, 0.0, 0.1)) == 200.3684151256554

    # real world example
    assert (
        evaluate.getPeMultipleIv(eps, avgPe, growthRate, marginOfSafety, discountRate)
    ) == 93.77753864756693


def testGrahamIv():
    # comparable example
    assert (evaluate.getGrahamIv(34.47, 0.158, 0, 0.0356)) == 971.3568539325844

    # real world example
    assert (
        evaluate.getGrahamIv(eps, growthRate, marginOfSafety, discountRate)
    ) == 90.27889787095644


def testDcfIv():
    # comparable example
    assert (
        evaluate.getDcfIv(
            66636000000.00,
            40174000000.00,
            241975000000.00,
            4334000000.00,
            0.1147,
            0.25,
            0.05,
            0.09,
        )
    ) == 247.53201610941994

    # real world example
    assert (
        evaluate.getDcfIv(
            fcf,
            cash,
            liabilities,
            sharesOutstanding,
            growthRate,
            marginOfSafety,
            declineRate,
            discountRate,
        )
    ) == -17.157924989918474


def testRoeIv():
    # comparible example
    assert (
        evaluate.getRoeIv(90488000.00, 0.4506, 4520000.00, 3.00, 0.0986, 0.25, 0.09)
    ) == 116.57792047556342

    # real world example
    assert (
        evaluate.getRoeIv(
            equity,
            avgRoe,
            sharesOutstanding,
            dividendYield,
            growthRate,
            marginOfSafety,
            discountRate,
        )
    ) == 138.35472348831217


def testLiquidationIv():
    assert (evaluate.getLiquidationIv(equity, sharesOutstanding)) == 100.81496034344757


def testAltmanZScore():
    assert (
        evaluate.getAltmanZScore(
            assets,
            liabilities,
            retainedEarnings,
            earningsBeforeInterestAndTax,
            totalRevenue,
        )
    ) == 3.0900649244837606


def testGetYearsOfOperation():
    # test an empty stock
    stockA = Stock()
    assert evaluate.getYearsOfOperation(stockA) == 0

    # test a stock with unequal statements
    incomeStatementsB = {}
    incomeStatementsB["1"] = IncomeStatement()
    financialStatementsB = FinancialStatements(incomeStatements=incomeStatementsB)
    stockB = Stock(financialStatements=financialStatementsB)
    assert (
        evaluate.getYearsOfOperation(stockB) == 0
    )  # no balance sheets and cf statements

    # test a stock with equal statements
    incomeStatementsC = {}
    incomeStatementsC["1"] = IncomeStatement()
    balanceSheetsC = {}
    balanceSheetsC["1"] = BalanceSheet()
    cashFlowStatementsC = {}
    cashFlowStatementsC["1"] = CashFlowStatement()
    financialStatementsC = FinancialStatements(
        incomeStatements=incomeStatementsC,
        balanceSheets=balanceSheetsC,
        cashFlowStatements=cashFlowStatementsC,
    )
    stockC = Stock(financialStatements=financialStatementsC)
    assert evaluate.getYearsOfOperation(stockC) == 1


def testGetViability():
    valuation = Valuation()
    model = ValuationModel()

    # it should return False with an empty valuation
    assert not evaluate.getViability(valuation, model)

    # it should return True with all required values
    valuation.roe = model.minRoe
    valuation.dte = model.maxDte
    valuation.cr = model.minCr
    valuation.eps = model.minEps
    valuation.pe = model.maxPe
    valuation.peg = model.maxPeg
    valuation.pb = model.maxPb
    valuation.altmanZScore = model.minAltmanZScore
    assert evaluate.getViability(valuation, model)

    # it should return False when roe does not meet requirements
    valuation.roe = 0
    assert not evaluate.getViability(valuation, model)

    # it should return False when dte does not meet requirements
    valuation.roe = model.minRoe / 2
    valuation.dte = model.maxDte * 2
    assert not evaluate.getViability(valuation, model)

    # it should return False when cr does not meet requirements
    valuation.dte = model.maxDte
    valuation.cr = model.minCr / 2
    assert not evaluate.getViability(valuation, model)

    # it should return False when eps does not meet requirements
    valuation.cr = model.minCr
    valuation.eps = model.minEps / 2
    assert not evaluate.getViability(valuation, model)

    # it should return False when pe does not meet requirements
    valuation.cr = model.minCr
    valuation.pe = model.maxPe * 2
    assert not evaluate.getViability(valuation, model)

    # it should return False when peg does not meet requirements
    valuation.pe = model.maxPe
    valuation.peg = model.maxPeg * 2
    assert not evaluate.getViability(valuation, model)

    # # it should return False when pb does not meet requirements
    valuation.peg = model.maxPeg
    valuation.pb = model.maxPb * 2
    assert not evaluate.getViability(valuation, model)

    # # it should return False when altmanZScore does not meet requirements
    valuation.pb = model.maxPb
    valuation.altmanZScore = model.minAltmanZScore / 2
    assert not evaluate.getViability(valuation, model)

