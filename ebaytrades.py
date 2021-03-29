import market

import requests
import bs4 as bs
import csv
import sys

marketAPI = market.Market()
graphicsCardAvgPrices = []


# event loop like a true programmer
while True:
    cycleWeightedAvg = 0
    cycleWeightedSum = 0
    toCsv = []

    # loop over first three pages of ebay graphics card searches
    for i in range(1, 3):
        ebayUrl = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=graphics+card&_sacat=0&_pgn=" + str(i)
        req = requests.get(ebayUrl)
        data = req.text
        soup = bs.BeautifulSoup(data, features="lxml")

        # get all of the item groupboxes
        listings = soup.find_all('li', attrs={'class': 's-item'})

        # go over the listings and get the prices for each one that has a title
        for listing in listings:
            prodName = ""
            for name in listing.find_all('h3', attrs={'class': "s-item__title"}):
                if str(name.find(text=True, recursive=False)) != "None":
                    prodName = str(name.find(text=True, recursive=False))

            if prodName != "":
                priceString = str(listing.find('span', attrs={'class': "s-item__price"}))
                if '$' in priceString and '<' in priceString:
                    priceFixed = priceString.split('$')[1]
                    priceFixed = priceFixed.split('<')[0]
                    priceFixed = priceFixed.replace(',', "")
                    price = float(priceFixed)

                    # add to our temp values for this cycle
                    cycleWeightedSum = cycleWeightedSum + (1/float(i))
                    cycleWeightedAvg = cycleWeightedAvg + (price * (1 / float(i)))

    # calculate our new weighted average for this cycle
    cycleWeightedAvg = cycleWeightedAvg / cycleWeightedSum
    graphicsCardAvgPrices.append(cycleWeightedAvg)

    # see how our last three weighted averages compare to the previous 15 weighted average if we have 20
    if len(graphicsCardAvgPrices) >= 20:
        graphicsCardAvgPrices = graphicsCardAvgPrices[-20:]
        prevCardAvg = sum(graphicsCardAvgPrices[:15])/15
        recentCardAvg = sum(graphicsCardAvgPrices[-5:])/5

        # if a .15% increase, expect crypto to go up and set a buy order. clear prices so we dont buy again on this peak
        if recentCardAvg >= (prevCardAvg + (prevCardAvg * 0.015)):
            print(recentCardAvg, prevCardAvg, "BUY")
            marketAPI.buy_coin_possible("ETHUSD", 10)
            graphicsCardAvgPrices.clear()

    # log because I need those sweet graphs
    accountBalance = marketAPI.get_account_value()
    toCsv = [accountBalance]
    with open('account_data.csv', 'a', newline='') as file:
        writer = csv.writer(file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(toCsv)


    # for logging ethusd vs graphics card prices
    # lastTradePrice = marketAPI.get_symbol_price("ETHUSD")
    # toCsv = [cycleWeightedAvg, lastTradePrice]
    # with open('trend-data.csv', 'a', newline='') as file:
    #     writer = csv.writer(file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    #     writer.writerow(toCsv)


# while True:
#     marketAPI = market.Market()
#
#     marketAPI.buy_coin_possible("ETHUSD", 10)
#
