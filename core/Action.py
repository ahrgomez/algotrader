
class Action():
    type = None
    entryPoint = None
    stopLoss = None
    takeProfit = None
    support = None
    resistence = None
    date = None

    def New(self, type, entryPoint, stopLoss, takeProfit, support, resistence, date):

        self.type = type
        self.entryPoint = entryPoint
        self.stopLoss = stopLoss
        self.takeProfit = takeProfit
        self.support = support
        self.resistence = resistence
        self.date = date

        return self