import asyncio
import websockets
import json

async def exchange_client():
    uri = "ws://localhost:8765"  # Адреса вашого серверу веб-сокетів

    async with websockets.connect(uri) as websocket:
        while True:
            command = input("Введіть команду ('exchange X' або 'quit'): ")
            if command == "quit":
                break
            await websocket.send(command)

            response = await websocket.recv()
            print(f"Отримано від сервера: {response}")

async def main():
    await exchange_client()

if __name__ == "__main__":
    asyncio.run(main())
