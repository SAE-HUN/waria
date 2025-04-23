from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Quote:
    current_price: float
    change_percent: float
    open: float
    high: float
    low: float
    volume: int
    market_cap: int
    high_52week: float
    low_52week: float


@dataclass
class Technical:
    open: float
    high: float
    low: float
    close: float
    ma_5: float
    ma_20: float
    ma_60: float
    rsi_14: float
    macd: float
    macd_signal: float
    bollinger_upper: float
    bollinger_lower: float


@dataclass
class Fundamentals:
    pe_trailing: Optional[float]
    pe_forward: Optional[float]
    pb_ratio: Optional[float]
    roe: Optional[float]
    eps: Optional[float]
    dividend_yield: Optional[float]


@dataclass
class NewsItem:
    title: str
    description: str
    summary: str
    pubDate: str


@dataclass
class StockData:
    quote: Quote
    technicals: Dict[str, Technical]  # key: date string ("YYYY-MM-DD")
    fundamentals: Fundamentals
    news: List[NewsItem]
