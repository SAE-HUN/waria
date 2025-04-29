from dataclasses import dataclass
from typing import Any, List


@dataclass
class TechnicalData:
    ohlcv_and_indicators: Any
    current_price: float
    change_percent: float
    market_cap: int
    high_52week: float
    low_52week: float


@dataclass
class FundamentalData:
    pe_trailing: float
    pe_forward: float
    pb_ratio: float
    roe: float
    eps: float
    dividend_yield: float
    earnings_surprises: List
    recommendation_trends: List
    earnings_calendar: List
    news: List
