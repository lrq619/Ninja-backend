from typing import Tuple, Callable
import json
from ws.utils import debug, NULL_RESPONSE, send_msg_with_debug
from ws.room import GAME_HALL
from protocol import WS_message, WS_response

def handshake(username:str, message_args:dict) -> str:
    debug("%s wants to establish handshake with ..."%username)
    return "Success!"

async def create_room(username:str, message_args:dict) -> str:
    response_args = {}
    response = WS_response(source=username, action='create_room', code=0)
    
    try:
        websocket = message_args['websocket']
        room_id = GAME_HALL.create_room(username, websocket0=websocket)
        response_args['room_id'] = room_id
        response.set_code(0)
        
    except:
        response.set_code(-1)

    response.set_args(response_args)
    
    return response.__str__()

async def join_room(username:str, message_args:dict) -> str:
    response_args = {}
    response = WS_response(source=username, action='join_room', code=0)
    # try:
    websocket = message_args['websocket']
    room_id = message_args['room_id']
    room = GAME_HALL.join_room(room_id, username, websocket)
    debug("user %s joined room %d"%(username,room_id))
    response_args["room_id"] = room_id
    if room != None:
        response.set_code(0)
        broadcast_args = {'owner':room.owner, 'guest':room.guest,'room_id':room.room_id}
        broadcast_response = WS_response(source="ws_server", action='ready',code=0, args=broadcast_args)
        await room.broadcast(str(broadcast_response))
    else:
        debug("Cannot find room with room_id: %d"%room_id)
        response.set_code(-1)
    response.set_args(response_args)
    return str(response)

async def post_gesture(username:str, message_args:dict) -> str:
    room = GAME_HALL.find_room_with_user(username)
    battlefiled = room.battlefiled
    gesture_type = message_args['gesture_type']
    if room != None:
        # broadcast_args = {'gesture_source':username,'gesture_type':gesture_type}
        # broadcast_response = WS_response(source="ws_server",action='post_gesture',code=0,args=broadcast_args)
        await battlefiled.parse_gestures(username, gesture_type=gesture_type)
        
        # await room.broadcast(str(broadcast_response))
    else:
        debug("Cannot find user %s's room"%username)
    return NULL_RESPONSE

async def quit_room(username:str, message_args:dict) -> str:
    room_id = message_args['room_id']
    room = GAME_HALL.find_room(room_id)
    if room != None:
        await room.quit(username)
        if room.room_num == 0:
            await GAME_HALL.delete_room(room_id)
        else:
            response = WS_response(source=username,action='quit_room',code=0,args={})
            if room.websocket0:
                await send_msg_with_debug(room.websocket0,str(response))
            else:
                await send_msg_with_debug(room.websocket1,str(response))
    else:
        debug("Cannot find room with room_id: %d"%room_id)
        return NULL_RESPONSE
    
    return NULL_RESPONSE

async def start_play(username:str, message_args:dict) -> str:
    response_args = {}
    response = WS_response(source=username, action='start_play', code=0)
    room_id = message_args['room_id']
    websocket = message_args['websocket']
    room = GAME_HALL.find_room(room_id)
    if room != None:
        await room.start_play(username,websocket)
        response_args['message'] = "username %s started play in room %d"%(username,room_id)
        response.set_args(response_args)
        return NULL_RESPONSE
    else:
        return NULL_RESPONSE



handler_dict = {
    'join_room':join_room,
    'create_room':create_room,
    'post_gesture':post_gesture,
    'quit_room':quit_room,
    'start_play':start_play,
}

def parse(message:str) -> Tuple[str, Callable[[str,dict],str], list[str]]:
    try:
        msg_json = json.loads(message)
        ws_message = WS_message()
        ws_message.fetch(msg_json)
        username, action, args = ws_message.decode()
        handler = handler_dict[action]
        return username, handler, args
    except:
        return None, None, None
    

