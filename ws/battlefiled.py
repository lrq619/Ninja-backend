from enum import Enum
from threading import Timer
from utils import is_socket_exist_and_connected,debug, send_msg_with_debug
import time
import asyncio

ATTACK_CHECK_INTERVAL = 10000 # in ms

class PStatus(Enum):
    NORMAL = 0
    LIGHT_SHIELD = 1
    HEAVY_SHIELD = 2

class Player:
    def __init__(self, username:str="", pstatus:PStatus=PStatus.NORMAL, websocket=None) -> None:
        self.username:str = username
        self.status:PStatus = pstatus
        self.websocket = websocket
        self.gesture_buffer = []

    def light_shield(self, time_out=0): # time_out in milliseconds
        time.sleep(float(time_out/1000))
        self.status = PStatus.LIGHT_SHIELD

    def heavy_shield(self, time_out=0):
        time.sleep(float(time_out/1000))
        self.status = PStatus.HEAVY_SHIELD

    def back_normal(self, time_out=0):
        time.sleep(float(time_out/1000))
        self.status = PStatus.NORMAL

class BattleField:
    def __init__(self, room_id:int=-1) -> None:
        self.room_id = room_id
        self.players :dict[str,Player] = {}
        self.in_play_num = 0
        
    async def broadcast_delay(self, message:str, time_out:int = 0): # time_out is milliseconds
        await asyncio.sleep(time_out / 1000)
        for u in self.players:
            player = self.players[u]
            if is_socket_exist_and_connected(player.websocket):
                await send_msg_with_debug(player.websocket, message=message)
                # await player.websocket.send(message)

    def get_player(self,username):
        return self.players.get(username)
    def get_enemy(self,username): #username is yourself, this will return the player != username
        for u in self.players:
            if username != u:
                return self.players[u]
            
    def add_player(self, username, websocket):
        self.players[username] = Player(username=username,websocket=websocket) 
        self.in_play_num += 1


    async def parse_gestures(self, username:str, gesture_type:str):
        player = self.get_player(username)
        enemy = self.get_enemy(username)

        # By Lechen: Add buffer behavior
        player.gesture_buffer.append(gesture_type)
        add_buffer_task = asyncio.create_task(self.add_gesture_buffer(player,gesture_type))

        if gesture_type == "ILoveYou":
            await self.attack(player, enemy, gesture_type)
        elif gesture_type == "Thumb_Up":
            await self.light_shield(player, gesture_type)
        pass   

# By Lechen: parse speech
    async def parse_speech(self, username:str, speech_type:str):
        player = self.get_player(username)
        enemy = self.get_enemy(username)

        if speech_type == "ILoveYou":
            await self.attack(player, enemy, speech_type)
        #elif gesture_type == "Thumb_Up":
        #    await self.light_shield(player, gesture_type)
        #pass   

    
        
    async def game_start(self):
        username0 = list(self.players.keys())[0]
        username1 = list(self.players.keys())[1]
        game_start_message = {"source":"ws_server", "action":"GameStart", "args":{"username0":username0,"username1":username1},"code":0}
        await self.broadcast_delay(message=str(game_start_message))
    
    async def attack(self, player:Player, enemy:Player, gesture_type:str):
        #add_buffer_task = asyncio.create_task(self.add_gesture_buffer(player,gesture_type))
        light_attack_task = asyncio.create_task(self.light_attack(player))
        results_check_task = asyncio.create_task(self.attack_result_check(player,enemy,ATTACK_CHECK_INTERVAL))

    async def light_shield(self, player:Player, gesture_type:str):
        #add_buffer_task = asyncio.create_task(self.add_gesture_buffer(player,gesture_type))
        change_status_task = asyncio.create_task(self.change_player_status(player=player, status=PStatus.LIGHT_SHIELD.value))
        

    async def add_gesture_buffer(self, player:Player, gesture_type:str):
        debug("add gesture: %s to %s's buffer"%(gesture_type, player.username))
        add_buffer_message = {"source":player.username, "action":"AddGestureBuffer","args":{"gesture_type":gesture_type},"code":0}
        await self.broadcast_delay(str(add_buffer_message))

    async def light_attack(self,player:Player):
        light_attack_message = {
            "source":player.username, 
            "action":"ReleaseSkill",
            "args":{"skill":"LIGHT_ATTACK"},
            "code":0
            }
        await self.broadcast_delay(str(light_attack_message))
    
    async def change_player_status(self, player:Player, status:PStatus, time_out:int=0):
        await asyncio.sleep(time_out / 1000)
        debug("player %s change status"%player.username)
        player.status = status # change player's status in server
        change_status_message = {
            "source":player.username, 
            "action":"ReleaseSkill",
            "args":{"skill":"LIGHT_SHIELD"},
            "code":0
        }
        await self.broadcast_delay(str(change_status_message))


    async def attack_result_check(self, player:Player, enemy:Player, time_out:int = 0):
        await asyncio.sleep(time_out / 1000)
        debug("check enemy %s's status"%enemy.username)
        attack_result_message = {"source":enemy.username, "action":"","args":{},"code":0}
        if enemy.status == PStatus.LIGHT_SHIELD:
            attack_result_message["action"] = "DefendSuccess"
            attack_result_message["args"]["skill"] = "LIGHT_SHIELD"
        elif enemy.status == PStatus.HEAVY_SHIELD:
            attack_result_message["action"] = "DefendSuccess"
            attack_result_message["args"]["skill"] = "HEAVY_SHIELD"
        else:
            attack_result_message["action"] = "ChangeHP"
            attack_result_message["args"]["value"] = -10
        await self.broadcast_delay(str(attack_result_message))
        

    

    
    
    
