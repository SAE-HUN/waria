from datetime import datetime, timedelta
from app.finance.interface import TechnicalData, FundamentalData
from app.finance.fetchers.yahoo_finance import YahooFinanceFetcher
from app.finance.fetchers.finnhub import FinnhubFetcher


class Fetcher:
    def __init__(self, FINNHUB_API_KEY) -> None:
        self.yahoo_fetcher = YahooFinanceFetcher()
        self.finnhub_fetcher = FinnhubFetcher(FINNHUB_API_KEY)

    def get_technical_data(self, symbol: str) -> TechnicalData:
        quote = self.yahoo_fetcher.get_quote(symbol)
        ohlcv_and_indicators = self.yahoo_fetcher.get_ohlcv_and_indicators(symbol)
        technical_data = TechnicalData(
            ohlcv_and_indicators=ohlcv_and_indicators,
            current_price=quote["current_price"],
            change_percent=quote["change_percent"],
            market_cap=quote["market_cap"],
            high_52week=quote["high_52week"],
            low_52week=quote["low_52week"],
        )

        return technical_data

    def get_fundamental_data(self, symbol: str) -> FundamentalData:
        news = self.yahoo_fetcher.get_news(symbol)
        fundamental_metrics_from_yahoo = self.yahoo_fetcher.get_fundamental_metrics(
            symbol
        )
        fundamental_metrics_from_finnhub = self.finnhub_fetcher.get_fundamental_metrics(
            symbol,
            from_date=datetime.now() - timedelta(days=365),
            to_date=datetime.now(),
        )

        fundamental_data = FundamentalData(
            pe_trailing=fundamental_metrics_from_yahoo["pe_trailing"],
            pe_forward=fundamental_metrics_from_yahoo["pe_forward"],
            pb_ratio=fundamental_metrics_from_yahoo["pb_ratio"],
            roe=fundamental_metrics_from_yahoo["roe"],
            eps=fundamental_metrics_from_yahoo["eps"],
            dividend_yield=fundamental_metrics_from_yahoo["dividend_yield"],
            earnings_surprises=fundamental_metrics_from_finnhub["earnings_surprises"],
            recommendation_trends=fundamental_metrics_from_finnhub[
                "recommendation_trends"
            ],
            earnings_calendar=fundamental_metrics_from_finnhub["earnings_calendar"],
            news=news,
        )

        return fundamental_data
