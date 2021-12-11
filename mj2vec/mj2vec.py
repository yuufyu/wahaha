"""
 mj2vec
"""
import json
import argparse
import numpy as np
import dataclasses
import re

from mjlegal.game_state import GameState
from mjlegal.player_state import PlayerState
from mjlegal.possible_action import PossibleActionGenerator
from mjlegal.mjai import MjaiLoader
from mjlegal.mjtypes import Tile, TilesUtil
from mjlegal.mjtypes import ActionType
from mjlegal.action import Action
from mjlegal.mjai_possible_action import MjaiPossibleActionGenerator

@dataclasses.dataclass
class Elem :
    value : int = -1 # TODO assertion value < size
    size  : int = -1

    def updateValue(self, value) :
        self.value = min(value, self.size - 1)

    @staticmethod
    def createElem(value, size) :
        return Elem(value = min(value, size - 1), size = size)

@dataclasses.dataclass
class PlayerElem :
    hand : list
    tsumo : Elem

@dataclasses.dataclass
class GameElem :
    style   : Elem = None
    kyotaku : Elem = None
    kyoku   : Elem = None
    honba   : Elem = None
    bakaze  : Elem = None
    dora1 : Elem = None
    dora2 : Elem = None
    dora3 : Elem = None
    dora4 : Elem = None
    dora5 : Elem = None


TILE37_SUIT_OFFSET_TABLE = {"m" : 0, "p" : 10, "s" : 20, "z" : 29 }
def to_tile37(tile_str) :
    num = int(tile_str[0])
    suit = tile_str[1]
    #is_aka = (num == 0)
    offset = TILE37_SUIT_OFFSET_TABLE[suit]
    tile37 = offset + num
    assert len(tile_str) == 2
    assert not("z" == suit and (num < 1 or 7 < num) )
    return tile37

def load_mjai_records(filename) :
    records = []
    log_input_file = open(filename, 'r', encoding="utf-8")
    for line in log_input_file :
        mjai_ev = json.loads(line)
        records.append(mjai_ev)
    log_input_file.close()
    return records

class Player2Vec :
    def __init__(self, player_id) :
        self.player_id = player_id

    def action(self, record) :
        pass

class Mj2Vec :
    def __init__(self) :
        self.mjlegal_client = MjaiLoader()
        self.game_elem = GameElem()

    def action(self, record) :
        self.mjlegal_client.action(record)

        action_type = record["type"]
        if action_type == "start_game" :
            self.setup_game_style(record)
            self.setup_players(record)
        elif action_type == "start_kyoku" :
            self.setup_kyoku(record)
            self.setup_kyotaku(record)
            self.setup_honba(record)
            self.setup_bakaze(record)

    def setup_players(self, record) :
        assert "start_game" == record["type"], "record type must be start_game."
        self.players = []
        for id, name in enumerate(record["names"]) :
            player = Player2Vec(id)
            self.players.append(player)
    
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

    def dump(self) :
        return self.game_elem

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filename")
    args = parser.parse_args()
    
    filename = args.mjson_filename
    
    mj2vec = Mj2Vec()
    records = load_mjai_records(filename)
    for record in records :
        mj2vec.action(record)
    print("dump:", mj2vec.dump())

if __name__ == '__main__':
    main()
