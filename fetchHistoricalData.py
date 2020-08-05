from models import Stock
from fetchHistoricalPricing import fetchHistoricalPricing
from fetchHistoricalFundamentals import fetchHistoricalFundamentals
from makeProfile import makeProfile
from makeHistoricalFinancialStatements import makeHistoricalFinancialStatements


def fetchHistoricalData(stock: Stock, exchange: str) -> Stock:
    stock.historicalPricing = fetchHistoricalPricing(stock.symbol, exchange)
    fundamentals = fetchHistoricalFundamentals(stock.symbol, exchange)

    if not fundamentals:
        return None

    stock.profile = makeProfile(fundamentals)
    stock.financialStatements = makeHistoricalFinancialStatements(fundamentals)

    return stock
