from ws.utils import debug, is_socket_exist_and_connected, send_msg_with_debug
from battlefiled import BattleField, Player, PStatus
NULL_ROOM_ID = -1

class Room:
    def __init__(self, room_id = -1, owner='', guest='', websocket0=None, websocket1=None) -> None:
        self.room_id = room_id
        self.room_num = 0 # number of players in the room
        self.owner : str = owner
        self.guest : str = guest
        self.websocket0 = websocket0
        self.websocket1 = websocket1
        self.battlefiled : BattleField = BattleField(room_id=room_id)

    async def destroy(self):
        if is_socket_exist_and_connected(self.websocket0):
            await self.websocket0.close()
        if is_socket_exist_and_connected(self.websocket1):
            await self.websocket1.close()
        

    async def broadcast(self, message:str):
        if is_socket_exist_and_connected(self.websocket0):
            await send_msg_with_debug(self.websocket0, message)
        else:
            debug("user %s is disconnected"%self.owner)
        if is_socket_exist_and_connected(self.websocket1):
            await send_msg_with_debug(self.websocket1, message)
        else:
            debug("user %s is disconnected"%self.guest)

    def user_exists(self,username:str):
        return self.owner == username or self.guest == username
    
    async def quit(self,username:str):
        if not self.user_exists(username):
            debug("room %d does not have user %s"%(self.room_id,username))
        if username == self.owner:
            if is_socket_exist_and_connected(self.websocket0):
                await self.websocket0.close()
            self.owner = ""
            self.websocket0 = None
        else:
            if is_socket_exist_and_connected(self.websocket1):
                await self.websocket1.close()
            self.guest =  ""
            self.websocket1 = None
        self.room_num -= 1

    async def start_play(self, username:str, websocket):
        if username == self.owner:
            await self.websocket0.close()
            self.websocket0 = websocket
        elif username == self.guest:
            await self.websocket1.close()
            self.websocket1 = websocket
        else:
            debug("user: %s doesn't exist in room: %d"%(username,self.room_id))
        self.battlefiled.add_player(username,websocket)
        if self.battlefiled.in_play_num == 2:
            debug("Battle field created! Game start!")
            await self.battlefiled.game_start()
        





class Hall:
    def __init__(self) -> None:
        self.room_max_id : int = -1
        self.room_list : list[Room] = []
        self.user_room_dict = {}

    def find_room(self, room_id):
        for room in self.room_list:
            if room.room_id == room_id:
                return room
        return None

    def create_room(self, owner, websocket0):
        debug("Enter create room")
        self.room_max_id += 1
        room = Room(room_id=self.room_max_id, owner=owner,websocket0=websocket0)
        room.room_num = 1
        self.room_list.append(room)
        self.user_room_dict[owner] = room.room_id
        return room.room_id
    
    def owner_connect(self,room_id,websocket0):
        room = self.find_room(room_id)
        if room != None:
            room.websocket0 = websocket0
            debug("%s connected to room %d"%(room.owner, room.room_id))
        else:
            debug("Cannot connect to room %d"%(room_id))

    def guest_connect(self,room_id,websocket1):
        room = self.find_room(room_id)
        if room != None:
            room.websocket1 = websocket1
            debug("%s connected to room %d"%(room.guest, room.room_id))
        else:
            debug("Cannot connect to room %d"%(room_id))

    def quit_room(self, username):
        room = self.find_room_with_user(username)
        if room == None:
            debug("user %s is not in any room, cannot quit"%username)
            return False
        room.quit(username)
        self.user_room_dict.pop(username)
        return True

    async def delete_room(self, room_id):
        room = self.find_room(room_id)
        if room == None:
            debug("room_id: %d doesn't exist! Cannot delete it!"%room_id)
            return
        if room.room_num != 0:
            debug("room: %d still has %d members, cannot delete!"%(room_id,room.room_num))
            return
        self.room_list.remove(room)
        debug("room %d deleted!"%room_id)
        self.room_max_id = self.get_max_room_id()
        
        

    def join_room(self,room_id, guest, websocket1):
        room = self.find_room(room_id)
        if room == None:
            debug("room_id: %d doesn't exist!"%room_id)
            return None
        room.guest = guest
        room.websocket1 = websocket1
        room.room_num += 1
        self.user_room_dict[guest] = room.room_id
        return room
    
    def check_room_num(self,room_id):
        room = self.find_room(room_id)
        if room == None:
            return -1
        return room.room_num
    
    def find_room_with_user(self, username):
        room_id = self.user_room_dict.get(username)
        if room_id == NULL_ROOM_ID:
            return None
        return self.find_room(room_id)
    
    def get_max_room_id(self):
        max_id = -1
        for room in self.room_list:
            max_id = max(room.room_id, max_id)
        return max_id

    

# global game hall
GAME_HALL : Hall = Hall()