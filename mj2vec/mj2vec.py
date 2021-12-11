"""
 mj2vec
"""
import json
import argparse
import numpy as np
import dataclasses
import re
from enum import IntEnum, auto
from collections import OrderedDict

from mjlegal.game_state import GameState
from mjlegal.player_state import PlayerState
from mjlegal.possible_action import PossibleActionGenerator
from mjlegal.mjai import MjaiLoader
from mjlegal.mjtypes import Tile, TilesUtil
from mjlegal.mjtypes import ActionType
from mjlegal.action import Action
# from mjlegal.mjai_possible_action import MjaiPossibleActionGenerator

def feature_count_to_offset(counts : OrderedDict, initial_offset = 0) :
    offsets = {}
    offset = initial_offset
    for key, count in counts.items() :
        offsets[key] = count + offset
        offset += count
    return offsets

SPARSE_FEATURE_COUNT = OrderedDict([
    ("style", 2),
    ("seat"  , 3),
    ("bakaze" , 3),
    ("kyoku" , 3),
    ("honba" , 4),
    ("kyotaku" , 3),
    ("dora_0" , 37),
    ("dora_1" , 37),
    ("dora_2" , 37),
    ("dora_3" , 37),
    ("dora_4" , 37),
    ("rank"   , 3),
    ("hand"   , 136),
    ("tsumo_tile" , 37)
])

SPARSE_FEATURE_OFFSET = feature_count_to_offset(SPARSE_FEATURE_COUNT)

PROGRESSION_FEATURE_COUNT_ = OrderedDict([
    ("dahai_tsumogiri", 2),
    ("dahai_tedasi"  , 3),
    ("reach" , 3),
    ("pon" , 3),
    ("daiminkan" , 4),
    ("ankan" , 3),
    ("kakan" , 37),
    ("nukidora" , 37),
])
class ProgressionElem(IntEnum) :
    BEGIN           = 0
    DAHAI_TSUMOGIRI = auto()
    DAHAI_TEDASI    = auto()
    REACH           = auto()
    PON             = auto()
    DAIMINKAN       = auto()
    ANKAN           = auto()
    KAKAN           = auto()
    NUKI            = auto()

PROGRESSION_FEATURE_COUNT = [
    1,  # BEGIN
    37, # DAHAI_TSUMOGIRI
    37, # DAHAI_TEDASI
    1,  # REACH
    37, # PON
    34, # DAIMINKAN
    34, # ANKAN
    34, # KAKAN
    1,  # NUKI
]
PROGRESSION_FEATURE_OFFSETS = np.insert(np.cumsum(PROGRESSION_FEATURE_COUNT), 0, 0)
PROGRESSION_FEATURE_PLAYER_OFFSET = PROGRESSION_FEATURE_OFFSETS[-1]

@dataclasses.dataclass
class Elem :
    value : int = 0 # TODO assertion value < size
    size  : int = -1

    def updateValue(self, value) :
        self.value = min(value, self.size - 1)

    @staticmethod
    def createElem(value, size) :
        return Elem(value = min(value, size - 1), size = size)

    @staticmethod
    def createElemTile37(mjai_pai_str : str) :
        tile37 = mjai_pai_to_tile37(mjai_pai_str)
        return Elem(value = tile37, size = 37)

@dataclasses.dataclass
class PlayerElem :
    hand : list
    tsumo : Elem

@dataclasses.dataclass
class GameElem :
    style   : int = -1
    kyotaku : int = -1
    kyoku   : int = -1
    honba   : int = -1
    bakaze  : int = -1
    dora_markers : list = None

TILE37_SUIT_OFFSET_TABLE = {"m" : 0, "p" : 10, "s" : 20, "z" : 29 }
TILE37_LOOKUP_MJAI_PAI_NAME_TABLE = {'5mr': '0m', '5pr': '0p', '5sr': '0s', 'E': '1z', 'S': '2z', 'W': '3z', 'N': '4z', 'P': '5z', 'F': '6z', 'C': '7z'}

