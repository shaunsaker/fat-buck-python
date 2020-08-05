import json
from typing import List
import typedload
import utils
from models import Symbol, SymbolData


def removeSymbol(symbol: Symbol, exchange: str):
    path = f"data/symbols/{exchange}.json"
    with open(path) as file:
        symbols = typedload.load(json.load(file), List[SymbolData])

        for data in symbols:
            if data["symbol"] == symbol:
                symbols.remove(data)
                print(symbol, "no longer exists and has been removed.")

    with utils.safeOpenWrite(path) as file:
        jsonString = json.dumps(symbols, default=lambda o: o.__dict__, indent=2)
        file.write(jsonString)
