#  private key - environment var as alphavantage
#  win: SET alphavantage=key
#  linux: export alphavantage=key
#  generate on https://www.alphavantage.co/


import requests
import os
import json
import time
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
global symbols


class PlotPoint:
    def __init__(self, date, close, symbol):
        self.date = date
        self.close = close
        self.symbol = symbol

    def __str__(self):
        return f"{self.symbol} was worth £{self.close} on {self.date}"

    def __repr__(self):
        return f"{self.symbol}-£{self.close}-{self.date}"


def get_finance_data():
    global symbols
    symbols = ["AAPL", "AMZN", "GOOGL", "MSFT", "NVDA"]
    stocks = {"last_modified": time.time(), "readable_last_modified": time.strftime("%c")}
    if not os.path.exists("stocks.json"):
        with open("stocks.json", "x"):
            pass
    try:
        with open("stocks.json") as f:
            old_stocks = json.load(f)
            if old_stocks["last_modified"] + 86400 > time.time():  # if a day hasn't passed
                print(f"Using stock data as of {old_stocks['readable_last_modified']}")  # had to format stupidly sorry
                return old_stocks
    except json.decoder.JSONDecodeError:
        print("JSON file is empty. Repopulating...")
    print("Retrieving new stock market information...")
    for item in symbols:
        pl = {
            "function": "TIME_SERIES_DAILY",
            "symbol": item,
            "outputsize": "full",
            "apikey": os.environ["alphavantage"]
             }
        r = requests.get("https://www.alphavantage.co/query", params=pl)
        stocks[item] = r.json()
    with open("stocks.json", "w") as f:
        json.dump(stocks, f)
    return stocks


def get_exchange_rate():
    if os.path.exists("cache.json"):
        with open("cache.json", "r") as f:
            price_data = json.load(f)
        if price_data["last_modified"] >= time.time() - 86400:
            print("Using current stored exchange rate")
            return price_data["GBP"]
    with open("cache.json", "w") as f:
        print("Refreshing exchange rate...")
        r = requests.get("https://open.er-api.com/v6/latest/USD")
        response = r.json()
        if response["result"] != "success":
            raise requests.exceptions.ConnectionError("The exchange rate API is down!")
        response = {"GBP": response["rates"]["GBP"], "last_modified": time.time()}
        json.dump(response, f)
        return response["GBP"]


def organize_data(data):
    global symbols
    filing_cabinet = {}
    ex_rate = get_exchange_rate()
    for item in symbols:
        closes = []
        for stock in data[item]["Time Series (Daily)"]:
            close = round(float(data[item]["Time Series (Daily)"][stock]["4. close"]) * ex_rate, 2)
            point = PlotPoint(stock, close, item)
            closes.append(point)
        closes = closes[::-1]  # switches from DESC to ASC
        filing_cabinet[item] = closes
    return filing_cabinet


def plot(data):
    for item in data.keys():
        x_points, y_points = [], []
        for point in data[item]:
            x_points.append(point.date)
            y_points.append(point.close)
    print(data["NVDA"])
    datetime_dates = [dt.datetime.strptime(str(d), "%Y-%m-%d").date() for d in x_points]
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=12))
    plt.xlabel("Dates")
    plt.ylabel("Closing Price (£)")
    plt.plot(datetime_dates, y_points, color="red")
    plt.show()


def main():
    stocks = get_finance_data()
    sorted_data = organize_data(stocks)
    plot(sorted_data)


if __name__ == "__main__":
    main()
