"""
 mj2vec
"""
import json
import argparse
from mjlegal.game_state import GameState
from mjlegal.player_state import PlayerState
from mjlegal.possible_action import PossibleActionGenerator
from mjlegal.mjai import MjaiLoader
from mjlegal.mjtypes import Tile, TilesUtil
from mjlegal.mjtypes import ActionType
from mjlegal.action import Action
from mjlegal.mjai_possible_action import MjaiPossibleActionGenerator

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

class Mj2Vec :
    def __init__(self) :
        self.mjlegal_client = MjaiLoader()

    def action(self, record) :
        self.mjlegal_client.action(record)

    def to_sparse(self) :
        pass
    

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filename")
    args = parser.parse_args()
    
    filename = args.mjson_filename
    
    mj2vec = Mj2Vec()
    records = load_mjai_records(filename)
    for record in records :
        mj2vec.action(record)

if __name__ == '__main__':
    main()
