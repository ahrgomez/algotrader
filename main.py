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
        addToReport(action.date, "ORDER", action.type, action.entryPoint, action.stopLoss, action.takeProfit, action.support, action.resistence)


def reviewOrder(orderService, order, candle):

    messageType = None

    if order.type == "BUY":
        if cross.candleTouchPrice(candle, order.take_profit):
            orderService.DeactivateOrder(order, " SUCCESS")
            messageType = "SUCCESS"
        elif cross.candleTouchPrice(candle, order.stop_loss):
            orderService.DeactivateOrder(order, " FAILED")
            messageType = "FAILED"
    elif order.type == "SELL":
        if cross.candleTouchPrice(candle, order.take_profit):
            orderService.DeactivateOrder(order, " SUCCESS")
            messageType = "SUCCESS"
        elif cross.candleTouchPrice(candle, order.stop_loss):
            orderService.DeactivateOrder(order, " FAILED")
            messageType = "FAILED"

    if messageType is not None:
        addToReport(candle.time, messageType, order.type, candle.mid.c, order.stop_loss, order.take_profit,
                    order.support, order.resistence, messageType=messageType)

def makeActiveOrderIfIsPossible(orderService, order, candle):
    if cross.candleTouchPrice(candle, order.price):
        if cross.candleTouchPrice(candle, order.price):
            orderService.ActivateOrder(order)
            addToReport(candle.time, "ACTIVATED", order.type, candle.mid.c, order.stop_loss, order.take_profit,
                        order.support, order.resistence, messageType="INFO")
            return True

    return False

# ------REPORTS-------

def addToReport(date, action, type, entryPoint, stopLoss, takeProfit, support, resistence, messageType = None):
    initColor = ""
    endColor = ""

    if messageType == "SUCCESS":
        initColor = '\033[94m'
        endColor = '\033[0m'
    elif messageType == "FAILED":
        initColor = '\033[91m'
        endColor = '\033[0m'
    elif messageType == "INFO":
        initColor = '\033[93m'
        endColor = '\033[0m'

    print(initColor + "Action: " + action + "/ Type: " + type + "/ D: " + str(date) +
          "/ P: " + str(entryPoint) + "/ SL: " + str(stopLoss) +
          "/ TP: " + str(takeProfit) + "/ S: " + str(support) +
          "/ R: " + str(resistence) + endColor)

    if messageType == "SUCCESS" or messageType == "FAILED":
        print("")

    finalReport.append(str(date) + "," + action + "," +
                       type + "," + str(entryPoint) +
                       "," + str(stopLoss) + "," + str(takeProfit) +
                       "," + str(support) + "," + str(resistence))
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