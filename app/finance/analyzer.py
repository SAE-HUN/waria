from typing import Any, Dict

from app.finance.interface import StockData
from app.finance.yahoo_finance import YahooStockFetcher


class Analyzer:
    def __init__(self) -> None:
        self.fetcher = YahooStockFetcher()

    def get_data(self, symbol: str) -> StockData:
        return self.fetcher.get_all_data(symbol)
