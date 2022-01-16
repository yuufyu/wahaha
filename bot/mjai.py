""" 
 mjai_bot.py

"""

import argparse
import json
import asyncio
from .client import Client

class MjaiBot :
    def __init__(self, model_path) :
        self.model_path = model_path
        self.client = Client(self.model_path)

    async def open(self, host, port) :
        self.host = host 
        self.port = port
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send(self, data) :
        send_str = json.dumps(data) + '\n'
        self.writer.write(send_str.encode())
        await self.writer.drain()

    async def receive(self) :
        data = await self.reader.readline()
        data_str = data.decode()
        receive_json = json.loads(data_str)
        return receive_json

    async def run(self) :
        while True :
            # Receive an event from mjai server
            event = await self.receive()
            print("<- ", event)

            # ai client
            self.client.update_state(event)
            move = self.client.choose_action()
            print("-> ", move)

            # Send a move to mjai server
            await self.send(move)

            # End of game
            if event["type"] == "end_game" :
                break

def parse_argument() :
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path")
    parser.add_argument("--host", type = str, default = "localhost")
    parser.add_argument("--port", type = int, default = 11600)
    args = parser.parse_args()
    return args

async def main() :
    args = parse_argument()
    mjai = MjaiBot(args.model_path)
    await mjai.open(host = args.host, port = args.port)
    await mjai.run()
    exit(0)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
    asyncio.get_event_loop().run_forever()
