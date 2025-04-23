from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import yfinance as yf

from app.finance.interface import StockData


class YahooStockFetcher:
    def __init__(self):
        pass

    def fetch_info(self, symbol):
        return yf.Ticker(symbol).info

    def fetch_history(self, symbol, period="1y", interval="1d"):
        return yf.Ticker(symbol).history(period=period, interval=interval)

    def fetch_history_temp(self, symbol, period="1y", interval="1d"):
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        df.reset_index(names='date', inplace=True)
        df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            },
            inplace=True,
        )
        return df

    def fetch_news(self, symbol):
        return yf.Ticker(symbol).news

    def extract_content_info(self, item):
        fields = ["title", "description", "summary", "pubDate"]
        content = item.get("content", {})
        return {key: content.get(key, "") for key in fields}

    def fetch_all(self, symbol):
        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.fetch_info, symbol): "info",
                executor.submit(self.fetch_history, symbol): "history",
                executor.submit(self.fetch_news, symbol): "news",
            }

            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    print(f"Error: {str(e)}")

        return results

    def get_all_data(self, symbol) -> StockData:
        data = self.fetch_all(symbol)

        info = data.get("info", {})
        df = data.get("history", pd.DataFrame())
        news_list = data.get("news", [])

        # 1. quote summary
        quote = {
            "current_price": info.get("regularMarketPrice"),
            "change_percent": info.get("regularMarketChangePercent"),
            "open": info.get("regularMarketOpen"),
            "high": info.get("regularMarketDayHigh"),
            "low": info.get("regularMarketDayLow"),
            "volume": info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "high_52week": info.get("fiftyTwoWeekHigh"),
            "low_52week": info.get("fiftyTwoWeekLow"),
        }

        technicals = {}
        if not df.empty:
            df["open"] = df["Open"]
            df["high"] = df["High"]
            df["low"] = df["Low"]
            df["close"] = df["Close"]
            df["volume"] = df["Volume"]

            close = df["close"]

            # 2. technical indicators
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

            df_selected = (
                df[
                    [
                        "open",
                        "high",
                        "low",
                        "close",
                        "ma_5",
                        "ma_20",
                        "ma_60",
                        "rsi_14",
                        "macd",
                        "macd_signal",
                        "bollinger_upper",
                        "bollinger_lower",
                    ]
                ]
                .dropna()
                .round(2)
            )
            df_selected.index = df_selected.index.strftime('%Y-%m-%d')

            technicals = df_selected.to_dict(orient="index")

        # 3. fundamental metrics
        fundamentals = {
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": (
                round(info.get("returnOnEquity", 0) * 100, 2)
                if info.get("returnOnEquity")
                else None
            ),
            "eps": info.get("trailingEps"),
            "dividend_yield": (
                round(info.get("dividendYield", 0) * 100, 2)
                if info.get("dividendYield")
                else None
            ),
        }

        parsed_news = []
        for news in news_list:
            parsed_news.append(self.extract_content_info(news))

        result = {
            "quote": quote,
            "technicals": technicals,
            "fundamentals": fundamentals,
            "news": parsed_news,
        }

        return result

    def extract_content_info(self, item):
        fields = ["title", "description", "summary", "pubDate"]
        content = item.get("content", {})
        result = {key: content.get(key, "") for key in fields}

        return result
