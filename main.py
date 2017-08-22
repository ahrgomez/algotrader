from api.oanda import Candles
from strategies import SupportsStrategy
import time
from service.OrderService import OrderService
from common import cross

data = []
backtest_data = []
ELEMENTS_COUNT = 670
BACKTEST_MODE = True
BACKTEST_FROM = "2017-01-01T00:00:00Z"
BACKTEST_TO = "2017-08-19T00:00:00Z"
SR_TEMPORALITY = "D"
PROCESS_TEMPORALITY = "H1"
instrument = "EUR_USD"
finalReport = []
REPORT_PATH = "./final_report.csv"
SUPPORTS_PATH = "./sr_final_report.csv"

def main():
    if BACKTEST_MODE:
        print("INIT BACKTEST")
        print("-------------")
        print("FROM: ", BACKTEST_FROM)
        print("TO: ", BACKTEST_TO)
        print("IN: ", instrument)
        print("-------------")
        print("")

    getDataToAnalize(instrument, ELEMENTS_COUNT)
    if BACKTEST_MODE:
        getBackTestData(instrument)

    strategy = SupportsStrategy.SupportsStrategy(instrument)
    strategy.Initialize(data)

    initProcess(strategy)

def initProcess(strategy):
    orderService = OrderService()
    orderService.InitInstrument(instrument)
    for candle in getNextCandle():
        activeOrder = orderService.GetActiveOrder(instrument)
        if activeOrder is None:
            orderActivated = False
            inactiveOrders = orderService.GetInactiveOrders(instrument)
            if inactiveOrders is not None:
                for inactiveOrder in inactiveOrders:
                    orderActivated = makeActiveOrderIfIsPossible(orderService, inactiveOrder, candle)
                    if orderActivated:
                        break
            if not orderActivated:
                action = strategy.GetAction(candle)
                if action is not None:
                    makeOrder(instrument, orderService, action)
            else:
                strategy.UpdateSupportsAndResistences(candle)
        else:
            reviewOrder(orderService, activeOrder, candle)
            strategy.UpdateSupportsAndResistences(candle)

    writeReportFile()
    writeSupportsAndResistences(strategy.supportsAndResistences)

    print("END OF PROCESS!")

def getDataToAnalize(instrument, count):
    global data

    candlesApi = Candles()
    srKawrgs = {}
    srKawrgs['granularity'] = SR_TEMPORALITY


    if BACKTEST_MODE:
        srKawrgs['toTime'] = BACKTEST_FROM

    srKawrgs['count'] = str(count)

    data = candlesApi.GetCandleSticks(instrument, **srKawrgs)
    data = [row for row in data if row.complete == True]

def getBackTestData(instrument):
    global backtest_data

    candlesApi = Candles()
    srKawrgs = {}
    srKawrgs['granularity'] = PROCESS_TEMPORALITY
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

def makeOrder(instrument, orderService, action):

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

    if orderService.SaveOrder(instrument, price, action.type, stop_loss, take_profit, action.support, action.resistence, action.date):
        print("Type: " + action.type + "/ D: " + str(action.date) +
              "/ P: " + str(price) + "/ SL: " + str(stop_loss) +
              "/ TP: " + str(take_profit) + "/ S: " + str(action.support) +
              "/ R: " + str(action.resistence))

        finalReport.append(str(action.date) + ",ORDER," +
                           action.type + "," + str(price) +
                           "," + str(stop_loss) + "," + str(take_profit) +
                           "," + str(action.support) + "," + str(action.resistence))

def reviewOrder(orderService, order, candle):
    if order.type == "BUY":
        if cross.priceInRange(order.take_profit, candle.mid.l, candle.mid.h):
            orderService.DeactivateOrder(order, "SUCCESS")
            print('\033[92m' + "SUCCESS: " + str(candle.mid.c) + '\033[0m')

            finalReport.append(str(order.date) + ",SUCCESS," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))

        elif cross.priceInRange(order.stop_loss, candle.mid.l, candle.mid.h):
            orderService.DeactivateOrder(order, "FAILED")
            print('\033[91m' + "FAILED: " + str(candle.mid.c) + '\033[0m')

            finalReport.append(str(order.date) + ",FAILED," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))
    elif order.type == "SELL":
        if cross.priceInRange(order.take_profit, candle.mid.l, candle.mid.h):
            orderService.DeactivateOrder(order, "SUCCESS")
            print('\033[92m' + "SUCCESS: " + str(candle.mid.c) + '\033[0m')

            finalReport.append(str(order.date) + ",SUCCESS," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))
        elif cross.priceInRange(order.stop_loss, candle.mid.l, candle.mid.h):
            orderService.DeactivateOrder(order, "FAILED")
            print('\033[91m' + "FAILED: " + str(candle.mid.c) + '\033[0m')

            finalReport.append(str(order.date) + ",FAILED," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))

def makeActiveOrderIfIsPossible(orderService, order, candle):
    if order.type == "BUY":
        if cross.priceInRange(order.price, candle.mid.l, candle.mid.h):
            orderService.ActivateOrder(order)
            print("ACTIVATED Type: " + order.type + "/ P: " + str(order.price) + "/ SL: " + str(order.stop_loss) + "/ TP: " + str(order.take_profit))

            finalReport.append(str(order.date) + ",ACTIVATED," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))
            return True
    elif order.type == "SELL":
        if cross.priceInRange(order.price, candle.mid.l, candle.mid.h):
            orderService.ActivateOrder(order)
            print("ACTIVATED Type: " + order.type + "/ P: " + str(order.price) + "/ SL: " + str(order.stop_loss) + "/ TP: " + str(order.take_profit))

            finalReport.append(str(order.date) + ",ACTIVATED," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))
            return True

    return False

def writeReportFile():
    import csv
    with open(REPORT_PATH, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for text in finalReport:
            writer.writerow(text)

def writeSupportsAndResistences(supportsAndResistences):
    import csv
    with open(SUPPORTS_PATH, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for text in supportsAndResistences:
            writer.writerow(str(text))

if __name__ == "__main__":
    main()