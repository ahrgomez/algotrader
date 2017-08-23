from dateutil import parser
import datetime

class HistoryService():
    historyData = []

    def AddDataToHistory(self, data):
        data.time = parser.parse(data.time)
        self.historyData.append(data)

    def AddArrayDataToHistory(self, arrayData):
        for data in arrayData:
            self.AddDataToHistory(data)

    def GetData(self, fromTime=None, toTime=None, count=None):

        result = self.historyData

        if fromTime is not None:
            if not isinstance(fromTime, datetime.date):
                fromTime = parser.parse(fromTime)
            result = [x for x in result if x.time >= fromTime]

        if toTime is not None:
            if not isinstance(toTime, datetime.date):
                toTime = parser.parse(toTime)
            result = [x for x in result if x.time <= toTime]

        if count is not None:
            result = result[count*-1:]

        return result

    def GetLastCandle(self):
        return self.historyData[-1:][0]