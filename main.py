from api.oanda import Candles
from strategies import SupportsStrategy
import time

data = []
backtest_data = []
ELEMENTS_COUNT = 670
BACKTEST_MODE = True
BACKTEST_FROM = "2017-03-01T00:00:00Z"
BACKTEST_TO = "2017-03-28T00:00:00Z"

def main():
    getDataToAnalize(ELEMENTS_COUNT)
    if BACKTEST_MODE:
        getBackTestData()

    strategy = SupportsStrategy.SupportsStrategy()
    strategy.Initialize(data)

    initProcess(strategy)

def initProcess(strategy):
    for candle in getNextCandle():
        action = strategy.GetAction(candle)
        print(action)


def getDataToAnalize(count):
    global data

    candlesApi = Candles()
    instrument = "EUR_USD"
    srKawrgs = {}
    srKawrgs['granularity'] = "D"


    if BACKTEST_MODE:
        srKawrgs['toTime'] = BACKTEST_FROM

    srKawrgs['count'] = str(count)

    data = candlesApi.GetCandleSticks(instrument, **srKawrgs)
    data = [row for row in data if row.complete == True]

def getBackTestData():
    global backtest_data

    candlesApi = Candles()
    instrument = "EUR_USD"
    srKawrgs = {}
    srKawrgs['granularity'] = "H1"
    srKawrgs['fromTime'] = BACKTEST_FROM
    srKawrgs['toTime'] = BACKTEST_TO

    backtest_data = candlesApi.GetCandleSticks(instrument, **srKawrgs)
    backtest_data = [row for row in backtest_data if row.complete == True]

def getNextCandle():
    global backtest_data

    if BACKTEST_MODE:
        for candle in backtest_data:
            yield candle
    else:
        while(True):
            yield data[0]
            time.sleep(10)

if __name__ == "__main__":
    main()