from .mjai import MjaiLoader

class MjaiPlayerLoader :
    def __init__(self) :
        self.mjaiLoader = MjaiLoader()
        
    # <-
    def action_receive(self, action) :
        self.mjaiLoader.action(action)

        action_type = action["type"]
        if action_type == "start_game" :
            self.mjaiLoader.game.player_id = action["id"]

    # ->
    def action_send(self, action) :
        action_type = action["type"]
        if action_type == 'join' :
            pass
        elif action_type == 'none' :
            pass

    @property
    def game(self) :
        return self.mjaiLoader.game

