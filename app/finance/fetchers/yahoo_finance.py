import pandas as pd
import yfinance as yf


class YahooFinanceFetcher:
    def __init__(self):
        pass

    def fetch_analysis(self, symbol):
        return yf.Ticker(symbol)._analysis

    def fetch_info(self, symbol):
        return yf.Ticker(symbol).info

    def fetch_history(self, symbol, period="3mo", interval="1d"):
        return yf.Ticker(symbol).history(period=period, interval=interval)

    def fetch_news(self, symbol):
        return yf.Ticker(symbol).news

    def extract_content_info(self, item):
        fields = ["title", "description", "summary", "pubDate"]
        content = item.get("content", {})
        return {key: content.get(key, "") for key in fields}

    def get_news(self, symbol):
        news = self.fetch_news(symbol)
        parsed_news = []
        for article in news:
            parsed_news.append(self.extract_content_info(article))
        return parsed_news

    def get_analysis(self, symbol):
        analysis = self.fetch_analysis(symbol)

        try:
            eps_trend = analysis.eps_trend
            if isinstance(eps_trend, pd.DataFrame):
                eps_trend = eps_trend.to_dict()
                
            eps_trend_of_next_quarter = {
                'current': eps_trend['current']['+1q'],
                '7daysAgo': eps_trend['7daysAgo']['+1q'],
                # '30daysAgo': eps_trend['30daysAgo']['+1q'],
                # '60daysAgo': eps_trend['60daysAgo']['+1q'],
                # '90daysAgo': eps_trend['90daysAgo']['+1q'],
            }
        except (AttributeError, TypeError, KeyError):
            eps_trend_of_next_quarter = {}
            
        return {
            "eps_trend_of_next_quarter": eps_trend_of_next_quarter,
        }

    def get_fundamental_metrics(self, symbol):
        info = self.fetch_info(symbol)
        analysis = self.get_analysis(symbol)

        return {
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": (
                round(info.get("returnOnEquity", 0) * 100, 2)
                if info.get("returnOnEquity")
                else None
            ),
            "eps": info.get("trailingEps"),
            "eps_trend_of_next_quarter": analysis.get("eps_trend_of_next_quarter"),
            "dividend_yield": (
                round(info.get("dividendYield", 0) * 100, 2)
                if info.get("dividendYield")
                else None
            ),
        }

    def get_quote(self, symbol):
        info = self.fetch_info(symbol)
        return {
            "current_price": info.get("regularMarketPrice"),
            "change_percent": info.get("regularMarketChangePercent"),
            "market_cap": info.get("marketCap"),
            "high_52week": info.get("fiftyTwoWeekHigh"),
            "low_52week": info.get("fiftyTwoWeekLow"),
        }

    def get_ohlcv_and_indicators(self, symbol):
        df = self.fetch_history(symbol)
        df["open"] = df["Open"]
        df["high"] = df["High"]
        df["low"] = df["Low"]
        df["close"] = df["Close"]
        df["volume"] = df["Volume"]

        close = df["close"]

        df["ma_5"] = close.rolling(window=5).mean()
        df["ma_20"] = close.rolling(window=20).mean()
        df["ma_60"] = close.rolling(window=60).mean()

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        df["rsi_14"] = 100 - (100 / (1 + rs))

        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        ma_20 = df["ma_20"]
        std_20 = close.rolling(window=20).std()
        df["bollinger_upper"] = ma_20 + (2 * std_20)
        df["bollinger_lower"] = ma_20 - (2 * std_20)

        df_selected = df[
            [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "ma_5",
                "ma_20",
                "ma_60",
                "rsi_14",
                "macd",
                "macd_signal",
                "bollinger_upper",
                "bollinger_lower",
            ]
        ].round(2)
        df_selected.index = df_selected.index.strftime('%Y-%m-%d')
        df_selected = df_selected.astype(object).where(pd.notnull(df_selected), None)

        return df_selected.to_dict(orient="index")
