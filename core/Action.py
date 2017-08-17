
class Action():
    type = None
    lastMin = None
    lastMax = None
    support = None
    resistence = None
    date = None

    def New(self, type, lastMin, lastMax, support, resistence, date):

        self.type = type
        self.lastMin = lastMin
        self.lastMax = lastMax
        self.support = support
        self.resistence = resistence
        self.date = date

        return self