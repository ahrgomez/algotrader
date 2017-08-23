from api.oanda import Candles
from strategies import SupportsStrategy
import time
from service.OrderService import OrderService
from service.HistoryService import HistoryService
from common import cross

data = []
backtest_data = []
ELEMENTS_COUNT = 670
BACKTEST_MODE = True
BACKTEST_FROM = "2017-01-01T00:00:00Z"
BACKTEST_TO = "2017-08-19T00:00:00Z"
SR_TEMPORALITY = "D"
PROCESS_TEMPORALITY = "H1"
instrument = "EUR_CAD"
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

    # ------Init services-------

    historyService = HistoryService()
    historyService.AddArrayDataToHistory(getTemporarilyData(instrument))

    orderService = OrderService()
    orderService.InitInstrument(instrument)

    # ------Init strategy-------

    strategy = SupportsStrategy.SupportsStrategy(instrument, historyService)
    strategy.Initialize(data)

    # ------Init process--------

    initProcess(strategy, orderService, historyService)

def initProcess(strategy, orderService, historyService):

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
        historyService.AddDataToHistory(candle)

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

def getTemporarilyData(instrument):
    candlesApi = Candles()
    srKawrgs = {}
    srKawrgs['granularity'] = PROCESS_TEMPORALITY
    srKawrgs['toTime'] = BACKTEST_FROM

    tempData = candlesApi.GetCandleSticks(instrument, **srKawrgs)
    tempData = [row for row in tempData if row.complete == True]

    return tempData

def getNextCandle():
    global backtest_data

    if BACKTEST_MODE:
        for candle in backtest_data:
            yield candle
    else:
        while(True):
            yield data[0]
            time.sleep(10)

# ------ORDERS-------

def makeOrder(instrument, orderService, action):

    if orderService.SaveOrder(instrument, action.entryPoint, action.type, action.stopLoss, action.takeProfit, action.support, action.resistence, action.date):
        print("Type: " + action.type + "/ D: " + str(action.date) +
              "/ P: " + str(action.entryPoint) + "/ SL: " + str(action.stopLoss) +
              "/ TP: " + str(action.takeProfit) + "/ S: " + str(action.support) +
              "/ R: " + str(action.resistence))

        finalReport.append(str(action.date) + ",ORDER," +
                           action.type + "," + str(action.entryPoint) +
                           "," + str(action.stopLoss) + "," + str(action.takeProfit) +
                           "," + str(action.support) + "," + str(action.resistence))

def reviewOrder(orderService, order, candle):
    if order.type == "BUY":
        if cross.candleTouchPrice(candle, order.take_profit):
            orderService.DeactivateOrder(order, " SUCCESS")
            print('\033[92m' + str(candle.time) + "SUCCESS: " + str(candle.mid.c) + '\033[0m')

            finalReport.append(str(candle.time) + ",SUCCESS," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))

        elif cross.candleTouchPrice(candle, order.stop_loss):
            orderService.DeactivateOrder(order, " FAILED")
            print('\033[91m' + str(candle.time) + "FAILED: " + str(candle.mid.c) + '\033[0m')

            finalReport.append(str(candle.time) + ",FAILED," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))
    elif order.type == "SELL":
        if cross.candleTouchPrice(candle, order.take_profit):
            orderService.DeactivateOrder(order, " SUCCESS")
            print('\033[92m' + str(candle.time) + "SUCCESS: " + str(candle.mid.c) + '\033[0m')

            finalReport.append(str(candle.time) + ",SUCCESS," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))
        elif cross.candleTouchPrice(candle, order.stop_loss):
            orderService.DeactivateOrder(order, " FAILED")
            print('\033[91m' + str(candle.time) + "FAILED: " + str(candle.mid.c) + '\033[0m')

            finalReport.append(str(candle.time) + ",FAILED," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))

def makeActiveOrderIfIsPossible(orderService, order, candle):
    if cross.candleTouchPrice(candle, order.price):
        if cross.candleTouchPrice(candle, order.price):
            orderService.ActivateOrder(order)
            print(str(candle.time) + " ACTIVATED Type: " + order.type + "/ P: " + str(order.price) + "/ SL: " + str(order.stop_loss) + "/ TP: " + str(order.take_profit))

            finalReport.append(str(candle.time) + ",ACTIVATED," +
                               order.type + "," + str(order.price) +
                               "," + str(order.stop_loss) + "," + str(order.take_profit) +
                               "," + str(order.support) + "," + str(order.resistence))
            return True

    return False

# ------REPORTS-------

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