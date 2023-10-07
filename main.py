import platform
from datetime import datetime, timedelta
import logging
import argparse
import aiohttp
import asyncio

async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    r = await resp.json()
                    return r
                logging.error(f"Error status: {resp.status} for {url}")
                return None
        except aiohttp.ClientConnectorError as err:
            logging.error(f"Connection error: {str(err)}")
            return None

async def get_exchange(currency_code: str, days: int):
    today = datetime.now()
    exchange_rates = []

    for i in range(days):
        date = today - timedelta(days=i)
        formatted_date = date.strftime('%d.%m.%Y')
        result = await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={formatted_date}')

        if result:
            rates = result.get("exchangeRate")
            exc_eur, = list(filter(lambda element: element["currency"] == "EUR", rates))
            exc_usd, = list(filter(lambda element: element["currency"] == "USD", rates))

            exchange_rates.append({
                formatted_date: {
                    'EUR': {
                        'sale': exc_eur['saleRateNB'],
                        'purchase': exc_eur['purchaseRateNB']
                    },
                    'USD': {
                        'sale': exc_usd['saleRateNB'],
                        'purchase': exc_usd['purchaseRateNB']
                    }
                }
            })

    return exchange_rates

def main():
    parser = argparse.ArgumentParser(description='Get exchange rates from PrivatBank')
    parser.add_argument('days', type=int, help='Number of days to retrieve exchange rates (up to 10 days)')
    args = parser.parse_args()

    if args.days > 10 or args.days < 1:
        print("Error: Number of days should be between 1 and 10.")
        return

    logging.basicConfig(level=logging.ERROR)

    loop = asyncio.get_event_loop()
    exchange_rates = loop.run_until_complete(get_exchange("EUR", args.days))
    print(exchange_rates)


if __name__ == "__main__":
    main()
