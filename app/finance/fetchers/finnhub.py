import finnhub
import logging

logger = logging.getLogger(__name__)

class FinnhubFetcher:
    def __init__(self, API_KEY: str) -> None:
        self.client = finnhub.Client(api_key=API_KEY)

    def get_earnings_surprises(self, symbol: str) -> list:
        try:
            return self.client.company_earnings(symbol)
        except Exception as e:
            logger.error({
                "function": "get_earnings_surprises",
                "symbol": symbol,
                "error": str(e),
            })
            return []

    def get_recommendation_trends(self, symbol: str) -> list:
        try:
            return self.client.recommendation_trends(symbol)
        except Exception as e:
            logger.error({
                "function": "get_recommendation_trends",
                "symbol": symbol,
                "error": str(e),
            })
            return []

    def get_earnings_calendar(
        self, symbol: str = None, from_date: str = None, to_date: str = None
    ) -> list:
        try:
            return self.client.earnings_calendar(
                symbol=symbol, _from=from_date, to=to_date
            )
        except Exception as e:
            logger.error({
                "function": "get_earnings_calendar",
                "symbol": symbol,
                "error": str(e),
            })
            return []

    def get_fundamental_metrics(
        self, symbol: str, from_date: str = None, to_date: str = None
    ) -> dict:
        earnings_surprises = self.get_earnings_surprises(symbol)
        recommendation_trends = self.get_recommendation_trends(symbol)
        earnings_calendar = self.get_earnings_calendar(symbol, from_date, to_date)

        return {
            "earnings_surprises": earnings_surprises,
            "recommendation_trends": recommendation_trends,
            "earnings_calendar": earnings_calendar,
        }
