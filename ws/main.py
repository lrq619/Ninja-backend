import asyncio
from websockets.server import serve
import sys
sys.path.append("..") 
from config import WS_PORT
from ws.utils import debug, NULL_RESPONSE, send_msg_with_debug
from handlers import parse
import json

sockets = {}


async def handle(websocket):
    async for message in websocket:
        debug("Messages coming! message: %s"%message)
        username, handler, args = parse(message)
        if(username == None):
            debug("received message is invalid, message: %s"%message)
            return
        # add aditional parameters
        args['websocket'] = websocket
        
        response = await handler(username, args)
        if response != NULL_RESPONSE:
            await send_msg_with_debug(websocket, response)
            # await websocket.send(response)

async def main():
    async with serve(handle, "0.0.0.0", WS_PORT):
        debug("Listen to websocket request on port: %d"%WS_PORT)
        await asyncio.Future()  # run forever

asyncio.run(main())