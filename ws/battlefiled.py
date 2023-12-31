from enum import Enum
from threading import Timer
from utils import is_socket_exist_and_connected,debug, send_msg_with_debug
import time
import asyncio
from protocol import WS_message, WS_response

ATTACK_CHECK_INTERVAL = 3000 # in ms
SHIELD_INTERVAL = 1000

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
        self.hp = 100

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
        add_buffer_task = asyncio.create_task(self.add_gesture_buffer(player,gesture_type))
     

# By Lechen: parse speech
    async def parse_speech(self, username:str, speech_type:str):
        player = self.get_player(username)
        enemy = self.get_enemy(username)

        debug("Received speech %s from user %s"%(speech_type, player.username))

        if speech_type == "RELEASE":
            await self.release(player, enemy, speech_type)
        elif speech_type == "CANCEL":
            await self.clear_gesture_buffer(player)  
        elif speech_type == "MENU":
            await self.invoke_menu(player)

    
        
    async def game_start(self):
        username0 = list(self.players.keys())[0]
        username1 = list(self.players.keys())[1]
        
        game_start_message = {"source":"ws_server", "action":"GameStart", "args":{"username0":username0,"username1":username1},"code":0}
        await self.broadcast_delay(message=str(game_start_message))
    
    async def release(self, player:Player, enemy:Player, gesture_type:str):
        
        '''
            Closed_Fist -> Light attack
            Closed_Fist + Open_Palm -> Heavy attack
            Victory -> Light shield
            Thumb_Up + ILoveYou -> Heavy shield
        '''
        if player.status != PStatus.NORMAL:
            debug("player %s is in status: %d, cannot release anything!"%(player.username,player.status.value))
            return
        recent_gesture = ("NULL", "NULL")

        if(len(player.gesture_buffer) == 0):
            pass
        elif(len(player.gesture_buffer) == 1):
            recent_gesture = ("NULL", player.gesture_buffer[-1])
        else:
            recent_gesture = (player.gesture_buffer[-2], player.gesture_buffer[-1])

        debug("When release, %s's recent gestures are: %s, %s."%(player.username, recent_gesture[0], recent_gesture[1]))

        # Light attack
        if(recent_gesture[1] == "Closed_Fist"):
            asyncio.create_task(self.light_attack(player))
            asyncio.create_task(self.clear_gesture_buffer(player))
            results_check_task = asyncio.create_task(self.attack_result_check(player,enemy,False,ATTACK_CHECK_INTERVAL))
        # Heavy attack
        elif(recent_gesture == ("Closed_Fist", "Open_Palm")):
            asyncio.create_task(self.clear_gesture_buffer(player))
            asyncio.create_task(self.heavy_attack(player))
            results_check_task = asyncio.create_task(self.attack_result_check(player,enemy,True, ATTACK_CHECK_INTERVAL))
        # Light shield
        elif(recent_gesture[1] == "Victory"):
            asyncio.create_task(self.clear_gesture_buffer(player))
            asyncio.create_task(self.light_shield(player))
        # Heavy shield
        elif(recent_gesture == ("Thumb_Up", "ILoveYou")):
            asyncio.create_task(self.clear_gesture_buffer(player))
            asyncio.create_task(self.heavy_shield(player))
        # TODO: Release failed
        else:
            debug("%s's Release Failed!"%(player.username))


    async def light_shield(self, player:Player):
        #add_buffer_task = asyncio.create_task(self.add_gesture_buffer(player,gesture_type))
        debug("%s released a light shield!"%(player.username))
        change_status_task = asyncio.create_task(self.change_player_status(player=player, status=PStatus.LIGHT_SHIELD))
        change_status_task = asyncio.create_task(self.change_player_status(player=player, status=PStatus.NORMAL, time_out= SHIELD_INTERVAL))
    
    async def heavy_shield(self, player:Player):
        debug("%s released a heavy shield!"%(player.username))
        change_status_task = asyncio.create_task(self.change_player_status(player=player, status=PStatus.HEAVY_SHIELD))
        change_status_task = asyncio.create_task(self.change_player_status(player=player, status=PStatus.NORMAL, time_out= SHIELD_INTERVAL))

    async def add_gesture_buffer(self, player:Player, gesture_type:str):
        debug("add gesture: %s to %s's buffer"%(gesture_type, player.username))
        player.gesture_buffer.append(gesture_type)
        add_buffer_message = {"source":player.username, "action":"AddGestureBuffer","args":{"gesture_type":gesture_type},"code":0}
        await self.broadcast_delay(str(add_buffer_message))

    async def clear_gesture_buffer(self, player:Player):
        debug("clear %s's buffer"%(player.username))
        player.gesture_buffer = []
        clear_buffer_message = {"source":player.username, "action":"ClearGestureBuffer","args":{},"code":0}
        await self.broadcast_delay(str(clear_buffer_message))

    async def invoke_menu(self, player:Player):
        debug("player: %s invokes menu"%player.username)
        invoke_menu_message = WS_response(source=player.username, action="InvokeMenu")
        await self.broadcast_delay(str(invoke_menu_message))

    async def light_attack(self,player:Player):
        debug("%s released a light attack!"%(player.username))
        light_attack_message = {
            "source":player.username, 
            "action":"ReleaseSkill",
            "args":{"skill":"LIGHT_ATTACK"},
            "code":0
            }
        await self.broadcast_delay(str(light_attack_message))
    
    async def heavy_attack(self,player:Player):
        debug("%s released a heavy attack!"%(player.username))
        heavy_attack_message = {
            "source":player.username, 
            "action":"ReleaseSkill",
            "args":{"skill":"HEAVY_ATTACK"},
            "code":0
            }
        await self.broadcast_delay(str(heavy_attack_message))

    async def change_player_status(self, player:Player, status:PStatus, time_out:int=0):
        await asyncio.sleep(time_out / 1000)
        debug("player %s change status to %d"%(player.username,status.value))
        player.status = status # change player's status in server
        
        skill = "LIGHT_SHIELD"
        if status == PStatus.HEAVY_SHIELD:
            skill = "HEAVY_SHIELD"
        elif status == PStatus.LIGHT_SHIELD:
            skill = "LIGHT_SHIELD"
        elif status == PStatus.NORMAL:
            skill = "BACK_NORMAL"
            
        change_status_message = {
            "source":player.username, 
            "action":"ReleaseSkill",
            "args":{"skill":skill},
            "code":0
        }
        
        await self.broadcast_delay(str(change_status_message))


    async def attack_result_check(self, player:Player,enemy:Player, is_heavy:bool, time_out:int = 0):
        await asyncio.sleep(time_out / 1000)
        debug("check enemy %s's status: %d"%(enemy.username,enemy.status.value))
        attack_result_message = {"source":enemy.username, "action":"","args":{},"code":0}
        if not is_heavy:
            if enemy.status == PStatus.LIGHT_SHIELD:
                attack_result_message["action"] = "DefendSuccess"
                attack_result_message["args"]["skill"] = "LIGHT_SHIELD"
            elif enemy.status == PStatus.HEAVY_SHIELD:
                attack_result_message["action"] = "DefendSuccess"
                attack_result_message["args"]["skill"] = "HEAVY_SHIELD"
            else:
                attack_result_message["action"] = "ChangeHP"
                attack_result_message["args"]["value"] = -10
                enemy.hp -= 10
        if is_heavy:
            if enemy.status == PStatus.HEAVY_SHIELD:
                attack_result_message["action"] = "DefendSuccess"
                attack_result_message["args"]["skill"] = "HEAVY_SHIELD"
            else:
                attack_result_message['action'] = "ChangeHP"
                attack_result_message["args"]["value"] = -20
                enemy.hp -= 20
        asyncio.create_task(self.game_over_check(player,enemy))

        await self.broadcast_delay(str(attack_result_message))

    async def game_over_check(self, player:Player, enemy:Player):
        if enemy.hp <= 0:
            game_over_message = WS_response(source=enemy.username, action="GameOver",args={
                "winner":player.username,
                "loser":enemy.username
                })
            await self.broadcast_delay(str(game_over_message))

    

    
    
    
