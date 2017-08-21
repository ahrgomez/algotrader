
class Order():
    active = False
    date = None
    price = None
    type = None
    stop_loss = None
    take_profit = None
    instrument = None
    cancelled = False
    succedded = None
    support = None
    resistence = None

    def New(self, instrument, price, type, stop_loss, take_profit, support, resistence, date):

        self.instrument = instrument
        self.price = price
        self.type = type
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.support = support
        self.resistence = resistence
        self.date = date

        return self

class OrderService():

    orders = {}
    activatedOrders = {}
    successOrders = {}
    failedOrders = {}

    def InitInstrument(self, instrument):
        if instrument not in self.orders:
            self.orders[instrument] = []
            self.activatedOrders[instrument] = []
            self.successOrders[instrument] = []
            self.failedOrders[instrument] = []

    def GetActiveOrder(self, instrument):
        if len(self.activatedOrders[instrument]) == 0:
            return None
        else:
            return self.activatedOrders[instrument][0]

    def GetInactiveOrders(self, instrument):
        if len(self.orders[instrument]) == 0:
            return None
        else:
            return self.orders[instrument]

    def SaveOrder(self, instrument, price, type, stop_loss, take_profit, support, resistence, date):
        found = False
        for order in self.orders[instrument]:
            if order.type == type:
                found = True
                break
        if not found:
            self.orders[instrument].append(Order().New(instrument, price, type, stop_loss, take_profit, support, resistence, date))
            return True

        return False

    def ActivateOrder(self, order):
        order.active = True
        self.activatedOrders[order.instrument].append(order)
        self.orders[order.instrument] = []

    def DeactivateOrder(self, order, result):
        order.active = False
        order.succedded = (result == "SUCCESS")
        self.activatedOrders[order.instrument] = []
        if result == "SUCCESS":
            self.successOrders[order.instrument].append(order)
        else:
            self.failedOrders[order.instrument].append(order)

