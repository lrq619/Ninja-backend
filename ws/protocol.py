from ws.utils import debug
import json
class WS_message:
    def __init__(self) -> None:
        self.username = ''
        self.action = ''
        self.args = {}

    def fetch(self, json_obj):
        try:
            self.username = json_obj['username']
            self.action = json_obj['action']
            self.args = json_obj['args']
            return True
        except:
            debug("fetch from json failed!")
            return False

    def decode(self):
        return self.username, self.action, self.args

    

class WS_response:
    def __init__(self, source='', action='',code=0, args={}) -> None:
        self.source = source # username of message source
        self.action = action
        self.code = code # 0 on success, -1 on error
        self.args = args

    def set_args(self, args):
        self.args = args

    def set_code(self, code):
        self.code = code

    def __str__(self) -> str:
        json_obj = {}
        json_obj['source'] = self.source
        json_obj['action'] = self.action
        json_obj['code'] = self.code
        json_obj['args'] = self.args
        return json.dumps(json_obj)
        