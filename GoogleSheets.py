import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials


class Writer:
    def __init__(self):
        self.service = None

        self.spreadsheet_id = '1s1iQV4ywYQbHsHOWOjOdQczpDiuBgbC6G4vKSZDpQnw'
        credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json',
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])

        httpauth = credentials.authorize(httplib2.Http())
        self.service = discovery.build('sheets', 'v4', http=httpauth)

        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": "Основа!A1:C2",
                     "majorDimension": "COLUMNS",
                     "values": [["Код валюты"], ["Название валюты"], ["Цена р2р Бинанс"]]
                     }
                ]
            }
        ).execute()

    def write_payment_types(self, ranged, data):
        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": "Оплата!" + ranged,
                     "majorDimension": "ROWS",
                     "values": data
                     }
                ]
            }
        ).execute()

    def write(self, ranged, data):
        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": "Основа!" + ranged,
                     "majorDimension": "ROWS",
                     "values": data
                     }
                ]
            }
        ).execute()
