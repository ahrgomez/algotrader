from core import SupportsAndResistences, Action
import numpy as np
from api.oanda import Candles
from dateutil import parser
from common import cross

class SupportsStrategy(object):

    historyService = None
    supportsAndResistences = []
    data = []
    inCourseDate = None
    lastLineCrossed = []
    instrument = None

    def __init__(self, instrument, historyService):
        self.instrument = instrument
        self.historyService = historyService
        pass

    def Initialize(self, data):
        # Calculate supports and resistences
        # ----------------------------------
        srInstance = SupportsAndResistences.SupportsAndResistences()
        self.data = data
        self.supportsAndResistences = srInstance.Calculate(self.data)
        # ----------------------------------

    def GetAction(self, candle):

        candleDate = parser.parse(candle.time)
        self.UpdateSupportsAndResistences(candle)

        nearSupport, nearResistence = self.getNearLines(candle.mid.l)
        result = self.isPriceInUmbral(candle.mid.c, nearSupport, nearResistence)

        line = None

        if result[0]:
            line = nearSupport
        elif result[1]:
            line = nearResistence

        if line is not None:

            lastCrossedLine, lastCrossPoint = self.getLastLineCrossedFrom(candle, line)

            if lastCrossPoint is None:
                return None

            pullBackExists, firstPullbackCrossPoint = self.getPullBack(lastCrossPoint, candle, line)

            if pullBackExists:
                pullbackPreviousCandle = self.historyService.GetData(toTime=firstPullbackCrossPoint.time, count=2)[0]
                lastCandle = self.historyService.GetLastCandle()
                entryPoint = None
                stopLoss = None
                takeProfit = None

                if lastCrossedLine > line:
                    type = "SELL"
                    entryPoint = lastCandle.mid.l
                    stopLoss = pullbackPreviousCandle.mid.h

                    auxSupport, auxResistence = self.getNearLines(entryPoint)
                    takeProfit = auxResistence - ((auxResistence - auxSupport) * 0.90)

                elif lastCrossedLine < line:
                    type = "BUY"
                    entryPoint = lastCandle.mid.h
                    stopLoss = pullbackPreviousCandle.mid.l

                    auxSupport, auxResistence = self.getNearLines(entryPoint)
                    takeProfit = auxSupport + ((auxResistence - auxSupport) * 0.90)

                else:
                    return None
                return Action.Action().New(type, entryPoint, stopLoss, takeProfit, nearSupport, nearResistence, candleDate)
            else:
                return None
        else:
            return None

    def getNearLines(self, price):
        nearPosition = self.getNearPosition(price)
        nearResistence = self.supportsAndResistences[nearPosition]
        nearSupport = self.supportsAndResistences[nearPosition - 1]

        return nearSupport, nearResistence

    def UpdateSupportsAndResistences(self, candle):
        candleDate = parser.parse(candle.time)

        if self.inCourseDate == None or candleDate.day != self.inCourseDate.day:
            self.data.append(self.getDayCandle(candleDate.year, candleDate.month, candleDate.day))
            srInstance = SupportsAndResistences.SupportsAndResistences()
            self.supportsAndResistences = srInstance.Calculate(self.data)
            self.inCourseDate = candleDate

    def isPriceInUmbral(self, price, nearSupport, nearResistence):
        return np.isclose(price, [nearSupport, nearResistence,], atol=0.0005)

    def getNearPosition(self, price):
        return np.searchsorted(self.supportsAndResistences, [price, ], side='right')[0]

    def getSupportRefutesFrom(self, lastCrossedCandle, candle, line):
        upRefutes = []
        downRefutes = []

        refutes, validRefutes = self.getLineRefutes(lastCrossedCandle, candle, line)

        for refute in refutes:
            if refute not in validRefutes:
                continue
            candleItem = refutes[refute][0]
            if candleItem.mid.h > nearSupport:
                upRefutes.append(refute)
            else:
                downRefutes.append(refute)

        return validRefutes, len(validRefutes), len(upRefutes), len(downRefutes)

    def getLineRefutes(self, lastCrossedCandle, candle, line):
        refutes = {}
        actualCross = None

        lastCandles = self.getCandlesInnerCandles(lastCrossedCandle, candle)

        for candleItem in lastCandles:
            if cross.priceInRange(line, candleItem.mid.h, candleItem.mid.l):
                actualCross = candleItem
                if actualCross not in refutes:
                    refutes[actualCross] = []
            else:
                if actualCross is not None:
                    refutes[actualCross].append(candleItem)



        validRefutes = [row for row in refutes if len(refutes[row]) > 5]

        return refutes, validRefutes

    def getPullBack(self, lastCrossedCandle, candle, line):
        validRefutes, validRefutesCount, upRefutesCount, downRefutesCount = self.getSupportRefutesFrom(lastCrossedCandle, candle, line)

        if validRefutesCount == 1:
            if lastCrossedCandle.mid.l > candle.mid.l:
                #BAJISTA
                if downRefutesCount == 1:
                    return True, validRefutes[0]
                    #PULLBACK
            else:
                #ALCISTA
                if upRefutesCount == 1:
                    return True, validRefutes[0]
                    #THROWBACK
        return False, None


    def getLastLineCrossedFrom(self, candle, actualline):

        candles = self.getCandlesFrom(candle)

        if candles is None:
            return None, None

        for i in range(len(candles) - 1, -1,-1):
            candle = candles[i]
            for line in [line for line in self.supportsAndResistences if actualline != line]:
                if cross.priceInRange(line, candle.mid.h, candle.mid.l):
                    return line, candle
        return None, None


    # -------Get Data---------

    def getCandlesFrom(self, candle):

        return self.historyService.GetData(toTime=candle.time)

    def getCandlesInnerCandles(self, candle1, candle2):

        return self.historyService.GetData(fromTime= candle1.time, toTime=candle2.time)

    def getDayCandle(self, year, month, day):
        if len(str(month)) == 1:
            month = "0" + str(month)

        if len(str(day)) == 1:
            day = "0" + str(day)

        fromTime = str(year) + "-" + str(month) + "-" + str(day) + "T00:00:00Z"

        candlesApi = Candles()
        instrument = self.instrument
        srKawrgs = {}
        srKawrgs['granularity'] = "D"
        srKawrgs['count'] = 1
        srKawrgs['fromTime'] = fromTime

        result = candlesApi.GetCandleSticks(instrument, **srKawrgs)
        result = [row for row in result if row.complete == True]

        return result[0]

    def getMinMaxFromLastCrossPoint(self, candle, lastCrossPoint):
        result = self.historyService.GetData(fromTime=lastCrossPoint.time, toTime=candle.time)

        lows = [row.mid.l for row in result if row.complete == True]
        highs = [row.mid.h for row in result if row.complete == True]

        return np.amin(lows), np.amax(highs)