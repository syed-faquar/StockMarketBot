from dataclasses import dataclass
from pickle import TRUE
import tda
from tda.auth import easy_client
from tda.client import Client
from tda.streaming import StreamClient
from tda.orders.equities import equity_buy_market, equity_sell_market
import atexit
import pytz
import datetime
from datetime import timedelta
import asyncio
from contextlib import suppress
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import ta
import numpy as np
import pandas as pd
import math
import logging
import locale
import threading
import time
import sys
import os
import .config as cnf

class Bar:
    open = 0
    close = 0
    low = 0
    high = 0
    volume = 0
    date = datetime.datetime.now()
    def __init__(self):
        self.open = 0
        self.close = 0
        self.low = 0
        self.high = 0
        self.volume = 0
        self.date = datetime.datetime.now()

class Bot():
    barsize = 1
    currentBar = Bar()
    bars = []
    client = ""
    account_id = 0
    account_size = 10000
    firstTime = True
    rsi = []
    rsiPeriod = 14
    stream_client = ''
    status = None
    initialbartime = datetime.datetime.now().astimezone(pytz.timezone("America/New_York"))
    def __init__(self):
        try:
            API_KEY = cfg.TDA_API_KEY
            REDIRECT_URI = cfg.URL
            TOKEN_PATH = cfg.TOKEN_PATH
            self.client = tda.auth.easy_client(API_KEY, REDIRECT_URI,  TOKEN_PATH, self.make_webdriver)
            r = self.client.get_accounts()
            assert r.status_code == 200, r.raise_for_status()
            data = r.json()
            self.account_id = data[0]['securitiesAccount']['accountID']
            self.account_size = data[0]['securitiesAccount']['currentbalances']['cashBalance']
            self.stream_client = StreamClient(self.client, account_id=self.account_id)
            print("Logged into TDA Account")
            self.symbol = input("Enter interested ticker name:")
            self.barsize = int(input('Enter barsize'))
            self.stream_client = StreamClient(self.client, account_id= self.account_id)
            asyncio.run(self.read_stream())
        except Exception as e:
            print(e)
    async def read_stream(self):
        try:
            await self.stream_client.login()
            await self.stream_client.quality_of_service(StreamClient.QOSLevel.EXPRESS)
            await self.stream_client.chart_equity_subs([self.symbol])
            self.stream_client.add_chart_equity_handler(self.onBarUpdate)
            print('Streaming real time data....')
            while True:
                try:
                    await self.stream_client.handle_message()
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)
    def onBarUpdate(self,msg):
        try:
            msg = json.dumps(msg, indent=4)
            msg = json.loads(msg)
            for bar in msg['content']:
                bartime = datetime.datetime.fromtimestamp(msg['timestamp']/1000).astimezone()
                min_diff = (bartime-self.initialbartime).total_seconds() / 60.0
                self.currentBar.date = bartime
                if (min_diff>0 and math.floor(min_diff)% self.barsize == 0):
                    self.initialbartime = bartime
                    closes = []
                    for histbar in self.bars:
                        closes.append(histbar.close)
                    self.close_array = pd.Series(np.asarray(closes))
                    if (len(self.bars)>0):
                        self.rsi = ta.momentum.rsi(self.close_array, self.rsiPeriod, True)
                        print(self.rsi[len(self.rsi)-1])
                    self.currentBar.close = bar['CLOSE_PRICE']
                    print("New Bar.")
                    self.bars.append(self.currentBar)
                    self.currentBar = Bar()
                    self.currentBar.open = bar['OPEN_PRICE']
                if (self.currentBar.open == 0):
                    self.currentBar.open = bar['OPEN_PRICE']
                if (self.currentBar.high == 0 or bar['HIGH_PRICE'] > self.currentBar.high):
                    self.currentBar.high = bar['HIGH_PRICE']
                if (self.currentBar.low == 0 or bar['LOW_PRICE'] < self.currentBar.low):
                    self.currentBar.low = bar['LOW_PRICE']
        except Exception as e:
            print(e)
    def make_webdriver(self):
        # To do
        pass
