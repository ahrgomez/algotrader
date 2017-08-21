from core import SupportsAndResistences, Action
import numpy as np
from api.oanda import Candles
from dateutil import parser
from common import cross

class SupportsStrategy(object):

    supportsAndResistences = []
    data = []
    inCourseDate = None
    lastLineCrossed = []
    instrument = None

    def __init__(self, instrument):
        self.instrument = instrument
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

            pullBackExists = self.getPullBack(lastCrossPoint, candle, line)

            #refutesCount, upRefutesCount, downRefutesCount = self.getSupportRefutesCountFrom(lastCrossPoint, candle, line)

            if pullBackExists:
                min48, max48 = self.getMinMaxFromLastCrossPoint(candle, lastCrossPoint)
                if lastCrossedLine > line:
                    type = "SELL"
                    if min48 < nearSupport:
                        nearSupport, auxResistence = self.getNearLines(min48)
                elif lastCrossedLine < line:
                    type = "BUY"
                    if max48 > nearResistence:
                        auxSupport, nearResistence = self.getNearLines(max48)
                else:
                    return None
                return Action.Action().New(type, min48, max48, nearSupport, nearResistence, candleDate)
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

    def getLastNCandlesFrom(self, candle, candlesCount = 48):
        candlesApi = Candles()
        instrument = self.instrument
        srKawrgs = {}
        srKawrgs['granularity'] = "H1"
        srKawrgs['count'] = candlesCount
        srKawrgs['toTime'] = candle.time

        result = candlesApi.GetCandleSticks(instrument, **srKawrgs)
        result = [row for row in result if row.complete == True]

        return result

    def getMinMaxFromLast24CandlesFrom(self, candle):
        candlesApi = Candles()
        instrument = self.instrument
        srKawrgs = {}
        srKawrgs['granularity'] = "H1"
        srKawrgs['count'] = 24
        srKawrgs['toTime'] = candle.time

        result = candlesApi.GetCandleSticks(instrument, **srKawrgs)
        lows = [row.mid.l for row in result if row.complete == True]
        highs = [row.mid.h for row in result if row.complete == True]

        return np.amin(lows), np.amax(highs)

    def getMinMaxFromLastCrossPoint(self, candle, lastCrossPoint):
        candlesApi = Candles()
        instrument = self.instrument
        srKawrgs = {}
        srKawrgs['granularity'] = "H1"
        srKawrgs['fromTime'] = lastCrossPoint.time
        srKawrgs['toTime'] = candle.time

        result = candlesApi.GetCandleSticks(instrument, **srKawrgs)
        lows = [row.mid.l for row in result if row.complete == True]
        highs = [row.mid.h for row in result if row.complete == True]

        return np.amin(lows), np.amax(highs)

    def isPriceInUmbral(self, price, nearSupport, nearResistence):
        return np.isclose(price, [nearSupport, nearResistence,], atol=0.0005)

    def getNearPosition(self, price):
        return np.searchsorted(self.supportsAndResistences, [price, ], side='right')[0]

    def getSupportRefutesCountFrom(self, lastCrossedCandle, candle, nearSupport):
        upRefutes = []
        downRefutes = []

        refutes, validRefutes = self.getLineRefutes(lastCrossedCandle, candle, nearSupport)

        for refute in refutes:
            if refute not in validRefutes:
                continue
            candleItem = refutes[refute][0]
            if candleItem.mid.h > nearSupport:
                upRefutes.append(refute)
            else:
                downRefutes.append(refute)

        return len(validRefutes), len(upRefutes), len(downRefutes)


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
        validRefutesCount, upRefutesCount, downRefutesCount = self.getSupportRefutesCountFrom(lastCrossedCandle, candle, line)

        if validRefutesCount == 1:
            if lastCrossedCandle.mid.l > candle.mid.l:
                #BAJISTA
                if downRefutesCount == 1:
                    return True
                    #PULLBACK
            else:
                #ALCISTA
                if upRefutesCount == 1:
                    return True
                    #THROWBACK
        return False

    def getTendenciaFrom(self, candle):
        lastNElements = self.getLastNCandlesFrom(candle, 192)
        firstLow = lastNElements[0].mid.l
        actualLow = candle.mid.l
        tendencia = None

        if firstLow < actualLow:
            tendencia = "TOHIGH"
        else:
            tendencia = "TOLOW"

        return tendencia

    def anotherRefutesFuntion(self, candle, nearSupport):
        last48Elements = self.getLastNCandlesFrom(candle, 96)
        upFound = False
        for candleItem in last48Elements:
            if not upFound:
                if candleItem.mid.l > nearSupport and candleItem.mid.h > nearSupport:
                    upFound = True
            else:
                if candleItem.mid.l < nearSupport and candleItem.mid.h > nearSupport:
                    refutesCount = refutesCount + 1
                    upFound = False

        if refutesCount == 0:
            upFound = False
            for candleItem in last48Elements:
                if not upFound:
                    if candleItem.mid.h < nearSupport and candleItem.mid.l < nearSupport:
                        upFound = True
                else:
                    if candleItem.mid.h > nearSupport and candleItem.mid.l > nearSupport:
                        refutesCount = refutesCount + 1
                        upFound = False

        return refutesCount

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

    def getCandlesFrom(self, candle):
        candlesApi = Candles()
        instrument = self.instrument
        srKawrgs = {}
        srKawrgs['granularity'] = "H1"
        srKawrgs['toTime'] = candle.time

        result = candlesApi.GetCandleSticks(instrument, **srKawrgs)
        result = [row for row in result if row.complete == True]

        if result is None:
            print('puta')

        return result

    def getCandlesInnerCandles(self, candle1, candle2):
        candlesApi = Candles()
        instrument = self.instrument
        srKawrgs = {}
        srKawrgs['granularity'] = "H1"
        srKawrgs['fromTime'] = candle1.time
        srKawrgs['toTime'] = candle2.time

        result = candlesApi.GetCandleSticks(instrument, **srKawrgs)
        result = [row for row in result if row.complete == True]

        return result