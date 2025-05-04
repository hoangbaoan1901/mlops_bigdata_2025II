import requests

url = "https://data.alpaca.markets/v2/stocks/bars/latest?symbols=AAPL&feed=iex&currency=USD"

headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": "PKRXUCDN0XDY4GR63ADC",
    "APCA-API-SECRET-KEY": "eN1SU1UpOToWZaKxH8f9d7KipzGUFeenLOPDqUkw"
}

response = requests.get(url, headers=headers)

print(response.text)