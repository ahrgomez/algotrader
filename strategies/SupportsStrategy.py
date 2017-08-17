from core import SupportsAndResistences
import numpy as np
from api.oanda import Candles
from dateutil import parser

class SupportsStrategy(object):

    supportsAndResistences = []
    data = []
    inCourseDate = None

    def __init__(self):
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

        if self.inCourseDate == None or candleDate.day != self.inCourseDate.day:
            self.data.append(self.getDayCandle(candleDate.year, candleDate.month, candleDate.day))
            srInstance = SupportsAndResistences.SupportsAndResistences()
            self.supportsAndResistences = srInstance.Calculate(self.data)
            self.inCourseDate = candleDate

        nearPosition = self.getNearPosition(candle.mid.l)
        nearResistence = self.supportsAndResistences[nearPosition]
        nearSupport = self.supportsAndResistences[nearPosition - 1]

        result = self.isPriceInUmbral(candle.mid.c, nearSupport, nearResistence)

        if result[0]:
            refutesCount = self.getSupportRefutesCountFrom(candle, nearSupport)
            if refutesCount > 2:
                return str(candleDate) + " BUY: " + "(" + str(nearSupport) + ", " + str(nearResistence) + ") --> " + str(candle.mid.c)
        elif result[1]:
            return None
        else:
            return None

    def getLast48CandlesFrom(self, candle):
        candlesApi = Candles()
        instrument = "EUR_USD"
        srKawrgs = {}
        srKawrgs['granularity'] = "H1"
        srKawrgs['count'] = 48
        srKawrgs['toTime'] = candle.time

        result = candlesApi.GetCandleSticks(instrument, **srKawrgs)
        result = [row for row in result if row.complete == True]

        return result

    def isPriceInUmbral(self, price, nearSupport, nearResistence):
        return np.isclose(price, [nearSupport, nearResistence,], atol=0.0005)

    def getNearPosition(self, price):
        return np.searchsorted(self.supportsAndResistences, [price, ], side='right')[0]

    def getSupportRefutesCountFrom(self, candle, nearSupport):
        last48Elements = self.getLast48CandlesFrom(candle)

        refutesCount = 0
        upFound = False
        for candle in last48Elements:
            if not upFound:
                if candle.mid.l > nearSupport:
                    upFound = True
            else:
                if candle.mid.l < nearSupport:
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
        instrument = "EUR_USD"
        srKawrgs = {}
        srKawrgs['granularity'] = "D"
        srKawrgs['count'] = 1
        srKawrgs['fromTime'] = fromTime

        result = candlesApi.GetCandleSticks(instrument, **srKawrgs)
        result = [row for row in result if row.complete == True]

        return result[0]