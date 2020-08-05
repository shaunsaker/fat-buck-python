from dataclasses import dataclass, field
from typing import Dict, List, Any

Symbol = str
Date = str
Currency = float
Ratio = float
Shares = int
Score = float


@dataclass
class HistoricalPrice:
    open: Currency = 0.00
    close: Currency = 0.00


HistoricalPricing = Dict[Date, HistoricalPrice]


@dataclass
class HistoricalFundamentalsGeneralOfficer:
    Name: str
    Title: str
    YearBorn: str = ""


@dataclass
class HistoricalFundamentalsGeneral:
    Name: str
    Sector: str
    Industry: str
    Description: str
    Address: str
    Phone: str
    WebURL: str
    Officers: Dict[str, HistoricalFundamentalsGeneralOfficer]


@dataclass
class HistoricalIncomeStatement:
    totalRevenue: str
    discontinuedOperations: str
    netIncomeFromContinuingOps: str
    netIncome: str
    incomeBeforeTax: str
    interestIncome: str
    interestExpense: str


@dataclass
class HistoricalBalanceSheet:
    totalAssets: str
    totalCurrentAssets: str
    totalLiab: str
    totalCurrentLiabilities: str
    retainedEarnings: str
    cash: str


@dataclass
class HistoricalCashFlowStatement:
    dividendsPaid: str
    totalCashFromOperatingActivities: str
    capitalExpenditures: str


@dataclass
class HistoricalFundamentalsIncomeStatements:
    yearly: Dict[Date, HistoricalIncomeStatement]
    quarterly: Dict[Date, HistoricalIncomeStatement]

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class HistoricalFundamentalsBalanceSheets:
    yearly: Dict[Date, HistoricalBalanceSheet]
    quarterly: Dict[Date, HistoricalBalanceSheet]

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class HistoricalFundamentalsCashFlowStatements:
    yearly: Dict[Date, HistoricalCashFlowStatement]
    quarterly: Dict[Date, HistoricalCashFlowStatement]

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class HistoricalFundamentalsFinancials:
    Income_Statement: HistoricalFundamentalsIncomeStatements
    Balance_Sheet: HistoricalFundamentalsBalanceSheets
    Cash_Flow: HistoricalFundamentalsCashFlowStatements


@dataclass
class HistoricalFundamentals:
    General: HistoricalFundamentalsGeneral
    Financials: HistoricalFundamentalsFinancials


@dataclass
class ProfileOfficer:
    name: str = ""
    title: str = ""
    yearBorn: str = ""


@dataclass
class Profile:
    name: str = ""
    sector: str = ""
    industry: str = ""
    description: str = ""
    address: str = ""
    phone: str = ""
    webUrl: str = ""
    officers: List[ProfileOfficer] = field(default_factory=list)


@dataclass
class IncomeStatement:
    totalRevenue: Currency = 0.00
    netIncome: Currency = 0.00
    incomeBeforeTax: Currency = 0.00
    interestIncome: Currency = 0.00
    interestExpense: Currency = 0.00
    estimate: bool = False  # it may be extrapolated data

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class BalanceSheet:
    assets: Currency = 0.00
    currentAssets: Currency = 0.00
    liabilities: Currency = 0.00
    currentLiabilities: Currency = 0.00
    retainedEarnings: Currency = 0.00
    cash: Currency = 0.00
    estimate: bool = False

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class CashFlowStatement:
    dividendsPaid: Currency = 0.00
    cashFromOperations: Currency = 0.00
    capex: Currency = 0.00
    estimate: bool = False

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class AllIncomeStatements:
    quarterly: Dict[Date, IncomeStatement] = field(default_factory=dict)
    yearly: Dict[Date, IncomeStatement] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class AllBalanceSheets:
    quarterly: Dict[Date, BalanceSheet] = field(default_factory=dict)
    yearly: Dict[Date, BalanceSheet] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class AllCashFlowStatements:
    quarterly: Dict[Date, CashFlowStatement] = field(default_factory=dict)
    yearly: Dict[Date, CashFlowStatement] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class AllFinancialStatements:
    incomeStatements: AllIncomeStatements
    balanceSheets: AllBalanceSheets
    cashFlowStatements: AllCashFlowStatements

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class FinancialStatements:
    incomeStatements: Dict[Date, IncomeStatement] = field(default_factory=dict)
    balanceSheets: Dict[Date, BalanceSheet] = field(default_factory=dict)
    cashFlowStatements: Dict[Date, CashFlowStatement] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryIncomeStatement:
    TotalRevenue: str
    NetIncome: str
    PretaxIncome: str
    InterestIncome: str
    InterestExpense: str

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryBalanceSheet:
    TotalAssets: str
    CurrentAssets: str
    TotalLiabilitiesNetMinorityInterest: str
    CurrentLiabilities: str
    RetainedEarnings: str
    CashAndCashEquivalents: str

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryCashFlowStatement:
    OperatingCashFlow: str
    CapitalExpenditure: str

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryIncomeStatements:
    quarterly: Dict[Date, YahooQueryIncomeStatement] = field(default_factory=dict)
    yearly: Dict[Date, YahooQueryIncomeStatement] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryBalanceSheets:
    quarterly: Dict[Date, YahooQueryBalanceSheet] = field(default_factory=dict)
    yearly: Dict[Date, YahooQueryBalanceSheet] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryCashFlowStatements:
    quarterly: Dict[Date, YahooQueryCashFlowStatement] = field(default_factory=dict)
    yearly: Dict[Date, YahooQueryCashFlowStatement] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryFinancialStatements:
    incomeStatements: YahooQueryIncomeStatements
    balanceSheets: YahooQueryBalanceSheets
    cashFlowStatements: YahooQueryCashFlowStatements

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQuerySummaryDetailData:
    fiveYearAvgDividendYield: str

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryKeyStatsData:
    sharesOutstanding: str

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryPriceData:
    regularMarketPrice: str

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class YahooQueryTickerData:
    summary_detail: Dict[Symbol, YahooQuerySummaryDetailData]
    key_stats: Dict[Symbol, YahooQueryKeyStatsData]
    price: Dict[Symbol, YahooQueryPriceData]
    income_statement: Any  # I've got no clue how to type a Callable with positional args
    balance_sheet: Any
    cash_flow: Any
    history: Any


