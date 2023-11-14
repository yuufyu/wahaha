from .mjtypes import Tile

class GameState :
    
    def __init__(self) :
        self.reset()
        self.start_kyoku()

    def reset(self) :
        self.bakaze = "E"
        self.kyoku = 0
        self.honba = 0
        self.chicha = 0 # 常に0
        self.init_num_pipais = 108 - (14 + (13 * 3))# 三人麻雀 抜きドラありルール
        self.player_states = []
        self.player_id = -1 # player log

    def start_kyoku(self) :
        self.oya = 0
        self.num_pipais = self.init_num_pipais
        self.dora_markers = []
        self.previous_action = None

    def tsumo(self) :
        self.num_pipais = self.num_pipais - 1
        assert self.num_pipais >= 0, "pipai is empty."
        return Tile.from_str("?")

    @property
    def num_players(self) :
        return len(self.player_states)

    @property
    def scores(self) :
        return [player_state.score for player_state in self.player_states]
    
    @scores.setter
    def scores(self, scores) :
        self.set_scores(scores)

    def set_scores(self, scores) :
        assert len(scores) == len(self.player_states)
        for i, score in enumerate(scores) :
            self.player_states[i].score = score

    def set_delta_scores(self, delta_scores) :
        assert len(delta_scores) == len(self.player_states)
        for i, delta_score in enumerate(delta_scores) :
            self.player_states[i].score += delta_score

    @property
    def previous_player(self) :
        if self.previous_action :
            previous_player_id = self.previous_action.actor
            return self.player_states[previous_player_id]

    def player_wind(self, player_id) :
        winds = ["E", "S", "W", "N"]
        return winds[(player_id - self.oya + 3) % 3]

    
