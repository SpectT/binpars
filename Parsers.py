import requests
import json
import time
from bs4 import BeautifulSoup
from Data import headers as common_headers

from Data import fiats
from Data import headers
from Data import names
from datetime import date

import GoogleSheets

from time import sleep

MAX_RETRIES = 5  # Максимальное количество попыток
DELAY = 5  # Задержка между попытками (в секундах)
REQUEST_INTERVAL = 1  # Интервал между запросами (в секундах)

def parsers():
    fiats_range = []
    names_range = []
    middle_price_range = []
    nbank = [[""] for _ in range(100)]
    wise = []
    revolut = []
    transfer = []
    fin = []
    visa = []
    mastercard = []

    gbp_course = requests.get(
        "https://my.transfergo.com/api/transfers/quote?&calculationBase=sendAmount&amount=1000.00&fromCountryCode=GB&toCountryCode=US&fromCurrencyCode=GBP&toCurrencyCode=USD").text
    gbp_course = json.loads(gbp_course)
    gbp_course = gbp_course["deliveryOptions"]["standard"]["paymentOptions"]["card"]["quote"]["receivingAmount"]

    for fiat in range(len(fiats)):
        try:
            print(fiats[fiat])
            data = {
                "asset": "USDT",
                "countries": [],
                "fiat": fiats[fiat],
                "merchantCheck": False,
                "page": 1,
                "payTypes": [],
                "publisherType": None,
                "rows": 10,
                "tradeType": "BUY",
            }

            r = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers, json=data,
                              timeout=(10, 20))
            response = json.loads(r.text)

            amount = 0
            tradable_quantity = 0
            for item in range(len(response["data"])):
                amount += float(response["data"][item]["adv"]["price"])
                tradable_quantity += float(response["data"][item]["adv"]["tradableQuantity"])
            if len(response["data"]) == 0:
                amount = "Нет данных"
            else:
                amount = amount / len(response["data"])

            fiats_range.append([fiats[fiat]])
            names_range.append([names[fiat]])
            middle_price_range.append([amount])

            data = {"filter": [{"left": "name", "operation": "nempty"},
                               {"left": "name,description", "operation": "match", "right": "USD"}],
                    "options": {"lang": "ru"}, "markets": ["forex"],
                    "symbols": {"query": {"types": ["forex"]}, "tickers": []},
                    "columns": ["base_currency_logoid", "currency_logoid", "name", "close", "change", "change_abs",
                                "bid", "ask", "high", "low", "Recommend.All", "description", "type", "subtype",
                                "update_mode", "pricescale", "minmov", "fractional",
                                "minmove2"], "sort": {"sortBy": "name", "sortOrder": "asc"}, "range": [0, 150]}

            data["filter"][1]["right"] = f"USD{fiats[fiat]}"

            response = requests.post("https://scanner.tradingview.com/forex/scan", json=data)
            response = json.loads(response.text)
            try:
                nbank[fiats.index(response["data"][0]["s"][10:13])] = [response["data"][0]["d"][3]]
            except:  # NOQA
                pass

            if fiats[fiat] not in ["USD", "VES"]:
                try:
                    wise_val = requests.get(
                        f'https://wise.com/ru/currency-converter/usd-to-{fiats[fiat].lower()}-rate?amount=1',
                        headers=headers, timeout=(10, 20))
                    soup = BeautifulSoup(wise_val.text, 'lxml')
                    price = soup.find("span", "text-success").text
                    price = price[:price.find('.')] + "," + price[price.find('.') + 1:]
                    wise.append([price])
                except:  # NOQA
                    wise.append([""])
            elif fiats[fiat] == "USD":
                wise.append([1.000])
            else:
                wise.append([""])

            if fiats[fiat] != "USD":
                try:
                    revolut_json = json.loads(requests.get(
                        f'https://www.revolut.com/api/exchange/quote/?amount=1&country=GB&fromCurrency=USD&isRecipientAmount=false&toCurrency={fiats[fiat]}',
                        headers=headers).text)
                    revolut.append([revolut_json["rate"]["rate"]])
                except:  # NOQA
                    revolut.append([""])
            elif fiats[fiat] == "USD":
                revolut.append([1.000])

            if fiats[fiat] != "USD":
                try:
                    transfer_go = requests.get(
                        f"https://my.transfergo.com/api/transfers/quote?&calculationBase=sendAmount&amount=1000.00&fromCountryCode=GB&toCountryCode={str(fiats[fiat])[:2]}&fromCurrencyCode=GBP&toCurrencyCode={fiats[fiat]}",
                        headers=headers).text
                    transfer_go = json.loads(transfer_go)

                    transfer.append([
                        transfer_go["deliveryOptions"]["standard"]["paymentOptions"]["card"]["quote"][
                            "receivingAmount"] / gbp_course])
                except Exception as ex:  # NOQA
                    transfer.append(["Нет данных"])
            elif fiats[fiat] == "USD":
                transfer.append([1.000])

            if fiats[fiat] != "USD":
                
                fin_headers = common_headers.copy()
                fin_headers["Referer"] = "https://www.fin.do/"
                            
                for attempt in range(MAX_RETRIES):
                    try:
                        data = {
                            "amount": 1000,
                            "type": "SENDER",
                            "sender": {"sourceType": "CARD", "currency": "USD", "country": "GB"},
                            "receiver": {"sourceType": "CARD", "currency": str(fiats[fiat]), "country": "GB"}
                        }
                        fin_response = requests.post(f'https://api.fin.do/v1/api/fin/AssumeCommission', headers=fin_headers, json=data)
                        
                        # Если статус ответа 429, делаем паузу и пробуем снова
                        if fin_response.status_code == 429:
                            print("Too many requests. Retrying...")
                            time.sleep(DELAY)
                            continue
                            
                        fin_response_json = fin_response.json()  # Преобразование ответа в JSON формат
                        
                        # Проверка статуса ответа
                        if fin_response.status_code == 400 and "currency" in fin_response_json.get("message", "").lower():
                            raise ValueError(fin_response_json["message"])  # Прокинем ошибку для дальнейшего перехвата в except
                            
                        print(fin_response_json)
                        fin.append([fin_response_json["payload"]["receiver"]["amountToReceive"] / 1000])
                        break
                    except ValueError as ve:  # Отдельная обработка для временно отключенных валют
                        print(f"Currency {fiats[fiat]} is disabled: {ve}")
                        fin.append(["Валюта отключена"])
                        break
                    except json.JSONDecodeError:  # Обработка ошибки декодирования JSON
                        print(f"Error decoding response for fiat {fiats[fiat]}. Maybe empty response?")
                        fin.append(["Нет данных"])
                        break
                    except Exception as e:  # Используйте Exception для обработки всех других ошибок
                        print(f"Error for fiat {fiats[fiat]}: {e}")  # Вывести информацию об ошибке
                        fin.append(["Нет данных"])
                        break
                    
                    time.sleep(REQUEST_INTERVAL)  # Задержка между запросами
            elif fiats[fiat] == "USD":
                fin.append([1.000])

            if fiats[fiat] != "USD":
                sleep(1)
                
                #mastercard_headers = common_headers.copy()
                #mastercard_headers["Referer"] = "https://www.mastercard.com/global/en/personal/get-support/convert-currency.html"
                
                try:
                    mastercard_response = requests.get(
                        f"https://www.mastercard.com/settlement/currencyrate/conversion-rate?fxDate=0000-00-00&transCurr=USD&crdhldBillCurr={fiats[fiat]}&bankFee=0&transAmt=1",
                        headers=headers).text
                    print(mastercard_response)
                    mastercard_response = json.loads(mastercard_response)
                    mastercard.append([mastercard_response["data"]["conversionRate"]])
                except Exception as e:  
                    print(f"Error with MasterCard API: {e}")
                    mastercard.append(["Нет данных"])
            elif fiats[fiat] == "USD":
                mastercard.append([1.000])

            if fiats[fiat] != "USD":
                current_date = date.today()
                str_current_date = ""
                if len(str(current_date.month)) == 1:
                    str_current_date += "0"
                str_current_date += str(current_date.month) + "%2F"
                if len(str(current_date.day)) == 1:
                    str_current_date += "0"
                str_current_date += str(current_date.day) + "%2F" + str(current_date.year)
                
                # Создаем копию заголовков и добавляем referer
                visa_headers = common_headers.copy()
                visa_headers["referer"] = "https://usa.visa.com/"
                
                try:
                    visa_response = requests.get(
                        f"https://usa.visa.com/cmsapi/fx/rates?amount=1&fee=0&utcConvertedDate={str_current_date}&exchangedate={str_current_date}&fromCurr={fiats[fiat]}&toCurr=USD", 
                        headers=visa_headers).text
                    visa_response = json.loads(visa_response)
                    tmp = visa_response["convertedAmount"]
                    tmp = tmp.replace(',', '')
                    tmp = tmp.replace('.', ',')
                    visa.append([tmp])
                    # print("from visa: ", tmp, " " + str(fiats[fiat]))
                except Exception as ex:  # NOQA
                    print(ex)
                    visa.append(["Нет данных"])
            elif fiats[fiat] == "USD":
                visa.append([1.000])

        except Exception as ex:
            print(ex, "smth went wrong...")
            continue

    writer = GoogleSheets.Writer()
    writer.write(f"C2:C{len(middle_price_range) + 1}", middle_price_range)
    writer.write(f"D2:D{len(nbank) + 1}", nbank)
    writer.write(f"F2:F{len(wise) + 1}", wise)
    writer.write(f"G2:G{len(revolut) + 1}", revolut)
    writer.write(f"J2:J{len(fin) + 1}", fin)
    writer.write(f"K2:K{len(transfer) + 1}", transfer)
    writer.write(f"M2:M{len(visa) + 1}", visa)
    writer.write(f"N2:N{len(mastercard) + 1}", mastercard)
