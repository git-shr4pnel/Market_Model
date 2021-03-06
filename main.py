#  private key - environment var as alphavantage
#  win: SET alphavantage=key
#  unix: export alphavantage=key
#  generate on https://www.alphavantage.co/


import requests
import os
import json
import time
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk
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


def seperate_plot(data):
    colors = ("blue", "red", "purple", "green", "black")
    for n, item in enumerate(data.keys()):
        x_points, y_points = [], []
        for point in data[item]:
            x_points.append(point.date)
            y_points.append(point.close)
        x_points = [dt.datetime.strptime(str(d), "%Y-%m-%d").date() for d in x_points]  # creates dt object
        plt.figure(figsize=(10, 7.5))
        plt.plot(x_points, y_points, color=colors[n], label=item)
        plt.xlabel("Dates")
        plt.ylabel("Closing Price (£)")
        plt.xticks(rotation=30)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))  # sets format of dates
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=12))
        plt.title(item)
    plt.show()


def spec_prompt(data):
    # window init
    window = tk.Tk()
    window.title("Choose stocks:")
    window.focus_force()
    window.geometry("350x150+100+100")
    window.resizable(False, False)
    window.attributes("-topmost", 1)
    # checkbutton init
    checkboxes, values = [], []
    for val in range(5):
        var = tk.BooleanVar()
        var.set(False)
        values.append(var)  # setting state of checkboxes (off, it has to be done like this)
    for check in range(5):
        box = ttk.Checkbutton(window, text=tuple(data.keys())[check], variable=values[check])
        checkboxes.append(box)
    for n, item in enumerate(checkboxes):
        item.grid(column=0, row=n+1, sticky="sw", padx=30)
    # label init
    label = ttk.Label(text="Select the stocks you wish to visualize:")
    label.grid(row=0, column=0, pady=5, padx=10)
    # button init
    tk_quit = ttk.Button(text="Quit", command=lambda: (window.destroy(), sys.exit(0)))
    tk_confirm = ttk.Button(text="Apply", command=lambda: window.destroy())
    tk_quit.place(x=260, y=110)
    tk_confirm.place(x=175, y=110)
    # radiobutton init
    var = tk.IntVar()
    var.set(0)
    tk_seperate = ttk.Radiobutton(window, text="Seperate", variable=var, value=0)
    tk_intersection = ttk.Radiobutton(window, text="Intersection", variable=var, value=1)
    tk_seperate.place(x=175, y=80)
    tk_intersection.place(x=255, y=80)
    window.mainloop()
    # verifying tickboxes
    verif = {"state": var.get()}
    for n, item in enumerate(values):
        state = item.get()
        symb = tuple(data.keys())[n]
        verif[symb] = state
    if True not in verif.values():
        print("You need to select at least one stock to plot on the graph.")
        return
    new_data = {}
    for n, v in enumerate(tuple(verif.values())[1:]):
        if v:
            new_data[tuple(verif.keys())[n+1]] = data[tuple(data.keys())[n]]
    if not verif["state"]:  # if radiobutton selected is "seperate":
        seperate_plot(new_data)
        return
    multi_plot(new_data)


def prompt(data):
    # window init
    window = tk.Tk()
    window.title("Stocks")
    window.geometry("300x100+100+100")
    window.focus_force()
    window.resizable(False, False)
    window.attributes("-topmost", 1)  # this means that the window stays on top until closed
    # button init
    tk_all = ttk.Button(text="All", command=lambda: (window.destroy(), multi_plot(data)))
    tk_individual = ttk.Button(text="Individual", command=lambda: (window.destroy(), spec_prompt(data)))
    tk_quit = ttk.Button(text="Quit", command=lambda: (window.destroy(), sys.exit(0)))
    tk_all.place(x=37, y=70)
    tk_individual.place(x=112.5, y=70)
    tk_quit.place(x=188.5, y=70)
    label = ttk.Label(text="Select a visualisation!")
    label.place(x=95, y=10)
    window.mainloop()


def multi_plot(data):
    colors = ("blue", "red", "purple", "green", "black")
    plt.figure(figsize=(15, 7.5))  # the amount of googling it took for this line was distressing
    for n, item in enumerate(data.keys()):
        x_points, y_points = [], []
        for point in data[item]:
            x_points.append(point.date)
            y_points.append(point.close)
        x_points = [dt.datetime.strptime(str(d), "%Y-%m-%d").date() for d in x_points]
        plt.plot(x_points, y_points, color=colors[n], label=item)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=12))
    plt.xlabel("Dates")
    plt.ylabel("Closing Price (£)")
    plt.xticks(rotation=22.5)
    plt.legend()
    plt.show()


def startup():
    try:
        os.environ["alphavantagea"]
    except KeyError:
        window = tk.Tk()
        window.geometry("300x150+100+100")
        window.focus_force()
        window.mainloop()


def main():
    startup()
    stocks = get_finance_data()
    sorted_data = organize_data(stocks)
    while 1:
        prompt(sorted_data)


if __name__ == "__main__":
    main()
