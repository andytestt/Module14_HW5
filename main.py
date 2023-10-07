import platform
from datetime import datetime, timedelta
import logging
import argparse
import aiohttp
import asyncio
import websockets
import json
import aiofiles
from aiopath import AsyncPath

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

async def log_exchange(command, filename):
    async with aiofiles.open(filename, mode='a') as file:
        await file.write(f"{datetime.now()}: {command}\n")

async def exchange_handler(websocket, path):
    async for command in websocket:
        if command.startswith("exchange"):
            _, days_str = command.split()
            try:
                days = int(days_str)
                if days < 1 or days > 10:
                    await websocket.send("Error: Number of days should be between 1 and 10.")
                    continue
                exchange_rates = await get_exchange("EUR", days)
                await websocket.send(json.dumps(exchange_rates))
                await log_exchange(command, "exchange.log")
            except ValueError:
                await websocket.send("Error: Invalid number of days.")
        else:
            await websocket.send("Unknown command.")

def main():
    parser = argparse.ArgumentParser(description='Get exchange rates from PrivatBank')
    parser.add_argument('days', type=int, help='Number of days to retrieve exchange rates (up to 10 days)')
    parser.add_argument('--currencies', nargs='+', default=['EUR', 'USD'], help='Additional currencies to retrieve')
    args = parser.parse_args()

    if args.days > 10 or args.days < 1:
        print("Error: Number of days should be between 1 and 10.")
        return

    logging.basicConfig(level=logging.ERROR)

    loop = asyncio.get_event_loop()
    exchange_rates = loop.run_until_complete(get_exchange("EUR", args.days))
    print(exchange_rates)

    start_server = websockets.serve(exchange_handler, 'localhost', 8765)
    loop.run_until_complete(start_server)
    loop.run_forever()


if __name__ == "__main__":
    main()
