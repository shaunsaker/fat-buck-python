import json
import typedload
from models import Symbol, HistoricalFundamentals
import config
import utils
from removeSymbol import removeSymbol


def fetchHistoricalFundamentals(
    symbol: Symbol, exchange: str
) -> HistoricalFundamentals:
    filepath = "data/raw/fundamentals/" + exchange + "/" + symbol + ".json"

    # # if the raw data already exists locally, use that
    # if utils.fileExists(filepath):
    #     with open(filepath) as file:
    #         data = typedload.load(json.load(file), HistoricalFundamentals)
    # else:
    eodSymbol = (
        symbol.split(".")[0] + "." + exchange
    )  # us the correct exchange identifier
    url = config.eodApi + eodSymbol + "?api_token=" + config.eodApiKey
    data = utils.fetchJson(url)

    # store the raw fundamentals data
    with utils.safeOpenWrite(filepath) as file:
        jsonString = json.dumps(data, default=lambda o: o.__dict__, indent=2)
        file.write(jsonString)

    if not data or "Financials" not in data:
        removeSymbol(symbol, exchange)
        return None

    fundamentals = typedload.load(data, HistoricalFundamentals)

    return fundamentals
