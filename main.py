from api.oanda import Candles
from strategies import SupportsStrategy
import time
from service.OrderService import OrderService

data = []
backtest_data = []
ELEMENTS_COUNT = 670
BACKTEST_MODE = True
BACKTEST_FROM = "2017-03-01T00:00:00Z"
BACKTEST_TO = "2017-08-17T00:00:00Z"

def main():
    getDataToAnalize(ELEMENTS_COUNT)
    if BACKTEST_MODE:
        getBackTestData()

    strategy = SupportsStrategy.SupportsStrategy()
    strategy.Initialize(data)

    initProcess(strategy)

def initProcess(strategy):
    orderService = OrderService()
    orderService.InitInstrument("EUR_USD")
    for candle in getNextCandle():
        activeOrder = orderService.GetActiveOrder("EUR_USD")
        if activeOrder is None:
            orderActivated = False
            inactiveOrders = orderService.GetInactiveOrders("EUR_USD")
            if inactiveOrders is not None:
                for inactiveOrder in inactiveOrders:
                    orderActivated = makeActiveOrderIfIsPossible(orderService, inactiveOrder, candle)
                    if orderActivated:
                        break

            if not orderActivated:
                action = strategy.GetAction(candle)
                if action is not None:
                    makeOrder(orderService, action)
            else:
                strategy.UpdateSupportsAndResistences(candle)
        else:
            reviewOrder(orderService, activeOrder, candle)
            strategy.UpdateSupportsAndResistences(candle)

    print("END OF PROCESS!")

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

def makeOrder(orderService, action):

    price = None
    take_profit = None
    stop_loss = None

    if action.type == "BUY":
        price = action.lastMax
        stop_loss = action.lastMin
        take_profit = action.support + ((action.resistence - action.support) * 0.90)
    elif action.type == "SELL":
        price = action.lastMin
        take_profit = action.resistence - ((action.resistence - action.support) * 0.90)
        stop_loss = action.lastMax

    if orderService.SaveOrder("EUR_USD", price, action.type, stop_loss, take_profit, action.support, action.resistence):
        print("Type: " + action.type + "/ D: " + str(action.date) +
              "/ P: " + str(price) + "/ SL: " + str(stop_loss) +
              "/ TP: " + str(take_profit) + "/ S: " + str(action.support) +
              "/ R: " + str(action.resistence))

def reviewOrder(orderService, order, candle):
    if order.type == "BUY":
        if priceInRange(order.take_profit, candle.mid.l, candle.mid.h):
            orderService.DeactivateOrder(order, "SUCCESS")
            print("SUCCESS: " + str(candle.mid.c))
        elif priceInRange(order.stop_loss, candle.mid.l, candle.mid.h):
            orderService.DeactivateOrder(order, "FAILED")
            print("FAILED: " + str(candle.mid.c))
    elif order.type == "SELL":
        if priceInRange(order.take_profit, candle.mid.l, candle.mid.h):
            orderService.DeactivateOrder(order, "SUCCESS")
            print("SUCCESS: " + str(candle.mid.c))
        elif priceInRange(order.stop_loss, candle.mid.l, candle.mid.h):
            orderService.DeactivateOrder(order, "FAILED")
            print("FAILED: " + str(candle.mid.c))


def makeActiveOrderIfIsPossible(orderService, order, candle):
    if order.type == "BUY":
        if priceInRange(order.price, candle.mid.l, candle.mid.h):
            orderService.ActivateOrder(order)
            print("ACTIVATED Type: " + order.type + "/ P: " + str(order.price) + "/ SL: " + str(order.stop_loss) + "/ TP: " + str(order.take_profit))
            return True
    elif order.type == "SELL":
        if priceInRange(order.price, candle.mid.l, candle.mid.h):
            orderService.ActivateOrder(order)
            print("ACTIVATED Type: " + order.type + "/ P: " + str(order.price) + "/ SL: " + str(order.stop_loss) + "/ TP: " + str(order.take_profit))
            return True

    return False

def priceInRange(price, num1, num2):
    minValue = num1
    maxValue = num2

    if num1 < num2:
        minValue = num1
        maxValue = num2
    else:
        minValue = num2
        maxValue = num2

    return minValue <= price <= maxValue

if __name__ == "__main__":
    main()