from binance.client import Client
from binance import exceptions
import time

apiKey = ""
apiSecret = ""

makerFee = .09
takerFee = .09


class Market:
    def __init__(self):
        self.client = Client(api_key=apiKey, api_secret=apiSecret, tld='us')

    def buy_coin_possible(self, symbol, percentOfEquity):
        # Get equity amount of our USD, BTC, ETH
        accountValue = float(self.client.get_asset_balance("USD")["free"])
        accountValue += float(self.client.get_asset_balance("BTC")["free"]) * float(self.client.get_symbol_ticker(symbol="BTCUSD")["price"])
        accountValue += float(self.client.get_asset_balance("ETH")["free"]) * float(self.client.get_symbol_ticker(symbol="ETHUSD")["price"])

        # calculate how much of the symbol that is
        moneyToSpend = percentOfEquity * accountValue / 100.0
        symbolQuantity = moneyToSpend / float(self.client.get_symbol_ticker(symbol=symbol)["price"])

        # get recent trades to see current volatility
        recentTrades = self.client.get_recent_trades(symbol=symbol)
        lastTrade = {}
        totalSum = 0
        weightedSum = 0
        for trade in recentTrades:
            if lastTrade == {} or int(trade["time"]) > int(lastTrade["time"]):
                lastTrade = trade
            totalSum += float(trade["qty"])
            weightedSum += float(trade["price"]) * float(trade["qty"])
        weightedAvg = weightedSum / totalSum

        # calculate the price we should strive for with current volatility
        symbolQtyAdjustedBefore = symbolQuantity * (1.0 - takerFee)
        symbolQtyAdjustedAfter = symbolQtyAdjustedBefore * (1.0 - takerFee)
        endProfitPrice = 0
        if weightedAvg > float(lastTrade["price"]):
            endProfitPrice = weightedAvg + (weightedAvg - float(lastTrade["price"])) * .5
        else:
            endProfitPrice = float(lastTrade["price"]) + abs(weightedAvg - float(lastTrade["price"])) * .5

        # calculate stop loss at 3 : 1 risk ratio using expected profit
        expectedProfit = (endProfitPrice * symbolQtyAdjustedAfter) - (float(lastTrade["price"]) * symbolQtyAdjustedAfter)
        if expectedProfit <= 0:
            return
        stopLossPrice = float(lastTrade["price"]) - expectedProfit * (1/3)
        # possibleLoss = (stopLossPrice * symbolQtyAdjusted) - (float(lastTrade["price"]) * symbolQtyAdjusted) # for reference

        # set the limit buy so we get it at the price we want hopefully
        order = None
        try:
            order = self.client.order_limit_buy(
                symbol=symbol,
                quantity="{:0.0{}f}".format(symbolQuantity, 3),
                price="{:0.0{}f}".format(float(lastTrade["price"]) + float(lastTrade["price"]) * .001, 2),
            )
        except exceptions.BinanceAPIException as e:
            print(e)
            return

        # wait 3 seconds.  usually small orders will go through immediately but if this scales it wouldn't
        time.sleep(5)

        # see if it went through at our price, otherwise cancel it
        if order is not None:
            for openOrder in self.client.get_open_orders():
                if order["orderId"] == openOrder["orderId"]:
                    self.client.cancel_order(symbol=symbol, orderId=order["orderId"])
                    return

        try:
            # set our end/expected price for this trade
            self.client.order_limit_sell(
                symbol=symbol,
                quantity="{:0.0{}f}".format(symbolQtyAdjustedBefore, 3),
                price="{:0.0{}f}".format(endProfitPrice, 2)
            )

            self.client.create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
                quantity="{:0.0{}f}".format(symbolQtyAdjustedBefore, 3),
                price="{:0.0{}f}".format(stopLossPrice, 2),
                stopPrice="{:0.0{}f}".format(stopLossPrice + .01, 2),
                timeInForce=Client.TIME_IN_FORCE_GTC
            )
        except exceptions.BinanceAPIException as e:
            print(e)
            return


    def get_symbol_price(self, symbol):
        recentTrades = self.client.get_recent_trades(symbol=symbol)
        lastTrade = {}

        for trade in recentTrades:
            if lastTrade == {} or int(trade["time"]) > int(lastTrade["time"]):
                lastTrade = trade

        return float(lastTrade["price"])

    def get_account_value(self):
        valueInUSD = 0.0
        usdBalance = self.client.get_asset_balance("USD")
        valueInUSD = valueInUSD + float(usdBalance["free"]) + float(usdBalance["locked"])
        time.sleep(.1)

        ethBalance = self.client.get_asset_balance("ETH")
        ethPrice = self.get_symbol_price("ETHUSD")
        valueInUSD = valueInUSD + float(ethBalance["free"]) * ethPrice + float(ethBalance["locked"]) * ethPrice
        time.sleep(.1)

        btcBalance = self.client.get_asset_balance("BTC")
        btcPrice = self.get_symbol_price("BTCUSD")
        valueInUSD = valueInUSD + float(btcBalance["free"]) * btcPrice + float(btcBalance["locked"]) * btcPrice
        time.sleep(.1)

        return valueInUSD





    










