import requests
import json

import GoogleSheets

from Data import fiats
from Data import headers, headersPaysend
from Data import namesPaysend, idsPaysend


from time import sleep


def count_number(fiat):
    page = 1
    data = {
        "asset": "USDT",
        "countries": [],
        "fiat": fiat,
        "merchantCheck": False,
        "page": None,
        "payTypes": [],
        "publisherType": None,
        "rows": 10,
        "tradeType": "BUY",
    }
    try:
        while True:
            data["page"] = page
            r = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers, json=data)
            response = json.loads(r.text)
            if response["message"] == "Please check the input info":
                return page - 1
            elif len(response["data"]) == 0:
                return page - 1
            else:
                page += 1
    except:  # NOQA
        return 1


def collect_v():
    tr_quantity = []
    paysend = []

    for fiat in range(len(fiats)):
        try:
            max_page = count_number(fiats[fiat])
            tradable_quantity = 0
            for page in range(1, max_page + 1):
                data = {
                    "asset": "USDT",
                    "countries": [],
                    "fiat": fiats[fiat],
                    "merchantCheck": False,
                    "page": page,
                    "payTypes": [],
                    "publisherType": None,
                    "rows": 10,
                    "tradeType": "BUY",
                }

                r = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers,
                                  json=data, timeout=(10, 20))
                response = json.loads(r.text)

                for item in range(len(response["data"])):
                    tradable_quantity += float(response["data"][item]["adv"]["tradableQuantity"])
            tr_quantity.append([round(tradable_quantity, 3)])
        except:  # NOQA
            tr_quantity.append(["Нет предложений"])
            continue

        #if fiats[fiat] != "USD":
        #    try:
         #       link = f"https://paysend.com/api/en-lv/send-money/from-the-united-states-of-america-to-{str(namesPaysend[fiats[fiat]])}?fromCurrId=840&toCurrId={str(idsPaysend[namesPaysend[fiats[fiat]]])}&isFrom=true"
#
 #               response = requests.post(link, headers=headersPaysend)
  #              if response.status_code == 500:
   #                 paysend.append(["Недействительный ответ сервера"])
    #            print(response)
     #           response = json.loads(response.text)
      #          value = [str(response["commission"]["convertRate"]).replace('.', ',')]
       #         paysend.append(value)
        #        print(str(fiats[fiat]), 'convert rate', value)

         #       sleep(10)
          #  except Exception as ex:  # NOQA
           #     paysend.append(["Нет данных"])
            #    print(ex)
        #elif fiats[fiat] == "USD":
         #   paysend.append([1.000])



    writer = GoogleSheets.Writer()
    writer.write(f"I2:I{len(tr_quantity) + 1}", tr_quantity)
    writer.write(f"L2:L{len(paysend) + 1}", paysend)
