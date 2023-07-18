import sys
import websockets

NULL_RESPONSE = "NULL"

def debug(input:str):
    print(input, file=sys.stderr)

def is_socket_exist_and_connected(websocket):
    if websocket:
        return websocket.state == websockets.protocol.State.OPEN
    
async def send_msg_with_debug(websocket,message):
    debug("Messages going! message: "+message)
    await websocket.send(message)