def mjai_pai_to_tile37(mjai_str) :
    tile_str = TILE37_LOOKUP_MJAI_PAI_NAME_TABLE[mjai_str] if mjai_str in TILE37_LOOKUP_MJAI_PAI_NAME_TABLE else mjai_str
    assert len(tile_str) == 2

    num = int(tile_str[0])
    suit = tile_str[1]
    assert not("z" == suit and (num < 1 or 7 < num) )

    offset = TILE37_SUIT_OFFSET_TABLE[suit]
    tile37 = offset + num
    return tile37

def mjai_pai_to_tile34(pai) :
    return TilesUtil.tiles_to_tiles34([Tile.from_str(pai)])[0]

def load_mjai_records(filename) :
    records = []
    log_input_file = open(filename, 'r', encoding="utf-8")
    for line in log_input_file :
        mjai_ev = json.loads(line)
        records.append(mjai_ev)
    log_input_file.close()
    return records

def game_state_to_feature(game_state : GameState, player_id) :
    player_state = game_state.player_states[player_id]
    tiles = player_state.tiles
    tiles136 = TilesUtil.tiles_to_tiles136(tiles)
    tsumo_tile = player_state.tsumo_tile
    tsumo_tile37 = None
    if tsumo_tile :
        tsumo_tile37 = tsumo_tile
    return tiles136, tsumo_tile37

class Progression2Vec :
    def __init__(self, player_id) :
        self.player_id = player_id
        
    def to_rel_seat(self, id) :
        return ((id - self.player_id + 3) % 3)

    # actor : abs id
    def feature_num(self, type:ProgressionElem, actor, num = 0) :
        assert num < PROGRESSION_FEATURE_COUNT[type], f"invalid num (type={type}, num={num})" 
        offset = PROGRESSION_FEATURE_OFFSETS[type]
        rel_actor_id = self.to_rel_seat(actor)
        return (num + offset) + (PROGRESSION_FEATURE_PLAYER_OFFSET)* rel_actor_id

    def action(self, record) :
        action_type = record["type"]
        if action_type == "start_kyoku" :
            self.progression = [Elem(1,1)] # Begging of the round
        elif "actor" in record :
            actor_id = record["actor"]
            if action_type == "tsumo" :
                pass
            elif action_type == "dahai" :
                pai = record["pai"]
                tsumogiri = record["tsumogiri"]
                self.dahai(actor_id, pai, tsumogiri)
            elif action_type == "reach" :
                self.reach(actor_id)
            elif action_type == "pon" :
                pai = record["pai"]
                # target = record["target"]
                consumed = record["consumed"]
                self.pon(actor_id, pai, consumed)
            elif action_type == "daiminkan" :
                pai = record["pai"]
                # target = record["target"]
                consumed = record["consumed"]
                self.daiminkan(actor_id, pai)
            elif action_type == "kakan" :
                pai = record["pai"]
                self.kakan(actor_id, pai)
            elif action_type == "ankan" :
                consumed = record["consumed"]
                self.ankan(actor_id, consumed)
            elif action_type == "nukidora" :
                # pai = record["pai"]
                self.nukidora(actor_id)

    def dahai(self, actor, pai, tsumogiri) :
        tile37 = mjai_pai_to_tile37(pai)
        progression_type = ProgressionElem.DAHAI_TSUMOGIRI if tsumogiri else ProgressionElem.DAHAI_TEDASI
        num = self.feature_num(progression_type, actor, tile37)
        self.progression.append(num)

    def reach(self, actor) :
        num = self.feature_num(ProgressionElem.REACH, actor, 0)
        self.progression.append(num)
    
    def pon(self, actor, pai, consumed) :
        pai_list = [pai] + consumed
        tile37_list = [mjai_pai_to_tile37(pai) for pai in pai_list]
        tile37 = min(tile37_list) # 赤ドラを含む場合は赤ドラ牌を選出する
        num = self.feature_num(ProgressionElem.PON, actor, tile37)
        self.progression.append(num)
    
    def daiminkan(self, actor, pai) :
        tile34 = mjai_pai_to_tile34(pai)
        num = self.feature_num(ProgressionElem.DAIMINKAN, actor, tile34)
        self.progression.append(num)
    
    def ankan(self, actor, consumed) :
        pai = consumed[0]
        tile34 = mjai_pai_to_tile34(pai)
        num = self.feature_num(ProgressionElem.ANKAN, actor, tile34)
        self.progression.append(num)
    
    def kakan(self, actor, pai) :
        tile34 = mjai_pai_to_tile34(pai)
        num = self.feature_num(ProgressionElem.KAKAN, actor, tile34)
        self.progression.append(num)

    def nukidora(self, actor) :
        num = self.feature_num(ProgressionElem.NUKI, actor, 0)
        self.progression.append(num)