@dataclass
class SymbolData:
    symbol: Symbol

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class PortfolioTransaction:
    date: Date = ""
    amount: Currency = 0.00
    transactionType: str = ""  # BUY, SELL, DIVIDEND, DEPOSIT
    symbol: Symbol = ""
    price: Currency = 0.00
    noShares: int = 0


@dataclass
class PortfolioStock:
    avgPrice: Currency = 0.00
    noShares: Shares = 0


@dataclass
class SimulateTestStockModel:
    symbol: str = ""
    startDate: str = ""
    endDate: str = ""


@dataclass
class DateRange:
    start: str = ""
    end: str = ""


@dataclass
class Valuation:
    dividendYield: Ratio = 0.00
    marketCap: Ratio = 0.00
    roe: Ratio = 0.00
    roa: Ratio = 0.00
    growthRate: Ratio = 0.0
    priceGrowthRate: Ratio = 0.0
    dte: Ratio = 0.00
    cr: Ratio = 0.00
    eps: Currency = 0.00
    pe: Ratio = 0.00
    peg: Ratio = 0.00
    pb: Ratio = 0.00
    blendedMultiplier: Ratio = 0.00
    fcf: Currency = 0.00
    liquidationIv: Currency = 0.00
    peMultipleIv: Currency = 0.00
    grahamIv: Currency = 0.00
    dcfIv: Currency = 0.00
    roeIv: Currency = 0.00
    altmanZScore: Ratio = 0.00
    statementYears: int = 0
    fairValue: Currency = 0.00
    mos: Ratio = 0.00
    buyPrice: Currency = 0.00
    sellPrice: Currency = 0.00
    instruction: str = ""

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class ValuationModel:
    name: str = ""
    discountRate: Ratio = 0.07  # historical jse growth rate
    declineRate: Ratio = 0.056  # inflation rate (CPI)
    taxRate: Ratio = 0.18  # fixed
    minMos: Ratio = 0.25  # margin of safety
    topUp: Currency = 1000.00
    buyLimit: Currency = 1000.00
    startDate: str = ""
    minRoe: Ratio = 0.15
    minRoa: Ratio = 0.02
    minGrowthRate: Ratio = 0.03
    maxPriceGrowthRate: Ratio = 0.00  # must be negative (it's currently unloved)
    maxDte: Ratio = 0.5
    minCr: Ratio = 2.0
    minEps: Currency = 0.00  # must at least be positive
    maxPe: Ratio = 25.0
    maxPeg: Ratio = 1.0
    maxPb: Ratio = 1.0
    minAltmanZScore: Ratio = 3.0
    minStatementYears: int = 3  # we extrapolate between statements so we'll need at least 2 yrs annual statements to be accurate and 3 yrs to be more accurate
    maxBlendedMultiplier: Ratio = 22.5


@dataclass
class Portfolio:
    cash: Currency = 0.00
    transactionHistory: Dict[Date, PortfolioTransaction] = field(default_factory=dict)
    stocks: Dict[Symbol, PortfolioStock] = field(default_factory=dict)
    roi: Ratio = 0.00
    model: ValuationModel = ValuationModel()


@dataclass
class Stock:
    symbol: Symbol = ""
    currentPrice: Currency = 0.00
    sharesOutstanding: Shares = 0
    profile: Profile = field(default_factory=Profile)
    historicalPricing: HistoricalPricing = field(default_factory=dict)
    financialStatements: FinancialStatements = field(
        default_factory=FinancialStatements
    )
    valuation: Valuation = field(default_factory=Valuation)
    lastUpdated: str = ""

    def __getitem__(self, key):
        return getattr(self, key)


Stocks = Dict[Symbol, Stock]