class Players2Vec :
    def __init__(self) :
        self.players_progress = [] 

    def action(self, record) :
        action_type = record["type"]
        if action_type == "start_kyoku" :
            self.players_progress = [Progression2Vec(i) for i in range(3)]
        if len(self.players_progress) == 0 :
            return
        for progress in self.players_progress :
            progress.action(record)

    def progression(self, player_id) :
        return self.players_progress[player_id].progression

class Sparse2Vec :
    def __init__(self) :
        self.players = None
        self.game_elem = None
    def action(self, record) :
        action_type = record["type"]
        if action_type == "start_game" :
            self.game_elem = GameElem()
            self.setup_game_style(record)
        elif action_type == "start_kyoku" :
            self.setup_kyoku(record)
            self.setup_kyotaku(record)
            self.setup_honba(record)
            self.setup_bakaze(record)
            self.setup_dora_markers(record)
    
    def setup_game_style(self, start_game_record) :
        assert "start_game" == start_game_record["type"], "record type must be start_game."
        game_type = 1 # 東風(0), 半荘(1)
        if "uri" in start_game_record :
            uri = start_game_record["uri"]
            m = re.search("log=\d{10}gm-([0-9a-f]{4})-",uri)
            if "00b1" == m.group(1) :
                game_type = 0
        self.game_elem.style = Elem(value = game_type, size = 2)

    def setup_kyotaku(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        kyotaku = record["kyotaku"]
        self.game_elem.kyotaku = Elem.createElem(value = kyotaku, size = 3)

    def setup_kyoku(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        kyoku = record["kyoku"]
        self.game_elem.kyoku = Elem(value = kyoku, size = 3)

    def setup_honba(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        honba = record["honba"]
        self.game_elem.honba = Elem.createElem(value = honba, size = 4)

    def setup_bakaze(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        bakaze_str = record["bakaze"]
        bakaze = "ESW".index(bakaze_str)
        self.game_elem.bakaze = Elem(value = bakaze, size = 3)

    def setup_dora_markers(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        dora_marker = record["dora_marker"]
        self.game_elem.dora_markers = [Elem.createElemTile37(dora_marker)]

    def dump(self) :
        return self.game_elem

class Mj2Vec :
    def __init__(self) :
        self.mjlegal_client = MjaiLoader()
        self.sparse2vec = Sparse2Vec()
        self.players2vec = Players2Vec()
        self.possible_action_generator = PossibleActionGenerator()

    def action(self, record) :
        self.mjlegal_client.action(record)
        self.sparse2vec.action(record)
        self.players2vec.action(record)

        # possible action


def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filename")
    args = parser.parse_args()
    
    filename = args.mjson_filename
    
    mj2vec = Mj2Vec()
    records = load_mjai_records(filename)
    for record in records :
        mj2vec.action(record)
    print("dump:", mj2vec.sparse2vec.dump())

if __name__ == '__main__':
    main()
